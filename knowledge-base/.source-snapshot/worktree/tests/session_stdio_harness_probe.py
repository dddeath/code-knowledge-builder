from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.session_stdio import activate_session_stdio


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--session-id", required=True)
    args = parser.parse_args()
    result = activate_session_stdio(
        harness="generic",
        session_id=args.session_id,
        output=args.out,
        root=args.root,
        parent_pid=os.getpid(),
    )
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result.get("status") == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
