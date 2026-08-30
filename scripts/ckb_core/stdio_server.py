"""Single-process JSONL transport for deterministic machine retrieval."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, TextIO

from .agent_protocol import audit_agent_protocol
from .common import CkbError, json_load, json_write
from .feedback import audit_feedback
from .machine_knowledge import retrieve_machine


STDIO_RETRIEVAL_PROTOCOL = "ckb-stdio-retrieval"
STDIO_RETRIEVAL_PROTOCOL_VERSION = 2
_IDEMPOTENCY_KEY = re.compile(r"[A-Za-z0-9._:-]{1,160}")


def _write_line(stream: TextIO, value: dict[str, Any]) -> None:
    # JSON escapes keep the transport valid even when a Windows host exposes a
    # legacy console code page.  Receivers recover the original Unicode value.
    stream.write(json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n")
    stream.flush()


def _integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise CkbError(f"stdio request {name} must be an integer in [{minimum}, {maximum}]")
    return value


def _utf8_safe(value: str) -> str:
    """Replace lone UTF-16 surrogate code points before UTF-8 consumers see them."""
    return "".join("\ufffd" if 0xD800 <= ord(character) <= 0xDFFF else character for character in value)


def _required_text(request: dict[str, Any], name: str, maximum: int) -> str:
    value = request.get(name)
    if not isinstance(value, str) or not value.strip():
        raise CkbError(f"stdio record-explanation {name} must be a non-empty string")
    value = _utf8_safe(value).strip()
    if len(value) > maximum:
        raise CkbError(f"stdio record-explanation {name} exceeds {maximum} characters")
    return value


def _record_explanation(
    output: Path,
    request: dict[str, Any],
    retrieval: dict[str, Any],
) -> dict[str, Any]:
    """Persist one provider explanation without a second tool-using Agent turn."""
    retrieval_id = _required_text(request, "retrieval_request_id", 200)
    pack_text = _required_text(request, "pack", 4_096)
    question = _required_text(request, "question", 12_000)
    selected_text = _required_text(request, "selected_text", 24_000)
    source_path = _required_text(request, "source_path", 4_096)
    source_title = _required_text(request, "source_title", 512)
    explanation = _required_text(request, "explanation", 40_000)
    idempotency_key = _required_text(request, "idempotency_key", 160)
    if not _IDEMPOTENCY_KEY.fullmatch(idempotency_key):
        raise CkbError("stdio record-explanation idempotency_key contains unsupported characters")
    if retrieval_id != str(retrieval.get("request_id") or ""):
        raise CkbError("stdio record-explanation retrieval request does not match this server session")
    expected_pack = Path(str(retrieval.get("pack") or "")).resolve()
    pack = Path(pack_text).resolve()
    pack_root = (output / "machine" / "agent-packs").resolve()
    try:
        pack.relative_to(pack_root)
    except ValueError as exc:
        raise CkbError("stdio record-explanation pack is outside machine/agent-packs") from exc
    if pack != expected_pack or not pack.is_file():
        raise CkbError("stdio record-explanation pack does not match the completed retrieval")
    query_record = Path(str(retrieval.get("record") or "")).resolve()
    try:
        query_record.relative_to(pack_root)
    except ValueError as exc:
        raise CkbError("stdio record-explanation retrieval record is outside machine/agent-packs") from exc
    if not query_record.is_file():
        raise CkbError("stdio record-explanation retrieval record is missing")
    pack_record = json_load(query_record)
    if pack_record.get("status") != "passed" or not pack_record.get("source_grounded"):
        raise CkbError("stdio record-explanation requires a passed, source-grounded Agent pack")

    idempotency_root = output / "workspace-meta" / "stdio" / "idempotency"
    idempotency_root.mkdir(parents=True, exist_ok=True)
    idempotency_path = idempotency_root / (idempotency_key.replace(":", "_") + ".json")
    if idempotency_path.is_file():
        previous = json_load(idempotency_path)
        if previous.get("status") != "passed":
            raise CkbError("stdio record-explanation idempotency record is incomplete")
        return previous

    evidence_root = output / "workspace-meta" / "stdio" / "explanations"
    evidence_root.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_root / (idempotency_key.replace(":", "_") + ".json")
    evidence = {
        "schema_version": 1,
        "status": "pending-audit",
        "kind": "learning-explanation-evidence",
        "retrieval_request_id": retrieval_id,
        "pack": str(pack),
        "query_record": str(query_record),
        "source_path": source_path,
        "source_title": source_title,
        "question": question,
        "selected_text": selected_text,
        "explanation": explanation,
    }
    json_write(evidence_path, evidence)
    feedback = audit_feedback(output)
    policy = audit_agent_protocol(output)
    if feedback.get("status") != "passed" or policy.get("status") != "passed":
        evidence["status"] = "failed"
        json_write(evidence_path, evidence)
        raise CkbError("stdio record-explanation audit failed")
    evidence.update(
        {
            "status": "passed",
            "feedback_audit": str((output / "workspace-meta" / "feedback-audit.json").resolve()),
            "agent_policy_audit": str((output / "workspace-meta" / "agent-protocol-audit.json").resolve()),
        }
    )
    json_write(evidence_path, evidence)
    result = {
        "schema_version": 1,
        "status": "passed",
        "retrieval_request_id": retrieval_id,
        "pack": str(pack),
        "evidence": str(evidence_path.resolve()),
        # Kept for one-version transport compatibility. It is machine evidence,
        # never a human analysis page.
        "record": str(evidence_path.resolve()),
        "compatibility_record": None,
        "feedback_audit": str((output / "workspace-meta" / "feedback-audit.json").resolve()),
        "agent_policy_audit": str((output / "workspace-meta" / "agent-protocol-audit.json").resolve()),
    }
    json_write(idempotency_path, result)
    return result


def serve_stdio(
    output: Path,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    retrieve: Callable[[Path, str, int, int, str], dict[str, Any]] | None = None,
    record_explanation: Callable[[Path, dict[str, Any], dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Serve newline-delimited retrieval requests until shutdown or EOF.

    The transport is deliberately local and single-threaded.  Every response
    is one compact JSON line, so a Harness can keep this process alive for one
    task without opening a port or introducing a service dependency.
    """

    output = output.resolve()
    if not (output / "machine/knowledge.sqlite").is_file():
        raise CkbError("machine knowledge is missing; run finalize or machine-reindex")
    if input_stream is None and hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="strict", newline="\n")
    if output_stream is None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="strict", newline="\n", write_through=True)
    source = input_stream or sys.stdin
    destination = output_stream or sys.stdout
    retrieve_value = retrieve or retrieve_machine
    record_value = record_explanation or _record_explanation
    retrievals: dict[str, dict[str, Any]] = {}
    handled = 0
    succeeded = 0
    failed = 0
    shutdown = False
    for raw_line in source:
        line = raw_line.strip()
        if not line:
            continue
        handled += 1
        request_id: Any = None
        method: Any = None
        started = time.perf_counter_ns()
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise CkbError("stdio request must be a JSON object")
            request_id = request.get("id")
            if not isinstance(request_id, (str, int)) or isinstance(request_id, bool):
                raise CkbError("stdio request id must be a string or integer")
            method = request.get("method")
            if method == "ping":
                result = {
                    "status": "ready",
                    "protocol": STDIO_RETRIEVAL_PROTOCOL,
                    "protocol_version": STDIO_RETRIEVAL_PROTOCOL_VERSION,
                    "output": str(output),
                    "methods": ["ping", "retrieve", "record-explanation", "shutdown"],
                }
            elif method == "retrieve":
                question = request.get("question")
                if not isinstance(question, str) or not question.strip():
                    raise CkbError("stdio retrieve question must be a non-empty string")
                question = _utf8_safe(question).strip()
                budget = _integer(request.get("budget", 1500), "budget", 200, 1_000_000)
                max_pages = _integer(request.get("max_pages", 8), "max_pages", 1, 32)
                profile = request.get("profile", "fast")
                if profile not in {"fast", "precise"}:
                    raise CkbError("stdio retrieve profile must be fast or precise")
                result = retrieve_value(output, question, budget, max_pages, profile)
                if result.get("status") != "passed" or not result.get("pack"):
                    raise CkbError("stdio retrieve did not return a passed Agent pack")
                retrievals[str(request_id)] = {**result, "request_id": str(request_id)}
            elif method == "record-explanation":
                retrieval_id = request.get("retrieval_request_id")
                if not isinstance(retrieval_id, (str, int)) or isinstance(retrieval_id, bool):
                    raise CkbError("stdio record-explanation retrieval_request_id must be a string or integer")
                retrieval = retrievals.get(str(retrieval_id))
                if retrieval is None:
                    raise CkbError("stdio record-explanation requires a completed retrieval from this server session")
                result = record_value(output, request, retrieval)
            elif method == "shutdown":
                result = {"status": "shutting-down"}
                shutdown = True
            else:
                raise CkbError("stdio request method must be ping, retrieve, record-explanation, or shutdown")
            succeeded += 1
            _write_line(
                destination,
                {
                    "id": request_id,
                    "ok": True,
                    "method": method,
                    "elapsed_ms": round((time.perf_counter_ns() - started) / 1_000_000, 6),
                    "result": result,
                },
            )
        except (json.JSONDecodeError, CkbError) as exc:
            failed += 1
            _write_line(
                destination,
                {
                    "id": request_id,
                    "ok": False,
                    "method": method,
                    "elapsed_ms": round((time.perf_counter_ns() - started) / 1_000_000, 6),
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "exit_code": exc.exit_code if isinstance(exc, CkbError) else 2,
                    },
                },
            )
        except Exception as exc:
            failed += 1
            _write_line(
                destination,
                {
                    "id": request_id,
                    "ok": False,
                    "method": method,
                    "elapsed_ms": round((time.perf_counter_ns() - started) / 1_000_000, 6),
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "exit_code": 1,
                    },
                },
            )
        if shutdown:
            break
    return {
        "schema_version": 1,
        "status": "stopped",
        "protocol": STDIO_RETRIEVAL_PROTOCOL,
        "protocol_version": STDIO_RETRIEVAL_PROTOCOL_VERSION,
        "requests": handled,
        "succeeded": succeeded,
        "failed": failed,
        "shutdown_requested": shutdown,
    }
