from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.common import CkbError
from ckb_core.management_agent import (
    MANAGEMENT_CAPABILITIES,
    _audit_event,
    _locked_registry,
    audit_manager_registry,
    bind_conversation,
    binding_schema,
    binding_status,
    canonical_binding_input,
    create_management_task,
    harness_capabilities,
    management_context,
    management_task_status,
    review_management_task,
    unbind_conversation,
)


def git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr)
    return completed.stdout.strip()


class ManagementSchemaPersistenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-manager-")
        self.root = Path(self.temporary.name)
        self.registry = self.root / "manager.json"
        for name in ("workspace", "workspace/repo", "workspace/knowledge"):
            (self.root / name).mkdir(exist_ok=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def payload(self, **values: object) -> dict[str, object]:
        return {
            "schema_version": 1,
            "conversation_id": "conversation-fixture",
            "harness_id": "generic",
            "workspace_root": str(self.root / "workspace"),
            "repo_root": str(self.root / "workspace/repo"),
            "knowledge_base": str(self.root / "workspace/knowledge"),
            "integration_branch": "main",
            **values,
        }

    def test_public_schema_has_four_separate_capabilities_and_privacy_contract(self) -> None:
        schema = binding_schema()
        capability_fields = schema["properties"]["capabilities"]["properties"]
        self.assertEqual(set(capability_fields), set(MANAGEMENT_CAPABILITIES))
        self.assertFalse(schema["privacy"]["raw_conversation_content"])
        self.assertFalse(schema["privacy"]["credentials"])
        self.assertIn("transcript_path", schema["privacy"]["forbidden_fields"])

    def test_canonical_input_drops_unrecognized_sensitive_content(self) -> None:
        canonical, ignored = canonical_binding_input(
            self.payload(
                prompt="do not persist this prompt",
                secret="fixture-secret-value",
                transcript_path="/private/transcript.jsonl",
                arbitrary={"token": "nested-secret"},
            )
        )
        serialized = json.dumps(canonical, ensure_ascii=False)
        self.assertEqual(ignored, ["arbitrary", "prompt", "secret", "transcript_path"])
        self.assertNotIn("do not persist", serialized)
        self.assertNotIn("fixture-secret", serialized)
        self.assertNotIn("transcript", serialized)
        self.assertNotIn("nested-secret", serialized)

    def test_unknown_harness_declares_only_generic_binding(self) -> None:
        capabilities = harness_capabilities("unknown-harness")
        self.assertTrue(capabilities["binding"]["available"])
        self.assertFalse(capabilities["prompt_injection"]["available"])
        self.assertFalse(capabilities["event_sync"]["available"])
        self.assertFalse(capabilities["task_dispatch"]["available"])

    def test_malformed_registry_is_reported_without_replacement(self) -> None:
        original = b'{"schema_version": 99, "prompt": "private"}\n'
        self.registry.write_bytes(original)
        result = audit_manager_registry(self.registry)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.registry.read_bytes(), original)

    def test_locked_registry_serializes_concurrent_audit_events(self) -> None:
        def append(index: int) -> None:
            with _locked_registry(self.registry) as (_path, value):
                value["audit_log"].append(_audit_event(None, "fixture", "passed", f"event-{index}"))

        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(append, range(24)))
        stored = json.loads(self.registry.read_text(encoding="utf-8"))
        self.assertEqual(len(stored["audit_log"]), 24)
        self.assertEqual(audit_manager_registry(self.registry)["status"], "passed")

    def test_canonical_input_rejects_missing_identity(self) -> None:
        payload = self.payload()
        del payload["conversation_id"]
        with self.assertRaises(CkbError):
            canonical_binding_input(payload)


class ManagementBindingLifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-manager-lifecycle-")
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "workspace"
        self.repo = self.workspace / "repo"
        self.output = self.workspace / "knowledge"
        self.registry = self.root / "manager.json"
        self.repo.mkdir(parents=True)
        self.output.mkdir()
        (self.repo / "app.py").write_text("def value():\n    return 1\n", encoding="utf-8")
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "initial")
        git(self.repo, "checkout", "-b", "integration")
        (self.output / "state.json").write_text(
            json.dumps(
                {
                    "schema_version": 4,
                    "status": "complete",
                    "repository": {"root": str(self.repo), "commit": git(self.repo, "rev-parse", "HEAD")},
                    "source_snapshot": {"root": str(self.repo), "status": "snapshot-ready"},
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def payload(self, conversation: str = "conversation-fixture", **values: object) -> dict[str, object]:
        return {
            "schema_version": 1,
            "conversation_id": conversation,
            "harness_id": "generic",
            "workspace_root": str(self.workspace),
            "repo_root": str(self.repo),
            "knowledge_base": str(self.output),
            "integration_branch": "integration",
            **values,
        }

    def test_bind_is_idempotent_status_is_live_and_unbind_preserves_audit(self) -> None:
        first = bind_conversation(
            self.payload(prompt="private-prompt", secret="private-secret", transcript_path="private.jsonl"),
            self.registry,
        )
        second = bind_conversation(self.payload(), self.registry)
        self.assertEqual(first["status"], "bound")
        self.assertEqual(second["status"], "already-bound")
        self.assertEqual(first["binding"]["binding_id"], second["binding"]["binding_id"])
        self.assertEqual(binding_status("conversation-fixture", "generic", self.registry)["status"], "ready")
        serialized = self.registry.read_text(encoding="utf-8")
        self.assertNotIn("private-prompt", serialized)
        self.assertNotIn("private-secret", serialized)
        self.assertNotIn("private.jsonl", serialized)
        removed = unbind_conversation("conversation-fixture", "generic", self.registry)
        repeated = unbind_conversation("conversation-fixture", "generic", self.registry)
        self.assertEqual(removed["status"], "unbound")
        self.assertEqual(repeated["status"], "already-unbound")
        self.assertEqual(binding_status("conversation-fixture", "generic", self.registry)["status"], "unbound")
        audit = audit_manager_registry(self.registry)
        self.assertEqual(audit["status"], "passed")
        self.assertEqual(audit["active_bindings"], 0)
        self.assertGreaterEqual(audit["audit_events"], 2)

    def test_conflicting_project_for_same_conversation_fails_without_rebinding(self) -> None:
        original = bind_conversation(self.payload(), self.registry)
        other_repo = self.workspace / "other-repo"
        other_output = self.workspace / "other-knowledge"
        other_repo.mkdir()
        other_output.mkdir()
        (other_repo / "other.py").write_text("value = 1\n", encoding="utf-8")
        git(other_repo, "init")
        git(other_repo, "config", "user.email", "fixture@example.invalid")
        git(other_repo, "config", "user.name", "Fixture")
        git(other_repo, "add", ".")
        git(other_repo, "commit", "-m", "initial")
        git(other_repo, "checkout", "-b", "integration")
        (other_output / "state.json").write_text("{}\n", encoding="utf-8")
        with self.assertRaises(CkbError):
            bind_conversation(
                self.payload(repo_root=str(other_repo), knowledge_base=str(other_output)),
                self.registry,
            )
        current = binding_status("conversation-fixture", "generic", self.registry)
        self.assertEqual(current["binding"]["binding_id"], original["binding"]["binding_id"])
        self.assertEqual(Path(current["binding"]["repo_root"]), self.repo.resolve())

    def test_missing_repo_output_branch_and_dirty_tree_fail_preflight(self) -> None:
        with self.assertRaisesRegex(CkbError, "repository does not exist"):
            bind_conversation(self.payload("missing-repo", repo_root=str(self.workspace / "absent")), self.registry)
        with self.assertRaisesRegex(CkbError, "knowledge base does not exist"):
            bind_conversation(self.payload("missing-output", knowledge_base=str(self.workspace / "absent-out")), self.registry)
        with self.assertRaisesRegex(CkbError, "branch mismatch"):
            bind_conversation(self.payload("wrong-branch", integration_branch="absent"), self.registry)
        (self.repo / "app.py").write_text("def value():\n    return 2\n", encoding="utf-8")
        with self.assertRaisesRegex(CkbError, "must be clean"):
            bind_conversation(self.payload("dirty"), self.registry)
        self.assertEqual(audit_manager_registry(self.registry)["status"], "passed")

    def test_status_detects_head_drift_and_dirty_tree_after_binding(self) -> None:
        bind_conversation(self.payload(), self.registry)
        (self.repo / "second.py").write_text("value = 2\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "drift")
        drift = binding_status("conversation-fixture", "generic", self.registry)
        self.assertEqual(drift["status"], "blocked")
        self.assertIn("integration-head-drift", drift["blockers"])
        (self.repo / "app.py").write_text("def value():\n    return 3\n", encoding="utf-8")
        dirty = binding_status("conversation-fixture", "generic", self.registry)
        self.assertIn("integration-worktree-dirty", dirty["blockers"])

    def test_concurrent_repeated_bind_and_unbind_have_one_active_object(self) -> None:
        def bind(_index: int) -> str:
            return bind_conversation(self.payload(), self.registry)["status"]

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(bind, range(20)))
        self.assertEqual(results.count("bound"), 1)
        self.assertEqual(results.count("already-bound"), 19)
        stored = json.loads(self.registry.read_text(encoding="utf-8"))
        self.assertEqual(len(stored["bindings"]), 1)

        def unbind(_index: int) -> str:
            return unbind_conversation("conversation-fixture", "generic", self.registry)["status"]

        with ThreadPoolExecutor(max_workers=8) as executor:
            removed = list(executor.map(unbind, range(20)))
        self.assertEqual(removed.count("unbound"), 1)
        self.assertEqual(removed.count("already-unbound"), 19)
        self.assertEqual(audit_manager_registry(self.registry)["status"], "passed")

    def test_context_rechecks_feedback_sqlite_and_maintenance_gates(self) -> None:
        bind_conversation(self.payload(), self.registry)
        (self.output / "machine").mkdir()
        for database in (self.output / "machine/knowledge.sqlite", self.output / "agent-index.sqlite"):
            connection = sqlite3.connect(database)
            connection.close()
        feedback = self.output / "workspace-meta/feedback/open/feedback-fixture.json"
        feedback.parent.mkdir(parents=True)
        feedback.write_text(
            json.dumps({"id": "feedback-fixture", "severity": "error", "target": "pages/fixture.md"}),
            encoding="utf-8",
        )
        result = management_context(
            "conversation-fixture",
            "generic",
            "检查管理上下文的动态门",
            self.registry,
            python=Path(sys.executable),
            ckb=ROOT / "scripts/ckb.py",
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("open-error-feedback", result["blockers"])
        self.assertEqual(result["knowledge"]["open_feedback"]["count"], 1)
        self.assertIn("brief --out", result["prompt"])
        self.assertIn("feedback list", result["prompt"])
        self.assertIn("gaps list", result["prompt"])
        self.assertIn("reference list", result["prompt"])
        self.assertIn("record --out", result["prompt"])
        self.assertIn("maintain --out", result["prompt"])
        self.assertNotIn("private-prompt", result["prompt"])

    def ready_context(self) -> dict[str, object]:
        current = binding_status("conversation-fixture", "generic", self.registry)
        return {
            "status": "ready",
            "binding": current["binding"],
            "runtime": current["runtime"],
            "blockers": [],
        }

    def test_task_dispatch_creates_independent_worktree_prompt_and_review_gate(self) -> None:
        bind_conversation(self.payload(), self.registry)
        worktree = self.workspace / "worktrees/feature"
        test_command = f'"{sys.executable}" -c "from pathlib import Path; assert Path(\'feature.py\').is_file(); print(\'TASK_OK\')"'
        with mock.patch("ckb_core.management_agent.management_context", return_value=self.ready_context()):
            created = create_management_task(
                "conversation-fixture",
                "generic",
                "feature-task",
                "codex/feature-task",
                worktree,
                self.registry,
                allowed_paths=["feature.py"],
                forbidden_paths=[str(self.repo), str(self.output)],
                tests=[test_command],
                python=Path(sys.executable),
                ckb=ROOT / "scripts/ckb.py",
            )
        task = created["task"]
        self.assertEqual(created["status"], "created")
        self.assertTrue(worktree.is_dir())
        self.assertEqual(git(worktree, "rev-parse", "HEAD"), task["base_commit"])
        self.assertEqual(git(worktree, "branch", "--show-current"), "codex/feature-task")
        prompt = Path(task["prompt_path"])
        self.assertTrue(prompt.is_file())
        prompt_text = prompt.read_text(encoding="utf-8")
        self.assertIn("允许路径", prompt_text)
        self.assertIn("禁止路径", prompt_text)
        self.assertIn("验证命令", prompt_text)
        self.assertIn("结构化返回格式", prompt_text)
        self.assertIn("不得自行 merge", prompt_text)
        (worktree / "feature.py").write_text("FEATURE = True\n", encoding="utf-8")
        git(worktree, "add", ".")
        git(worktree, "commit", "-m", "add feature")
        before = management_task_status(task["dispatch_id"], self.registry)
        self.assertEqual(before["status"], "blocked")
        self.assertEqual(before["development"]["commit_count"], 1)
        with ThreadPoolExecutor(max_workers=6) as executor:
            reviews = list(executor.map(lambda _index: review_management_task(task["dispatch_id"], self.registry), range(6)))
        self.assertTrue(all(item["status"] == "passed" for item in reviews))
        self.assertEqual(sum(not item["idempotent"] for item in reviews), 1)
        reviewed = reviews[0]
        self.assertEqual(reviewed["verification"]["results"][0]["exit_status"], 0)
        self.assertIn("TASK_OK", reviewed["verification"]["results"][0]["stdout"])
        after = management_task_status(task["dispatch_id"], self.registry)
        self.assertEqual(after["status"], "merge-ready")
        self.assertFalse(after["merge_performed"])
        self.assertEqual(audit_manager_registry(self.registry)["status"], "passed")
        (worktree / "feature.py").write_text("FEATURE = False\n", encoding="utf-8")
        stale = management_task_status(task["dispatch_id"], self.registry)
        self.assertIn("task-worktree-dirty", stale["blockers"])

    def test_task_dispatch_is_idempotent_and_blocks_integration_drift(self) -> None:
        bind_conversation(self.payload(), self.registry)
        worktree = self.workspace / "worktrees/idempotent"
        arguments = dict(
            conversation_id="conversation-fixture",
            harness_id="generic",
            task_id="idempotent-task",
            branch="codex/idempotent-task",
            worktree=worktree,
            registry_path=self.registry,
            tests=[f'"{sys.executable}" -c "print(\'OK\')"'],
        )
        with mock.patch("ckb_core.management_agent.management_context", return_value=self.ready_context()):
            with ThreadPoolExecutor(max_workers=6) as executor:
                dispatched = list(executor.map(lambda _index: create_management_task(**arguments), range(6)))
        self.assertEqual(sum(item["status"] == "created" for item in dispatched), 1)
        self.assertEqual(sum(item["status"] == "already-created" for item in dispatched), 5)
        self.assertEqual(len({item["task"]["dispatch_id"] for item in dispatched}), 1)
        (self.repo / "drift.py").write_text("DRIFT = True\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "integration drift")
        with mock.patch("ckb_core.management_agent.management_context", return_value=self.ready_context()):
            with self.assertRaisesRegex(CkbError, "Git gate failed"):
                create_management_task(
                    "conversation-fixture",
                    "generic",
                    "blocked-task",
                    "codex/blocked-task",
                    self.workspace / "worktrees/blocked",
                    self.registry,
                    tests=[f'"{sys.executable}" -c "print(\'NO\')"'],
                )
        self.assertFalse((self.workspace / "worktrees/blocked").exists())
        self.assertEqual(git(self.repo, "branch", "--list", "codex/blocked-task"), "")

    def test_task_review_records_literal_failure_without_merge(self) -> None:
        bind_conversation(self.payload(), self.registry)
        worktree = self.workspace / "worktrees/failing"
        with mock.patch("ckb_core.management_agent.management_context", return_value=self.ready_context()):
            created = create_management_task(
                "conversation-fixture",
                "generic",
                "failing-task",
                "codex/failing-task",
                worktree,
                self.registry,
                tests=[f'"{sys.executable}" -c "import sys; print(\'EXPECTED_FAILURE\'); sys.exit(3)"'],
            )
        (worktree / "feature.py").write_text("VALUE = 1\n", encoding="utf-8")
        git(worktree, "add", ".")
        git(worktree, "commit", "-m", "add failing fixture")
        reviewed = review_management_task(created["task"]["dispatch_id"], self.registry)
        self.assertEqual(reviewed["status"], "failed")
        self.assertEqual(reviewed["verification"]["results"][0]["exit_status"], 3)
        self.assertIn("EXPECTED_FAILURE", reviewed["verification"]["results"][0]["stdout"])
        self.assertFalse(reviewed["merge_performed"])


if __name__ == "__main__":
    unittest.main()
