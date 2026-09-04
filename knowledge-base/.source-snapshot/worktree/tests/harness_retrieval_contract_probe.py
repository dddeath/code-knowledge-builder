from __future__ import annotations

import atexit
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sqlite3
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ckb_core.automation import automation_status, ingest_event, register_project
from ckb_core.freshness import check_fact_freshness
from ckb_core.session_stdio import (
    audit_sessions,
    cleanup_sessions,
    close_session,
    request_session,
)


INSTRUCTION_PATHS = (
    Path("AGENTS.md"),
    Path("CLAUDE.md"),
    Path("GEMINI.md"),
    Path(".github/copilot-instructions.md"),
    Path(".cursor/rules/code-knowledge-builder.mdc"),
)
COUNT_FIELDS = (
    "skill_activations",
    "events",
    "sessions",
    "active_sessions",
    "turns",
    "changed_paths",
    "pending_reviews",
    "reviewed",
    "pending_spool",
    "failed_spool",
)


def _git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        raise RuntimeError(
            f"git -C {repo} {' '.join(arguments)} failed with {completed.returncode}: "
            f"{(completed.stderr or completed.stdout).strip()}"
        )
    return completed.stdout.strip()


def _run_ckb(ckb: Path, *arguments: str, environment: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-X", "utf8", str(ckb), *arguments],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    if completed.returncode:
        raise RuntimeError(
            f"ckb {' '.join(arguments)} failed with {completed.returncode}: "
            f"{(completed.stderr or completed.stdout).strip()}"
        )
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ckb {' '.join(arguments)} returned invalid JSON: {completed.stdout[:500]}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"ckb {' '.join(arguments)} did not return one JSON object")
    return value


def _assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{label}: expected={expected!r}; actual={actual!r}")


def _assert(condition: bool, label: str) -> None:
    if not condition:
        raise RuntimeError(label)


def _file_evidence(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": str(path.resolve()),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _activation_source(output: Path, session_id: str) -> str | None:
    database = output / "machine/automation.sqlite"
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT activation_source FROM skill_activations "
            "WHERE harness='generic' AND external_session_id=? AND skill_name='code-knowledge-builder' "
            "ORDER BY activated_at_utc DESC LIMIT 1",
            (session_id,),
        ).fetchone()
    finally:
        connection.close()
    return str(row[0]) if row else None


@contextmanager
def _environment_value(name: str, value: str):
    previous = os.environ.get(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = previous


def _make_fixture_repo(root: Path) -> tuple[Path, str]:
    repo = root / "project"
    repo.mkdir(parents=True)
    (repo / "fixture.py").write_text("def fixture():\n    return 1\n", encoding="utf-8", newline="\n")
    _git(repo, "init")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Harness Contract Fixture")
    _git(repo, "add", "fixture.py")
    _git(repo, "commit", "-m", "fixture baseline")
    for relative in INSTRUCTION_PATHS:
        _assert(not (repo / relative).exists(), f"isolated fixture unexpectedly contains {relative.as_posix()}")
    return repo, _git(repo, "rev-parse", "HEAD")


def _fallback_wrapper(path: Path, ckb: Path) -> None:
    path.write_text(
        "from __future__ import annotations\n"
        "import subprocess\n"
        "import sys\n"
        f"REAL_CKB = {str(ckb.resolve())!r}\n"
        "if len(sys.argv) > 1 and sys.argv[1] == 'serve':\n"
        "    raise SystemExit(91)\n"
        "raise SystemExit(subprocess.call([sys.executable, '-X', 'utf8', REAL_CKB, *sys.argv[1:]]))\n",
        encoding="utf-8",
        newline="\n",
    )


def run_probe(output: Path, ckb: Path) -> dict[str, Any]:
    output = output.expanduser().resolve()
    ckb = ckb.expanduser().resolve()
    _assert((output / "state.json").is_file(), f"isolated OUTPUT is missing state.json: {output}")
    _assert(
        (output / "machine/knowledge.sqlite").is_file(),
        f"isolated OUTPUT is missing machine/knowledge.sqlite: {output}",
    )
    _assert(ckb.is_file(), f"CKB entrypoint is missing: {ckb}")

    with tempfile.TemporaryDirectory(prefix="ckb-no-agents-harness-", ignore_cleanup_errors=True) as value:
        fixture_root = Path(value).resolve()
        repo, initial_head = _make_fixture_repo(fixture_root)
        registry = fixture_root / "automation-registry.json"
        session_root = fixture_root / "stdio"
        run_token = hashlib.sha256(str(fixture_root).encode("utf-8")).hexdigest()[:12]
        missing_session = f"missing-skill-{run_token}"
        skill_session = f"skill-only-{run_token}"
        fallback_session = f"fallback-session-{run_token}"

        def cleanup_probe_sessions() -> None:
            for session_id in (skill_session, fallback_session):
                try:
                    close_session(
                        harness="generic",
                        session_id=session_id,
                        output=output,
                        root=session_root,
                        reason="probe-finally",
                        timeout=5,
                    )
                except Exception:
                    pass
            try:
                cleanup_sessions(root=session_root)
            except Exception:
                pass

        atexit.register(cleanup_probe_sessions)
        register = register_project(repo, output, registry, ["generic"])
        _assert_equal(register.get("status"), "registered", "fixture registration")

        before_missing = automation_status(output)
        missing_start = ingest_event(
            "generic",
            {
                "canonical_type": "session.start",
                "event_id": f"missing-skill-start-{run_token}",
                "session_id": missing_session,
                "cwd": str(repo),
            },
            registry,
        )
        missing_prompt = ingest_event(
            "generic",
            {
                "canonical_type": "turn.prompt",
                "event_id": f"missing-skill-prompt-{run_token}",
                "session_id": missing_session,
                "cwd": str(repo),
                "prompt": "检查当前项目。",
            },
            registry,
        )
        after_missing = automation_status(output)
        _assert_equal(missing_start.get("reason"), "skill-not-applied-in-session", "missing-skill start")
        _assert_equal(missing_prompt.get("reason"), "skill-not-applied-in-session", "missing-skill prompt")
        _assert_equal(
            {field: after_missing[field] for field in COUNT_FIELDS},
            {field: before_missing[field] for field in COUNT_FIELDS},
            "missing-skill zero-write counters",
        )

        with _environment_value("CKB_SESSION_STDIO_ROOT", str(session_root)):
            applied = ingest_event(
                "generic",
                {
                    "canonical_type": "skill.applied",
                    "event_id": f"exact-skill-application-{run_token}",
                    "session_id": skill_session,
                    "cwd": str(repo),
                    "skill_name": "code-knowledge-builder",
                    "ckb_skill_applied": True,
                },
                registry,
        )
        _assert_equal(applied.get("status"), "recorded", "exact skill application")
        applied_source = _activation_source(output, skill_session)
        _assert_equal(applied_source, "native-skill-event", "exact activation source")
        _assert_equal((applied.get("session_stdio") or {}).get("status"), "ready", "resident stdio activation")

        resident_environment = os.environ.copy()
        resident_environment.update(
            {
                "CKB_HARNESS": "generic",
                "CKB_SESSION_ID": skill_session,
                "CKB_SESSION_STDIO_ROOT": str(session_root),
            }
        )
        question = "会话级 stdio 检索失败时如何执行 CLI fallback？"
        brief = _run_ckb(
            ckb,
            "brief",
            "--out",
            str(output),
            question,
            "--budget",
            "900",
            "--max-pages",
            "4",
            "--profile",
            "fast",
            environment=resident_environment,
        )
        _assert_equal(brief.get("status"), "passed", "skill-only brief")
        _assert_equal((brief.get("session_stdio") or {}).get("mode"), "resident-stdio", "brief transport")
        pack = Path(str(brief.get("pack")))
        record = Path(str(brief.get("record")))
        _assert(pack.is_file(), f"brief pack cannot be reopened: {pack}")
        _assert(record.is_file(), f"brief record cannot be reopened: {record}")
        record_value = json.loads(record.read_text(encoding="utf-8"))
        _assert_equal(record_value.get("pack"), str(pack), "record pack path")
        _assert(bool(record_value.get("selected_entities")), "brief record contains no selected entities")

        selector = str(record_value["selected_entities"][0]["entity_id"])
        source = _run_ckb(
            ckb,
            "source",
            "--out",
            str(output),
            selector,
            "--context-lines",
            "2",
            environment=resident_environment,
        )
        _assert_equal(source.get("status"), "passed", "narrow source read")
        _assert(bool(source.get("source_path")), "narrow source read has no source_path")

        feedback = _run_ckb(ckb, "feedback", "list", "--out", str(output), "--status", "open")
        gaps = _run_ckb(ckb, "gaps", "list", "--out", str(output), "--status", "open")
        _assert_equal(feedback.get("status"), "ready", "open feedback")
        _assert_equal(gaps.get("status"), "ready", "open research gaps")

        source_read = _run_ckb(
            ckb,
            "brief",
            "--out",
            str(output),
            "zzqvxykplm987654321",
            "--budget",
            "600",
            "--max-pages",
            "2",
            "--profile",
            "fast",
        )
        _assert_equal(source_read.get("status"), "needs-source-read", "needs-source-read branch")
        _assert_equal(source_read.get("pack"), None, "needs-source-read pack")

        maintenance = _run_ckb(ckb, "maintain", "--out", str(output))
        _assert_equal(maintenance.get("status"), "passed", "task-required maintenance")
        _assert_equal(maintenance.get("page_writes"), 0, "maintenance page writes")

        state_path = output / "state.json"
        state_bytes = state_path.read_bytes()
        state = json.loads(state_bytes.decode("utf-8-sig"))
        try:
            state["repository"]["root"] = str(repo)
            state["repository"]["commit"] = initial_head
            state["repository"]["tree"] = _git(repo, "rev-parse", "HEAD^{tree}")
            state_path.write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            current = check_fact_freshness(output, repo, session_id=skill_session, trigger="probe-current")
            _assert_equal(current.get("state"), "current", "fixture current freshness")
            (repo / "fixture.py").write_text("def fixture():\n    return 2\n", encoding="utf-8", newline="\n")
            _git(repo, "add", "fixture.py")
            _git(repo, "commit", "-m", "fixture drift")
            stale = check_fact_freshness(output, repo, session_id=skill_session, trigger="probe-stale")
            _assert(
                str(stale.get("state", "")).startswith("stale"),
                f"fixture stale freshness: {stale.get('state')!r}",
            )
            _assert_equal(stale.get("stable_facts_current"), False, "stale stable_facts_current")
        finally:
            state_path.write_bytes(state_bytes)

        closed = close_session(
            harness="generic",
            session_id=skill_session,
            output=output,
            root=session_root,
            reason="probe-resident-complete",
            timeout=5,
        )
        _assert_equal(closed.get("status"), "closed", "resident session close")

        with _environment_value("CKB_SESSION_STDIO_ROOT", str(session_root)):
            fallback_applied = ingest_event(
                "generic",
                {
                    "canonical_type": "skill.applied",
                    "event_id": f"fallback-skill-application-{run_token}",
                    "session_id": fallback_session,
                    "cwd": str(repo),
                    "skill_name": "code-knowledge-builder",
                    "ckb_skill_applied": True,
                },
                registry,
            )
        _assert_equal(fallback_applied.get("status"), "recorded", "fallback skill application")
        close_session(
            harness="generic",
            session_id=fallback_session,
            output=output,
            root=session_root,
            reason="prepare-cli-fallback",
            timeout=5,
        )
        wrapper = fixture_root / "stdio-failover.py"
        _fallback_wrapper(wrapper, ckb)
        fallback = request_session(
            harness="generic",
            session_id=fallback_session,
            output=output,
            root=session_root,
            executable=Path(sys.executable),
            ckb=wrapper,
            request={
                "id": "fallback-brief",
                "method": "brief",
                "question": question,
                "budget": 900,
                "max_pages": 4,
                "profile": "fast",
            },
            start_timeout=2,
            request_timeout=15,
        )
        _assert_equal(fallback.get("status"), "passed", "CLI fallback status")
        _assert_equal(fallback.get("mode"), "cli-fallback", "CLI fallback mode")
        _assert_equal(fallback.get("resident"), False, "CLI fallback resident flag")
        _assert_equal(fallback.get("cli_exit_status"), 0, "CLI fallback exit status")
        _assert_equal(
            ((fallback.get("response") or {}).get("result") or {}).get("status"),
            "passed",
            "CLI fallback brief result",
        )

        cleanup_sessions(root=session_root)
        lifecycle_audit = audit_sessions(root=session_root)
        _assert_equal(lifecycle_audit.get("active"), 0, "stdio lifecycle active leases")
        _assert(
            not any((lifecycle_audit.get("object_counts") or {}).values()),
            f"stdio lifecycle leaked objects: {lifecycle_audit.get('object_counts')}",
        )
        atexit.unregister(cleanup_probe_sessions)

        return {
            "schema_version": 1,
            "status": "passed",
            "fixture": {
                "root": str(fixture_root),
                "project_instruction_files": {
                    relative.as_posix(): (repo / relative).exists() for relative in INSTRUCTION_PATHS
                },
                "initial_head": initial_head,
                "final_head": _git(repo, "rev-parse", "HEAD"),
            },
            "skill_missing": {
                "ckb_applied": False,
                "start_reason": missing_start.get("reason"),
                "prompt_reason": missing_prompt.get("reason"),
                "counter_delta": {
                    field: int(after_missing[field]) - int(before_missing[field]) for field in COUNT_FIELDS
                },
                "brief": None,
            },
            "skill_only": {
                "ckb_applied": True,
                "activation_source": applied_source,
                "brief": {
                    "status": brief.get("status"),
                    "profile": brief.get("profile"),
                    "transport": brief.get("session_stdio"),
                    "pack": _file_evidence(pack),
                    "record": _file_evidence(record),
                },
                "open_feedback": feedback.get("count"),
                "open_gaps": gaps.get("count"),
                "source": {
                    "status": source.get("status"),
                    "source_path": source.get("source_path"),
                    "start_line": source.get("start_line"),
                    "end_line": source.get("end_line"),
                },
                "needs_source_read": {
                    "status": source_read.get("status"),
                    "pack": source_read.get("pack"),
                    "record": source_read.get("record"),
                },
                "freshness": {
                    "before": current.get("state"),
                    "after": stale.get("state"),
                    "changed_paths": (stale.get("change_summary") or {}).get("changed_paths"),
                },
                "maintenance": {
                    "status": maintenance.get("status"),
                    "failed_checks": maintenance.get("failed_checks"),
                    "page_writes": maintenance.get("page_writes"),
                },
                "cli_fallback": {
                    "status": fallback.get("status"),
                    "mode": fallback.get("mode"),
                    "resident": fallback.get("resident"),
                    "cli_exit_status": fallback.get("cli_exit_status"),
                    "brief_status": ((fallback.get("response") or {}).get("result") or {}).get("status"),
                },
            },
            "stdio_audit": {
                "status": lifecycle_audit.get("status"),
                "active": lifecycle_audit.get("active"),
                "object_counts": lifecycle_audit.get("object_counts"),
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="在不提供项目级 Agent 指令的隔离目录中验证 CKB Skill 激活与检索闭环。"
    )
    parser.add_argument("--out", type=Path, required=True, help="可写的隔离 CKB OUTPUT；探针会生成 pack、日志和自动化记录。")
    parser.add_argument("--ckb", type=Path, default=ROOT / "scripts/ckb.py")
    parser.add_argument("--write", type=Path, required=True)
    args = parser.parse_args()
    result = run_probe(args.out, args.ckb)
    target = args.write.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    reopened = json.loads(target.read_text(encoding="utf-8"))
    _assert_equal(reopened.get("status"), "passed", "reopened probe report")
    print(json.dumps({**result, "report": _file_evidence(target)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
