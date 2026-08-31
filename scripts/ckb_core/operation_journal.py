"""Bounded, privacy-filtered machine operation journal for completed CKB commands."""

from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import date, timedelta
import json
import os
from pathlib import Path, PurePosixPath
import re
import time
from typing import Any, Iterator

from .common import CkbError, json_load, json_write, path_inside, stable_id, utc_now


OPERATION_JOURNAL_SCHEMA_VERSION = 1
OPERATION_TYPES = ("compile", "query", "record", "audit", "maintenance")
MAX_RECORDS_PER_SHARD = 2_000
MAX_SHARD_BYTES = 1_048_576
RETENTION_DAYS = 30
LATEST_EVENT_LIMIT = 20
_EVENT_FIELDS = {
    "schema_version",
    "event_id",
    "recorded_at_utc",
    "operation",
    "command",
    "result_status",
    "evidence_paths",
}
_SAFE_TOKEN = re.compile(r"^[a-z0-9][a-z0-9:._-]{0,79}$")
_SHARD_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.jsonl$")
_EVIDENCE_KEYS = {
    "audit",
    "compatibility_file",
    "file",
    "human_file",
    "manifest",
    "pack",
    "path",
    "record",
    "report",
    "review_template",
    "source",
}


def _root(output: Path) -> Path:
    return output.resolve() / "workspace-meta/operations"


@contextmanager
def _journal_lock(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".lock"
    deadline = time.monotonic() + 5.0
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, str(os.getpid()).encode("ascii"))
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > 30:
                    lock.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise CkbError(f"operation journal is busy: {lock}")
            time.sleep(0.05)
    try:
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        lock.unlink(missing_ok=True)


def _read_shard(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.is_file():
        return records
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CkbError(f"invalid operation journal JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise CkbError(f"operation journal record must be an object: {path}:{line_number}")
        records.append(value)
    return records


def _serialized_lines(records: list[dict[str, Any]]) -> bytes:
    return ("".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in records)).encode("utf-8")


def _write_shard(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(_serialized_lines(records))
    os.replace(temporary, path)


def _state(root: Path) -> dict[str, Any]:
    path = root / "state.json"
    if not path.is_file():
        return {
            "schema_version": OPERATION_JOURNAL_SCHEMA_VERSION,
            "dropped_records": 0,
            "expired_records": 0,
            "deduplicated_records": 0,
        }
    value = json_load(path)
    if not isinstance(value, dict):
        raise CkbError(f"operation journal state must be an object: {path}")
    return value


def _retention_cutoff(today: date) -> date:
    return today - timedelta(days=RETENTION_DAYS - 1)


def _prune_expired(root: Path, today: date, state: dict[str, Any]) -> None:
    cutoff = _retention_cutoff(today)
    for path in sorted(root.glob("*.jsonl")):
        matched = _SHARD_NAME.fullmatch(path.name)
        if not matched:
            continue
        shard_date = date.fromisoformat(matched.group(1))
        if shard_date >= cutoff:
            continue
        state["expired_records"] = int(state.get("expired_records", 0)) + len(_read_shard(path))
        path.unlink()


def _all_events(root: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.jsonl")):
        if _SHARD_NAME.fullmatch(path.name):
            events.extend(_read_shard(path))
    return events


def _latest_summary(root: Path, events: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    shards = []
    for path in sorted(root.glob("*.jsonl")):
        matched = _SHARD_NAME.fullmatch(path.name)
        if not matched:
            continue
        shard_events = _read_shard(path)
        shards.append(
            {
                "date": matched.group(1),
                "path": path.name,
                "records": len(shard_events),
                "bytes": path.stat().st_size,
            }
        )
    by_operation = Counter(str(item.get("operation")) for item in events)
    by_status = Counter(str(item.get("result_status")) for item in events)
    return {
        "schema_version": OPERATION_JOURNAL_SCHEMA_VERSION,
        "status": "passed",
        "updated_at_utc": utc_now(),
        "retention_days": RETENTION_DAYS,
        "max_records_per_shard": MAX_RECORDS_PER_SHARD,
        "max_shard_bytes": MAX_SHARD_BYTES,
        "records": len(events),
        "counts_by_operation": {name: by_operation.get(name, 0) for name in OPERATION_TYPES},
        "counts_by_status": dict(sorted(by_status.items())),
        "shards": shards,
        "latest": events[-LATEST_EVENT_LIMIT:],
        "bounded_drops": {
            "size_or_count": int(state.get("dropped_records", 0)),
            "retention": int(state.get("expired_records", 0)),
            "deduplicated": int(state.get("deduplicated_records", 0)),
        },
    }


def _relative_evidence(output: Path, result: dict[str, Any]) -> list[str]:
    evidence: set[str] = set()
    for key in sorted(_EVIDENCE_KEYS):
        value = result.get(key)
        values = value if isinstance(value, list) else [value]
        for candidate in values:
            if not isinstance(candidate, str) or not candidate.strip():
                continue
            path = Path(candidate)
            if not path.is_absolute():
                path = output / path
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if not resolved.exists() or not path_inside(resolved, output):
                continue
            evidence.add(resolved.relative_to(output).as_posix())
    return sorted(evidence)[:8]


def _command_name(args: Any) -> str:
    command = str(getattr(args, "command", "")).strip().lower()
    nested_fields = (
        "migration_command",
        "reference_command",
        "feedback_command",
        "workspace_command",
        "agent_policy_command",
        "automation_command",
    )
    for field in nested_fields:
        value = getattr(args, field, None)
        if value:
            return f"{command}:{str(value).strip().lower()}"
    if command == "audit":
        return "audit:global" if getattr(args, "global_audit", False) else "audit:chunk"
    if command == "record":
        kind = str(getattr(args, "kind", "")).strip().lower()
        return f"record:{kind}" if kind else command
    return command


def _operation_type(command: str) -> str | None:
    root = command.split(":", 1)[0]
    if root in {"init", "run", "build-chunk", "review-chunk", "review-pack", "merge", "finalize", "human-refresh", "reindex", "migrate", "relink"}:
        return "compile"
    if root in {"query", "retrieve", "brief", "context", "coverage", "entity", "neighbors", "source", "changes", "path", "explain", "status"}:
        return "query"
    if root == "maintain":
        return "maintenance"
    if root == "audit" or command in {"reference:audit", "feedback:audit", "agent-policy:check", "migrate:audit"}:
        return "audit"
    if root == "record" or command in {
        "reference:ingest",
        "reference:review",
        "reference:rollback",
        "feedback:create",
        "feedback:resolve",
        "workspace:session-start",
        "workspace:session-finish",
        "automation:review",
    }:
        return "record"
    return None


def record_operation(output: Path, operation: str, command: str, result_status: str, evidence_paths: list[str]) -> dict[str, Any]:
    output = output.resolve()
    if operation not in OPERATION_TYPES:
        raise CkbError(f"unsupported operation journal type: {operation}")
    command = command.strip().lower()
    result_status = result_status.strip().lower() or "completed"
    if not _SAFE_TOKEN.fullmatch(command) or not _SAFE_TOKEN.fullmatch(result_status):
        raise CkbError("operation journal command and status must use bounded machine tokens")
    normalized_evidence = []
    for value in sorted(set(evidence_paths))[:8]:
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or not value.strip():
            raise CkbError(f"operation evidence must be relative to OUTPUT: {value}")
        normalized_evidence.append(path.as_posix())
    stamp = utc_now()
    day = stamp[:10]
    event = {
        "schema_version": OPERATION_JOURNAL_SCHEMA_VERSION,
        "event_id": stable_id("operation", day, operation, command, result_status, *normalized_evidence),
        "recorded_at_utc": stamp,
        "operation": operation,
        "command": command,
        "result_status": result_status,
        "evidence_paths": normalized_evidence,
    }
    root = _root(output)
    with _journal_lock(root):
        state = _state(root)
        today = date.fromisoformat(day)
        _prune_expired(root, today, state)
        shard = root / f"{day}.jsonl"
        events = _read_shard(shard)
        if any(item.get("event_id") == event["event_id"] for item in events):
            state["deduplicated_records"] = int(state.get("deduplicated_records", 0)) + 1
            json_write(root / "state.json", state)
            all_events = _all_events(root)
            json_write(root / "latest.json", _latest_summary(root, all_events, state))
            return {"status": "passed", "event_id": event["event_id"], "idempotent": True, "journal": str(shard.resolve())}
        events.append(event)
        dropped = 0
        while len(events) > MAX_RECORDS_PER_SHARD or len(_serialized_lines(events)) > MAX_SHARD_BYTES:
            events.pop(0)
            dropped += 1
        state["dropped_records"] = int(state.get("dropped_records", 0)) + dropped
        _write_shard(shard, events)
        json_write(root / "state.json", state)
        all_events = _all_events(root)
        json_write(root / "latest.json", _latest_summary(root, all_events, state))
    return {"status": "passed", "event_id": event["event_id"], "idempotent": False, "journal": str(shard.resolve())}


def record_cli_operation(args: Any, result: Any) -> dict[str, Any] | None:
    if str(getattr(args, "command", "")) == "operations" or not isinstance(result, dict):
        return None
    output_value = getattr(args, "out", None)
    if output_value is None:
        return None
    output = Path(output_value).resolve()
    if not (output / "state.json").is_file():
        return None
    command = _command_name(args)
    operation = _operation_type(command)
    if operation is None:
        return None
    status = str(result.get("status") or "completed")
    evidence = _relative_evidence(output, result)
    return record_operation(output, operation, command, status, evidence)


def list_operations(output: Path, operation: str | None = None, result_status: str | None = None, limit: int = 50) -> dict[str, Any]:
    if operation is not None and operation not in OPERATION_TYPES:
        raise CkbError(f"unsupported operation filter: {operation}")
    if limit < 1 or limit > 500:
        raise CkbError("operation list limit must be between 1 and 500")
    events = _all_events(_root(output))
    selected = [
        item
        for item in events
        if (operation is None or item.get("operation") == operation)
        and (result_status is None or item.get("result_status") == result_status)
    ]
    return {
        "schema_version": OPERATION_JOURNAL_SCHEMA_VERSION,
        "status": "ready",
        "filters": {"operation": operation, "result_status": result_status},
        "count": len(selected),
        "operations": selected[-limit:][::-1],
    }


def _event_errors(item: dict[str, Any], path: Path, line_number: int) -> list[str]:
    prefix = f"{path.name}:{line_number}"
    errors = []
    if set(item) != _EVENT_FIELDS:
        errors.append(f"{prefix}: fields differ from the fixed operation schema")
        return errors
    if item.get("schema_version") != OPERATION_JOURNAL_SCHEMA_VERSION:
        errors.append(f"{prefix}: schema version mismatch")
    if item.get("operation") not in OPERATION_TYPES:
        errors.append(f"{prefix}: unsupported operation type")
    if not isinstance(item.get("command"), str) or not _SAFE_TOKEN.fullmatch(item["command"]):
        errors.append(f"{prefix}: invalid command token")
    if not isinstance(item.get("result_status"), str) or not _SAFE_TOKEN.fullmatch(item["result_status"]):
        errors.append(f"{prefix}: invalid result status token")
    if not isinstance(item.get("event_id"), str) or not item["event_id"].startswith("operation-"):
        errors.append(f"{prefix}: invalid event id")
    if not isinstance(item.get("recorded_at_utc"), str) or len(item["recorded_at_utc"]) != 20:
        errors.append(f"{prefix}: invalid recorded timestamp")
    evidence = item.get("evidence_paths")
    if not isinstance(evidence, list) or len(evidence) > 8:
        errors.append(f"{prefix}: evidence_paths must be a bounded list")
    else:
        for value in evidence:
            if not isinstance(value, str):
                errors.append(f"{prefix}: evidence path must be text")
                continue
            relative = PurePosixPath(value)
            if relative.is_absolute() or ".." in relative.parts:
                errors.append(f"{prefix}: evidence path escapes OUTPUT")
    return errors


def audit_operation_journal(output: Path) -> dict[str, Any]:
    output = output.resolve()
    root = _root(output)
    if not root.is_dir():
        return {
            "schema_version": OPERATION_JOURNAL_SCHEMA_VERSION,
            "status": "passed",
            "records": 0,
            "shards": 0,
            "initialized": False,
            "errors": [],
        }
    errors: list[str] = []
    events: list[dict[str, Any]] = []
    shard_paths = sorted(root.glob("*.jsonl"))
    seen_ids: set[str] = set()
    for path in shard_paths:
        matched = _SHARD_NAME.fullmatch(path.name)
        if not matched:
            errors.append(f"unexpected operation shard name: {path.name}")
            continue
        if path.stat().st_size > MAX_SHARD_BYTES:
            errors.append(f"operation shard exceeds byte limit: {path.name}")
        shard_events = _read_shard(path)
        if len(shard_events) > MAX_RECORDS_PER_SHARD:
            errors.append(f"operation shard exceeds record limit: {path.name}")
        for line_number, item in enumerate(shard_events, start=1):
            errors.extend(_event_errors(item, path, line_number))
            event_id = item.get("event_id")
            if isinstance(event_id, str):
                if event_id in seen_ids:
                    errors.append(f"duplicate operation event id: {event_id}")
                seen_ids.add(event_id)
        events.extend(shard_events)
    state_path = root / "state.json"
    latest_path = root / "latest.json"
    if not state_path.is_file() or not latest_path.is_file():
        errors.append("operation journal state.json and latest.json are required after initialization")
        state = _state(root)
        latest = {}
    else:
        state = _state(root)
        latest = json_load(latest_path)
    expected = _latest_summary(root, events, state)
    for key in (
        "schema_version",
        "status",
        "retention_days",
        "max_records_per_shard",
        "max_shard_bytes",
        "records",
        "counts_by_operation",
        "counts_by_status",
        "shards",
        "latest",
        "bounded_drops",
    ):
        if latest.get(key) != expected.get(key):
            errors.append(f"operation latest summary mismatch: {key}")
    if (output / "human/operations").exists() or (output / "markdown/operations").exists():
        errors.append("machine operation journal must not create human operation pages")
    return {
        "schema_version": OPERATION_JOURNAL_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "records": len(events),
        "shards": len(shard_paths),
        "initialized": True,
        "latest": str(latest_path.resolve()),
        "errors": errors,
    }
