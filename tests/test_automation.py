from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
CLI = SKILL_ROOT / "scripts" / "ckb.py"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from ckb_core.automation import (
    SUPPORTED_HARNESSES,
    activate_skill_session,
    automation_status,
    drain_automation,
    enqueue_event,
    ingest_event,
    normalize_event,
    pending_automation_reviews,
    register_project,
    retry_failed_automation,
    review_automation,
    search_automation,
    write_automation_review_template,
)
from ckb_core.automation_integrations import render_integration
from ckb_core.common import CkbError
from ckb_core.machine_knowledge import change_documents, retrieve_machine
from ckb_core.obsidian import NOTE_DIRECTORIES


def git(repo: Path, *args: str) -> None:
    completed = subprocess.run(["git", "-C", str(repo), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        raise RuntimeError(completed.stderr)


class AutomationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-automation-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.output = self.root / "knowledge"
        self.registry = self.root / "registry.json"
        self.repo.mkdir()
        self.output.mkdir()
        (self.repo / "app.py").write_text("def value():\n    return 1\n", encoding="utf-8")
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "initial")
        (self.output / "state.json").write_text(
            json.dumps(
                {
                    "schema_version": 4,
                    "status": "complete",
                    "repository": {"root": str(self.repo), "commit": "fixture"},
                    "source_snapshot": {"root": str(self.repo), "status": "snapshot-ready"},
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def register(self, *harnesses: str) -> None:
        result = register_project(self.repo, self.output, self.registry, list(harnesses) or None)
        self.assertEqual(result["status"], "registered")

    def event(self, name: str, **values: object) -> dict[str, object]:
        skill_applied = bool(values.pop("_skill_applied", True))
        event = {
            "session_id": "session-1",
            "cwd": str(self.repo),
            "hook_event_name": name,
            **values,
        }
        if skill_applied:
            event["applied_skills"] = ["code-knowledge-builder"]
        return event

    def test_project_opt_in_and_hook_output(self) -> None:
        ignored = ingest_event("codex", self.event("SessionStart", source="startup"), self.registry)
        self.assertEqual(ignored["status"], "ignored")
        self.assertEqual(ignored["hook_output"], {})
        self.register("codex")
        recorded = ingest_event("codex", self.event("SessionStart", source="startup"), self.registry)
        self.assertEqual(recorded["status"], "recorded")
        self.assertEqual(recorded["canonical_type"], "session.start")
        self.assertEqual(automation_status(self.output)["events"], 1)

    def test_registered_session_stays_idle_until_skill_is_explicitly_applied(self) -> None:
        self.register("codex")
        ignored_start = ingest_event(
            "codex",
            self.event("SessionStart", source="startup", _skill_applied=False),
            self.registry,
        )
        self.assertEqual(ignored_start["status"], "ignored")
        self.assertEqual(ignored_start["reason"], "skill-not-applied-in-session")
        self.assertEqual(ignored_start["hook_output"], {})
        mention_only = ingest_event(
            "codex",
            self.event(
                "UserPromptSubmit",
                turn_id="turn-1",
                prompt="讨论 code-knowledge-builder 的设计，但本轮只做普通问答。",
                _skill_applied=False,
            ),
            self.registry,
        )
        self.assertEqual(mention_only["status"], "ignored")
        before = automation_status(self.output)
        self.assertEqual(before["skill_activations"], 0)
        self.assertEqual(before["events"], 0)
        explicit = ingest_event(
            "codex",
            self.event(
                "UserPromptSubmit",
                turn_id="turn-1",
                prompt="$code-knowledge-builder 扫描当前项目并维护知识库。",
                _skill_applied=False,
            ),
            self.registry,
        )
        self.assertEqual(explicit["status"], "recorded")
        after = automation_status(self.output)
        self.assertEqual(after["skill_activations"], 1)
        self.assertEqual(after["events"], 1)
        other_session = ingest_event(
            "codex",
            {
                "session_id": "session-other",
                "cwd": str(self.repo),
                "hook_event_name": "PostToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": "app.py"},
            },
            self.registry,
        )
        self.assertEqual(other_session["reason"], "skill-not-applied-in-session")

    def test_agent_activation_command_uses_harness_session_and_workspace(self) -> None:
        self.register("codex")
        activated = activate_skill_session("codex", "agent-session", self.repo, self.registry)
        self.assertEqual(activated["status"], "activated")
        repeated = activate_skill_session("codex", "agent-session", self.repo, self.registry)
        self.assertEqual(repeated["status"], "already-activated")
        recorded = ingest_event(
            "codex",
            {
                "session_id": "agent-session",
                "cwd": str(self.repo),
                "hook_event_name": "PostToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": "app.py"},
            },
            self.registry,
        )
        self.assertEqual(recorded["status"], "recorded")

    def test_redaction_idempotency_change_capture_and_pending_review(self) -> None:
        self.register("codex")
        ingest_event("codex", self.event("SessionStart", source="startup"), self.registry)
        prompt = self.event(
            "UserPromptSubmit",
            turn_id="turn-1",
            prompt="修改 app.py，api_key=secret-value-12345，token=plain-token-67890",
        )
        first = ingest_event("codex", prompt, self.registry)
        duplicate = ingest_event("codex", prompt, self.registry)
        self.assertEqual(first["status"], "recorded")
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertGreater(first["redaction_count"], 0)
        (self.repo / "app.py").write_text("def value():\n    return 2\n", encoding="utf-8")
        ingest_event(
            "codex",
            self.event(
                "PostToolUse",
                turn_id="turn-1",
                tool_name="apply_patch",
                tool_use_id="tool-1",
                tool_input={"command": "*** Update File: app.py"},
                tool_response={"status": "ok"},
            ),
            self.registry,
        )
        ingest_event(
            "codex",
            self.event(
                "Stop",
                turn_id="turn-1",
                last_assistant_message="已经修改 app.py，并执行验证。",
                stop_hook_active=False,
            ),
            self.registry,
        )
        # A retried Stop maps to the completed turn and remains idempotent.
        retried = ingest_event(
            "codex",
            self.event(
                "Stop",
                turn_id="turn-1",
                last_assistant_message="已经修改 app.py，并执行验证。",
                stop_hook_active=False,
            ),
            self.registry,
        )
        self.assertEqual(retried["status"], "duplicate")
        status = automation_status(self.output)
        self.assertEqual(status["events"], 4)
        self.assertEqual(status["turns"], 1)
        self.assertEqual(status["pending_reviews"], 1)
        pending = pending_automation_reviews(self.output)["reviews"]
        self.assertEqual(pending[0]["changed_paths"], ["app.py"])
        connection = sqlite3.connect(self.output / "machine/automation.sqlite")
        payloads = "\n".join(row[0] for row in connection.execute("SELECT payload_json FROM events"))
        connection.close()
        self.assertNotIn("secret-value-12345", payloads)
        self.assertNotIn("plain-token-67890", payloads)
        self.assertIn("[REDACTED:CREDENTIAL]", payloads)

    def test_claude_without_turn_ids_allows_repeated_prompt_after_completion(self) -> None:
        self.register("claude")
        ingest_event("claude", self.event("SessionStart", source="startup"), self.registry)
        prompt = self.event("UserPromptSubmit", prompt="重复执行同一个检查")
        ingest_event("claude", prompt, self.registry)
        ingest_event("claude", self.event("Stop", last_assistant_message="第一次检查完成。"), self.registry)
        ingest_event("claude", prompt, self.registry)
        ingest_event("claude", self.event("Stop", last_assistant_message="第二次检查完成。"), self.registry)
        status = automation_status(self.output)
        self.assertEqual(status["turns"], 2)
        self.assertEqual(status["pending_reviews"], 2)

    def test_stop_detects_further_change_to_file_dirty_at_session_start(self) -> None:
        self.register("codex")
        (self.repo / "app.py").write_text("def value():\n    return 2\n", encoding="utf-8")
        ingest_event("codex", self.event("SessionStart", source="startup"), self.registry)
        ingest_event(
            "codex",
            self.event("UserPromptSubmit", turn_id="turn-1", prompt="继续修改已经处于 dirty 状态的 app.py"),
            self.registry,
        )
        # Simulate a shell/external writer that produces no path-bearing tool event.
        (self.repo / "app.py").write_text("def value():\n    return 3\n", encoding="utf-8")
        ingest_event(
            "codex",
            self.event("Stop", turn_id="turn-1", last_assistant_message="已继续修改 app.py。", stop_hook_active=False),
            self.registry,
        )
        pending = pending_automation_reviews(self.output)["reviews"]
        self.assertEqual(pending[0]["changed_paths"], ["app.py"])

    def test_nested_untracked_project_bounds_git_status_and_uses_project_relative_paths(self) -> None:
        outer = self.root / "outer"
        nested = outer / "nested-project"
        output = self.root / "nested-knowledge"
        registry = self.root / "nested-registry.json"
        nested.mkdir(parents=True)
        output.mkdir()
        (outer / "README.md").write_text("outer repository\n", encoding="utf-8")
        (nested / "app.py").write_text("def value():\n    return 1\n", encoding="utf-8")
        (nested / "__pycache__").mkdir()
        (nested / "__pycache__/app.pyc").write_bytes(b"generated cache")
        git(outer, "init")
        git(outer, "config", "user.email", "fixture@example.invalid")
        git(outer, "config", "user.name", "Fixture")
        git(outer, "add", "README.md")
        git(outer, "commit", "-m", "outer baseline")
        (output / "state.json").write_text(
            json.dumps(
                {
                    "schema_version": 4,
                    "status": "complete",
                    "repository": {"root": str(nested), "commit": "fixture"},
                    "source_snapshot": {"root": str(nested), "status": "snapshot-ready"},
                }
            ),
            encoding="utf-8",
        )
        register_project(nested, output, registry, ["generic"])
        ingest_event(
            "generic",
            {"canonical_type": "session.start", "skill_name": "code-knowledge-builder", "ckb_skill_applied": True, "event_id": "nested-start", "session_id": "nested", "cwd": str(nested)},
            registry,
        )
        connection = sqlite3.connect(output / "machine/automation.sqlite")
        baseline_paths = json.loads(connection.execute("SELECT baseline_paths_json FROM sessions").fetchone()[0])
        connection.close()
        self.assertEqual(baseline_paths, ["app.py"])
        ingest_event(
            "generic",
            {
                "canonical_type": "turn.prompt",
                "event_id": "nested-prompt",
                "session_id": "nested",
                "turn_id": "turn-1",
                "cwd": str(nested),
                "prompt": "继续修改嵌套项目中的 app.py",
            },
            registry,
        )
        (nested / "app.py").write_text("def value():\n    return 2\n", encoding="utf-8")
        ingest_event(
            "generic",
            {
                "canonical_type": "turn.stop",
                "event_id": "nested-stop",
                "session_id": "nested",
                "turn_id": "turn-1",
                "cwd": str(nested),
                "assistant_message": "已完成嵌套项目文件修改。",
            },
            registry,
        )
        pending = pending_automation_reviews(output)["reviews"]
        self.assertEqual(pending[0]["changed_paths"], ["app.py"])

    def test_workspace_root_maps_parent_task_to_nested_repository(self) -> None:
        workspace = self.root / "workspace"
        repo = workspace / "source"
        output = workspace / "knowledge"
        scratch = workspace / "work"
        registry = self.root / "workspace-registry.json"
        repo.mkdir(parents=True)
        output.mkdir()
        scratch.mkdir()
        (repo / "app.py").write_text("def value():\n    return 1\n", encoding="utf-8")
        git(repo, "init")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "user.name", "Fixture")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "initial")
        (output / "state.json").write_text(
            json.dumps({"schema_version": 4, "status": "complete", "repository": {"root": str(repo), "commit": "fixture"}}),
            encoding="utf-8",
        )
        registered = register_project(repo, output, registry, ["generic"], workspace_roots=[workspace])
        self.assertEqual(registered["project"]["workspace_roots"], [str(workspace.resolve())])
        start = ingest_event(
            "generic",
            {"canonical_type": "session.start", "skill_name": "code-knowledge-builder", "ckb_skill_applied": True, "event_id": "start", "session_id": "workspace", "cwd": str(workspace)},
            registry,
        )
        self.assertEqual(start["registration_match"]["kind"], "workspace")
        ingest_event(
            "generic",
            {
                "canonical_type": "turn.prompt",
                "event_id": "prompt",
                "session_id": "workspace",
                "turn_id": "turn-1",
                "cwd": str(workspace),
                "prompt": "修改 source/app.py",
            },
            registry,
        )
        (repo / "app.py").write_text("def value():\n    return 2\n", encoding="utf-8")
        ingest_event(
            "generic",
            {
                "canonical_type": "tool.result",
                "event_id": "tool",
                "session_id": "workspace",
                "turn_id": "turn-1",
                "cwd": str(workspace),
                "changed_paths": ["source/app.py", "work/probe.py"],
                "tool_name": "write",
            },
            registry,
        )
        ingest_event(
            "generic",
            {
                "canonical_type": "turn.stop",
                "event_id": "stop",
                "session_id": "workspace",
                "turn_id": "turn-1",
                "cwd": str(workspace),
                "assistant_message": "已经完成源码修改。",
            },
            registry,
        )
        pending = pending_automation_reviews(output)["reviews"]
        self.assertEqual(pending[0]["changed_paths"], ["app.py"])

    def test_version_one_registry_is_read_compatibly(self) -> None:
        self.registry.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "projects": [
                        {
                            "registration_id": "legacy",
                            "enabled": True,
                            "repo_root": str(self.repo),
                            "knowledge_output": str(self.output),
                            "harnesses": ["generic"],
                            "max_field_chars": 12000,
                            "custom_redactions": [],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        result = ingest_event(
            "generic",
            {"canonical_type": "session.start", "skill_name": "code-knowledge-builder", "ckb_skill_applied": True, "event_id": "legacy-start", "session_id": "legacy", "cwd": str(self.repo)},
            self.registry,
        )
        self.assertEqual(result["status"], "recorded")

    def test_version_two_registry_upgrades_to_session_activation_contract(self) -> None:
        self.registry.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "projects": [
                        {
                            "registration_id": "legacy-v2",
                            "enabled": True,
                            "repo_root": str(self.repo),
                            "knowledge_output": str(self.output),
                            "workspace_roots": [],
                            "harnesses": ["generic"],
                            "max_field_chars": 12000,
                            "custom_redactions": [],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        ignored = ingest_event(
            "generic",
            {"canonical_type": "session.start", "event_id": "v2-idle", "session_id": "legacy-v2", "cwd": str(self.repo)},
            self.registry,
        )
        self.assertEqual(ignored["reason"], "skill-not-applied-in-session")
        activated = ingest_event(
            "generic",
            {
                "canonical_type": "skill.applied",
                "event_id": "v2-activate",
                "session_id": "legacy-v2",
                "cwd": str(self.repo),
                "skill_name": "code-knowledge-builder",
                "ckb_skill_applied": True,
            },
            self.registry,
        )
        self.assertEqual(activated["status"], "recorded")

    def test_opencode_and_generic_normalization(self) -> None:
        user = normalize_event(
            "opencode",
            {
                "type": "message.updated",
                "cwd": str(self.repo),
                "properties": {"info": {"sessionID": "open-1", "role": "user", "parts": [{"text": "分析模块"}]}},
            },
        )
        self.assertEqual(user["canonical_type"], "turn.prompt")
        self.assertEqual(user["prompt"], "分析模块")
        tool = normalize_event(
            "generic",
            {
                "canonical_type": "tool.result",
                "session_id": "generic-1",
                "turn_id": "turn-1",
                "cwd": str(self.repo),
                "tool_name": "write",
                "changed_paths": ["app.py"],
            },
        )
        self.assertEqual(tool["changed_paths"], ["app.py"])
        skill = normalize_event(
            "generic",
            {
                "canonical_type": "skill.applied",
                "session_id": "generic-1",
                "cwd": str(self.repo),
                "skill_name": "code-knowledge-builder",
                "ckb_skill_applied": True,
            },
        )
        self.assertEqual(skill["canonical_type"], "skill.applied")
        self.assertEqual(skill["skill_name"], "code-knowledge-builder")
        claude_expansion = normalize_event(
            "claude",
            {
                "hook_event_name": "UserPromptExpansion",
                "session_id": "claude-skill",
                "cwd": str(self.repo),
                "command_name": "code-knowledge-builder",
                "prompt": "/code-knowledge-builder 扫描项目",
            },
        )
        self.assertEqual(claude_expansion["canonical_type"], "skill.applied")
        self.assertEqual(claude_expansion["skill_name"], "code-knowledge-builder")

    def test_gemini_copilot_and_cursor_normalization(self) -> None:
        gemini_prompt = normalize_event(
            "gemini",
            {"hook_event_name": "BeforeAgent", "session_id": "gemini-1", "cwd": str(self.repo), "prompt": "分析模块"},
        )
        self.assertEqual(gemini_prompt["canonical_type"], "turn.prompt")
        gemini_stop = normalize_event(
            "gemini",
            {"hook_event_name": "AfterAgent", "session_id": "gemini-1", "cwd": str(self.repo), "prompt_response": "分析完成。"},
        )
        self.assertEqual(gemini_stop["assistant_message"], "分析完成。")
        copilot_tool = normalize_event(
            "copilot",
            {
                "hook_event_name": "PostToolUse",
                "session_id": "copilot-1",
                "cwd": str(self.repo),
                "tool_name": "Edit",
                "tool_input": {"file_path": "app.py"},
                "tool_result": {"result_type": "success", "text_result_for_llm": "done"},
            },
        )
        self.assertEqual(copilot_tool["canonical_type"], "tool.result")
        self.assertEqual(copilot_tool["changed_paths"], ["app.py"])
        cursor_file = normalize_event(
            "cursor",
            {"type": "afterFileEdit", "conversation_id": "cursor-1", "cwd": str(self.repo), "file_path": str(self.repo / "app.py")},
        )
        self.assertEqual(cursor_file["canonical_type"], "file.changed")
        self.assertEqual(cursor_file["session_id"], "cursor-1")

    def test_concurrent_hooks_are_serialized_without_event_loss(self) -> None:
        self.register("generic")
        ingest_event(
            "generic",
            {"canonical_type": "session.start", "skill_name": "code-knowledge-builder", "ckb_skill_applied": True, "event_id": "start", "session_id": "parallel", "cwd": str(self.repo)},
            self.registry,
        )
        events = [
            {
                "canonical_type": "tool.result",
                "event_id": f"event-{index}",
                "session_id": "parallel",
                "turn_id": "turn-1",
                "cwd": str(self.repo),
                "tool_name": "write",
                "tool_use_id": f"tool-{index}",
                "changed_paths": ["app.py"],
            }
            for index in range(16)
        ]
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda item: ingest_event("generic", item, self.registry), events))
        drain_automation(self.output)
        status = automation_status(self.output)
        self.assertEqual(status["events"], 17)
        self.assertEqual(status["pending_spool"], 0)
        self.assertEqual(status["failed_spool"], 0)

    def test_failed_spool_is_retained_and_retryable(self) -> None:
        self.register("generic")
        enqueue_event(self.output, {"schema_version": 1, "repo_root": str(self.repo), "event": {"broken": True}})
        failed = drain_automation(self.output)
        self.assertEqual(failed["failed"], 1)
        self.assertEqual(automation_status(self.output)["failed_spool"], 1)
        retried = retry_failed_automation(self.output)
        self.assertEqual(retried["retried"], 1)
        self.assertEqual(retried["drain"]["failed"], 1)

    def _prepare_human_projection(self) -> None:
        entity_id = "file-app"
        entity = {
            "id": entity_id,
            "name": "app.py",
            "qualified_name": "app.py",
            "kind": "file",
            "path": "app.py",
            "range": {"start_line": 1, "end_line": 2},
        }
        (self.output / "graph.json").write_text(json.dumps({"entities": [entity]}), encoding="utf-8")
        projection = {
            "schema_version": 1,
            "pages": [{"id": entity_id, "title": "app.py 代码导览", "file": "pages/app.py 代码导览.md", "page_type": "repository"}],
            "entity_owner_pages": {entity_id: entity_id},
        }
        for root_name in ("markdown", "human"):
            root = self.output / root_name
            root.mkdir()
            (root / "projection.json").write_text(json.dumps(projection), encoding="utf-8")
            for directory in NOTE_DIRECTORIES:
                (root / directory).mkdir()

    def test_agent_review_promotes_one_chinese_human_note(self) -> None:
        self._prepare_human_projection()
        self.register("generic")
        ingest_event(
            "generic",
            {"canonical_type": "session.start", "skill_name": "code-knowledge-builder", "ckb_skill_applied": True, "event_id": "start", "session_id": "review", "cwd": str(self.repo)},
            self.registry,
        )
        ingest_event(
            "generic",
            {
                "canonical_type": "turn.prompt",
                "event_id": "prompt",
                "session_id": "review",
                "turn_id": "turn-1",
                "cwd": str(self.repo),
                "prompt": "修改 app.py",
            },
            self.registry,
        )
        (self.repo / "app.py").write_text("def value():\n    return 3\n", encoding="utf-8")
        ingest_event(
            "generic",
            {
                "canonical_type": "tool.result",
                "event_id": "tool",
                "session_id": "review",
                "turn_id": "turn-1",
                "cwd": str(self.repo),
                "tool_name": "write",
                "tool_use_id": "tool-1",
                "changed_paths": ["app.py"],
            },
            self.registry,
        )
        ingest_event(
            "generic",
            {
                "canonical_type": "turn.stop",
                "event_id": "stop",
                "session_id": "review",
                "turn_id": "turn-1",
                "cwd": str(self.repo),
                "assistant_message": "修改已经完成。",
            },
            self.registry,
        )
        review_id = pending_automation_reviews(self.output)["reviews"][0]["review_id"]
        template_path = self.root / "review-template.json"
        template = write_automation_review_template(self.output, review_id, template_path)
        self.assertEqual(template["changed_paths"], ["app.py"])
        body = self.root / "review.md"
        body.write_text(
            "## 修改内容\n\n调整 app.py 的返回值。\n\n"
            "## 修改原因\n\n用于验证自动化记录经过 Agent 审阅后再进入人类知识库。\n\n"
            "## 验证结果\n\n已核对源码范围和自动化事件证据。\n",
            encoding="utf-8",
        )
        bad_review = self.root / "bad-review.json"
        bad_review.write_text(
            json.dumps(
                {
                    "review_id": review_id,
                    "status": "agent-reviewed",
                    "kind": "change",
                    "title": "错误审阅",
                    "body": str(body),
                    "evidence_note": "已经检查，但缺少逐路径证据。",
                    "source_checks": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        with self.assertRaises(CkbError):
            review_automation(self.output, bad_review)
        review = self.root / "review.json"
        review.write_text(
            json.dumps(
                {
                    "review_id": review_id,
                    "status": "agent-reviewed",
                    "kind": "change",
                    "title": "app.py 自动化修改记录",
                    "body": str(body),
                    "evidence_note": "重新打开 app.py 并核对自动化事件、工作树变化和验证说明。",
                    "source_checks": [
                        {
                            "path": "app.py",
                            "status": "agent-reviewed",
                            "evidence_note": "已重新打开 app.py，确认返回值修改与会话说明一致。",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        result = review_automation(self.output, review)
        self.assertEqual(result["status"], "agent-reviewed")
        human = self.output / "human/changes/app.py 自动化修改记录.md"
        markdown = self.output / "markdown/changes/app.py 自动化修改记录.md"
        self.assertTrue(human.is_file())
        self.assertEqual(human.read_bytes(), markdown.read_bytes())
        self.assertIn("[[app.py 代码导览]]", human.read_text(encoding="utf-8"))
        self.assertEqual(pending_automation_reviews(self.output)["count"], 0)

    def test_render_all_harness_integrations(self) -> None:
        for harness in sorted(SUPPORTED_HARNESSES):
            destination = self.root / "integrations" / harness
            result = render_integration(harness, destination, Path(sys.executable), CLI, self.registry)
            self.assertEqual(result["status"], "rendered")
            manifest = json.loads((destination / "integration.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["project_opt_in_required"])
            self.assertFalse(manifest["transcript_parsing"])
            for relative in manifest["files"]:
                self.assertTrue((destination / relative).is_file(), relative)
        codex = json.loads((self.root / "integrations/codex/hooks/hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(set(codex["hooks"]), {"SessionStart", "UserPromptSubmit", "PostToolUse", "Stop", "PreCompact", "PostCompact", "SessionEnd"})
        dsh = json.loads((self.root / "integrations/dsh/hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(set(dsh["hooks"]), {"SessionStart", "UserPromptSubmit", "PostToolUse", "Stop"})
        self.assertNotIn("{{", (self.root / "integrations/opencode/.opencode/plugins/code-knowledge-builder-sync.mjs").read_text(encoding="utf-8"))
        opencode_v2 = (self.root / "integrations/opencode-v2/.opencode/plugins/code-knowledge-builder-sync-v2.mjs").read_text(encoding="utf-8")
        self.assertIn('ctx.session.hook("context"', opencode_v2)
        self.assertNotIn('@opencode-ai/plugin/v2', opencode_v2)
        gemini = json.loads((self.root / "integrations/gemini/.gemini/settings.json").read_text(encoding="utf-8"))
        self.assertEqual(set(gemini["hooks"]), {"SessionStart", "BeforeAgent", "AfterTool", "AfterAgent", "PreCompress", "SessionEnd"})
        copilot = json.loads((self.root / "integrations/copilot/.github/hooks/code-knowledge-builder.json").read_text(encoding="utf-8"))
        self.assertEqual(copilot["version"], 1)
        self.assertIn("powershell", copilot["hooks"]["SessionStart"][0])
        cursor = json.loads((self.root / "integrations/cursor/.cursor/hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(cursor["version"], 1)
        self.assertIn("afterFileEdit", cursor["hooks"])
        claude = json.loads((self.root / "integrations/claude/.claude/settings.json").read_text(encoding="utf-8"))
        self.assertIn("UserPromptExpansion", claude["hooks"])
        self.assertEqual(claude["hooks"]["PreToolUse"][0]["matcher"], "Skill")
        for harness in sorted(SUPPORTED_HARNESSES):
            manifest = json.loads((self.root / "integrations" / harness / "integration.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["session_skill_activation_required"])
            self.assertEqual(manifest["required_skill"], "code-knowledge-builder")

    def test_automation_fts_finds_pending_machine_record(self) -> None:
        self.register("generic")
        ingest_event(
            "generic",
            {"canonical_type": "turn.prompt", "event_id": "p", "session_id": "fts", "turn_id": "t", "cwd": str(self.repo), "prompt": "$code-knowledge-builder 实现会话自动化更新"},
            self.registry,
        )
        ingest_event(
            "generic",
            {"canonical_type": "turn.stop", "event_id": "s", "session_id": "fts", "turn_id": "t", "cwd": str(self.repo), "assistant_message": "已经形成自动化记录。"},
            self.registry,
        )
        matches = search_automation(self.output, "会话自动化", 8)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["status"], "pending-agent-review")

    def test_machine_retrieval_and_changes_include_pending_automation(self) -> None:
        self.register("generic")
        ingest_event(
            "generic",
            {"canonical_type": "turn.prompt", "event_id": "p", "session_id": "machine", "turn_id": "t", "cwd": str(self.repo), "prompt": "$code-knowledge-builder 实现会话自动化更新"},
            self.registry,
        )
        ingest_event(
            "generic",
            {"canonical_type": "turn.stop", "event_id": "s", "session_id": "machine", "turn_id": "t", "cwd": str(self.repo), "assistant_message": "已经形成自动化记录。"},
            self.registry,
        )
        database = self.output / "machine/knowledge.sqlite"
        connection = sqlite3.connect(database)
        connection.executescript(
            """
            CREATE TABLE entities(entity_id TEXT PRIMARY KEY,name TEXT,qualified_name TEXT,source_path TEXT);
            CREATE TABLE terms(term TEXT,entity_id TEXT,weight REAL);
            CREATE TABLE documents(document_id TEXT PRIMARY KEY,kind TEXT,title TEXT,tag TEXT,human_file TEXT,source_entity_id TEXT,content TEXT,token_estimate INTEGER);
            CREATE TABLE relations(source_entity_id TEXT,target_entity_id TEXT,weight REAL);
            CREATE VIRTUAL TABLE entity_fts USING fts5(entity_id UNINDEXED,name,qualified_name,meaning_zh,role_zh,change_when_zh,description_zh,source_path,tokenize='trigram');
            CREATE VIRTUAL TABLE section_fts USING fts5(section_id UNINDEXED,document_id UNINDEXED,heading,content,source_path,tokenize='trigram');
            CREATE VIRTUAL TABLE source_fts USING fts5(source_path UNINDEXED,content,tokenize='trigram');
            """
        )
        connection.commit()
        connection.close()
        retrieved = retrieve_machine(self.output, "会话自动化", 1000, 4, "fast")
        self.assertEqual(retrieved["status"], "passed")
        self.assertEqual(retrieved["selected_entities"], [])
        self.assertTrue(retrieved["pending_agent_review"])
        self.assertEqual(retrieved["related_documents"][0]["status"], "pending-agent-review")
        changes = change_documents(self.output, "session", 20)
        self.assertEqual(changes["status"], "passed")
        self.assertTrue(any(item.get("status") == "pending-agent-review" for item in changes["documents"]))


if __name__ == "__main__":
    unittest.main()
