from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.freshness import (
    FRESHNESS_STATES,
    _state_lock,
    attach_freshness_to_retrieval,
    check_fact_freshness,
    classify_git_trigger,
    create_migration_plan,
    discard_overlay,
    query_collaboration_records,
    record_collaboration,
)
from ckb_core.automation import ingest_event, register_project
from ckb_core.common import CkbError


def git(repo: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and completed.returncode:
        raise RuntimeError(completed.stderr or completed.stdout)
    return completed


class FactFreshnessStateMachineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-freshness-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.output = self.root / "knowledge"
        self.repo.mkdir()
        self.output.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")
        (self.repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "baseline")
        self.bound = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        self._write_output_state(self.output, self.bound)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_output_state(self, output: Path, commit: str, *, complete: bool = True, migration: bool = False) -> None:
        output.mkdir(parents=True, exist_ok=True)
        state = {
            "schema_version": 4,
            "status": "complete" if complete else "in-progress",
            "repository": {
                "root": str(self.repo.resolve()),
                "commit": commit,
                "tree": git(self.repo, "rev-parse", f"{commit}^{{tree}}").stdout.strip(),
            },
        }
        if migration:
            state["migration"] = {"status": "passed"}
        (output / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if complete:
            (output / ".complete").write_text("{}\n", encoding="utf-8")
            (output / "audit").mkdir(exist_ok=True)
            (output / "audit/global.json").write_text('{"status":"passed"}\n', encoding="utf-8")
        if migration:
            (output / "migration").mkdir(exist_ok=True)
            (output / "migration/audit.json").write_text('{"status":"passed"}\n', encoding="utf-8")

    def _commit(self, value: int, message: str = "change") -> str:
        (self.repo / "app.py").write_text(f"VALUE = {value}\n", encoding="utf-8")
        git(self.repo, "add", "app.py")
        git(self.repo, "commit", "-m", message)
        return git(self.repo, "rev-parse", "HEAD").stdout.strip()

    def test_contract_declares_only_the_six_frozen_states(self) -> None:
        self.assertEqual(
            FRESHNESS_STATES,
            {
                "current",
                "stale-committed",
                "provisional-dirty",
                "migration-pending",
                "migration-ready",
                "unavailable",
            },
        )

    def test_same_session_and_same_head_reuse_without_rebuilding(self) -> None:
        baseline_state = (self.output / "state.json").read_bytes()
        first = check_fact_freshness(self.output, self.repo, session_id="session-a", trigger="skill-start")
        second = check_fact_freshness(self.output, self.repo, session_id="session-a", trigger="first-brief")
        self.assertEqual(first["state"], "current")
        self.assertFalse(first["cache_hit"])
        self.assertEqual(second["state"], "current")
        self.assertTrue(second["cache_hit"])
        self.assertEqual(second["bound_commit"], self.bound)
        self.assertEqual((self.output / "state.json").read_bytes(), baseline_state)
        self.assertFalse(second["writes"]["stable_facts"])
        self.assertFalse(second["writes"]["human_layer"])

    def test_new_commit_marks_stable_facts_stale_and_summarizes_range(self) -> None:
        current = self._commit(2)
        result = check_fact_freshness(self.output, self.repo, session_id="session-a", trigger="git:commit")
        self.assertEqual(result["state"], "stale-committed")
        self.assertEqual(result["stable_state"], "stale-committed")
        self.assertEqual(result["current_head"], current)
        self.assertEqual(result["bound_commit"], self.bound)
        self.assertEqual(result["change_summary"]["changed_paths"], ["app.py"])
        self.assertEqual(result["next_action"]["action"], "create-migration-plan")
        self.assertFalse(result["stable_facts_current"])

    def test_dirty_worktree_creates_discardable_overlay_without_promoting_it(self) -> None:
        (self.repo / "app.py").write_text("VALUE = 9\n", encoding="utf-8")
        (self.repo / "scratch.txt").write_text("temporary\n", encoding="utf-8")
        result = check_fact_freshness(self.output, self.repo, session_id="session-dirty", trigger="turn-start")
        self.assertEqual(result["state"], "provisional-dirty")
        self.assertEqual(result["stable_state"], "current")
        self.assertFalse(result["stable_facts_current"])
        overlay = result["overlay"]
        overlay_path = Path(overlay["path"])
        self.assertTrue(overlay_path.is_file())
        stored = json.loads(overlay_path.read_text(encoding="utf-8"))
        self.assertEqual(stored["source"]["session_id"], "session-dirty")
        self.assertEqual(stored["lifetime"]["policy"], "discardable-24h")
        self.assertEqual(stored["write_layer"], "machine-temporary-overlay")
        self.assertNotIn("patch", json.dumps(stored, ensure_ascii=False).casefold())
        discarded = discard_overlay(self.output, overlay["overlay_id"])
        self.assertEqual(discarded["status"], "discarded")
        self.assertFalse(overlay_path.exists())
        self.assertTrue((self.repo / "app.py").is_file())
        self.assertTrue(git(self.repo, "status", "--porcelain").stdout.strip())

    def test_dirty_tree_overlays_committed_drift_without_hiding_stable_state(self) -> None:
        self._commit(2)
        (self.repo / "app.py").write_text("VALUE = 3\n", encoding="utf-8")
        result = check_fact_freshness(self.output, self.repo, session_id="session-layered", trigger="git:commit")
        self.assertEqual(result["state"], "provisional-dirty")
        self.assertEqual(result["stable_state"], "stale-committed")
        self.assertEqual(result["change_summary"]["changed_paths"], ["app.py"])

    def test_staging_requires_all_completion_evidence_before_ready(self) -> None:
        current = self._commit(2)
        staging = self.root / "knowledge-staging"
        plan = create_migration_plan(self.output, self.repo, staging, session_id="manager-a")
        self.assertEqual(plan["state"], "migration-pending")
        self.assertFalse(staging.exists())
        self.assertEqual(plan["target_commit"], current)
        self._write_output_state(staging, current, complete=False, migration=True)
        pending = check_fact_freshness(self.output, self.repo, session_id="manager-a", trigger="migration-status")
        self.assertEqual(pending["state"], "migration-pending")
        self.assertIn("staging-not-complete", pending["migration"]["blockers"])
        self._write_output_state(staging, current, complete=True, migration=True)
        ready = check_fact_freshness(self.output, self.repo, session_id="manager-a", trigger="migration-status")
        self.assertEqual(ready["state"], "migration-ready")
        self.assertEqual(ready["migration"]["target_commit"], current)
        self.assertEqual(ready["next_action"]["action"], "review-and-cutover-explicitly")
        self.assertFalse(ready["stable_facts_current"])

    def test_unavailable_preserves_last_confirmed_and_recovers_on_retry(self) -> None:
        confirmed = check_fact_freshness(self.output, self.repo, session_id="session-recovery", trigger="initial")
        state_path = self.output / "state.json"
        original = state_path.read_bytes()
        state_path.write_text('{"status":"complete","repository":{}}\n', encoding="utf-8")
        failed = check_fact_freshness(self.output, self.repo, session_id="session-recovery", trigger="broken-binding")
        self.assertEqual(failed["state"], "unavailable")
        self.assertEqual(failed["last_confirmed"]["state"], confirmed["state"])
        state_path.write_bytes(original)
        recovered = check_fact_freshness(self.output, self.repo, session_id="session-recovery", trigger="retry")
        self.assertEqual(recovered["state"], "current")
        self.assertTrue(recovered["recovered_from_unavailable"])

    def test_stale_retrieval_pack_and_record_carry_a_deterministic_conclusion_guard(self) -> None:
        pack = self.output / "machine/agent-packs/pack.md"
        record = self.output / "machine/agent-packs/pack.json"
        pack.parent.mkdir(parents=True)
        pack.write_text("# Agent 机器知识阅读包\n\n固定事实正文。\n", encoding="utf-8")
        record.write_text('{"status":"passed","source_grounded":true}\n', encoding="utf-8")
        current = self._commit(2)
        freshness = check_fact_freshness(self.output, self.repo, session_id="retrieval", trigger="first-brief")
        attached = attach_freshness_to_retrieval(
            self.output,
            {"status": "passed", "source_grounded": True, "pack": str(pack), "record": str(record)},
            freshness,
        )
        self.assertEqual(attached["fact_freshness"]["state"], "stale-committed")
        self.assertEqual(attached["fact_freshness"]["current_head"], current)
        self.assertFalse(attached["current_source_grounded"])
        self.assertIn("不得据此形成当前确定性结论", pack.read_text(encoding="utf-8"))
        persisted = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(persisted["fact_freshness"]["state"], "stale-committed")
        self.assertFalse(persisted["current_source_grounded"])

    def test_cli_status_returns_stale_exit_and_plan_never_creates_staging(self) -> None:
        cli = ROOT / "scripts/ckb.py"
        current = subprocess.run(
            [sys.executable, str(cli), "freshness", "status", "--out", str(self.output), "--repo", str(self.repo), "--session-id", "cli"],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(current.returncode, 0, current.stderr)
        self.assertEqual(json.loads(current.stdout)["state"], "current")
        self._commit(2)
        stale = subprocess.run(
            [sys.executable, str(cli), "freshness", "status", "--out", str(self.output), "--repo", str(self.repo), "--session-id", "cli"],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(stale.returncode, 6, stale.stderr)
        self.assertEqual(json.loads(stale.stdout)["state"], "stale-committed")
        staging = self.root / "staging-cli"
        planned = subprocess.run(
            [
                sys.executable,
                str(cli),
                "freshness",
                "plan",
                "--out",
                str(self.output),
                "--repo",
                str(self.repo),
                "--staging-out",
                str(staging),
                "--session-id",
                "cli",
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(planned.returncode, 0, planned.stderr)
        self.assertEqual(json.loads(planned.stdout)["state"], "migration-pending")
        self.assertFalse(staging.exists())

    def test_dead_lock_is_recovered_and_concurrent_checks_serialize(self) -> None:
        freshness_root = self.output / "workspace-meta/freshness"
        freshness_root.mkdir(parents=True)
        lock = freshness_root / "state.lock"
        lock.write_text(json.dumps({"owner_token": "dead", "pid": 999999999, "created_unix": 1}) + "\n", encoding="utf-8")
        os.utime(lock, (1, 1))
        recovered = check_fact_freshness(self.output, self.repo, session_id="session-lock", trigger="lock-recovery")
        self.assertEqual(recovered["state"], "current")
        self.assertTrue(recovered["lock_recovered"])

        def inspect(index: int) -> str:
            return check_fact_freshness(
                self.output,
                self.repo,
                session_id=f"concurrent-{index % 3}",
                trigger="parallel",
            )["state"]

        with ThreadPoolExecutor(max_workers=8) as executor:
            states = list(executor.map(inspect, range(32)))
        self.assertEqual(set(states), {"current"})
        persisted = json.loads((freshness_root / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(persisted["state"], "current")
        self.assertLessEqual(len(persisted["session_cache"]), 64)

    def test_release_retries_windows_sharing_violation_and_leaves_no_lock(self) -> None:
        lock_path = self.output / "workspace-meta/freshness/state.lock"
        original_unlink = Path.unlink
        attempts = 0

        def sharing_violation(path: Path, *args: object, **kwargs: object) -> None:
            nonlocal attempts
            if path == lock_path and attempts < 3:
                attempts += 1
                raise PermissionError(13, "fixture sharing violation", str(path), 32)
            original_unlink(path, *args, **kwargs)

        with mock.patch.object(Path, "unlink", sharing_violation):
            with _state_lock(self.output, release_timeout=0.5):
                self.assertTrue(lock_path.is_file())
        self.assertEqual(attempts, 3)
        self.assertFalse(lock_path.exists())

    def test_release_never_deletes_lock_replaced_by_another_owner(self) -> None:
        lock_path = self.output / "workspace-meta/freshness/state.lock"
        replacement = {
            "schema_version": 1,
            "owner_token": "replacement-owner",
            "pid": os.getpid(),
            "created_unix": time.time(),
        }
        with _state_lock(self.output, release_timeout=0.2):
            lock_path.write_text(json.dumps(replacement) + "\n", encoding="utf-8")
        self.assertTrue(lock_path.is_file())
        self.assertEqual(json.loads(lock_path.read_text(encoding="utf-8"))["owner_token"], "replacement-owner")
        lock_path.unlink()

    def test_release_timeout_is_bounded_diagnostic_and_preserves_owned_lock(self) -> None:
        lock_path = self.output / "workspace-meta/freshness/state.lock"
        original_unlink = Path.unlink

        def always_busy(path: Path, *args: object, **kwargs: object) -> None:
            if path == lock_path:
                raise PermissionError(13, "fixture sharing violation", str(path), 32)
            original_unlink(path, *args, **kwargs)

        started = time.monotonic()
        with mock.patch.object(Path, "unlink", always_busy):
            with self.assertRaisesRegex(CkbError, "state lock release timeout.*owner_token"):
                with _state_lock(self.output, release_timeout=0.08):
                    self.assertTrue(lock_path.is_file())
        elapsed = time.monotonic() - started
        self.assertGreaterEqual(elapsed, 0.05)
        self.assertLess(elapsed, 0.8)
        self.assertTrue(lock_path.is_file())
        lock_path.unlink()


class GitTriggerAndCollaborationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-collaboration-")
        self.output = Path(self.temporary.name) / "knowledge"
        self.output.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_git_tool_commands_classify_only_the_four_required_event_families(self) -> None:
        cases = {
            "git commit -m done": "commit",
            "git -C repo merge feature": "merge",
            "git.exe pull --ff-only origin main": "pull",
            "git switch topic": "branch-switch",
            "git checkout main": "branch-switch",
            "python build.py": None,
            "git status --short": None,
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(classify_git_trigger({"command": command}), expected)

    def test_branch_commit_task_queries_and_duplicate_candidates_keep_evidence_boundary(self) -> None:
        planned = record_collaboration(
            self.output,
            feature="源码事实新鲜度",
            summary="计划为 Git HEAD 漂移增加状态检查",
            status="planned",
            branch="codex/freshness-a",
            commit="a" * 40,
            task="task-a",
            paths=["scripts/ckb_core/freshness.py"],
        )
        revised_plan = record_collaboration(
            self.output,
            feature="源码事实新鲜度",
            summary="改为由 Git 事件触发有界状态检查",
            status="planned",
            branch="codex/freshness-a",
            commit="a" * 40,
            task="task-a",
            paths=["scripts/ckb_core/freshness.py"],
        )
        self.assertNotEqual(planned["record_id"], revised_plan["record_id"])
        implemented = record_collaboration(
            self.output,
            feature="源码事实新鲜度检查",
            summary="实现 Git HEAD 漂移状态机和迁移计划",
            status="implemented",
            branch="codex/freshness-b",
            commit="b" * 40,
            task="task-b",
            paths=["scripts/ckb_core/freshness.py", "tests/test_git_fact_freshness.py"],
        )
        superseded = record_collaboration(
            self.output,
            feature="旧轮询方案",
            summary="旧后台轮询方案已被事件触发状态机替代",
            status="superseded",
            branch="codex/old-polling",
            commit="c" * 40,
            task="task-old",
            paths=["scripts/ckb_core/automation.py"],
            supersedes=[planned["record_id"]],
        )
        by_branch = query_collaboration_records(self.output, branch="codex/freshness-b")
        self.assertEqual([item["record_id"] for item in by_branch["records"]], [implemented["record_id"]])
        by_commit = query_collaboration_records(self.output, commit="c" * 40)
        self.assertEqual(by_commit["records"][0]["status"], "superseded")
        by_task = query_collaboration_records(self.output, task="task-a")
        self.assertEqual(len(by_task["records"]), 2)
        self.assertEqual({item["status"] for item in by_task["records"]}, {"planned"})
        candidates = query_collaboration_records(
            self.output,
            summary="为 Git HEAD 漂移实现源码事实新鲜度状态机",
            paths=["scripts/ckb_core/freshness.py"],
        )["duplicate_candidates"]
        self.assertTrue(candidates)
        self.assertTrue(all(item["classification"] == "candidate-only" for item in candidates))
        self.assertTrue(all("duplicate" not in item or item["duplicate"] is not True for item in candidates))
        self.assertIn(superseded["record_id"], {item["record_id"] for item in query_collaboration_records(self.output)["records"]})


class RealGitEventSequenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-freshness-e2e-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.output = self.root / "knowledge"
        self.remote = self.root / "remote.git"
        self.peer = self.root / "peer"
        self.registry = self.root / "automation-registry.json"
        self.repo.mkdir()
        self.output.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")
        (self.repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "baseline")
        self.bound = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        state = {
            "status": "complete",
            "repository": {"root": str(self.repo), "commit": self.bound, "tree": git(self.repo, "rev-parse", "HEAD^{tree}").stdout.strip()},
        }
        (self.output / "state.json").write_text(json.dumps(state) + "\n", encoding="utf-8")
        (self.output / ".complete").write_text("{}\n", encoding="utf-8")
        (self.output / "audit").mkdir()
        (self.output / "audit/global.json").write_text('{"status":"passed"}\n', encoding="utf-8")
        register_project(self.repo, self.output, self.registry, ["generic"])

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_commit_branch_switch_merge_and_pull_each_drive_a_real_check(self) -> None:
        with mock.patch("ckb_core.automation.activate_session_stdio", return_value={"state": "ready"}):
            activated = ingest_event(
                "generic",
                {
                    "canonical_type": "skill.applied",
                    "event_id": "skill-start",
                    "session_id": "e2e",
                    "cwd": str(self.repo),
                    "skill_name": "code-knowledge-builder",
                    "ckb_skill_applied": True,
                },
                self.registry,
            )
        self.assertEqual(activated["fact_freshness"]["state"], "current")

        def git_event(event_id: str, command: str) -> dict[str, object]:
            return ingest_event(
                "generic",
                {
                    "canonical_type": "tool.result",
                    "event_id": event_id,
                    "session_id": "e2e",
                    "turn_id": "git-events",
                    "cwd": str(self.repo),
                    "tool_name": "exec_command",
                    "tool_input": {"command": command},
                    "status": "completed",
                },
                self.registry,
            )

        git(self.repo, "checkout", "-b", "feature")
        (self.repo / "feature.py").write_text("FEATURE = True\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "feature")
        commit_result = git_event("commit", "git commit -m feature")
        self.assertEqual(commit_result["git_trigger"], "commit")
        self.assertEqual(commit_result["fact_freshness"]["state"], "stale-committed")

        git(self.repo, "checkout", "main")
        switch_result = git_event("switch", "git switch main")
        self.assertEqual(switch_result["git_trigger"], "branch-switch")
        self.assertEqual(switch_result["fact_freshness"]["state"], "current")
        git(self.repo, "merge", "--no-ff", "feature", "-m", "merge feature")
        merge_result = git_event("merge", "git merge --no-ff feature")
        self.assertEqual(merge_result["git_trigger"], "merge")
        self.assertEqual(merge_result["fact_freshness"]["state"], "stale-committed")

        self.remote.mkdir()
        git(self.remote, "init", "--bare")
        git(self.repo, "remote", "add", "origin", str(self.remote))
        git(self.repo, "push", "-u", "origin", "main")
        subprocess.run(["git", "clone", "-b", "main", str(self.remote), str(self.peer)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        git(self.peer, "config", "user.email", "peer@example.invalid")
        git(self.peer, "config", "user.name", "Peer")
        (self.peer / "remote.py").write_text("REMOTE = True\n", encoding="utf-8")
        git(self.peer, "add", ".")
        git(self.peer, "commit", "-m", "remote")
        git(self.peer, "push", "origin", "main")
        git(self.repo, "pull", "--ff-only", "origin", "main")
        pull_result = git_event("pull", "git pull --ff-only origin main")
        self.assertEqual(pull_result["git_trigger"], "pull")
        self.assertEqual(pull_result["fact_freshness"]["state"], "stale-committed")
        stored = json.loads((self.output / "workspace-meta/freshness/state.json").read_text(encoding="utf-8"))
        triggers = [item["trigger"] for item in stored["recent_events"]]
        for required in ("git:commit", "git:branch-switch", "git:merge", "git:pull"):
            self.assertIn(required, triggers)


if __name__ == "__main__":
    unittest.main()
