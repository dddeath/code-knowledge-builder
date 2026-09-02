#!/usr/bin/env python3
"""冻结 Markdown/Canvas session capture 判定入口。"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "prototypes" / "ckb-canvas-skill"
sys.path[:0] = [str(REPO), str(SKILL)]

from ckb_canvas.benchmark import run_session
from ckb_canvas.graph import canonical_json_bytes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--session", required=True, help="session ID 或明确的 capture JSON 路径")
    args = parser.parse_args(argv)
    result = run_session(args.run, args.session)
    sys.stdout.buffer.write(canonical_json_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
