"""Harness-neutral conversation and modification automation for CKB.

Every host adapter emits a small JSON event.  This module owns the durable
contract: explicit project registration, deterministic normalization and
redaction, write-ahead spooling, idempotent SQLite ingestion, turn/session
aggregation, and Agent-reviewed promotion into the human knowledge layer.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
from typing import Any, Iterator
import uuid

from .common import CkbError, json_load, json_write, run, safe_title, stable_id, utc_now


AUTOMATION_SCHEMA_VERSION = 2
AUTOMATION_DATABASE = "machine/automation.sqlite"
SUPPORTED_HARNESSES = {
    "codex",
    "claude",
    "opencode",
    "opencode-v2",
    "dsh",
    "gemini",
    "copilot",
    "cursor",
    "generic",
}
CANONICAL_EVENTS = {
    "session.start",
    "turn.prompt",
    "turn.assistant",
    "tool.result",
    "file.changed",
    "turn.stop",
    "compact.before",
    "compact.after",
    "session.end",
}
_IGNORED_CHANGE_PARTS = {
    ".git",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "bin",
    "node_modules",
    "obj",
    "venv",
}
_IGNORED_CHANGE_SUFFIXES = {".pyc", ".pyo"}
_CHANGE_HEADINGS = ("修改内容", "修改原因", "验证结果")
_SENSITIVE_KEY = re.compile(
    r"(?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|passwd|secret|cookie|private[_-]?key)",
    re.IGNORECASE,
)
_DEFAULT_STRING_REDACTIONS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "authorization",
        re.compile(r"(?i)\b(?:authorization\s*:\s*)?(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"),
    ),
    (
        "credential-assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|token|access[_-]?token|refresh[_-]?token|password|passwd|secret)\b"
            r"(\s*[:=]\s*)([^\s,;\]\}\)\"']{4,}|\"[^\"]{4,}\"|'[^']{4,}')"
        ),
    ),
    (
        "private-key",
        re.compile(r"-----BEGIN [^-\r\n]*PRIVATE KEY-----[\s\S]*?-----END [^-\r\n]*PRIVATE KEY-----"),
    ),
)
_PATH_KEYS = {
    "file_path",
    "filepath",
    "path",
    "output_path",
    "outputpath",
    "output_paths",
    "outputpaths",
    "changed_path",
    "changed_paths",
}
_PATCH_PATH = re.compile(r"^\*\*\*\s+(?:Add|Update|Delete)\s+File:\s*(.+?)\s*$", re.MULTILINE)


def default_registry_path() -> Path:
    configured = os.environ.get("CKB_AUTOMATION_REGISTRY")
    return Path(configured).expanduser() if configured else Path.home() / ".ckb" / "automation-registry.json"


def _path_key(path: Path | str) -> str:
    value = os.path.abspath(os.path.expanduser(str(path)))
    value = os.path.normcase(os.path.normpath(value))
    return value.replace("\\", "/").rstrip("/")


def _is_within(path: Path | str, root: Path | str) -> bool:
    value = _path_key(path)
    base = _path_key(root)
    return value == base or value.startswith(base + "/")


def _read_registry(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": AUTOMATION_SCHEMA_VERSION, "projects": []}
    value = json_load(path)
    if value.get("schema_version") == 1 and isinstance(value.get("projects"), list):
        # Version 1 matched events only against repo_root.  Read it as an empty
        # workspace-root list so existing opt-in registrations keep working;
        # the next registry write upgrades the on-disk document atomically.
        value = {
            **value,
            "schema_version": AUTOMATION_SCHEMA_VERSION,
            "projects": [
                {**item, "workspace_roots": list(item.get("workspace_roots") or [])}
                for item in value["projects"]
            ],
        }
    if value.get("schema_version") != AUTOMATION_SCHEMA_VERSION or not isinstance(value.get("projects"), list):
        raise CkbError(f"unsupported automation registry: {path}")
    for item in value["projects"]:
        item.setdefault("workspace_roots", [])
    return value


def register_project(
    repo: Path,
    output: Path,
    registry_path: Path | None = None,
    harnesses: list[str] | None = None,
    *,
    max_field_chars: int = 12_000,
    custom_redactions: list[str] | None = None,
    workspace_roots: list[Path] | None = None,
) -> dict[str, Any]:
    repo = repo.resolve()
    output = output.resolve()
    registry = (registry_path or default_registry_path()).expanduser().resolve()
    if not repo.is_dir():
        raise CkbError(f"automation repository does not exist: {repo}")
    if not (output / "state.json").is_file():
        raise CkbError(f"automation requires a CKB output with state.json: {output}")
    selected = sorted(set(harnesses or SUPPORTED_HARNESSES))
    unsupported = sorted(set(selected) - SUPPORTED_HARNESSES)
    if unsupported:
        raise CkbError(f"unsupported automation harnesses: {unsupported}")
    if max_field_chars < 256 or max_field_chars > 1_000_000:
        raise CkbError("automation max-field-chars must be between 256 and 1000000")
    patterns = list(custom_redactions or [])
    for pattern in patterns:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise CkbError(f"invalid custom redaction regex: {pattern}: {exc}") from exc
    value = _read_registry(registry)
    key = _path_key(repo)
    resolved_workspaces = sorted(
        {str(Path(item).expanduser().resolve()) for item in (workspace_roots or [])},
        key=_path_key,
    )
    for root in resolved_workspaces:
        if not Path(root).is_dir():
            raise CkbError(f"automation workspace root does not exist: {root}")
        if not (_is_within(repo, root) or _is_within(root, repo)):
            raise CkbError(f"automation workspace root must contain the repository or be inside it: {root}")
    for item in value["projects"]:
        if _path_key(item.get("repo_root", "")) == key:
            continue
        overlap = sorted(set(map(_path_key, item.get("workspace_roots", []))) & set(map(_path_key, resolved_workspaces)))
        if overlap:
            raise CkbError(
                "automation workspace root is already assigned to another repository: "
                f"{overlap}; use a narrower workspace root"
            )
    projects = [item for item in value["projects"] if _path_key(item.get("repo_root", "")) != key]
    entry = {
        "registration_id": stable_id("reg", key),
        "enabled": True,
        "repo_root": str(repo),
        "knowledge_output": str(output),
        "workspace_roots": resolved_workspaces,
        "harnesses": selected,
        "max_field_chars": max_field_chars,
        "custom_redactions": patterns,
        "registered_at_utc": utc_now(),
    }
    projects.append(entry)
    value["projects"] = sorted(projects, key=lambda item: _path_key(item["repo_root"]))
    json_write(registry, value)
    initialize_automation_database(output)
    return {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "status": "registered",
        "registry": str(registry),
        "project": entry,
    }


def unregister_project(repo: Path, registry_path: Path | None = None) -> dict[str, Any]:
    registry = (registry_path or default_registry_path()).expanduser().resolve()
    value = _read_registry(registry)
    key = _path_key(repo.resolve())
    before = len(value["projects"])
    value["projects"] = [item for item in value["projects"] if _path_key(item.get("repo_root", "")) != key]
    json_write(registry, value)
    return {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "status": "unregistered" if len(value["projects"]) != before else "not-registered",
        "registry": str(registry),
        "repo_root": str(repo.resolve()),
    }


def registry_status(registry_path: Path | None = None) -> dict[str, Any]:
    registry = (registry_path or default_registry_path()).expanduser().resolve()
    value = _read_registry(registry)
    return {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "status": "ready",
        "registry": str(registry),
        "project_count": len(value["projects"]),
        "projects": value["projects"],
    }


def _registration_for_event(registry: Path, cwd: Path, harness: str) -> tuple[dict[str, Any], str, str] | None:
    candidates: list[tuple[int, int, dict[str, Any], str, str]] = []
    for item in _read_registry(registry)["projects"]:
        if not item.get("enabled", False) or harness not in item.get("harnesses", []):
            continue
        if _is_within(cwd, item["repo_root"]):
            root = str(item["repo_root"])
            candidates.append((2, len(_path_key(root)), item, "repository", root))
        for workspace_root in item.get("workspace_roots", []):
            if _is_within(cwd, workspace_root):
                candidates.append((1, len(_path_key(workspace_root)), item, "workspace", str(workspace_root)))
    if not candidates:
        return None
    best = max(candidates, key=lambda value: (value[0], value[1]))
    tied = [value for value in candidates if value[:2] == best[:2] and value[2]["registration_id"] != best[2]["registration_id"]]
    if tied:
        raise CkbError(f"automation event cwd matches multiple registrations at the same priority: {cwd}")
    return best[2], best[3], best[4]


def _walk_values(value: Any) -> Iterator[tuple[str | None, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from _walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield None, child
            yield from _walk_values(child)


def _first_scalar(value: Any, keys: set[str]) -> str | None:
    lowered = {key.casefold() for key in keys}
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).casefold() in lowered and isinstance(child, (str, int)):
                text = str(child).strip()
                if text:
                    return text
        for child in value.values():
            found = _first_scalar(child, keys)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _first_scalar(child, keys)
            if found:
                return found
    return None


def _text_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [_text_content(item) for item in value]
        return "\n".join(item for item in parts if item)
    if isinstance(value, dict):
        direct = value.get("text")
        if isinstance(direct, str):
            return direct
        for key in ("content", "parts", "message", "delta", "info", "properties", "data"):
            if key in value:
                text = _text_content(value[key])
                if text:
                    return text
    return ""


def _event_name(raw: dict[str, Any]) -> str:
    for key in ("hook_event_name", "canonical_type", "event_type", "type"):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    event = raw.get("event")
    if isinstance(event, dict) and isinstance(event.get("type"), str):
        return event["type"]
    return "unknown"


def _message_role(raw: dict[str, Any]) -> str:
    return (_first_scalar(raw, {"role"}) or "").casefold()


def _canonical_type(raw: dict[str, Any], name: str) -> str:
    if name in CANONICAL_EVENTS:
        return name
    normalized = name.casefold()
    mapping = {
        "sessionstart": "session.start",
        "session.created": "session.start",
        "userpromptsubmit": "turn.prompt",
        "assistantmessage": "turn.assistant",
        "posttooluse": "tool.result",
        "posttoolusefailure": "tool.result",
        "tool.execute.after": "tool.result",
        "aftertool": "tool.result",
        "filechanged": "file.changed",
        "file.edited": "file.changed",
        "afterfileedit": "file.changed",
        "stop": "turn.stop",
        "afteragent": "turn.stop",
        "agentstop": "turn.stop",
        "stopfailure": "turn.stop",
        "session.idle": "turn.stop",
        "session.execution.succeeded.1": "turn.stop",
        "session.execution.failed.1": "turn.stop",
        "precompact": "compact.before",
        "precompress": "compact.before",
        "postcompact": "compact.after",
        "session.compacted": "compact.after",
        "sessionend": "session.end",
        "session.deleted": "session.end",
        "beforeagent": "turn.prompt",
        "beforesubmitprompt": "turn.prompt",
        "userpromptsubmitted": "turn.prompt",
        "afteragentresponse": "turn.assistant",
    }
    if normalized == "message.updated":
        return "turn.prompt" if _message_role(raw) == "user" else "turn.assistant"
    return mapping.get(normalized, "")


def _extract_paths(value: Any) -> list[str]:
    result: list[str] = []
    for key, child in _walk_values(value):
        if key and key.casefold() in _PATH_KEYS:
            if isinstance(child, str):
                result.append(child)
            elif isinstance(child, list):
                result.extend(str(item) for item in child if isinstance(item, (str, Path)))
        if isinstance(child, str):
            result.extend(match.strip() for match in _PATCH_PATH.findall(child))
    return list(dict.fromkeys(path.strip() for path in result if path.strip()))


def normalize_event(harness: str, raw: dict[str, Any]) -> dict[str, Any]:
    if harness not in SUPPORTED_HARNESSES:
        raise CkbError(f"unsupported automation harness: {harness}")
    if not isinstance(raw, dict):
        raise CkbError("automation event must be one JSON object")
    name = _event_name(raw)
    canonical = _canonical_type(raw, name)
    if not canonical:
        raise CkbError(f"unsupported automation event for {harness}: {name}")
    session_id = _first_scalar(
        raw,
        {"session_id", "sessionid", "sessionId", "session", "conversation_id", "conversationId", "composer_id"},
    ) or "session-unknown"
    turn_id = _first_scalar(raw, {"turn_id", "turnid", "turnId"})
    tool_use_id = _first_scalar(raw, {"tool_use_id", "tooluseid", "toolUseId", "toolCallID", "callID"})
    cwd = _first_scalar(raw, {"cwd", "directory", "worktree", "project_dir", "projectDir"}) or os.getcwd()
    prompt = str(raw.get("prompt") or raw.get("initial_prompt") or "").strip()
    assistant = str(
        raw.get("last_assistant_message")
        or raw.get("assistant_message")
        or raw.get("prompt_response")
        or raw.get("response")
        or raw.get("delta")
        or ""
    ).strip()
    if canonical in {"turn.prompt", "turn.assistant"} and not (prompt or assistant):
        text = _text_content(raw.get("message") or raw.get("info") or raw.get("properties") or raw)
        if canonical == "turn.prompt":
            prompt = text.strip()
        else:
            assistant = text.strip()
    tool_name = _first_scalar(raw, {"tool_name", "tool", "toolName"})
    tool_input = raw.get("tool_input", raw.get("toolArgs", raw.get("input")))
    tool_output = raw.get(
        "tool_response",
        raw.get("tool_result", raw.get("toolResult", raw.get("tool_output", raw.get("output", raw.get("result"))))),
    )
    failed_names = {"posttoolusefailure", "stopfailure", "session.execution.failed.1"}
    event_status = str(raw.get("status") or ("error" if name.casefold() in failed_names else "completed"))
    return {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "harness": harness,
        "event_name": name,
        "canonical_type": canonical,
        "external_event_id": _first_scalar(raw, {"event_id", "eventId", "idempotency_key"}),
        "session_id": session_id,
        "turn_id": turn_id,
        "tool_use_id": tool_use_id,
        "cwd": cwd,
        "prompt": prompt,
        "assistant_message": assistant,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output,
        "tool_status": event_status,
        "changed_paths": _extract_paths(raw),
        "source": raw.get("source") or raw.get("reason") or raw.get("trigger"),
        "received_at_utc": utc_now(),
        "raw": raw,
    }


def _redact_text(text: str, custom: list[re.Pattern[str]], max_chars: int) -> tuple[str, list[str]]:
    types: list[str] = []
    result = text
    for name, pattern in _DEFAULT_STRING_REDACTIONS:
        if pattern.search(result):
            types.append(name)
            if name == "credential-assignment":
                result = pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED:CREDENTIAL]", result)
            else:
                result = pattern.sub(f"[REDACTED:{name.upper()}]", result)
    for index, pattern in enumerate(custom, 1):
        if pattern.search(result):
            types.append(f"custom-{index}")
            result = pattern.sub(f"[REDACTED:CUSTOM-{index}]", result)
    encoded = result.encode("utf-8")
    if len(encoded) > max_chars:
        data = encoded[:max_chars]
        while True:
            try:
                result = data.decode("utf-8") + f"\n[TRUNCATED:{len(encoded) - len(data)}-BYTES]"
                break
            except UnicodeDecodeError as exc:
                data = data[: exc.start]
        types.append("size-limit")
    return result, types


def redact_event(event: dict[str, Any], custom_patterns: list[str], max_chars: int) -> dict[str, Any]:
    custom = [re.compile(pattern) for pattern in custom_patterns]
    redaction_types: list[str] = []

    def redact(value: Any, key: str | None = None) -> Any:
        if key and _SENSITIVE_KEY.search(key) and value not in (None, ""):
            redaction_types.append("sensitive-key")
            return "[REDACTED:SENSITIVE-KEY]"
        if isinstance(value, str):
            text, types = _redact_text(value, custom, max_chars)
            redaction_types.extend(types)
            return text
        if isinstance(value, dict):
            return {str(child_key): redact(child, str(child_key)) for child_key, child in value.items()}
        if isinstance(value, list):
            return [redact(child) for child in value[:200]]
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        return str(value)

    result = redact(event)
    result["redaction_count"] = len(redaction_types)
    result["redaction_types"] = sorted(set(redaction_types))
    return result


def _automation_root(output: Path) -> Path:
    root = output / "workspace-meta" / "automation"
    for relative in ("spool/pending", "spool/processed", "spool/failed", "pending-reviews"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    return root


def initialize_automation_database(output: Path) -> Path:
    output = output.resolve()
    path = output / AUTOMATION_DATABASE
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=10000")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(
                session_key TEXT PRIMARY KEY,
                harness TEXT NOT NULL,
                external_session_id TEXT NOT NULL,
                repo_root TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at_utc TEXT,
                ended_at_utc TEXT,
                first_prompt TEXT NOT NULL DEFAULT '',
                last_assistant_message TEXT NOT NULL DEFAULT '',
                turn_count INTEGER NOT NULL DEFAULT 0,
                baseline_paths_json TEXT NOT NULL DEFAULT '[]',
                baseline_state_json TEXT NOT NULL DEFAULT '{}',
                UNIQUE(harness, external_session_id, repo_root)
            );
            CREATE TABLE IF NOT EXISTS turns(
                turn_key TEXT PRIMARY KEY,
                session_key TEXT NOT NULL REFERENCES sessions(session_key),
                external_turn_id TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                status TEXT NOT NULL,
                prompt TEXT NOT NULL DEFAULT '',
                assistant_message TEXT NOT NULL DEFAULT '',
                started_at_utc TEXT,
                completed_at_utc TEXT,
                UNIQUE(session_key, external_turn_id),
                UNIQUE(session_key, ordinal)
            );
            CREATE TABLE IF NOT EXISTS events(
                event_id TEXT PRIMARY KEY,
                harness TEXT NOT NULL,
                event_name TEXT NOT NULL,
                canonical_type TEXT NOT NULL,
                session_key TEXT NOT NULL REFERENCES sessions(session_key),
                turn_key TEXT REFERENCES turns(turn_key),
                tool_use_id TEXT,
                cwd TEXT NOT NULL,
                received_at_utc TEXT NOT NULL,
                redaction_count INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS events_session ON events(session_key, received_at_utc);
            CREATE TABLE IF NOT EXISTS tool_events(
                event_id TEXT PRIMARY KEY REFERENCES events(event_id),
                session_key TEXT NOT NULL REFERENCES sessions(session_key),
                turn_key TEXT REFERENCES turns(turn_key),
                tool_name TEXT,
                status TEXT NOT NULL,
                changed_paths_json TEXT NOT NULL,
                detail_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS changed_paths(
                session_key TEXT NOT NULL REFERENCES sessions(session_key),
                path TEXT NOT NULL,
                first_event_id TEXT NOT NULL,
                last_event_id TEXT NOT NULL,
                change_count INTEGER NOT NULL,
                PRIMARY KEY(session_key, path)
            );
            CREATE TABLE IF NOT EXISTS pending_reviews(
                review_id TEXT PRIMARY KEY,
                session_key TEXT NOT NULL REFERENCES sessions(session_key),
                turn_key TEXT NOT NULL REFERENCES turns(turn_key),
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                changed_paths_json TEXT NOT NULL,
                status TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                created_at_utc TEXT NOT NULL,
                reviewed_at_utc TEXT,
                human_file TEXT,
                UNIQUE(turn_key)
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS automation_fts USING fts5(
                review_id UNINDEXED,
                title,
                content,
                changed_paths,
                tokenize='trigram'
            );
            """
        )
        session_columns = {row[1] for row in connection.execute("PRAGMA table_info(sessions)")}
        if "baseline_state_json" not in session_columns:
            connection.execute("ALTER TABLE sessions ADD COLUMN baseline_state_json TEXT NOT NULL DEFAULT '{}'")
        connection.execute("INSERT OR REPLACE INTO meta VALUES('schema_version',?)", (str(AUTOMATION_SCHEMA_VERSION),))
        connection.commit()
    finally:
        connection.close()
    _automation_root(output)
    return path


def _git_status_paths(repo: Path) -> list[str]:
    prefix_result = run(["git", "rev-parse", "--show-prefix"], cwd=repo)
    prefix = prefix_result.stdout.strip().replace("\\", "/") if prefix_result.returncode == 0 else ""
    completed = run(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", "."], cwd=repo)
    if completed.returncode:
        return []
    values: list[str] = []
    for record in completed.stdout.split("\0"):
        if len(record) < 4:
            continue
        path = record[3:].strip()
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        if path:
            path = path.replace("\\", "/")
            if prefix and path.startswith(prefix):
                path = path[len(prefix) :]
            path = path.removeprefix("./")
            if path and _change_path_allowed(path):
                values.append(path)
    return sorted(set(values))


def _change_path_allowed(relative: str) -> bool:
    path = Path(relative.replace("\\", "/"))
    return not any(part.casefold() in _IGNORED_CHANGE_PARTS for part in path.parts) and path.suffix.casefold() not in _IGNORED_CHANGE_SUFFIXES


def _working_file_state(repo: Path, paths: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for relative in paths:
        path = repo / relative
        if not path.is_file():
            result[relative] = {"exists": False, "size": 0, "content_sha256": None}
            continue
        digest = hashlib.sha256()
        try:
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            result[relative] = {"exists": True, "size": path.stat().st_size, "content_sha256": digest.hexdigest()}
        except OSError:
            result[relative] = {"exists": path.exists(), "size": -1, "content_sha256": None}
    return result


def _relative_changed_paths(paths: list[str], repo: Path, output: Path, event_cwd: Path | None = None) -> list[str]:
    result: list[str] = []
    for value in paths:
        candidate = Path(value)
        candidates = [candidate] if candidate.is_absolute() else [*([] if event_cwd is None else [event_cwd / candidate]), repo / candidate]
        for possible in candidates:
            if (
                not candidate.is_absolute()
                and event_cwd is not None
                and not _is_within(event_cwd, repo)
                and possible == repo / candidate
                and not possible.exists()
                and run(["git", "ls-files", "--error-unmatch", "--", candidate.as_posix()], cwd=repo).returncode != 0
            ):
                # A workspace-level relative path that is neither present nor
                # tracked in the source repository belongs to scratch/output,
                # not to an imaginary path with the same spelling under repo.
                continue
            try:
                resolved = possible.resolve()
            except OSError:
                continue
            if not _is_within(resolved, repo) or _is_within(resolved, output):
                continue
            try:
                relative = resolved.relative_to(repo.resolve()).as_posix()
            except ValueError:
                continue
            if relative and relative != "." and _change_path_allowed(relative):
                result.append(relative)
                break
    return sorted(set(result))


@contextmanager
def _drain_lock(output: Path, timeout: float = 3.0) -> Iterator[bool]:
    root = _automation_root(output)
    lock = root / "drain.lock"
    deadline = time.monotonic() + timeout
    acquired = False
    while time.monotonic() < deadline:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, f"{os.getpid()}\n{time.time()}\n".encode("ascii"))
            os.close(descriptor)
            acquired = True
            break
        except (FileExistsError, PermissionError):
            try:
                if time.time() - lock.stat().st_mtime > 60:
                    lock.unlink()
                    continue
            except FileNotFoundError:
                continue
            time.sleep(0.05)
    try:
        yield acquired
    finally:
        if acquired:
            try:
                lock.unlink()
            except FileNotFoundError:
                pass


def enqueue_event(output: Path, event: dict[str, Any]) -> Path:
    pending = _automation_root(output) / "spool" / "pending"
    name = f"{time.time_ns():020d}-{os.getpid()}-{uuid.uuid4().hex}.json"
    path = pending / name
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(event, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)
    return path


def _spool_events(directory: Path) -> list[Path]:
    return sorted(path for path in directory.glob("*.json") if not path.name.endswith(".error.json"))


def _session_key(event: dict[str, Any], repo: Path) -> str:
    return stable_id("autosession", event["harness"], event["session_id"], _path_key(repo))


def _ensure_session(
    connection: sqlite3.Connection,
    event: dict[str, Any],
    repo: Path,
    output: Path,
) -> str:
    key = _session_key(event, repo)
    existing = connection.execute("SELECT 1 FROM sessions WHERE session_key=?", (key,)).fetchone()
    if existing is None:
        baseline = _git_status_paths(repo) if event["canonical_type"] == "session.start" else []
        baseline_state = _working_file_state(repo, baseline)
        connection.execute(
            "INSERT INTO sessions(session_key,harness,external_session_id,repo_root,status,started_at_utc,baseline_paths_json,baseline_state_json) VALUES(?,?,?,?,?,?,?,?)",
            (
                key,
                event["harness"],
                event["session_id"],
                str(repo),
                "active",
                event["received_at_utc"],
                json.dumps(baseline, ensure_ascii=False),
                json.dumps(baseline_state, ensure_ascii=False, sort_keys=True),
            ),
        )
    if event["canonical_type"] == "session.start":
        connection.execute(
            "UPDATE sessions SET status='active',started_at_utc=COALESCE(started_at_utc,?) WHERE session_key=?",
            (event["received_at_utc"], key),
        )
    return key


def _resolve_turn(
    connection: sqlite3.Connection,
    event: dict[str, Any],
    session_key: str,
) -> tuple[str | None, str | None]:
    canonical = event["canonical_type"]
    if canonical in {"session.start", "session.end"}:
        return None, None
    supplied = event.get("turn_id")
    if supplied:
        external = str(supplied)
        row = connection.execute("SELECT turn_key FROM turns WHERE session_key=? AND external_turn_id=?", (session_key, external)).fetchone()
        if row:
            return str(row[0]), external
        ordinal = int(connection.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_key=?", (session_key,)).fetchone()[0])
        key = stable_id("autoturn", session_key, external)
        connection.execute(
            "INSERT INTO turns(turn_key,session_key,external_turn_id,ordinal,status,started_at_utc) VALUES(?,?,?,?,?,?)",
            (key, session_key, external, ordinal, "active", event["received_at_utc"]),
        )
        return key, external
    active = connection.execute(
        "SELECT turn_key,external_turn_id,prompt FROM turns WHERE session_key=? AND status='active' ORDER BY ordinal DESC LIMIT 1",
        (session_key,),
    ).fetchone()
    if canonical == "turn.prompt":
        prompt = event.get("prompt") or ""
        if active and str(active[2]) == prompt:
            return str(active[0]), str(active[1])
        ordinal = int(connection.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_key=?", (session_key,)).fetchone()[0])
        external = f"turn-{ordinal:06d}"
        key = stable_id("autoturn", session_key, external)
        connection.execute(
            "INSERT INTO turns(turn_key,session_key,external_turn_id,ordinal,status,started_at_utc) VALUES(?,?,?,?,?,?)",
            (key, session_key, external, ordinal, "active", event["received_at_utc"]),
        )
        return key, external
    if active:
        return str(active[0]), str(active[1])
    if canonical in {"turn.assistant", "turn.stop", "compact.before", "compact.after"}:
        latest = connection.execute(
            "SELECT turn_key,external_turn_id FROM turns WHERE session_key=? ORDER BY ordinal DESC LIMIT 1",
            (session_key,),
        ).fetchone()
        if latest:
            return str(latest[0]), str(latest[1])
    ordinal = int(connection.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_key=?", (session_key,)).fetchone()[0])
    external = f"turn-{ordinal:06d}"
    key = stable_id("autoturn", session_key, external)
    connection.execute(
        "INSERT INTO turns(turn_key,session_key,external_turn_id,ordinal,status,started_at_utc) VALUES(?,?,?,?,?,?)",
        (key, session_key, external, ordinal, "active", event["received_at_utc"]),
    )
    return key, external


def _event_id(event: dict[str, Any], session_key: str, turn_key: str | None) -> str:
    explicit = event.get("external_event_id")
    if explicit:
        return stable_id("autoevent", event["harness"], explicit)
    identity_payload = {
        "canonical_type": event["canonical_type"],
        "prompt": event.get("prompt") or "",
        "assistant_message": event.get("assistant_message") or "",
        "tool_name": event.get("tool_name"),
        "tool_use_id": event.get("tool_use_id"),
        "changed_paths": event.get("changed_paths") or [],
        "source": event.get("source"),
    }
    return stable_id(
        "autoevent",
        event["harness"],
        session_key,
        turn_key or "session",
        event["canonical_type"],
        event.get("tool_use_id") or "",
        json.dumps(identity_payload, ensure_ascii=False, sort_keys=True),
    )


def _pending_review_content(
    event: dict[str, Any],
    turn: sqlite3.Row,
    changed_paths: list[str],
) -> str:
    prompt = str(turn["prompt"] or "（本轮没有可用的用户消息。）")
    assistant = str(turn["assistant_message"] or event.get("assistant_message") or "（本轮没有可用的最终回答。）")
    path_lines = [f"- `{path}`" for path in changed_paths] or ["- 本轮没有检测到项目文件变化。"]
    return "\n".join(
        [
            "## 用户请求",
            "",
            prompt,
            "",
            "## Agent 最终回答",
            "",
            assistant,
            "",
            "## 修改证据",
            "",
            *path_lines,
            "",
            "## 审阅要求",
            "",
            "本页是机器层待审阅记录。Agent 需要重新核对关联源码和验证证据，使用简体中文确认修改内容、修改原因与验证结果后，才可晋升到人类知识库。",
        ]
    ).rstrip() + "\n"


def _create_pending_review(
    connection: sqlite3.Connection,
    output: Path,
    repo: Path,
    event: dict[str, Any],
    session_key: str,
    turn_key: str | None,
) -> str | None:
    if not turn_key:
        return None
    existing = connection.execute("SELECT review_id FROM pending_reviews WHERE turn_key=?", (turn_key,)).fetchone()
    if existing:
        return str(existing[0])
    turn = connection.execute("SELECT * FROM turns WHERE turn_key=?", (turn_key,)).fetchone()
    session = connection.execute("SELECT * FROM sessions WHERE session_key=?", (session_key,)).fetchone()
    if turn is None or session is None:
        return None
    recorded = [row[0] for row in connection.execute("SELECT path FROM changed_paths WHERE session_key=? ORDER BY path", (session_key,))]
    baseline = set(json.loads(session["baseline_paths_json"] or "[]"))
    baseline_state = json.loads(session["baseline_state_json"] or "{}")
    current = set(_git_status_paths(repo))
    current_state = _working_file_state(repo, sorted(current & baseline))
    changed_from_dirty_baseline = {
        path for path in current & baseline if current_state.get(path) != baseline_state.get(path)
    }
    changed_paths = sorted(set(recorded) | (current - baseline) | changed_from_dirty_baseline)
    content = _pending_review_content(event, turn, changed_paths)
    kind = "change" if changed_paths else "session"
    review_id = stable_id("autoreview", turn_key)
    title = f"{event['harness']} 会话第 {turn['ordinal']} 轮待审阅"
    evidence = {
        "harness": event["harness"],
        "external_session_id": event["session_id"],
        "external_turn_id": turn["external_turn_id"],
        "event_name": event["event_name"],
        "redaction_count": event.get("redaction_count", 0),
    }
    connection.execute(
        "INSERT INTO pending_reviews VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            review_id,
            session_key,
            turn_key,
            kind,
            title,
            content,
            json.dumps(changed_paths, ensure_ascii=False),
            "pending-agent-review",
            json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            event["received_at_utc"],
            None,
            None,
        ),
    )
    connection.execute("INSERT INTO automation_fts VALUES(?,?,?,?)", (review_id, title, content, " ".join(changed_paths)))
    sidecar = _automation_root(output) / "pending-reviews"
    body_path = sidecar / f"{review_id}.md"
    record_path = sidecar / f"{review_id}.json"
    body_path.write_text(content, encoding="utf-8", newline="\n")
    json_write(
        record_path,
        {
            "schema_version": AUTOMATION_SCHEMA_VERSION,
            "review_id": review_id,
            "status": "pending-agent-review",
            "kind": kind,
            "title": title,
            "body": str(body_path.resolve()),
            "changed_paths": changed_paths,
            "evidence": evidence,
            "created_at_utc": event["received_at_utc"],
        },
    )
    return review_id


def _process_event(
    connection: sqlite3.Connection,
    output: Path,
    repo: Path,
    event: dict[str, Any],
) -> dict[str, Any]:
    connection.row_factory = sqlite3.Row
    session_key = _ensure_session(connection, event, repo, output)
    turn_key, external_turn_id = _resolve_turn(connection, event, session_key)
    event_id = _event_id(event, session_key, turn_key)
    if connection.execute("SELECT 1 FROM events WHERE event_id=?", (event_id,)).fetchone():
        return {"status": "duplicate", "event_id": event_id, "session_key": session_key, "turn_key": turn_key}
    payload = json.dumps(event, ensure_ascii=False, sort_keys=True)
    connection.execute(
        "INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            event_id,
            event["harness"],
            event["event_name"],
            event["canonical_type"],
            session_key,
            turn_key,
            event.get("tool_use_id"),
            event["cwd"],
            event["received_at_utc"],
            int(event.get("redaction_count", 0)),
            payload,
        ),
    )
    canonical = event["canonical_type"]
    if canonical == "turn.prompt" and turn_key:
        connection.execute(
            "UPDATE turns SET prompt=?,status='active',started_at_utc=COALESCE(started_at_utc,?) WHERE turn_key=?",
            (event.get("prompt") or "", event["received_at_utc"], turn_key),
        )
        connection.execute(
            "UPDATE sessions SET first_prompt=CASE WHEN first_prompt='' THEN ? ELSE first_prompt END WHERE session_key=?",
            (event.get("prompt") or "", session_key),
        )
    elif canonical == "turn.assistant" and turn_key:
        connection.execute("UPDATE turns SET assistant_message=? WHERE turn_key=?", (event.get("assistant_message") or "", turn_key))
        connection.execute("UPDATE sessions SET last_assistant_message=? WHERE session_key=?", (event.get("assistant_message") or "", session_key))
    if canonical in {"tool.result", "file.changed"}:
        paths = _relative_changed_paths(
            event.get("changed_paths") or [],
            repo,
            output,
            Path(str(event.get("cwd") or repo)).expanduser(),
        )
        connection.execute(
            "INSERT INTO tool_events VALUES(?,?,?,?,?,?,?)",
            (event_id, session_key, turn_key, event.get("tool_name"), event.get("tool_status") or "completed", json.dumps(paths, ensure_ascii=False), payload),
        )
        for path in paths:
            connection.execute(
                "INSERT INTO changed_paths VALUES(?,?,?,?,1) ON CONFLICT(session_key,path) DO UPDATE SET last_event_id=excluded.last_event_id,change_count=changed_paths.change_count+1",
                (session_key, path, event_id, event_id),
            )
    review_id = None
    if canonical == "turn.stop" and turn_key:
        assistant = event.get("assistant_message") or ""
        if assistant:
            connection.execute("UPDATE turns SET assistant_message=? WHERE turn_key=?", (assistant, turn_key))
            connection.execute("UPDATE sessions SET last_assistant_message=? WHERE session_key=?", (assistant, session_key))
        connection.execute("UPDATE turns SET status='complete',completed_at_utc=? WHERE turn_key=?", (event["received_at_utc"], turn_key))
        connection.execute(
            "UPDATE sessions SET turn_count=(SELECT count(*) FROM turns WHERE session_key=? AND status='complete') WHERE session_key=?",
            (session_key, session_key),
        )
        review_id = _create_pending_review(connection, output, repo, event, session_key, turn_key)
    elif canonical == "session.end":
        active = connection.execute(
            "SELECT turn_key FROM turns WHERE session_key=? AND status='active' ORDER BY ordinal DESC LIMIT 1",
            (session_key,),
        ).fetchone()
        if active:
            connection.execute("UPDATE turns SET status='complete',completed_at_utc=? WHERE turn_key=?", (event["received_at_utc"], active[0]))
            review_id = _create_pending_review(connection, output, repo, event, session_key, str(active[0]))
        connection.execute("UPDATE sessions SET status='complete',ended_at_utc=? WHERE session_key=?", (event["received_at_utc"], session_key))
    return {
        "status": "recorded",
        "event_id": event_id,
        "session_key": session_key,
        "turn_key": turn_key,
        "external_turn_id": external_turn_id,
        "review_id": review_id,
    }


def drain_automation(output: Path, limit: int = 500) -> dict[str, Any]:
    output = output.resolve()
    initialize_automation_database(output)
    root = _automation_root(output)
    pending = root / "spool" / "pending"
    processed = root / "spool" / "processed"
    failed = root / "spool" / "failed"
    results: list[dict[str, Any]] = []
    with _drain_lock(output) as acquired:
        if not acquired:
            return {"schema_version": AUTOMATION_SCHEMA_VERSION, "status": "queued", "reason": "drain-lock-busy", "pending": len(_spool_events(pending))}
        connection = sqlite3.connect(output / AUTOMATION_DATABASE, timeout=10)
        try:
            connection.execute("PRAGMA busy_timeout=10000")
            for path in _spool_events(pending)[:limit]:
                try:
                    envelope = json_load(path)
                    event = envelope["event"]
                    repo = Path(envelope["repo_root"]).resolve()
                    connection.execute("BEGIN IMMEDIATE")
                    result = _process_event(connection, output, repo, event)
                    connection.commit()
                    destination = processed / f"{result['event_id']}.json"
                    if destination.exists():
                        path.unlink()
                    else:
                        path.replace(destination)
                    results.append(result)
                except Exception as exc:
                    connection.rollback()
                    destination = failed / path.name
                    if destination.exists():
                        destination = failed / f"{path.stem}-{uuid.uuid4().hex}.json"
                    path.replace(destination)
                    json_write(destination.with_suffix(".error.json"), {"status": "failed", "error": f"{type(exc).__name__}: {exc}"})
                    results.append({"status": "failed", "spool": str(destination), "error": f"{type(exc).__name__}: {exc}"})
        finally:
            connection.close()
    return {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "status": "passed" if not any(item["status"] == "failed" for item in results) else "failed",
        "processed": sum(item["status"] == "recorded" for item in results),
        "duplicates": sum(item["status"] == "duplicate" for item in results),
        "failed": sum(item["status"] == "failed" for item in results),
        "pending": len(_spool_events(pending)),
        "results": results,
    }


def retry_failed_automation(output: Path, limit: int = 500) -> dict[str, Any]:
    output = output.resolve()
    root = _automation_root(output)
    failed = root / "spool" / "failed"
    pending = root / "spool" / "pending"
    moved = 0
    for path in _spool_events(failed)[:limit]:
        destination = pending / f"retry-{time.time_ns():020d}-{uuid.uuid4().hex}.json"
        path.replace(destination)
        error = path.with_suffix(".error.json")
        if error.is_file():
            error.unlink()
        moved += 1
    result = drain_automation(output, limit)
    return {"schema_version": AUTOMATION_SCHEMA_VERSION, "status": result["status"], "retried": moved, "drain": result}


def _hook_context(output: Path) -> str:
    status = automation_status(output)
    return (
        "CKB 自动同步已启用：本轮事件会先进入脱敏、幂等的机器层队列。"
        f"当前待 Agent 审阅记录 {status['pending_reviews']} 条，失败事件 {status['failed_spool']} 条。"
        "分析和修改结论需使用简体中文核对来源后，再晋升到人类知识库。"
    )


def _hook_output(harness: str, event_name: str, context: str) -> dict[str, Any]:
    if event_name in {"SessionStart", "UserPromptSubmit"} and harness in {"codex", "claude", "dsh"}:
        return {
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "additionalContext": context,
            }
        }
    if harness == "gemini" and event_name in {"SessionStart", "BeforeAgent"}:
        return {"hookSpecificOutput": {"additionalContext": context}}
    if harness == "cursor" and event_name == "sessionStart":
        return {"additional_context": context}
    return {}


def ingest_event(
    harness: str,
    raw: dict[str, Any],
    registry_path: Path | None = None,
) -> dict[str, Any]:
    registry = (registry_path or default_registry_path()).expanduser().resolve()
    normalized = normalize_event(harness, raw)
    cwd = Path(str(normalized["cwd"])).expanduser().resolve()
    matched = _registration_for_event(registry, cwd, harness)
    if matched is None:
        return {
            "schema_version": AUTOMATION_SCHEMA_VERSION,
            "status": "ignored",
            "reason": "project-not-registered-for-harness",
            "harness": harness,
            "cwd": str(cwd),
            "hook_output": _hook_output(harness, normalized["event_name"], "CKB 自动同步未对当前项目启用。"),
        }
    registration, match_kind, matched_root = matched
    output = Path(registration["knowledge_output"]).resolve()
    repo = Path(registration["repo_root"]).resolve()
    if not (output / "state.json").is_file():
        raise CkbError(f"registered knowledge output is missing state.json: {output}")
    redacted = redact_event(normalized, registration.get("custom_redactions", []), int(registration.get("max_field_chars", 12_000)))
    redacted["registration_match"] = {"kind": match_kind, "root": matched_root}
    spool = enqueue_event(
        output,
        {
            "schema_version": AUTOMATION_SCHEMA_VERSION,
            "registration_id": registration["registration_id"],
            "repo_root": str(repo),
            "knowledge_output": str(output),
            "event": redacted,
        },
    )
    drained = drain_automation(output)
    return {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "status": "recorded" if drained["processed"] else "duplicate" if drained["duplicates"] else "queued",
        "harness": harness,
        "event_name": normalized["event_name"],
        "canonical_type": normalized["canonical_type"],
        "repo_root": str(repo),
        "registration_match": {"kind": match_kind, "root": matched_root},
        "knowledge_output": str(output),
        "spool": str(spool),
        "redaction_count": redacted["redaction_count"],
        "redaction_types": redacted["redaction_types"],
        "drain": drained,
        "hook_output": _hook_output(harness, normalized["event_name"], _hook_context(output)),
    }


def automation_status(output: Path) -> dict[str, Any]:
    output = output.resolve()
    path = initialize_automation_database(output)
    root = _automation_root(output)
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        counts = {
            "events": connection.execute("SELECT count(*) FROM events").fetchone()[0],
            "sessions": connection.execute("SELECT count(*) FROM sessions").fetchone()[0],
            "active_sessions": connection.execute("SELECT count(*) FROM sessions WHERE status='active'").fetchone()[0],
            "turns": connection.execute("SELECT count(*) FROM turns").fetchone()[0],
            "changed_paths": connection.execute("SELECT count(*) FROM changed_paths").fetchone()[0],
            "pending_reviews": connection.execute("SELECT count(*) FROM pending_reviews WHERE status='pending-agent-review'").fetchone()[0],
            "reviewed": connection.execute("SELECT count(*) FROM pending_reviews WHERE status='agent-reviewed'").fetchone()[0],
        }
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        connection.close()
    return {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "status": "ready" if integrity == "ok" else "failed",
        "database": str(path),
        **counts,
        "pending_spool": len(_spool_events(root / "spool/pending")),
        "failed_spool": len(_spool_events(root / "spool/failed")),
        "sqlite_integrity": integrity,
    }


def pending_automation_reviews(output: Path, include_reviewed: bool = False) -> dict[str, Any]:
    output = output.resolve()
    path = initialize_automation_database(output)
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        query = "SELECT review_id,kind,title,status,changed_paths_json,created_at_utc,reviewed_at_utc,human_file FROM pending_reviews"
        if not include_reviewed:
            query += " WHERE status='pending-agent-review'"
        query += " ORDER BY created_at_utc,review_id"
        rows = []
        for row in connection.execute(query):
            item = dict(row)
            item["changed_paths"] = json.loads(item.pop("changed_paths_json"))
            rows.append(item)
    finally:
        connection.close()
    return {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "status": "ready",
        "count": len(rows),
        "reviews": rows,
    }


def write_automation_review_template(output: Path, review_id: str, target: Path) -> dict[str, Any]:
    output = output.resolve()
    path = initialize_automation_database(output)
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute("SELECT * FROM pending_reviews WHERE review_id=?", (review_id,)).fetchone()
    finally:
        connection.close()
    if row is None:
        raise CkbError(f"automation review does not exist: {review_id}")
    changed_paths = json.loads(row["changed_paths_json"])
    template = {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "review_id": review_id,
        "status": "agent-reviewed",
        "kind": row["kind"],
        "title": "填写简洁的中文知识页标题",
        "body": "填写 Agent 重写并核实后的简体中文 Markdown 文件绝对路径",
        "evidence_note": "填写本次审阅如何核对会话、修改范围、源码和验证证据",
        "source_checks": [
            {
                "path": changed,
                "status": "agent-reviewed",
                "evidence_note": "填写重新打开并核对此路径后的中文证据说明",
            }
            for changed in changed_paths
        ],
        "linked_pages": [],
    }
    target = target.resolve()
    if target.exists():
        raise CkbError(f"automation review template already exists: {target}")
    json_write(target, template)
    return {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "status": "written",
        "review_id": review_id,
        "template": str(target),
        "changed_paths": changed_paths,
    }


def _heading_errors(text: str, changed: bool) -> list[str]:
    if not changed:
        return []
    headings = {
        re.sub(r"\s+", "", line.lstrip().lstrip("#").strip())
        for line in text.splitlines()
        if line.lstrip().startswith("#")
    }
    return [heading for heading in _CHANGE_HEADINGS if heading not in headings]


def review_automation(output: Path, review_path: Path) -> dict[str, Any]:
    output = output.resolve()
    value = json_load(review_path.resolve())
    if value.get("status") != "agent-reviewed":
        raise CkbError("automation review status must be agent-reviewed")
    review_id = str(value.get("review_id") or "")
    if not review_id:
        raise CkbError("automation review requires review_id")
    body_path = Path(str(value.get("body") or ""))
    if not body_path.is_file():
        raise CkbError(f"automation review body is missing: {body_path}")
    body = body_path.read_text(encoding="utf-8-sig").strip()
    from .machine_knowledge import contains_chinese_narrative

    if not contains_chinese_narrative(body):
        raise CkbError("automation review body must use Simplified Chinese")
    title = str(value.get("title") or "").strip()
    if not title:
        raise CkbError("automation review requires a human-readable title")
    evidence_note = str(value.get("evidence_note") or "").strip()
    if not contains_chinese_narrative(evidence_note):
        raise CkbError("automation review requires a Simplified-Chinese evidence_note")
    path = initialize_automation_database(output)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute("SELECT * FROM pending_reviews WHERE review_id=?", (review_id,)).fetchone()
        if row is None:
            raise CkbError(f"automation review does not exist: {review_id}")
        if row["status"] != "pending-agent-review":
            raise CkbError(f"automation review is not pending: {review_id}; status={row['status']}")
        changed_paths = json.loads(row["changed_paths_json"])
        source_checks = list(value.get("source_checks") or [])
        checked_paths = [str(item.get("path") or "").replace("\\", "/") for item in source_checks]
        if sorted(checked_paths) != sorted(changed_paths):
            raise CkbError(f"automation review source-check set differs from changed paths: expected={changed_paths}; actual={checked_paths}")
        for item in source_checks:
            if item.get("status") != "agent-reviewed" or not contains_chinese_narrative(str(item.get("evidence_note") or "")):
                raise CkbError(f"automation source check requires agent-reviewed Chinese evidence: {item.get('path')}")
        errors = _heading_errors(body, bool(changed_paths))
        if errors:
            raise CkbError(f"changed automation review requires headings: {errors}")
        kind = str(value.get("kind") or row["kind"])
        if kind not in {"analysis", "change", "pitfall", "experiment", "session"}:
            raise CkbError(f"unsupported automation review kind: {kind}")
        from .workspace_notes import record_note, selectors_for_changed_paths

        selectors = list(value.get("linked_pages") or selectors_for_changed_paths(output, changed_paths))
        note = record_note(output, kind, title, body_path, selectors=selectors)
        connection.execute(
            "UPDATE pending_reviews SET status='agent-reviewed',reviewed_at_utc=?,human_file=? WHERE review_id=?",
            (utc_now(), note.get("file"), review_id),
        )
        connection.commit()
    finally:
        connection.close()
    sidecar = _automation_root(output) / "pending-reviews" / f"{review_id}.json"
    record = json_load(sidecar)
    record.update(
        {
            "status": "agent-reviewed",
            "reviewed_at_utc": utc_now(),
            "human_note": note,
            "review_file": str(review_path.resolve()),
            "evidence_note": evidence_note,
            "source_checks": source_checks,
        }
    )
    json_write(sidecar, record)
    return {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "status": "agent-reviewed",
        "review_id": review_id,
        "human_note": note,
    }


def search_automation(output: Path, question: str, limit: int = 8) -> list[dict[str, Any]]:
    path = output.resolve() / AUTOMATION_DATABASE
    if not path.is_file():
        return []
    terms = [value for value in re.findall(r"[\w\u3400-\u9fff.-]+", question.casefold()) if len(value) >= 2][:16]
    if not terms:
        return []
    query = " OR ".join('"' + value.replace('"', '""') + '"' for value in terms)
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = [
            dict(row)
            for row in connection.execute(
                "SELECT p.review_id,p.title,p.kind,p.status,p.human_file,p.content,p.changed_paths_json,"
                "bm25(automation_fts,0.0,6.0,3.0,2.0) AS rank "
                "FROM automation_fts JOIN pending_reviews p USING(review_id) WHERE automation_fts MATCH ? ORDER BY rank, p.review_id LIMIT ?",
                (query, limit),
            )
        ]
    except sqlite3.OperationalError:
        rows = []
    finally:
        connection.close()
    for row in rows:
        row["changed_paths"] = json.loads(row.pop("changed_paths_json"))
    return rows


def automation_documents(output: Path, kind: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    path = output.resolve() / AUTOMATION_DATABASE
    if not path.is_file():
        return []
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        query = "SELECT review_id,kind,title,status,human_file,content,changed_paths_json,created_at_utc FROM pending_reviews"
        params: list[Any] = []
        if kind:
            query += " WHERE kind=?"
            params.append(kind)
        query += " ORDER BY created_at_utc DESC,review_id DESC LIMIT ?"
        params.append(limit)
        rows = [dict(row) for row in connection.execute(query, params)]
    finally:
        connection.close()
    for row in rows:
        row["document_id"] = f"automation:{row.pop('review_id')}"
        row["changed_paths"] = json.loads(row.pop("changed_paths_json"))
        row["token_estimate"] = (len(row["content"].encode("utf-8")) + 2) // 3
    return rows
