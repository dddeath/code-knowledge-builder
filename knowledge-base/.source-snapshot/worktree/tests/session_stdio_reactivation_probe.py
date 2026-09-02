from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.session_stdio import activate_session_stdio, audit_sessions, close_session, pid_exists, request_session


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--session-id", default="reactivation-session")
    parser.add_argument("--cycles", type=int, default=10)
    parser.add_argument("--question", default="Agent 会话级 stdio 生命周期")
    parser.add_argument("--write", type=Path, required=True)
    args = parser.parse_args()
    rows: list[dict[str, object]] = []
    server_pids: list[int] = []
    generations: list[str] = []
    status = "passed"
    for index in range(args.cycles):
        activation = activate_session_stdio(
            harness="codex",
            session_id=args.session_id,
            output=args.out,
            root=args.root,
        )
        row: dict[str, object] = {"cycle": index, "activation": activation}
        if activation.get("status") != "ready" or not activation.get("resident"):
            status = "failed"
            rows.append(row)
            break
        request = request_session(
            harness="codex",
            session_id=args.session_id,
            output=args.out,
            root=args.root,
            request={
                "id": f"brief-{index:02d}",
                "method": "brief",
                "question": args.question,
                "budget": 1800,
                "max_pages": 8,
                "profile": "fast",
            },
            require_activation=False,
        )
        row["brief"] = request
        server_pid = int(activation["server_pid"])
        generation = str(activation["generation"])
        valid_request = (
            request.get("status") == "passed"
            and request.get("resident") is True
            and request.get("server_pid") == server_pid
            and isinstance(request.get("response"), dict)
            and request["response"].get("ok") is True
            and isinstance(request["response"].get("result"), dict)
            and request["response"]["result"].get("status") == "passed"
        )
        if not valid_request:
            status = "failed"
            rows.append(row)
            break
        closed = close_session(
            harness="codex",
            session_id=args.session_id,
            output=args.out,
            root=args.root,
            reason="reactivation-probe-close",
        )
        row["closed"] = closed
        row["server_alive_after_close"] = pid_exists(server_pid)
        rows.append(row)
        server_pids.append(server_pid)
        generations.append(generation)
        if closed.get("status") != "closed" or row["server_alive_after_close"]:
            status = "failed"
            break
    gc.collect()
    audit = audit_sessions(root=args.root)
    result = {
        "schema_version": 1,
        "status": status,
        "cycles_requested": args.cycles,
        "cycles_completed": len(server_pids),
        "all_server_pids_unique": len(set(server_pids)) == len(server_pids),
        "all_generations_unique": len(set(generations)) == len(generations),
        "server_pids": server_pids,
        "generations": generations,
        "rows": rows,
        "final_audit": audit,
    }
    if (
        len(server_pids) != args.cycles
        or not result["all_server_pids_unique"]
        or not result["all_generations_unique"]
        or audit.get("active") != 0
        or any(int(value) for value in audit.get("object_counts", {}).values())
    ):
        result["status"] = "failed"
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 5


if __name__ == "__main__":
    raise SystemExit(main())
