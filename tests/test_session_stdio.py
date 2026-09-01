from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ckb_core.automation import activate_skill_session, ingest_event, register_project
from ckb_core.session_stdio import (
    _force_terminate_pid,
    activate_session_stdio,
    audit_sessions,
    cleanup_sessions,
    close_session,
    list_sessions,
    pid_exists,
    request_session,
)


def make_output(root: Path, name: str) -> tuple[Path, Path]:
    repo = root / f"repo-{name}"
    output = root / f"output-{name}"
    repo.mkdir()
    (repo / "fixture.py").write_text("def fixture():\n    return 1\n", encoding="utf-8")
    (output / "machine").mkdir(parents=True)
    database = output / "machine" / "knowledge.sqlite"
    connection = sqlite3.connect(database)
    try:
        connection.executescript(
            """
            CREATE TABLE entities(
                entity_id TEXT PRIMARY KEY,name TEXT,qualified_name TEXT,kind TEXT,language TEXT,
                source_path TEXT,classification TEXT,description_zh TEXT,meaning_zh TEXT,role_zh TEXT,change_when_zh TEXT
            );
            CREATE TABLE source_ranges(entity_id TEXT PRIMARY KEY,start_line INTEGER,end_line INTEGER);
            CREATE TABLE human_projection(entity_id TEXT PRIMARY KEY,title TEXT,page_file TEXT,display_mode TEXT);
            CREATE TABLE files(path TEXT PRIMARY KEY,source_text TEXT);
            CREATE TABLE relations(relation_id TEXT PRIMARY KEY,source_entity_id TEXT,target_entity_id TEXT,relation TEXT);
            CREATE TABLE documents(document_id TEXT PRIMARY KEY,kind TEXT,title TEXT,human_file TEXT,token_estimate INTEGER);
            INSERT INTO entities VALUES('fixture-entity','fixture','fixture','function','python','fixture.py','page','测试实体','测试含义','测试职责','修改时核对');
            INSERT INTO source_ranges VALUES('fixture-entity',1,2);
            INSERT INTO human_projection VALUES('fixture-entity','fixture','pages/fixture.md','page');
            INSERT INTO files VALUES('fixture.py','def fixture():\n    return 1\n');
            """
        )
        connection.commit()
    finally:
        connection.close()
    state = {
        "schema_version": 4,
        "status": "complete",
        "repository": {"root": str(repo), "commit": "fixture"},
        "source_snapshot": {"root": str(repo), "status": "snapshot-ready"},
    }
    (output / "state.json").write_text(json.dumps(state), encoding="utf-8")
    return repo, output


class SessionStdioLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-session-stdio-")
        self.root = Path(self.temporary.name)
        self.session_root = self.root / "session-root"
        self.registry = self.root / "automation-registry.json"
        self.repo, self.output = make_output(self.root, "one")
        register_project(self.repo, self.output, self.registry, ["generic"])
        self.environment = patch.dict(
            os.environ,
            {
                "CKB_SESSION_STDIO_ROOT": str(self.session_root),
                "CKB_HARNESS": "generic",
            },
        )
        self.environment.start()
        self.sessions: set[str] = set()

    def tearDown(self) -> None:
        for session_id in self.sessions:
            close_session(
                harness="generic",
                session_id=session_id,
                output=self.output,
                root=self.session_root,
                reason="test-teardown",
                timeout=4,
            )
        cleanup_sessions(root=self.session_root)
        self.environment.stop()
        self.temporary.cleanup()

    def event(self, canonical_type: str, session_id: str, **extra: object) -> dict[str, object]:
        return {
            "canonical_type": canonical_type,
            "session_id": session_id,
            "cwd": str(self.repo),
            "event_id": f"{canonical_type}:{session_id}:{time.time_ns()}",
            **extra,
        }

    def test_session_start_and_plain_prompt_do_not_start_stdio(self) -> None:
        session_id = "idle-session"
        self.assertEqual(list_sessions(root=self.session_root, active_only=True)["active"], 0)
        start = ingest_event("generic", self.event("session.start", session_id), self.registry)
        prompt = ingest_event(
            "generic",
            self.event("turn.prompt", session_id, prompt="只讨论 Code Knowledge Builder 项目名"),
            self.registry,
        )
        self.assertEqual(start["reason"], "skill-not-applied-in-session")
        self.assertEqual(prompt["reason"], "skill-not-applied-in-session")
        self.assertEqual(list_sessions(root=self.session_root, active_only=True)["active"], 0)

    def test_exact_skill_activation_reuses_pid_across_turn_stop_and_session_end_reaps(self) -> None:
        session_id = "lifecycle-session"
        self.sessions.add(session_id)
        applied = ingest_event(
            "generic",
            self.event(
                "skill.applied",
                session_id,
                skill_name="code-knowledge-builder",
                ckb_skill_applied=True,
            ),
            self.registry,
        )
        lifecycle = applied["session_stdio"]
        self.assertEqual(lifecycle["status"], "ready")
        server_pid = lifecycle["server_pid"]
        self.assertTrue(pid_exists(server_pid))
        requests = [
            {"id": "ping-one", "method": "ping"},
            {"id": "entity-one", "method": "entity", "selector": "fixture"},
            {"id": "bad-one", "method": "unknown"},
        ]
        results = [
            request_session(
                harness="generic",
                session_id=session_id,
                output=self.output,
                root=self.session_root,
                request=request,
            )
            for request in requests
        ]
        self.assertTrue(all("server_pid" in item for item in results), results)
        self.assertEqual({item["server_pid"] for item in results}, {server_pid})
        self.assertEqual([item["response"]["id"] for item in results], ["ping-one", "entity-one", "bad-one"])
        self.assertFalse(results[-1]["response"]["ok"])
        stop = ingest_event("generic", self.event("turn.stop", session_id), self.registry)
        self.assertEqual(stop["canonical_type"], "turn.stop")
        self.assertTrue(pid_exists(server_pid))
        followup = request_session(
            harness="generic",
            session_id=session_id,
            output=self.output,
            root=self.session_root,
            request={"id": "followup", "method": "ping"},
        )
        self.assertIn("server_pid", followup, followup)
        self.assertEqual(followup["server_pid"], server_pid)
        ended = ingest_event("generic", self.event("session.end", session_id), self.registry)
        self.assertEqual(ended["session_stdio"]["status"], "closed")
        self.assertFalse(pid_exists(server_pid))
        audit = audit_sessions(root=self.session_root)
        self.assertEqual(audit["active"], 0)
        self.assertFalse(any(audit["object_counts"].values()))

    def test_sixteen_concurrent_first_requests_singleflight_and_isolation(self) -> None:
        session_id = "parallel-session"
        self.sessions.add(session_id)
        connection = sqlite3.connect(self.output / "machine" / "automation.sqlite")
        try:
            connection.execute(
                "INSERT INTO skill_activations VALUES(?,?,?,?,?,?,?)",
                (
                    "parallel-activation",
                    "generic",
                    session_id,
                    str(self.repo),
                    "code-knowledge-builder",
                    "concurrent-test",
                    "2026-09-01T00:00:00Z",
                ),
            )
            connection.commit()
        finally:
            connection.close()

        def request(index: int) -> dict[str, object]:
            return request_session(
                harness="generic",
                session_id=session_id,
                output=self.output,
                root=self.session_root,
                request={"id": f"parallel-{index:02d}", "method": "ping"},
            )

        with ThreadPoolExecutor(max_workers=16) as executor:
            results = list(executor.map(request, range(16)))
        self.assertTrue(all("server_pid" in item for item in results), results)
        pids = {int(item["server_pid"]) for item in results}
        self.assertEqual(len(pids), 1)
        self.assertEqual(
            {item["response"]["id"] for item in results},
            {f"parallel-{index:02d}" for index in range(16)},
        )
        other_session = "isolated-session"
        self.sessions.add(other_session)
        other = activate_skill_session("generic", other_session, self.repo, self.registry, session_stdio_root=self.session_root)
        self.assertNotIn(other["session_stdio"]["server_pid"], pids)
        repo_two, output_two = make_output(self.root, "two")
        registry_two = self.root / "automation-two.json"
        register_project(repo_two, output_two, registry_two, ["generic"])
        output_isolated = activate_skill_session(
            "generic",
            session_id,
            repo_two,
            registry_two,
            session_stdio_root=self.session_root,
        )
        self.assertNotIn(output_isolated["session_stdio"]["server_pid"], pids)
        close_session(harness="generic", session_id=session_id, output=output_two, root=self.session_root, reason="test-output-isolation")

    def test_parent_death_reaps_and_explicit_close_is_idempotent(self) -> None:
        session_id = "parent-death-session"
        command = [
            sys.executable,
            str(ROOT / "tests" / "session_stdio_harness_probe.py"),
            "--out",
            str(self.output),
            "--root",
            str(self.session_root),
            "--session-id",
            session_id,
        ]
        completed = subprocess.run(command, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        activation = json.loads(completed.stdout)
        server_pid = activation["server_pid"]
        deadline = time.monotonic() + 12
        while pid_exists(server_pid) and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertFalse(pid_exists(server_pid))
        cleanup_sessions(root=self.session_root)
        audit = audit_sessions(root=self.session_root)
        self.assertEqual(audit["active"], 0)
        self.assertFalse(any(audit["object_counts"].values()))
        first = close_session(harness="generic", session_id=session_id, output=self.output, root=self.session_root)
        second = close_session(harness="generic", session_id=session_id, output=self.output, root=self.session_root)
        self.assertIn(first["status"], {"closed", "not-found"})
        self.assertEqual(second["status"], first["status"])

    def test_start_failure_is_bounded_cli_fallback_not_resident(self) -> None:
        result = activate_session_stdio(
            harness="generic",
            session_id="broken-start",
            output=self.output,
            root=self.session_root,
            ckb=self.root / "missing-ckb.py",
            start_timeout=2,
        )
        self.assertEqual(result["status"], "fallback")
        self.assertEqual(result["mode"], "cli-fallback")
        self.assertFalse(result["resident"])
        self.assertTrue(result["fallback"]["active"])
        self.assertLessEqual(len(result["fallback"]["reason"]), 340)

    def test_server_crash_restarts_once_then_falls_back_to_per_command_cli(self) -> None:
        session_id = "crash-session"
        self.sessions.add(session_id)
        activation = activate_skill_session(
            "generic",
            session_id,
            self.repo,
            self.registry,
            session_stdio_root=self.session_root,
        )["session_stdio"]
        original_pid = activation["server_pid"]
        _force_terminate_pid(original_pid)
        restarted = request_session(
            harness="generic",
            session_id=session_id,
            output=self.output,
            root=self.session_root,
            request={"id": "restart", "method": "ping"},
        )
        self.assertTrue(restarted["resident"])
        self.assertEqual(restarted["restart_count"], 1)
        self.assertNotEqual(restarted["server_pid"], original_pid)
        _force_terminate_pid(restarted["server_pid"])
        fallback = request_session(
            harness="generic",
            session_id=session_id,
            output=self.output,
            root=self.session_root,
            request={"id": "fallback", "method": "entity", "selector": "fixture"},
        )
        self.assertEqual(fallback["mode"], "cli-fallback")
        self.assertFalse(fallback["resident"])
        self.assertEqual(fallback["cli_exit_status"], 0)
        self.assertEqual(fallback["response"]["result"]["status"], "passed")
        deadline = time.monotonic() + 8
        while list_sessions(root=self.session_root, active_only=True)["active"] and time.monotonic() < deadline:
            time.sleep(0.05)
        cleanup_sessions(root=self.session_root)
        self.assertFalse(any(audit_sessions(root=self.session_root)["object_counts"].values()))

    def test_supervisor_crash_stale_lease_is_cleaned_before_reactivation(self) -> None:
        session_id = "supervisor-crash-session"
        first = activate_session_stdio(
            harness="generic",
            session_id=session_id,
            output=self.output,
            root=self.session_root,
        )
        self.assertEqual(first["status"], "ready")
        self.assertTrue(_force_terminate_pid(first["supervisor_pid"]))
        deadline = time.monotonic() + 8
        while pid_exists(first["server_pid"]) and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertFalse(pid_exists(first["server_pid"]))
        cleanup_sessions(root=self.session_root)
        second = activate_session_stdio(
            harness="generic",
            session_id=session_id,
            output=self.output,
            root=self.session_root,
        )
        self.assertEqual(second["status"], "ready")
        self.assertNotEqual(second["supervisor_pid"], first["supervisor_pid"])
        self.assertNotEqual(second["server_pid"], first["server_pid"])
        close_session(
            harness="generic",
            session_id=session_id,
            output=self.output,
            root=self.session_root,
            reason="recovery-complete",
        )
        self.assertFalse(any(audit_sessions(root=self.session_root)["object_counts"].values()))


if __name__ == "__main__":
    unittest.main()
