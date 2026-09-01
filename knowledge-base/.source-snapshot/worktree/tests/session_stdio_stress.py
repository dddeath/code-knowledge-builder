from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.session_stdio import (
    activate_session_stdio,
    audit_sessions,
    close_session,
    process_metrics,
    request_session,
)


def one_cycle(output: Path, root: Path, session_id: str) -> dict[str, object]:
    activation = activate_session_stdio(harness="generic", session_id=session_id, output=output, root=root)
    if activation.get("status") != "ready":
        raise RuntimeError(f"activation failed: {activation}")
    request = request_session(
        harness="generic",
        session_id=session_id,
        output=output,
        root=root,
        request={"id": f"ping:{session_id}", "method": "ping"},
        require_activation=False,
    )
    if request.get("status") != "passed" or not request.get("resident"):
        raise RuntimeError(f"resident request failed: {request}")
    closed = close_session(harness="generic", session_id=session_id, output=output, root=root, reason="stress-cycle")
    if closed.get("status") != "closed":
        raise RuntimeError(f"close failed: {closed}")
    return {
        "session_id": session_id,
        "supervisor_pid": activation.get("supervisor_pid"),
        "server_pid": activation.get("server_pid"),
        "request_server_pid": request.get("server_pid"),
        "close_status": closed.get("status"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=50)
    parser.add_argument("--write", type=Path, required=True)
    args = parser.parse_args()
    warmup = one_cycle(args.out.resolve(), args.root.resolve(), "stress-warmup")
    gc.collect()
    baseline = process_metrics()
    cycles = [one_cycle(args.out.resolve(), args.root.resolve(), f"stress-{index:03d}") for index in range(args.cycles)]
    gc.collect()
    final = process_metrics()
    audit = audit_sessions(root=args.root.resolve())
    rss_delta = int(final["rss_bytes"]) - int(baseline["rss_bytes"])
    handle_delta = int(final["handles"]) - int(baseline["handles"])
    status = (
        "passed"
        if audit.get("status") == "passed"
        and audit.get("active") == 0
        and not any(int(value) for value in audit.get("object_counts", {}).values())
        and rss_delta <= 16 * 1024 * 1024
        and handle_delta <= 8
        else "failed"
    )
    result = {
        "schema_version": 1,
        "status": status,
        "cycles": args.cycles,
        "warmup": warmup,
        "baseline": baseline,
        "final": final,
        "rss_delta_bytes": rss_delta,
        "handle_delta": handle_delta,
        "limits": {"rss_bytes": 16 * 1024 * 1024, "handles": 8},
        "audit": audit,
        "pid_reuse_checks": [item["server_pid"] == item["request_server_pid"] for item in cycles],
        "cycle_evidence": cycles,
    }
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if status == "passed" else 5


if __name__ == "__main__":
    raise SystemExit(main())
