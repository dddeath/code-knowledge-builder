from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any

from .benchmark import load_records, recompute
from .contracts import (
    TagNavigationError,
    atomic_write_json,
    canonical_json_bytes,
    ensure_within,
    sha256_file,
    validate_policy,
)
from .projection import build_projection
from .state_machine import audit_database
from .store import replay_with_rollback, rollback


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TagNavigationError("INVALID_JSON", f"{path} 根必须是对象")
    return value


def _write_result(path: Path, value: dict[str, Any], workspace: Path) -> dict[str, Any]:
    output = ensure_within(path, workspace, "out")
    atomic_write_json(output, value)
    return {**value, "output": str(output), "output_sha256": sha256_file(output)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ckb-tag-navigation")
    commands = parser.add_subparsers(dest="command", required=True)

    replay = commands.add_parser("replay")
    replay.add_argument("--input", type=Path, required=True)
    replay.add_argument("--database", type=Path, required=True)
    replay.add_argument("--rollback-manifest", type=Path, required=True)
    replay.add_argument("--workspace-root", type=Path, required=True)

    audit = commands.add_parser("audit")
    audit.add_argument("--database", type=Path, required=True)
    audit.add_argument("--policy", type=Path, required=True)
    audit.add_argument("--current-commit", required=True)
    audit.add_argument("--as-of", required=True)
    audit.add_argument("--out", type=Path, required=True)
    audit.add_argument("--workspace-root", type=Path, required=True)

    project = commands.add_parser("project")
    project.add_argument("--audit", type=Path, required=True)
    project.add_argument("--policy", type=Path, required=True)
    project.add_argument("--out", type=Path, required=True)
    project.add_argument("--workspace-root", type=Path, required=True)

    benchmark = commands.add_parser("benchmark")
    benchmark.add_argument("--fixture", type=Path, required=True)
    benchmark.add_argument("--records", type=Path, required=True)
    benchmark.add_argument("--out", type=Path, required=True)
    benchmark.add_argument("--workspace-root", type=Path, required=True)

    rollback_parser = commands.add_parser("rollback")
    rollback_parser.add_argument("--manifest", type=Path, required=True)
    rollback_parser.add_argument("--workspace-root", type=Path, required=True)
    return parser


def execute(arguments: argparse.Namespace) -> dict[str, Any]:
    if arguments.command == "replay":
        workspace = arguments.workspace_root.resolve()
        database = ensure_within(arguments.database, workspace, "database")
        manifest = ensure_within(arguments.rollback_manifest, workspace, "rollback-manifest")
        return replay_with_rollback(arguments.input.resolve(), database, manifest)
    if arguments.command == "audit":
        policy = validate_policy(_json(arguments.policy))
        result = audit_database(arguments.database.resolve(), policy, arguments.current_commit, arguments.as_of)
        return _write_result(arguments.out, result, arguments.workspace_root)
    if arguments.command == "project":
        policy = validate_policy(_json(arguments.policy))
        result = build_projection(_json(arguments.audit), policy)
        return _write_result(arguments.out, result, arguments.workspace_root)
    if arguments.command == "benchmark":
        result = recompute(_json(arguments.fixture), load_records(arguments.records))
        return _write_result(arguments.out, result, arguments.workspace_root)
    if arguments.command == "rollback":
        return rollback(arguments.manifest.resolve(), arguments.workspace_root.resolve())
    raise AssertionError(arguments.command)


def main(argv: list[str] | None = None) -> int:
    try:
        result = execute(build_parser().parse_args(argv))
    except (TagNavigationError, OSError, json.JSONDecodeError, sqlite3.Error) as exc:
        if isinstance(exc, TagNavigationError):
            reason = exc.reason
            detail = exc.detail
        else:
            reason = "IO_OR_JSON_ERROR"
            detail = str(exc)
        sys.stdout.buffer.write(canonical_json_bytes({"schema_version": 1, "status": "failed", "reason": reason, "detail": detail}))
        return 2
    sys.stdout.buffer.write(canonical_json_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
