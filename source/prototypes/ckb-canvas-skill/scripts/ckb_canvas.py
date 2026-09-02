#!/usr/bin/env python3
"""独立 CKB Canvas 实验命令薄入口。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_ROOT.parent.parent
for item in (REPO_ROOT, SKILL_ROOT):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from ckb_canvas.commands import generate, rollback, validate_only  # noqa: E402
from ckb_canvas.contracts import CanvasFailure  # noqa: E402
from ckb_canvas.graph import canonical_json_bytes  # noqa: E402


class StrictParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parser() -> argparse.ArgumentParser:
    parser = StrictParser(prog="ckb_canvas.py")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--request", required=True)
    generate_parser = commands.add_parser("generate")
    generate_parser.add_argument("--request", required=True)
    rollback_parser = commands.add_parser("rollback")
    rollback_parser.add_argument("--manifest", required=True)
    rollback_parser.add_argument("--expected-sha256", required=True)
    benchmark_parser = commands.add_parser("benchmark")
    benchmark_parser.add_argument("--run", required=True)
    benchmark_parser.add_argument("--session", required=True)
    summarize_parser = commands.add_parser("summarize")
    summarize_parser.add_argument("--run", required=True)
    summarize_parser.add_argument("--sessions", required=True)
    summarize_parser.add_argument("--write", required=True)
    return parser


def _emit(value: dict) -> None:
    sys.stdout.buffer.write(canonical_json_bytes(value))
    sys.stdout.buffer.flush()


def main(argv: list[str] | None = None) -> int:
    operation = "generate"
    try:
        args = _parser().parse_args(argv)
        operation = args.command
        if args.command == "validate":
            value = validate_only(args.request)
        elif args.command == "generate":
            value = generate(args.request).to_dict()
        elif args.command == "rollback":
            value = rollback(args.manifest, args.expected_sha256)
        elif args.command == "benchmark":
            from ckb_canvas.benchmark import run_session

            value = run_session(args.run, args.session)
        else:
            from ckb_canvas.benchmark import summarize_to_path

            value = summarize_to_path(args.run, args.sessions, args.write)
        _emit(value)
        return 0
    except CanvasFailure as exc:
        exc.operation = "benchmark" if operation in {"benchmark", "summarize"} else operation
        print(f"{exc.phase}: {exc.detail}", file=sys.stderr)
        _emit(exc.to_dict())
        return exc.exit_code
    except ValueError as exc:
        failure = CanvasFailure(
            "invalid_request",
            "request",
            f"command arguments are invalid: {exc}",
            operation="benchmark" if operation in {"benchmark", "summarize"} else operation,
            target_path="TARGET.canvas",
        )
        print(f"request: {failure.detail}", file=sys.stderr)
        _emit(failure.to_dict())
        return 2
    except Exception as exc:  # 稳定 CLI 边界：stdout 不泄露 traceback。
        failure = CanvasFailure(
            "io_failure",
            "benchmark" if operation in {"benchmark", "summarize"} else "staging",
            f"unexpected command failure: {type(exc).__name__}: {exc}",
            operation="benchmark" if operation in {"benchmark", "summarize"} else operation,
            target_path="TARGET.canvas",
        )
        print(f"{failure.phase}: {failure.detail}", file=sys.stderr)
        _emit(failure.to_dict())
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
