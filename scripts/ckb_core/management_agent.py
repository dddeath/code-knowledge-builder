"""Harness-neutral conversation bindings for the CKB management Agent.

This module owns only project-management identity, dispatch metadata and the
prompt assembled from existing CKB commands.  Conversation events, feedback,
references, research gaps and reviewed notes remain in their existing stores.
"""

from __future__ import annotations

from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
from typing import Any, Iterator

from .automation import SUPPORTED_HARNESSES
from .common import CkbError, json_load, json_write, run, stable_id, utc_now


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
        "event_id": stable_id("manager-event", binding_id or "none", action, status, reason, stamp, time.time_ns()),
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


def _git(repo: Path, *arguments: str, allow_failure: bool = False) -> str | None:
    completed = run(["git", "-C", str(repo), *arguments], timeout=60)
    if completed.returncode:
        if allow_failure:
            return None
        detail = (completed.stderr or completed.stdout).strip()
        raise CkbError(f"management Git command failed: git -C {repo} {' '.join(arguments)}: {detail}")
    return completed.stdout.strip()


def _is_within(path: Path | str, root: Path | str) -> bool:
    value = _path_key(path)
    base = _path_key(root)
    return value == base or value.startswith(base + "/")


def _git_preflight(
    workspace_root: Path,
    repo_root: Path,
    knowledge_base: Path,
    integration_branch: str,
) -> dict[str, Any]:
    if not workspace_root.is_dir():
        raise CkbError(f"management workspace does not exist: {workspace_root}")
    if not repo_root.is_dir():
        raise CkbError(f"management repository does not exist: {repo_root}")
    if not (_is_within(repo_root, workspace_root) or _is_within(workspace_root, repo_root)):
        raise CkbError("management workspace must contain the repository or be inside it")
    if not knowledge_base.is_dir():
        raise CkbError(f"management knowledge base does not exist: {knowledge_base}")
    if not (knowledge_base / "state.json").is_file():
        raise CkbError(f"management knowledge base is missing state.json: {knowledge_base}")
    top = _git(repo_root, "rev-parse", "--show-toplevel", allow_failure=True)
    if not top or _path_key(top) != _path_key(repo_root):
        raise CkbError(f"management repo_root must be the root of a Git worktree: {repo_root}")
    current_branch = _git(repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", allow_failure=True)
    if not current_branch:
        raise CkbError(f"management integration repository has no attached branch: {repo_root}")
    if current_branch != integration_branch:
        raise CkbError(
            f"management integration branch mismatch: expected={integration_branch}; current={current_branch}"
        )
    branch_head = _git(repo_root, "rev-parse", "--verify", f"refs/heads/{integration_branch}^{{commit}}", allow_failure=True)
    if not branch_head:
        raise CkbError(f"management integration branch does not exist: {integration_branch}")
    current_head = _git(repo_root, "rev-parse", "--verify", "HEAD", allow_failure=True)
    if not current_head:
        raise CkbError(f"management integration repository has no HEAD: {repo_root}")
    dirty = (_git(repo_root, "status", "--porcelain=v1", "--untracked-files=all") or "").splitlines()
    if dirty:
        raise CkbError(f"management integration worktree must be clean: {repo_root}; paths={dirty[:12]}")
    return {
        "workspace_root": str(workspace_root),
        "repo_root": str(repo_root),
        "knowledge_base": str(knowledge_base),
        "integration_branch": integration_branch,
        "current_branch": current_branch,
        "head": current_head,
        "clean": True,
    }


def _binding_identity(binding: dict[str, Any]) -> tuple[str, str]:
    return str(binding["harness_id"]).casefold(), str(binding["conversation_id"])


def _binding_project(binding: dict[str, Any]) -> tuple[str, str]:
    return _path_key(binding["repo_root"]), _path_key(binding["knowledge_base"])


def _binding_id(binding: dict[str, Any]) -> str:
    return stable_id(
        "manager-binding",
        binding["harness_id"],
        binding["conversation_id"],
        _path_key(binding["repo_root"]),
        _path_key(binding["knowledge_base"]),
    )


def bind_conversation(
    payload: dict[str, Any],
    registry_path: Path | None = None,
) -> dict[str, Any]:
    canonical, ignored_fields = canonical_binding_input(payload)
    binding_id = _binding_id(canonical)
    try:
        preflight = _git_preflight(
            Path(canonical["workspace_root"]),
            Path(canonical["repo_root"]),
            Path(canonical["knowledge_base"]),
            canonical["integration_branch"],
        )
    except CkbError as exc:
        with _locked_registry(registry_path) as (_registry, failed_value):
            failed_value["audit_log"].append(_audit_event(binding_id, "bind", "failed", type(exc).__name__))
        raise
    error: CkbError | None = None
    result: dict[str, Any] | None = None
    with _locked_registry(registry_path) as (registry, value):
        try:
            matches = [item for item in value["bindings"] if _binding_identity(item) == _binding_identity(canonical)]
            if matches:
                existing = matches[0]
                if _binding_project(existing) != _binding_project(canonical):
                    raise CkbError(
                        "management conversation identity is already bound to another project: "
                        f"binding_id={existing['binding_id']}"
                    )
                immutable_paths = ("workspace_root", "repo_root", "knowledge_base")
                conflicts = [field for field in immutable_paths if _path_key(existing[field]) != _path_key(canonical[field])]
                if existing["integration_branch"] != canonical["integration_branch"]:
                    conflicts.append("integration_branch")
                if conflicts:
                    raise CkbError(
                        f"management conversation binding conflicts with existing fields: {conflicts}; "
                        f"binding_id={existing['binding_id']}"
                    )
                if existing["status"] == "active":
                    result = {
                        "schema_version": MANAGEMENT_SCHEMA_VERSION,
                        "status": "already-bound",
                        "registry": str(registry),
                        "binding": existing,
                        "ignored_input_fields": ignored_fields,
                        "preflight": preflight,
                    }
                else:
                    stamp = utc_now()
                    existing.update(
                        {
                            "status": "active",
                            "bound_head": preflight["head"],
                            "updated_at_utc": stamp,
                            "unbound_at_utc": None,
                            "prompt_version": MANAGEMENT_PROMPT_VERSION,
                            "capabilities": canonical["capabilities"],
                            "notification_policy": canonical["notification_policy"],
                        }
                    )
                    value["audit_log"].append(_audit_event(existing["binding_id"], "bind", "passed", "reactivated"))
                    result = {
                        "schema_version": MANAGEMENT_SCHEMA_VERSION,
                        "status": "bound",
                        "registry": str(registry),
                        "binding": existing,
                        "ignored_input_fields": ignored_fields,
                        "preflight": preflight,
                    }
            else:
                # Recheck only the first creation while holding the registry
                # lock. Concurrent idempotent bind calls complete from the
                # canonical record instead of serializing repeated Git probes.
                preflight = _git_preflight(
                    Path(canonical["workspace_root"]),
                    Path(canonical["repo_root"]),
                    Path(canonical["knowledge_base"]),
                    canonical["integration_branch"],
                )
                stamp = utc_now()
                binding = {
                    "schema_version": MANAGEMENT_SCHEMA_VERSION,
                    "binding_id": binding_id,
                    "conversation_id": canonical["conversation_id"],
                    "harness_id": canonical["harness_id"],
                    "workspace_root": canonical["workspace_root"],
                    "repo_root": canonical["repo_root"],
                    "knowledge_base": canonical["knowledge_base"],
                    "integration_branch": canonical["integration_branch"],
                    "bound_head": preflight["head"],
                    "status": "active",
                    "created_at_utc": stamp,
                    "updated_at_utc": stamp,
                    "unbound_at_utc": None,
                    "prompt_version": MANAGEMENT_PROMPT_VERSION,
                    "notification_policy": canonical["notification_policy"],
                    "capabilities": canonical["capabilities"],
                }
                value["bindings"].append(binding)
                value["bindings"].sort(key=lambda item: item["binding_id"])
                value["audit_log"].append(_audit_event(binding_id, "bind", "passed", "created"))
                result = {
                    "schema_version": MANAGEMENT_SCHEMA_VERSION,
                    "status": "bound",
                    "registry": str(registry),
                    "binding": binding,
                    "ignored_input_fields": ignored_fields,
                    "preflight": preflight,
                }
        except CkbError as exc:
            value["audit_log"].append(_audit_event(binding_id, "bind", "failed", type(exc).__name__))
            error = exc
    if error is not None:
        raise error
    assert result is not None
    return result


def _find_binding(
    value: dict[str, Any],
    conversation_id: str,
    harness_id: str,
) -> dict[str, Any] | None:
    identity = (harness_id.strip().casefold(), conversation_id.strip())
    return next((item for item in value["bindings"] if _binding_identity(item) == identity), None)


def _runtime_state(binding: dict[str, Any]) -> dict[str, Any]:
    repo = Path(binding["repo_root"])
    branch = str(binding["integration_branch"])
    state: dict[str, Any] = {
        "repo_exists": repo.is_dir(),
        "git_repository": False,
        "current_branch": None,
        "integration_branch_exists": False,
        "current_head": None,
        "integration_head": None,
        "bound_head": binding["bound_head"],
        "head_drift": None,
        "clean": None,
        "dirty_paths": [],
        "errors": [],
    }
    if not repo.is_dir():
        state["errors"].append("repo-missing")
        return state
    top = _git(repo, "rev-parse", "--show-toplevel", allow_failure=True)
    if not top or _path_key(top) != _path_key(repo):
        state["errors"].append("not-git-root")
        return state
    state["git_repository"] = True
    state["current_branch"] = _git(repo, "symbolic-ref", "--quiet", "--short", "HEAD", allow_failure=True)
    state["current_head"] = _git(repo, "rev-parse", "--verify", "HEAD", allow_failure=True)
    state["integration_head"] = _git(repo, "rev-parse", "--verify", f"refs/heads/{branch}^{{commit}}", allow_failure=True)
    state["integration_branch_exists"] = bool(state["integration_head"])
    state["head_drift"] = state["integration_head"] != binding["bound_head"] if state["integration_head"] else None
    dirty = (_git(repo, "status", "--porcelain=v1", "--untracked-files=all", allow_failure=True) or "").splitlines()
    state["dirty_paths"] = dirty[:100]
    state["clean"] = not dirty
    if state["current_branch"] != branch:
        state["errors"].append("integration-branch-not-checked-out")
    if not state["integration_branch_exists"]:
        state["errors"].append("integration-branch-missing")
    if state["head_drift"]:
        state["errors"].append("integration-head-drift")
    if not state["clean"]:
        state["errors"].append("integration-worktree-dirty")
    return state


def binding_status(
    conversation_id: str,
    harness_id: str,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    registry = (registry_path or default_management_registry_path()).expanduser().resolve()
    value = _read_registry(registry)
    binding = _find_binding(value, conversation_id, harness_id)
    if binding is None:
        raise CkbError(f"management conversation binding does not exist: harness={harness_id}; conversation={conversation_id}")
    runtime = _runtime_state(binding)
    active = binding["status"] == "active"
    ready = active and not runtime["errors"]
    return {
        "schema_version": MANAGEMENT_SCHEMA_VERSION,
        "status": "ready" if ready else "unbound" if not active else "blocked",
        "registry": str(registry),
        "binding": binding,
        "runtime": runtime,
        "blockers": ([] if active else ["binding-unbound"]) + runtime["errors"],
    }


def unbind_conversation(
    conversation_id: str,
    harness_id: str,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    error: CkbError | None = None
    result: dict[str, Any] | None = None
    with _locked_registry(registry_path) as (registry, value):
        binding = _find_binding(value, conversation_id, harness_id)
        if binding is None:
            value["audit_log"].append(_audit_event(None, "unbind", "failed", "binding-not-found"))
            error = CkbError(
                f"management conversation binding does not exist: harness={harness_id}; conversation={conversation_id}"
            )
        elif binding["status"] == "unbound":
            result = {
                "schema_version": MANAGEMENT_SCHEMA_VERSION,
                "status": "already-unbound",
                "registry": str(registry),
                "binding": binding,
            }
        else:
            stamp = utc_now()
            binding.update({"status": "unbound", "updated_at_utc": stamp, "unbound_at_utc": stamp})
            value["audit_log"].append(_audit_event(binding["binding_id"], "unbind", "passed", "deactivated"))
            result = {
                "schema_version": MANAGEMENT_SCHEMA_VERSION,
                "status": "unbound",
                "registry": str(registry),
                "binding": binding,
            }
    if error is not None:
        raise error
    assert result is not None
    return result


def _sqlite_integrity(path: Path) -> str:
    if not path.is_file():
        return "missing"
    try:
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            row = connection.execute("PRAGMA integrity_check").fetchone()
            return str(row[0]) if row else "missing-result"
        finally:
            connection.close()
    except sqlite3.Error as exc:
        return f"error:{type(exc).__name__}"


def _feedback_snapshot(output: Path) -> dict[str, Any]:
    root = output / "workspace-meta/feedback/open"
    severities = {name: 0 for name in ("error", "warn", "suggest", "info")}
    invalid = 0
    records = []
    if root.is_dir():
        for path in sorted(root.glob("*.json")):
            try:
                item = json_load(path)
            except Exception:
                invalid += 1
                continue
            severity = str(item.get("severity", ""))
            if severity in severities:
                severities[severity] += 1
            else:
                invalid += 1
            records.append({"id": item.get("id"), "severity": severity, "target": item.get("target")})
    return {"count": len(records), "severities": severities, "invalid": invalid, "records": records[:20]}


def _knowledge_snapshot(output: Path, question: str) -> dict[str, Any]:
    from .llm_wiki_capabilities import compact_agent_brief, maintenance_check
    from .machine_knowledge import retrieve_machine
    from .research_gaps import list_gaps

    snapshot: dict[str, Any] = {
        "output_exists": output.is_dir(),
        "state_exists": (output / "state.json").is_file(),
        "machine_integrity": _sqlite_integrity(output / "machine/knowledge.sqlite"),
        "agent_index_integrity": _sqlite_integrity(output / "agent-index.sqlite"),
        "open_feedback": _feedback_snapshot(output),
        "open_gaps": {"status": "unavailable", "count": None},
        "brief": {"status": "unavailable", "reason": "machine-knowledge-missing"},
        "maintenance": {"status": "unavailable", "failed_checks": ["knowledge-base-missing"]},
    }
    if not snapshot["state_exists"]:
        return snapshot
    try:
        snapshot["open_gaps"] = list_gaps(output, "open")
    except Exception as exc:
        snapshot["open_gaps"] = {"status": "failed", "count": None, "error": type(exc).__name__}
    if snapshot["machine_integrity"] == "ok":
        try:
            retrieval = retrieve_machine(output, question, 1800, 8, "fast")
            snapshot["brief"] = compact_agent_brief(output, retrieval)
        except Exception as exc:
            snapshot["brief"] = {"status": "failed", "error": type(exc).__name__, "detail": str(exc)[:500]}
    try:
        snapshot["maintenance"] = maintenance_check(output)
    except Exception as exc:
        snapshot["maintenance"] = {
            "status": "failed",
            "failed_checks": ["maintenance-exception"],
            "error": type(exc).__name__,
            "detail": str(exc)[:500],
        }
    return snapshot


def _single_quote(value: str) -> str:
    return value.replace("'", "''")


def _manager_commands(binding: dict[str, Any], python: Path, ckb: Path, registry: Path) -> dict[str, str]:
    prefix = f"& '{_single_quote(str(python))}' '{_single_quote(str(ckb))}'"
    output = _single_quote(binding["knowledge_base"])
    identity = (
        f"--conversation-id '{_single_quote(binding['conversation_id'])}' "
        f"--harness '{_single_quote(binding['harness_id'])}' --registry '{_single_quote(str(registry))}'"
    )
    return {
        "brief": f"{prefix} brief --out '{output}' 'QUESTION' --budget 1800 --max-pages 8 --profile fast",
        "feedback_list": f"{prefix} feedback list --out '{output}' --status open",
        "gaps_list": f"{prefix} gaps list --out '{output}' --status open",
        "record": f"{prefix} record --out '{output}' --kind analysis --title 'TITLE' --body 'BODY.md' --from-pack 'PACK.json'",
        "reference_list": f"{prefix} reference list --out '{output}' --status all",
        "maintain": f"{prefix} maintain --out '{output}'",
        "manager_status": f"{prefix} manager status {identity}",
        "manager_context": f"{prefix} manager context {identity} --question 'QUESTION'",
        "manager_audit": f"{prefix} manager audit --registry '{_single_quote(str(registry))}'",
    }


def _management_prompt(
    binding: dict[str, Any],
    runtime: dict[str, Any],
    knowledge: dict[str, Any],
    commands: dict[str, str],
    blockers: list[str],
) -> str:
    feedback = knowledge["open_feedback"]
    gaps = knowledge["open_gaps"]
    maintenance = knowledge["maintenance"]
    blocker_lines = [f"- `{item}`" for item in blockers] or ["- 当前没有阻断项。"]
    return f"""# CKB 管理 Agent 完整上下文

## 当前绑定

- binding：`{binding['binding_id']}`
- Harness / conversation：`{binding['harness_id']}` / `{binding['conversation_id']}`
- workspace：`{binding['workspace_root']}`
- repo：`{binding['repo_root']}`
- knowledge base：`{binding['knowledge_base']}`
- integration branch：`{binding['integration_branch']}`
- bound HEAD：`{binding['bound_head']}`
- current integration HEAD：`{runtime.get('integration_head')}`
- HEAD drift：`{runtime.get('head_drift')}`
- integration worktree clean：`{runtime.get('clean')}`

## 当前管理门

- open feedback：{feedback['count']}，其中 error={feedback['severities']['error']}、warn={feedback['severities']['warn']}
- open research gaps：{gaps.get('count')}
- machine SQLite：`{knowledge['machine_integrity']}`
- agent-index SQLite：`{knowledge['agent_index_integrity']}`
- maintain：`{maintenance.get('status')}`，failed_checks={maintenance.get('failed_checks', [])}

阻断项：
{chr(10).join(blocker_lines)}

## 固定读取和维护入口

1. 每次新问题先执行 `brief --profile fast`，打开返回的 pack，再按 pack 使用 `entity`、`neighbors`、`source` 或 `changes`；复杂跨模块问题才用 `precise`。
2. 反馈、参考资料、研究缺口和工作记录继续使用既有单一状态机，不在管理注册表中复制正文或事实。
3. `human/pages`、`markdown/pages`、`human/references`、`markdown/references`、导航、投影清单和 SQLite 由生成器管理，不直接编辑。
4. 分析、修改原因、踩坑和实验只通过 `record` 写入简体中文正文，并从 pack/query 或唯一知识页建立来源链接。

```powershell
{commands['brief']}
{commands['feedback_list']}
{commands['gaps_list']}
{commands['reference_list']}
{commands['record']}
{commands['maintain']}
```

## 开发分支、审阅和合并门

1. 派发开发任务前重新执行 manager status/context；integration branch 必须仍在 bound HEAD、工作树干净且 maintain 通过。
2. 每项开发任务使用固定 bound HEAD 创建独立 branch/worktree；交接 Prompt 必须列出允许/禁止路径、测试、分批 commit 和结构化返回格式。
3. 开发任务不得自行合并或同步稳定知识库。审阅时重新打开 diff，验证开发 worktree 干净、提交可追溯、测试在最终 HEAD 运行且全部通过。
4. 只有明确收到合并指令且所有门通过时才进入合并；合并后必须在 integration branch 重新运行受影响测试，再以最小范围同步稳定知识库并重新执行 maintain，不能复用开发分支的旧测试或旧审计。

## Harness 能力边界

`binding`、`prompt_injection`、`event_sync`、`task_dispatch` 是四项独立能力。当前声明为：

```json
{json.dumps(binding['capabilities'], ensure_ascii=False, indent=2)}
```

`prompt_injection.available=false` 表示本上下文可由 CLI 获取并交给 Harness，但没有本地适配器自动注入；不得将其描述为自动注入。

## 结构化交接返回

最终交接固定列出：branch、base_commit、final_head、worktree clean；commit 表；base..HEAD diff stat 与逐文件用途；literal 测试命令/输出/退出状态；已确认行为、推断、未验证项；知识库影响；逐 commit revert、绑定备份/恢复和 unbind 回滚。不得把 Prompt、assistant 原文、secret、token 或 transcript path 写入管理注册表。
"""


def management_context(
    conversation_id: str,
    harness_id: str,
    question: str,
    registry_path: Path | None = None,
    *,
    python: Path | None = None,
    ckb: Path | None = None,
) -> dict[str, Any]:
    status = binding_status(conversation_id, harness_id, registry_path)
    binding = status["binding"]
    registry = Path(status["registry"])
    output = Path(binding["knowledge_base"])
    knowledge = _knowledge_snapshot(output, question.strip() or "管理当前 Code Knowledge Builder 项目")
    blockers = list(status["blockers"])
    if knowledge["machine_integrity"] != "ok":
        blockers.append("machine-knowledge-integrity")
    if knowledge["agent_index_integrity"] != "ok":
        blockers.append("agent-index-integrity")
    if knowledge["open_feedback"]["severities"]["error"]:
        blockers.append("open-error-feedback")
    if knowledge["open_feedback"]["invalid"]:
        blockers.append("invalid-feedback-record")
    if knowledge["maintenance"].get("status") != "passed":
        blockers.append("maintenance-failed")
    blockers = list(dict.fromkeys(blockers))
    python_path = (python or Path(sys.executable)).expanduser().resolve()
    ckb_path = (ckb or (Path(__file__).resolve().parents[1] / "ckb.py")).expanduser().resolve()
    commands = _manager_commands(binding, python_path, ckb_path, registry)
    prompt = _management_prompt(binding, status["runtime"], knowledge, commands, blockers)
    return {
        "schema_version": MANAGEMENT_SCHEMA_VERSION,
        "status": "ready" if not blockers else "blocked",
        "registry": str(registry),
        "binding": binding,
        "runtime": status["runtime"],
        "knowledge": knowledge,
        "blockers": blockers,
        "commands": commands,
        "prompt_version": MANAGEMENT_PROMPT_VERSION,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt": prompt,
    }
