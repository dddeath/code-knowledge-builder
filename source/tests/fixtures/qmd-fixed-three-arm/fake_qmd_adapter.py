from __future__ import annotations

import json
import os
import sys


mode = os.environ.get("FAKE_QMD_MODE")
command = sys.argv[1] if len(sys.argv) > 1 else ""

if mode == "process-failure":
    print("fixture QMD process failure", file=sys.stderr)
    raise SystemExit(7)

identity = {
    "package_name": "@tobilu/qmd",
    "package_version": "2.8.3",
    "build_commit": "facd35e",
    "node_version": "v24.19.0",
}

if command == "build" and mode == "build-output-drift":
    print(json.dumps({"schema_version": 2, "kind": "changed-build"}))
elif command == "query" and mode == "query-output-drift":
    print(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "qmd-query",
                "identity": identity,
                "question_id": "q01",
                "cache_state": "cold",
                "run_index": 1,
                "latency_ms": 1.0,
                "results": [{"file": "000000.md", "score": 0.5}],
            }
        )
    )
else:
    print(json.dumps({"schema_version": 1, "kind": "unexpected-fixture-mode"}))
