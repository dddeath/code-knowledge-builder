"""Deterministic CLI double for command-shape and projection-parity tests."""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path


REVISION = "fab27740975dcda1e93dbca718d1f620eda543c7"


def option(args: list[str], name: str) -> str | None:
    if name not in args:
        return None
    index = args.index(name)
    return args[index + 1] if index + 1 < len(args) else None


def main() -> int:
    args = sys.argv[1:]
    if "--version" in args:
        print(REVISION)
        return 0
    root_value = option(args, "--root-dir")
    root = Path(root_value) if root_value else Path.cwd()
    root.mkdir(parents=True, exist_ok=True)
    counts_path = root / "fake-counts.json"
    if "server" in args and "stop" in args:
        print("stopped")
        return 0
    if "graph" in args and "import" in args:
        input_path = Path(option(args, "--input") or "")
        text = input_path.read_text(encoding="utf-8")
        counts = {
            "pages": len(re.findall("页面说明：", text)),
            "page_entities": len(re.findall("源码入口：", text)),
            "appendix_entities": len(re.findall("内部实现：", text)),
            "boundary_entities": len(re.findall("边界协作：", text)),
            "relations": len(re.findall("(?<!边界)协作：", text)),
        }
        counts_path.write_text(json.dumps(counts), encoding="utf-8")
        print("imported")
        return 0
    if "graph" in args and "validate" in args:
        print("validated")
        return 0
    if "query" in args:
        query = option(args, "--query") or ""
        counts = json.loads(counts_path.read_text(encoding="utf-8"))
        if "页面说明" in query:
            name = "pages"
        elif "源码入口" in query:
            name = "page_entities"
        elif "内部实现" in query:
            name = "appendix_entities"
        elif "边界协作" in query:
            name = "boundary_entities"
        elif "协作" in query:
            name = "relations"
        else:
            return 2
        print(json.dumps({"status": "ok", "data": {"result": counts[name]}}))
        return 0
    if "graph" in args and "export" in args:
        file_path = Path(option(args, "--file") or "")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(file_path) as connection:
            connection.execute("CREATE TABLE ckb_probe (value TEXT NOT NULL)")
            connection.execute("INSERT INTO ckb_probe VALUES (?)", (REVISION,))
        print("exported")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
