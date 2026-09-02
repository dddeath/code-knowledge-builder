from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .contracts import FanoutError, canonical_json_bytes
from .benchmark import aggregate_benchmark, snapshot_read_only
from .generator import generate_fanout, rollback_fanout
from .judge import judge_arm


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ckb-page-fanout")
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate")
    generate.add_argument("--contract", type=Path, required=True)
    generate.add_argument("--corpus", type=Path, required=True)
    generate.add_argument("--source-root", type=Path, required=True)
    generate.add_argument("--conservative-root", type=Path, required=True)
    generate.add_argument("--out", type=Path, required=True)
    generate.add_argument("--rollback-manifest", type=Path, required=True)
    generate.add_argument("--workspace-root", type=Path, required=True)

    rollback = commands.add_parser("rollback")
    rollback.add_argument("--manifest", type=Path, required=True)
    rollback.add_argument("--workspace-root", type=Path, required=True)

    judge = commands.add_parser("judge")
    judge.add_argument("--judge-contract", type=Path, required=True)
    judge.add_argument("--projection-root", type=Path, required=True)
    judge.add_argument("--source-root", type=Path, required=True)
    judge.add_argument("--out", type=Path, required=True)
    judge.add_argument("--workspace-root", type=Path, required=True)

    snapshot = commands.add_parser("snapshot-read-only")
    snapshot.add_argument("--root", type=Path, required=True)
    snapshot.add_argument("--out", type=Path, required=True)
    snapshot.add_argument("--workspace-root", type=Path, required=True)

    aggregate = commands.add_parser("aggregate")
    aggregate.add_argument("--contract", type=Path, required=True)
    aggregate.add_argument("--corpus", type=Path, required=True)
    aggregate.add_argument("--arm-a", type=Path, required=True)
    aggregate.add_argument("--arm-b", type=Path, required=True)
    aggregate.add_argument("--read-only-before", type=Path, required=True)
    aggregate.add_argument("--read-only-after", type=Path, required=True)
    aggregate.add_argument("--out", type=Path, required=True)
    aggregate.add_argument("--workspace-root", type=Path, required=True)
    return parser


def execute(arguments: argparse.Namespace) -> dict[str, object]:
    if arguments.command == "generate":
        return generate_fanout(
            contract_path=arguments.contract,
            corpus_path=arguments.corpus,
            source_root=arguments.source_root,
            conservative_root=arguments.conservative_root,
            output_root=arguments.out,
            rollback_manifest=arguments.rollback_manifest,
            workspace_root=arguments.workspace_root,
        )
    if arguments.command == "rollback":
        return rollback_fanout(arguments.manifest, arguments.workspace_root)
    if arguments.command == "judge":
        result = judge_arm(
            judge_contract_path=arguments.judge_contract,
            projection_root=arguments.projection_root,
            source_root=arguments.source_root,
        )
        output = arguments.out.resolve()
        workspace = arguments.workspace_root.resolve()
        from .contracts import atomic_write_json, ensure_within

        atomic_write_json(ensure_within(output, workspace, "out"), result)
        return {**result, "output": str(output)}
    if arguments.command == "snapshot-read-only":
        result = snapshot_read_only(arguments.root)
        output = arguments.out.resolve()
        workspace = arguments.workspace_root.resolve()
        from .contracts import atomic_write_json, ensure_within

        atomic_write_json(ensure_within(output, workspace, "out"), result)
        return {**result, "output": str(output)}
    if arguments.command == "aggregate":
        result = aggregate_benchmark(
            contract_path=arguments.contract,
            corpus_path=arguments.corpus,
            arm_a_path=arguments.arm_a,
            arm_b_path=arguments.arm_b,
            read_only_before_path=arguments.read_only_before,
            read_only_after_path=arguments.read_only_after,
        )
        output = arguments.out.resolve()
        workspace = arguments.workspace_root.resolve()
        from .contracts import atomic_write_json, ensure_within

        atomic_write_json(ensure_within(output, workspace, "out"), result)
        return {**result, "output": str(output)}
    raise AssertionError(arguments.command)


def main(argv: list[str] | None = None) -> int:
    try:
        result = execute(build_parser().parse_args(argv))
    except (FanoutError, OSError, json.JSONDecodeError) as exc:
        if isinstance(exc, FanoutError):
            reason, detail = exc.reason, exc.detail
        else:
            reason, detail = "IO_OR_JSON_ERROR", str(exc)
        sys.stdout.buffer.write(canonical_json_bytes({"schema_version": 1, "status": "failed", "reason": reason, "detail": detail}))
        return 2
    sys.stdout.buffer.write(canonical_json_bytes(result))
    return 0
