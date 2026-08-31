"""Harness-neutral conversation bindings for the CKB management Agent.

This module owns only project-management identity, dispatch metadata and the
prompt assembled from existing CKB commands.  Conversation events, feedback,
references, research gaps and reviewed notes remain in their existing stores.
"""

from __future__ import annotations

from contextlib import contextmanager
import copy
import os
from pathlib import Path
import re
import time
from typing import Any, Iterator

from .automation import SUPPORTED_HARNESSES
from .common import CkbError, json_load, json_write, stable_id, utc_now


MANAGEMENT_SCHEMA_VERSION = 1
MANAGEMENT_PROMPT_VERSION = "1.0.0"
MANAGEMENT_SCHEMA_ID = "https://code-knowledge-builder.local/management-binding-v1.schema.json"
MANAGEMENT_REGISTRY_ENV = "CKB_MANAGER_REGISTRY"
MANAGEMENT_CAPABILITIES = ("binding", "prompt_injection", "event_sync", "task_dispatch")
NOTIFICATION_POLICIES = ("none", "status", "failures")
_BINDING_STATUSES = ("active", "unbound")
_TASK_STATUSES = ("created", "review-passed", "review-failed")
_FORBIDDEN_INPUT_FIELDS = {
    "assistant",
    "assistant_message",
    "authorization",
    "cookie",
    "password",
    "prompt",
    "secret",
    "token",
    "transcript",
    "transcript_path",
}
_OPAQUE_ID = re.compile(r"^[^\x00-\x1f\x7f]{1,512}$")


def default_management_registry_path() -> Path:
    configured = os.environ.get(MANAGEMENT_REGISTRY_ENV)
    return Path(configured).expanduser() if configured else Path.home() / ".ckb" / "management-bindings.json"


def _path_key(path: Path | str) -> str:
    value = os.path.abspath(os.path.expanduser(str(path)))
    return os.path.normcase(os.path.normpath(value)).replace("\\", "/").rstrip("/")


def _normalized_path(path: Path | str) -> str:
    return str(Path(path).expanduser().resolve())


def _empty_registry() -> dict[str, Any]:
    return {
        "schema_version": MANAGEMENT_SCHEMA_VERSION,
        "bindings": [],
        "tasks": [],
        "audit_log": [],
    }


def _read_registry(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _empty_registry()
    value = json_load(path)
    if not isinstance(value, dict):
        raise CkbError(f"management registry must be one JSON object: {path}")
    if value.get("schema_version") != MANAGEMENT_SCHEMA_VERSION:
        raise CkbError(f"unsupported management registry: {path}")
    for field in ("bindings", "tasks", "audit_log"):
        if not isinstance(value.get(field), list):
            raise CkbError(f"management registry field must be a list: {field}")
    return value


@contextmanager
def _registry_lock(path: Path, timeout: float = 5.0) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    deadline = time.monotonic() + timeout
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, f"{os.getpid()}\n{time.time()}\n".encode("ascii"))
        except (FileExistsError, PermissionError):
            try:
                if time.time() - lock.stat().st_mtime > 60:
                    lock.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise CkbError(f"management registry is busy: {path}")
            time.sleep(0.05)
    try:
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        lock.unlink(missing_ok=True)


@contextmanager
def _locked_registry(path: Path | None = None) -> Iterator[tuple[Path, dict[str, Any]]]:
    registry = (path or default_management_registry_path()).expanduser().resolve()
    with _registry_lock(registry):
        value = _read_registry(registry)
        before = copy.deepcopy(value)
        yield registry, value
        if value != before:
            json_write(registry, value)
            reopened = _read_registry(registry)
            if reopened != value:
                raise CkbError(f"management registry did not reopen with the written state: {registry}")


def _audit_event(binding_id: str | None, action: str, status: str, reason: str) -> dict[str, Any]:
    stamp = utc_now()
    return {
        "schema_version": MANAGEMENT_SCHEMA_VERSION,
        "event_id": stable_id("manager-event", binding_id or "none", action, status, reason, stamp),
        "binding_id": binding_id,
        "action": action,
        "status": status,
        "reason": reason,
        "recorded_at_utc": stamp,
    }


def _capability(available: bool, mode: str) -> dict[str, Any]:
    return {"available": available, "mode": mode}


def harness_capabilities(harness_id: str) -> dict[str, dict[str, Any]]:
    harness = harness_id.strip().casefold()
    if harness not in SUPPORTED_HARNESSES:
        return {
            "binding": _capability(True, "generic-cli"),
            "prompt_injection": _capability(False, "no-adapter"),
            "event_sync": _capability(False, "no-adapter"),
            "task_dispatch": _capability(False, "no-adapter"),
        }
    return {
        "binding": _capability(True, "manager-cli"),
        "prompt_injection": _capability(False, "manual-context"),
        "event_sync": _capability(True, "generic-json" if harness == "generic" else "automation-adapter"),
        "task_dispatch": _capability(True, "manager-cli"),
    }


def binding_schema() -> dict[str, Any]:
    capabilities = {
        name: {
            "type": "object",
            "additionalProperties": False,
            "required": ["available", "mode"],
            "properties": {"available": {"type": "boolean"}, "mode": {"type": "string"}},
        }
        for name in MANAGEMENT_CAPABILITIES
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": MANAGEMENT_SCHEMA_ID,
        "title": "Code Knowledge Builder canonical management binding",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "conversation_id",
            "harness_id",
            "workspace_root",
            "repo_root",
            "knowledge_base",
            "integration_branch",
        ],
        "properties": {
            "schema_version": {"const": MANAGEMENT_SCHEMA_VERSION},
            "conversation_id": {"type": "string", "minLength": 1, "maxLength": 512},
            "harness_id": {"type": "string", "minLength": 1, "maxLength": 80},
            "workspace_root": {"type": "string", "minLength": 1},
            "repo_root": {"type": "string", "minLength": 1},
            "knowledge_base": {"type": "string", "minLength": 1},
            "integration_branch": {"type": "string", "minLength": 1},
            "notification_policy": {"enum": list(NOTIFICATION_POLICIES)},
            "capabilities": {
                "type": "object",
                "additionalProperties": False,
                "required": list(MANAGEMENT_CAPABILITIES),
                "properties": capabilities,
            },
        },
        "privacy": {
            "persisted_fields": [
                "opaque conversation/task identity",
                "Harness identity",
                "normalized project paths",
                "integration branch and bound HEAD",
                "lifecycle timestamps and capability declarations",
            ],
            "forbidden_fields": sorted(_FORBIDDEN_INPUT_FIELDS),
            "raw_conversation_content": False,
            "credentials": False,
        },
    }


def canonical_binding_input(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(payload, dict):
        raise CkbError("management binding input must be one JSON object")
    if payload.get("schema_version") != MANAGEMENT_SCHEMA_VERSION:
        raise CkbError(f"management binding requires schema_version={MANAGEMENT_SCHEMA_VERSION}")
    allowed = set(binding_schema()["properties"])
    ignored = sorted(str(key) for key in payload if key not in allowed)
    value = {key: payload[key] for key in allowed if key in payload and key != "capabilities"}
    required = set(binding_schema()["required"])
    missing = sorted(field for field in required if not isinstance(value.get(field), (str, int)) or not str(value[field]).strip())
    if missing:
        raise CkbError(f"management binding input is missing required fields: {missing}")
    if int(value["schema_version"]) != MANAGEMENT_SCHEMA_VERSION:
        raise CkbError(f"management binding requires schema_version={MANAGEMENT_SCHEMA_VERSION}")
    for field in ("conversation_id", "harness_id"):
        text = str(value[field]).strip()
        if not _OPAQUE_ID.fullmatch(text):
            raise CkbError(f"management binding {field} must be bounded opaque text")
        value[field] = text
    value["harness_id"] = str(value["harness_id"]).casefold()
    policy = str(value.get("notification_policy", "none")).strip().casefold()
    if policy not in NOTIFICATION_POLICIES:
        raise CkbError(f"unsupported management notification policy: {policy}")
    value["notification_policy"] = policy
    for field in ("workspace_root", "repo_root", "knowledge_base"):
        value[field] = _normalized_path(str(value[field]))
    value["integration_branch"] = str(value["integration_branch"]).strip()
    value["capabilities"] = harness_capabilities(value["harness_id"])
    return value, ignored


def _privacy_errors(value: Any, location: str = "registry") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).casefold().replace("-", "_")
            if lowered in _FORBIDDEN_INPUT_FIELDS:
                errors.append(f"{location}: forbidden persisted field: {key}")
            errors.extend(_privacy_errors(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_privacy_errors(child, f"{location}[{index}]"))
    return errors


def audit_manager_registry(registry_path: Path | None = None) -> dict[str, Any]:
    registry = (registry_path or default_management_registry_path()).expanduser().resolve()
    try:
        value = _read_registry(registry)
    except CkbError as exc:
        return {
            "schema_version": MANAGEMENT_SCHEMA_VERSION,
            "status": "failed",
            "registry": str(registry),
            "binding_count": 0,
            "task_count": 0,
            "errors": [str(exc)],
        }
    errors = _privacy_errors(value)
    binding_ids: set[str] = set()
    active_identities: set[tuple[str, str]] = set()
    for index, binding in enumerate(value["bindings"]):
        prefix = f"binding[{index}]"
        if not isinstance(binding, dict):
            errors.append(f"{prefix}: binding must be an object")
            continue
        binding_id = binding.get("binding_id")
        if not isinstance(binding_id, str) or not binding_id.startswith("manager-binding-"):
            errors.append(f"{prefix}: invalid binding_id")
        elif binding_id in binding_ids:
            errors.append(f"{prefix}: duplicate binding_id")
        else:
            binding_ids.add(binding_id)
        if binding.get("schema_version") != MANAGEMENT_SCHEMA_VERSION:
            errors.append(f"{prefix}: schema version mismatch")
        if binding.get("status") not in _BINDING_STATUSES:
            errors.append(f"{prefix}: unsupported status")
        identity = (str(binding.get("harness_id", "")).casefold(), str(binding.get("conversation_id", "")))
        if binding.get("status") == "active":
            if identity in active_identities:
                errors.append(f"{prefix}: duplicate active conversation identity")
            active_identities.add(identity)
        capabilities = binding.get("capabilities")
        if not isinstance(capabilities, dict) or set(capabilities) != set(MANAGEMENT_CAPABILITIES):
            errors.append(f"{prefix}: capability set differs from canonical schema")
        for field in ("workspace_root", "repo_root", "knowledge_base"):
            path = binding.get(field)
            if not isinstance(path, str) or _path_key(path) != _path_key(_normalized_path(path)):
                errors.append(f"{prefix}: {field} is not normalized")
    dispatch_ids: set[str] = set()
    for index, task in enumerate(value["tasks"]):
        prefix = f"task[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix}: task must be an object")
            continue
        dispatch_id = task.get("dispatch_id")
        if not isinstance(dispatch_id, str) or not dispatch_id.startswith("manager-task-"):
            errors.append(f"{prefix}: invalid dispatch_id")
        elif dispatch_id in dispatch_ids:
            errors.append(f"{prefix}: duplicate dispatch_id")
        else:
            dispatch_ids.add(dispatch_id)
        if task.get("binding_id") not in binding_ids:
            errors.append(f"{prefix}: binding_id does not exist")
        if task.get("status") not in _TASK_STATUSES:
            errors.append(f"{prefix}: unsupported status")
    for index, event in enumerate(value["audit_log"]):
        if not isinstance(event, dict) or set(event) != {
            "schema_version", "event_id", "binding_id", "action", "status", "reason", "recorded_at_utc"
        }:
            errors.append(f"audit_log[{index}]: fields differ from the canonical audit schema")
    return {
        "schema_version": MANAGEMENT_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "registry": str(registry),
        "binding_count": len(value["bindings"]),
        "active_bindings": sum(item.get("status") == "active" for item in value["bindings"] if isinstance(item, dict)),
        "task_count": len(value["tasks"]),
        "audit_events": len(value["audit_log"]),
        "errors": errors,
    }
