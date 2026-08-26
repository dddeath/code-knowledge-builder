#!/usr/bin/env python3
"""Write a text-only unified patch for the Skill against an empty baseline."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "__pycache__", ".pytest_cache", "assets"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    chunks: list[str] = []
    for path in sorted(ROOT.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or any(part in SKIP for part in path.relative_to(ROOT).parts) or path.suffix in {".pyc", ".pyo", ".zip"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = (Path("code-knowledge-builder") / path.relative_to(ROOT)).as_posix()
        diff = "".join(difflib.unified_diff([], text.splitlines(keepends=True), fromfile="/dev/null", tofile=f"b/{relative}", n=3))
        if not diff.endswith("\n"):
            diff += "\n"
        chunks.append(f"diff --git a/{relative} b/{relative}\nnew file mode 100644\n" + diff)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(chunks), encoding="utf-8", newline="\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
