"""Deterministic Git-to-knowledge fact freshness state.

This machine-only layer observes the live repository without changing the fixed
source graph.  It records bounded drift summaries, disposable dirty overlays,
isolated migration plans, and conservative collaboration candidates.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Iterator
import uuid

from .common import CkbError, json_load, json_write, path_inside, run, stable_id, utc_now


FRESHNESS_SCHEMA_VERSION = 1
FRESHNESS_STATES = {
    "current",
    "stale-committed",
    "provisional-dirty",
    "migration-pending",
    "migration-ready",
    "unavailable",
}
COLLABORATION_STATUSES = {"implemented", "planned", "superseded"}
MAX_CHANGED_PATHS = 100
MAX_DIRTY_PATHS = 100
MAX_EVENTS = 100
MAX_SESSION_CACHE = 64
MAX_OVERLAYS = 64
MAX_COLLABORATION_RECORDS = 1000
OVERLAY_LIFETIME_SECONDS = 24 * 60 * 60
GIT_TIMEOUT_SECONDS = 20
LOCK_TIMEOUT_SECONDS = 10.0
LOCK_STALE_SECONDS = 60.0
LOCK_RELEASE_TIMEOUT_SECONDS = 1.0
LOCK_RETRY_SECONDS = 0.025
_HEX_OBJECT = re.compile(r"[0-9a-fA-F]{7,64}")
_GIT_ACTION = re.compile(
    r"(?i)(?:^|[;&|]\s*|\s)git(?:\.exe)?"
    r"(?:\s+-C\s+(?:\"[^\"]+\"|'[^']+'|\S+)|\s+--(?:git-dir|work-tree)(?:=\S+|\s+\S+)|\s+-[^\s]+)*"
    r"\s+(commit|merge|pull|switch|checkout)\b"
)


def _root(output: Path) -> Path:
    value = output.resolve() / "workspace-meta" / "freshness"
    for relative in ("overlays", "plans"):
        (value / relative).mkdir(parents=True, exist_ok=True)
    return value


def _pid_alive(pid: Any) -> bool:
    try:
        value = int(pid)
    except (TypeError, ValueError):
        return False
    if value <= 0:
        return False
    if value == os.getpid():
        return True
    if os.name == "nt":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, value)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(value, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _read_lock(path: Path) -> dict[str, Any]:
    try:
        value = json_load(path)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _lock_file_identity(path: Path) -> tuple[int, int] | None:
    try:
        metadata = path.stat()
    except OSError:
        return None
    return int(metadata.st_dev), int(metadata.st_ino)


def _release_owned_state_lock(
    lock_path: Path,
    owner_token: str,
    acquired_identity: tuple[int, int] | None,
    timeout: float,
) -> None:
    """Release only this owner while tolerating short Windows sharing conflicts."""

    deadline = time.monotonic() + max(0.0, timeout)
    last_error = "lock-remained-busy"
    while True:
        try:
            current = json_load(lock_path)
        except FileNotFoundError:
            return
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            last_error = f"read:{type(exc).__name__}:{str(exc)[:160]}"
        else:
            current_identity = _lock_file_identity(lock_path)
            if current.get("owner_token") != owner_token:
                return
            if acquired_identity is not None and current_identity != acquired_identity:
                return
            try:
                # Reopen immediately before deletion so every retry observes
                # the latest owner instead of acting on an earlier sample.
                confirmed = json_load(lock_path)
                confirmed_identity = _lock_file_identity(lock_path)
                if confirmed.get("owner_token") != owner_token:
                    return
                if acquired_identity is not None and confirmed_identity != acquired_identity:
                    return
                lock_path.unlink()
                return
            except FileNotFoundError:
                return
            except (PermissionError, OSError) as exc:
                last_error = f"unlink:{type(exc).__name__}:{str(exc)[:160]}"
        if time.monotonic() >= deadline:
            raise CkbError(
                "fact freshness state lock release timeout: "
                f"path={lock_path}; owner_token={owner_token}; last_error={last_error}"
            )
        time.sleep(LOCK_RETRY_SECONDS)


@contextmanager
def _state_lock(
    output: Path,
    timeout: float = LOCK_TIMEOUT_SECONDS,
    release_timeout: float = LOCK_RELEASE_TIMEOUT_SECONDS,
) -> Iterator[bool]:
    root = _root(output)
    lock_path = root / "state.lock"
    owner_token = uuid.uuid4().hex
    deadline = time.monotonic() + timeout
    recovered = False
    acquired = False
    acquired_identity: tuple[int, int] | None = None
    while time.monotonic() < deadline:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            payload = {
                "schema_version": FRESHNESS_SCHEMA_VERSION,
                "owner_token": owner_token,
                "pid": os.getpid(),
                "created_unix": time.time(),
            }
            os.write(descriptor, (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"))
            os.close(descriptor)
            acquired_identity = _lock_file_identity(lock_path)
            acquired = True
            break
        except (FileExistsError, PermissionError):
            current = _read_lock(lock_path)
            created = float(current.get("created_unix") or 0)
            has_owner = bool(current.get("owner_token")) and current.get("pid") is not None
            try:
                file_age = time.time() - lock_path.stat().st_mtime
            except FileNotFoundError:
                continue
            stale = (has_owner and not _pid_alive(current.get("pid"))) or (
                not has_owner and file_age > LOCK_STALE_SECONDS
            )
            if stale:
                try:
                    observed_identity = (
                        current.get("owner_token"),
                        current.get("pid"),
                        current.get("created_unix"),
                    )
                    latest = _read_lock(lock_path)
                    latest_identity = (
                        latest.get("owner_token"),
                        latest.get("pid"),
                        latest.get("created_unix"),
                    )
                    if observed_identity != latest_identity:
                        continue
                    lock_path.unlink()
                    recovered = True
                    continue
                except FileNotFoundError:
                    continue
                except PermissionError:
                    pass
            time.sleep(0.025)
    if not acquired:
        raise CkbError(f"fact freshness state lock timeout: {lock_path}")
    try:
        yield recovered
    finally:
        _release_owned_state_lock(lock_path, owner_token, acquired_identity, release_timeout)


def _bounded_text(value: Any, field: str, limit: int = 2000) -> str:
    text = str(value or "").strip()
    if not text or len(text) > limit or any(character in text for character in ("\x00", "\r", "\n")):
        raise CkbError(f"fact freshness {field} must be bounded nonempty single-line text")
    return text


def _repository_binding(output: Path, repository: Path | None) -> tuple[Path, dict[str, Any], str]:
    state_path = output.resolve() / "state.json"
    if not state_path.is_file():
        raise CkbError(f"fact freshness requires knowledge state.json: {state_path}")
    state = json_load(state_path)
    if not isinstance(state, dict) or state.get("status") != "complete":
        raise CkbError("fact freshness requires a complete knowledge output state")
    binding = state.get("repository")
    if not isinstance(binding, dict):
        raise CkbError("fact freshness knowledge state has no repository binding")
    bound_commit = str(binding.get("commit") or "").strip()
    if not _HEX_OBJECT.fullmatch(bound_commit):
        raise CkbError("fact freshness knowledge state has no valid bound commit")
    configured_root = str(binding.get("root") or "").strip()
    repo = (repository or (Path(configured_root) if configured_root else None))
    if repo is None:
        raise CkbError("fact freshness repository root is unavailable")
    repo = repo.expanduser().resolve()
    if not repo.is_dir():
        raise CkbError(f"fact freshness repository root is missing: {repo}")
    return repo, state, bound_commit


def _git(repo: Path, *arguments: str, allow_failure: bool = False) -> str | None:
    completed = run(["git", "-C", str(repo), *arguments], timeout=GIT_TIMEOUT_SECONDS)
    if completed.returncode:
        if allow_failure:
            return None
        detail = (completed.stderr or completed.stdout).strip()
        raise CkbError(f"fact freshness Git probe failed: git -C {repo} {' '.join(arguments)}: {detail[:500]}")
    return completed.stdout.strip()


def _status_records(repo: Path) -> list[dict[str, str]]:
    completed = run(
        ["git", "-C", str(repo), "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        timeout=GIT_TIMEOUT_SECONDS,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise CkbError(f"fact freshness Git status failed: {detail[:500]}")
    frames = completed.stdout.split("\0")
    records: list[dict[str, str]] = []
    index = 0
    while index < len(frames):
        frame = frames[index]
        index += 1
        if len(frame) < 3:
            continue
        status = frame[:2]
        path = frame[3:].replace("\\", "/")
        if path:
            records.append({"status": status, "path": path})
        if any(marker in status for marker in ("R", "C")) and index < len(frames):
            index += 1
    return sorted(records, key=lambda item: (item["path"], item["status"]))


def _repository_snapshot(repo: Path) -> dict[str, Any]:
    top = _git(repo, "rev-parse", "--show-toplevel")
    if not top or Path(top).resolve() != repo.resolve():
        raise CkbError(f"fact freshness repository must be the Git worktree root: {repo}")
    head = _git(repo, "rev-parse", "--verify", "HEAD")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    branch = _git(repo, "symbolic-ref", "--quiet", "--short", "HEAD", allow_failure=True)
    dirty_records = _status_records(repo)
    signature_payload = {
        "head": head,
        "tree": tree,
        "branch": branch,
        "dirty": dirty_records,
    }
    signature = hashlib.sha256(
        json.dumps(signature_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        **signature_payload,
        "signature": signature,
        "dirty_paths": [item["path"] for item in dirty_records[:MAX_DIRTY_PATHS]],
        "dirty_count": len(dirty_records),
        "dirty_truncated": len(dirty_records) > MAX_DIRTY_PATHS,
    }


def _change_summary(repo: Path, bound_commit: str, current_head: str) -> dict[str, Any]:
    if bound_commit == current_head:
        return {
            "comparison": "bound-commit-to-current-head",
            "changed": 0,
            "changed_paths": [],
            "counts": {},
            "truncated": False,
        }
    if _git(repo, "cat-file", "-e", f"{bound_commit}^{{commit}}", allow_failure=True) is None:
        raise CkbError(f"fact freshness bound commit object is unavailable: {bound_commit}")
    completed = run(
        ["git", "-C", str(repo), "diff", "--name-status", "--find-renames", bound_commit, current_head],
        timeout=GIT_TIMEOUT_SECONDS,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise CkbError(f"fact freshness committed range diff failed: {detail[:500]}")
    changes: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        raw_status = fields[0]
        kind = raw_status[:1] or "?"
        counts[kind] = counts.get(kind, 0) + 1
        changes.append(
            {
                "status": raw_status,
                "path": fields[-1].replace("\\", "/"),
                **({"from_path": fields[1].replace("\\", "/")} if len(fields) > 2 else {}),
            }
        )
    return {
        "comparison": "bound-commit-to-current-head",
        "changed": len(changes),
        "changed_paths": [item["path"] for item in changes[:MAX_CHANGED_PATHS]],
        "changes": changes[:MAX_CHANGED_PATHS],
        "counts": dict(sorted(counts.items())),
        "truncated": len(changes) > MAX_CHANGED_PATHS,
    }


def _iso_after(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _prune_overlays(root: Path) -> None:
    paths = sorted((root / "overlays").glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    now = time.time()
    for index, path in enumerate(paths):
        try:
            record = json_load(path)
            expired = float(record.get("lifetime", {}).get("expires_unix") or 0) <= now
        except Exception:
            expired = True
        if expired or index >= MAX_OVERLAYS:
            path.unlink(missing_ok=True)


def _write_overlay(
    output: Path,
    repository: Path,
    snapshot: dict[str, Any],
    session_id: str,
    trigger: str,
) -> dict[str, Any]:
    root = _root(output)
    overlay_id = stable_id("freshness-overlay", str(output.resolve()), session_id, snapshot["head"], snapshot["signature"])
    path = root / "overlays" / f"{overlay_id}.json"
    created_unix = time.time()
    record = {
        "schema_version": FRESHNESS_SCHEMA_VERSION,
        "overlay_id": overlay_id,
        "status": "provisional-dirty",
        "write_layer": "machine-temporary-overlay",
        "repository": str(repository.resolve()),
        "head": snapshot["head"],
        "worktree_signature": snapshot["signature"],
        "dirty_paths": snapshot["dirty_paths"],
        "dirty_count": snapshot["dirty_count"],
        "dirty_truncated": snapshot["dirty_truncated"],
        "source": {"session_id": session_id, "trigger": trigger},
        "lifetime": {
            "policy": "discardable-24h",
            "created_at_utc": utc_now(),
            "expires_at_utc": _iso_after(OVERLAY_LIFETIME_SECONDS),
            "expires_unix": created_unix + OVERLAY_LIFETIME_SECONDS,
        },
        "discard": {
            "action": "delete-machine-overlay-only",
            "command": ["freshness", "overlay-discard", "--out", str(output.resolve()), "--overlay-id", overlay_id],
            "git_worktree_changed": False,
        },
        "promoted_to_stable_facts": False,
        "promoted_to_human_layer": False,
    }
    json_write(path, record)
    _prune_overlays(root)
    return {**record, "path": str(path.resolve())}


def _migration_evidence(plan: dict[str, Any], current_head: str) -> dict[str, Any]:
    staging = Path(str(plan.get("staging_output") or "")).expanduser().resolve()
    blockers: list[str] = []
    staging_state: dict[str, Any] = {}
    if not staging.is_dir():
        blockers.append("staging-output-missing")
    else:
        state_path = staging / "state.json"
        if not state_path.is_file():
            blockers.append("staging-state-missing")
        else:
            try:
                staging_state = json_load(state_path)
            except Exception:
                blockers.append("staging-state-invalid")
        if staging_state.get("status") != "complete":
            blockers.append("staging-not-complete")
        staging_commit = str((staging_state.get("repository") or {}).get("commit") or "")
        if staging_commit != current_head:
            blockers.append("staging-target-commit-mismatch")
        if not (staging / ".complete").is_file():
            blockers.append("staging-complete-marker-missing")
        for relative, reason in (
            ("audit/global.json", "staging-global-audit-not-passed"),
            ("migration/audit.json", "staging-migration-audit-not-passed"),
        ):
            path = staging / relative
            try:
                passed = path.is_file() and json_load(path).get("status") == "passed"
            except Exception:
                passed = False
            if not passed:
                blockers.append(reason)
    return {
        **plan,
        "status": "ready" if not blockers else "pending",
        "target_commit": current_head,
        "staging_output": str(staging),
        "blockers": blockers,
        "cutover_performed": False,
    }


def _next_action(state: str, output: Path, repository: Path | None, head: str | None, overlay: dict[str, Any] | None, migration: dict[str, Any] | None) -> dict[str, Any]:
    if state == "current":
        return {"action": "reuse-stable-facts", "rebuild": False}
    if state == "stale-committed":
        staging = output.resolve().parent / f"{output.resolve().name}.staging-{str(head or 'unknown')[:12]}"
        return {
            "action": "create-migration-plan",
            "staging_output": str(staging),
            "command": [
                "freshness",
                "plan",
                "--out",
                str(output.resolve()),
                "--repo",
                str(repository.resolve()) if repository else "REPOSITORY",
                "--staging-out",
                str(staging),
            ],
        }
    if state == "provisional-dirty":
        return {
            "action": "commit-or-discard-worktree-overlay",
            "overlay_id": overlay.get("overlay_id") if overlay else None,
            "overlay_discard": overlay.get("discard", {}).get("command") if overlay else None,
            "git_worktree_changed_by_discard": False,
        }
    if state == "migration-pending":
        return {
            "action": "complete-isolated-staging",
            "staging_output": migration.get("staging_output") if migration else None,
            "blockers": migration.get("blockers", []) if migration else [],
        }
    if state == "migration-ready":
        return {
            "action": "review-and-cutover-explicitly",
            "staging_output": migration.get("staging_output") if migration else None,
            "automatic_cutover": False,
        }
    return {"action": "retry-freshness-check", "automatic_assumption": False}


def _event_record(result: dict[str, Any], trigger: str) -> dict[str, Any]:
    return {
        "schema_version": FRESHNESS_SCHEMA_VERSION,
        "event_id": stable_id(
            "freshness-event",
            trigger,
            result.get("current_head"),
            result.get("worktree_signature"),
            time.time_ns(),
        ),
        "observed_at_utc": result["observed_at_utc"],
        "trigger": trigger,
        "state": result["state"],
        "stable_state": result.get("stable_state"),
        "current_head": result.get("current_head"),
        "branch": result.get("branch"),
        "dirty_count": result.get("dirty", {}).get("count"),
        "error": result.get("error"),
    }


def _write_events(root: Path, events: list[dict[str, Any]]) -> None:
    path = root / "events.jsonl"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in events[-MAX_EVENTS:]),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def _last_confirmed(previous: dict[str, Any]) -> dict[str, Any] | None:
    stored = previous.get("last_confirmed")
    if isinstance(stored, dict):
        return stored
    if previous.get("state") in FRESHNESS_STATES - {"unavailable"}:
        return {
            key: previous.get(key)
            for key in ("state", "stable_state", "bound_commit", "current_head", "branch", "observed_at_utc")
        }
    return None


def _unavailable_result(output: Path, trigger: str, previous: dict[str, Any], error: Exception, recovered: bool) -> dict[str, Any]:
    result = {
        "schema_version": FRESHNESS_SCHEMA_VERSION,
        "state": "unavailable",
        "stable_state": "unavailable",
        "observed_at_utc": utc_now(),
        "trigger": trigger,
        "bound_commit": None,
        "current_head": None,
        "branch": None,
        "dirty": {"count": None, "paths": [], "truncated": False},
        "change_summary": None,
        "migration": None,
        "overlay": None,
        "cache_hit": False,
        "lock_recovered": recovered,
        "recovered_from_unavailable": False,
        "stable_facts_current": False,
        "last_confirmed": _last_confirmed(previous),
        "error": {"type": type(error).__name__, "message": str(error)[:500]},
        "writes": {"machine_freshness": True, "stable_facts": False, "human_layer": False},
        "next_action": _next_action("unavailable", output, None, None, None, None),
        "session_cache": dict(previous.get("session_cache") or {}),
    }
    return result


def check_fact_freshness(
    output: Path,
    repository: Path | None = None,
    *,
    session_id: str | None = None,
    trigger: str = "explicit-status",
    force: bool = False,
) -> dict[str, Any]:
    """Inspect one live repository and atomically update only machine freshness state."""

    output = output.expanduser().resolve()
    session = str(session_id or os.environ.get("CKB_FRESHNESS_SESSION_ID") or f"process-{os.getpid()}").strip()
    trigger_value = _bounded_text(trigger, "trigger", 200)
    probe: tuple[Path, dict[str, Any], str, dict[str, Any]] | None = None
    probe_error: Exception | None = None
    try:
        repo, knowledge_state, bound_commit = _repository_binding(output, repository)
        snapshot = _repository_snapshot(repo)
        probe = (repo, knowledge_state, bound_commit, snapshot)
    except Exception as exc:
        probe_error = exc
    with _state_lock(output) as lock_recovered:
        root = _root(output)
        state_path = root / "state.json"
        try:
            previous = json_load(state_path) if state_path.is_file() else {}
            if not isinstance(previous, dict):
                previous = {}
        except Exception:
            previous = {}
        try:
            if probe_error is not None:
                raise probe_error
            assert probe is not None
            repo, knowledge_state, bound_commit, snapshot = probe
            cache = dict(previous.get("session_cache") or {})
            cache_entry = cache.get(session) if isinstance(cache.get(session), dict) else None
            cache_hit = bool(cache_entry and cache_entry.get("signature") == snapshot["signature"] and not force)
            if cache_hit and isinstance(cache_entry.get("change_summary"), dict):
                change_summary = cache_entry["change_summary"]
            else:
                change_summary = _change_summary(repo, bound_commit, snapshot["head"])
            stable_state = "current" if snapshot["head"] == bound_commit else "stale-committed"
            migration = None
            plan = previous.get("migration_plan")
            if stable_state == "stale-committed" and isinstance(plan, dict):
                if plan.get("bound_commit") == bound_commit and plan.get("target_commit") == snapshot["head"]:
                    migration = _migration_evidence(plan, snapshot["head"])
                    stable_state = "migration-ready" if migration["status"] == "ready" else "migration-pending"
            overlay = None
            outward_state = stable_state
            if snapshot["dirty_count"]:
                overlay = _write_overlay(output, repo, snapshot, session, trigger_value)
                outward_state = "provisional-dirty"
            observed = utc_now()
            previous_unavailable = previous.get("state") == "unavailable"
            result = {
                "schema_version": FRESHNESS_SCHEMA_VERSION,
                "state": outward_state,
                "stable_state": stable_state,
                "observed_at_utc": observed,
                "trigger": trigger_value,
                "repository": str(repo),
                "knowledge_state": str((output / "state.json").resolve()),
                "knowledge_state_status": knowledge_state.get("status"),
                "bound_commit": bound_commit,
                "current_head": snapshot["head"],
                "current_tree": snapshot["tree"],
                "branch": snapshot["branch"],
                "worktree_signature": snapshot["signature"],
                "dirty": {
                    "count": snapshot["dirty_count"],
                    "paths": snapshot["dirty_paths"],
                    "truncated": snapshot["dirty_truncated"],
                },
                "change_summary": change_summary,
                "migration": migration,
                "migration_plan": plan if isinstance(plan, dict) else None,
                "overlay": overlay,
                "cache_hit": cache_hit,
                "forced": force,
                "lock_recovered": lock_recovered,
                "recovered_from_unavailable": previous_unavailable,
                "stable_facts_current": outward_state == "current",
                "last_confirmed": {
                    "state": outward_state,
                    "stable_state": stable_state,
                    "bound_commit": bound_commit,
                    "current_head": snapshot["head"],
                    "branch": snapshot["branch"],
                    "observed_at_utc": observed,
                },
                "error": None,
                "writes": {"machine_freshness": True, "stable_facts": False, "human_layer": False},
            }
            result["next_action"] = _next_action(outward_state, output, repo, snapshot["head"], overlay, migration)
            cache[session] = {
                "signature": snapshot["signature"],
                "head": snapshot["head"],
                "change_summary": change_summary,
                "stable_state": stable_state,
                "observed_at_utc": observed,
            }
            cache_items = sorted(cache.items(), key=lambda item: str(item[1].get("observed_at_utc") or ""), reverse=True)
            result["session_cache"] = dict(cache_items[:MAX_SESSION_CACHE])
        except Exception as exc:
            result = _unavailable_result(output, trigger_value, previous, exc, lock_recovered)
        previous_events = list(previous.get("recent_events") or []) if isinstance(previous.get("recent_events"), list) else []
        event = _event_record(result, trigger_value)
        recent_events = [*previous_events, event][-MAX_EVENTS:]
        result["recent_events"] = recent_events
        json_write(state_path, result)
        _write_events(root, recent_events)
        public = dict(result)
        public["state_file"] = str(state_path.resolve())
        public.pop("session_cache", None)
        return public


def create_migration_plan(
    output: Path,
    repository: Path,
    staging_output: Path,
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    output = output.expanduser().resolve()
    repository = repository.expanduser().resolve()
    staging = staging_output.expanduser().resolve()
    if staging == output or path_inside(staging, output) or path_inside(output, staging):
        raise CkbError("fact freshness staging output must be isolated from the stable output")
    if staging == repository or path_inside(staging, repository):
        raise CkbError("fact freshness staging output must not overlap the source repository")
    observed = check_fact_freshness(output, repository, session_id=session_id, trigger="migration-plan-preflight", force=True)
    if observed["stable_state"] not in {"stale-committed", "migration-pending", "migration-ready"}:
        raise CkbError(f"fact freshness migration plan requires committed HEAD drift: state={observed['state']}")
    plan_id = stable_id("freshness-migration", str(output), observed["bound_commit"], observed["current_head"], str(staging))
    plan = {
        "schema_version": FRESHNESS_SCHEMA_VERSION,
        "plan_id": plan_id,
        "status": "pending",
        "stable_output": str(output),
        "repository": str(repository),
        "bound_commit": observed["bound_commit"],
        "target_commit": observed["current_head"],
        "staging_output": str(staging),
        "created_at_utc": utc_now(),
        "created_by_session": str(session_id or "unspecified"),
        "command": [
            "migrate",
            "start",
            "--from-out",
            str(output),
            "--repo",
            str(repository),
            "--out",
            str(staging),
        ],
        "automatic_cutover": False,
        "stable_output_overwritten": False,
    }
    with _state_lock(output):
        root = _root(output)
        state_path = root / "state.json"
        current = json_load(state_path)
        if current.get("current_head") != plan["target_commit"] or current.get("bound_commit") != plan["bound_commit"]:
            raise CkbError("fact freshness repository changed while creating the migration plan")
        json_write(root / "plans" / f"{plan_id}.json", plan)
        current["migration_plan"] = plan
        current["migration"] = {**plan, "blockers": ["staging-output-missing"]}
        current["stable_state"] = "migration-pending"
        if current.get("state") != "provisional-dirty":
            current["state"] = "migration-pending"
        current["stable_facts_current"] = False
        current["next_action"] = _next_action(current["state"], output, repository, plan["target_commit"], current.get("overlay"), current["migration"])
        json_write(state_path, current)
    return {
        **plan,
        "state": "provisional-dirty" if observed["state"] == "provisional-dirty" else "migration-pending",
        "stable_state": "migration-pending",
        "plan_path": str((_root(output) / "plans" / f"{plan_id}.json").resolve()),
        "writes": {"machine_freshness": True, "stable_facts": False, "human_layer": False},
    }


def discard_overlay(output: Path, overlay_id: str) -> dict[str, Any]:
    output = output.expanduser().resolve()
    identity = _bounded_text(overlay_id, "overlay_id", 200)
    if not re.fullmatch(r"freshness-overlay-[0-9a-f]{32}", identity):
        raise CkbError("fact freshness overlay_id has invalid shape")
    with _state_lock(output):
        path = _root(output) / "overlays" / f"{identity}.json"
        existed = path.is_file()
        path.unlink(missing_ok=True)
        state_path = _root(output) / "state.json"
        if state_path.is_file():
            state = json_load(state_path)
            if (state.get("overlay") or {}).get("overlay_id") == identity:
                state["overlay"] = None
                json_write(state_path, state)
    return {
        "schema_version": FRESHNESS_SCHEMA_VERSION,
        "status": "discarded" if existed else "not-found",
        "overlay_id": identity,
        "machine_overlay_deleted": existed,
        "git_worktree_changed": False,
        "stable_facts_changed": False,
        "human_layer_changed": False,
    }


def _command_strings(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        preferred = {"command", "cmd", "script", "shell_command", "shellcommand", "input"}
        for key, child in value.items():
            if str(key).casefold() in preferred and isinstance(child, str):
                yield child
            elif isinstance(child, (dict, list)):
                yield from _command_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _command_strings(child)
    elif isinstance(value, str):
        yield value


def classify_git_trigger(tool_input: Any) -> str | None:
    """Classify only successful Git actions that can change HEAD or branch."""

    for command in _command_strings(tool_input):
        match = _GIT_ACTION.search(command.strip())
        if not match:
            continue
        action = match.group(1).casefold()
        return "branch-switch" if action in {"switch", "checkout"} else action
    return None


def _collaboration_path(output: Path) -> Path:
    return _root(output) / "collaboration.jsonl"


def _read_collaboration(output: Path) -> list[dict[str, Any]]:
    path = _collaboration_path(output)
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            records.append(value)
    return records[-MAX_COLLABORATION_RECORDS:]


def _write_collaboration(output: Path, records: list[dict[str, Any]]) -> None:
    path = _collaboration_path(output)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in records[-MAX_COLLABORATION_RECORDS:]),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def _relative_paths(paths: list[str] | None) -> list[str]:
    result = []
    for raw in paths or []:
        value = _bounded_text(raw, "collaboration path", 1000).replace("\\", "/").strip("/")
        if not value or value == "." or value.startswith("../") or "/../" in f"/{value}/":
            raise CkbError(f"fact freshness collaboration path must be relative: {raw}")
        result.append(value)
    return sorted(set(result))[:100]


def record_collaboration(
    output: Path,
    *,
    feature: str,
    summary: str,
    status: str,
    branch: str,
    commit: str,
    task: str,
    paths: list[str] | None = None,
    supersedes: list[str] | None = None,
) -> dict[str, Any]:
    output = output.expanduser().resolve()
    status_value = str(status or "").strip().casefold()
    if status_value not in COLLABORATION_STATUSES:
        raise CkbError(f"fact freshness collaboration status must be one of {sorted(COLLABORATION_STATUSES)}")
    feature_value = _bounded_text(feature, "feature", 500)
    summary_value = _bounded_text(summary, "summary", 2000)
    branch_value = _bounded_text(branch, "branch", 500)
    commit_value = _bounded_text(commit, "commit", 64)
    if not _HEX_OBJECT.fullmatch(commit_value):
        raise CkbError("fact freshness collaboration commit must be a Git object id")
    task_value = _bounded_text(task, "task", 500)
    path_values = _relative_paths(paths)
    supersedes_values = sorted(set(_bounded_text(item, "supersedes record", 200) for item in (supersedes or [])))[:100]
    record_id = stable_id(
        "freshness-collaboration",
        feature_value,
        summary_value,
        status_value,
        branch_value,
        commit_value,
        task_value,
        json.dumps(path_values),
        json.dumps(supersedes_values),
    )
    record = {
        "schema_version": FRESHNESS_SCHEMA_VERSION,
        "record_id": record_id,
        "feature": feature_value,
        "summary": summary_value,
        "status": status_value,
        "branch": branch_value,
        "commit": commit_value,
        "task": task_value,
        "paths": path_values,
        "supersedes": supersedes_values,
        "recorded_at_utc": utc_now(),
        "write_layer": "machine-collaboration",
        "automatic_duplicate_decision": False,
    }
    with _state_lock(output):
        records = _read_collaboration(output)
        existing = next((item for item in records if item.get("record_id") == record_id), None)
        if existing is not None:
            return {**existing, "idempotent": True}
        records.append(record)
        _write_collaboration(output, records)
    return {**record, "idempotent": False}


def _feature_terms(text: str) -> set[str]:
    values = re.findall(r"[A-Za-z0-9_.-]{2,}|[\u3400-\u9fff]{2,}", text.casefold())
    terms: set[str] = set()
    for value in values:
        terms.add(value)
        if re.fullmatch(r"[\u3400-\u9fff]+", value) and len(value) > 2:
            terms.update(value[index : index + 2] for index in range(len(value) - 1))
    return terms


def query_collaboration_records(
    output: Path,
    *,
    branch: str | None = None,
    commit: str | None = None,
    task: str | None = None,
    status: str | None = None,
    summary: str | None = None,
    paths: list[str] | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    output = output.expanduser().resolve()
    if limit < 1 or limit > 500:
        raise CkbError("fact freshness collaboration query limit must be in [1, 500]")
    records = _read_collaboration(output)
    filters = {"branch": branch, "commit": commit, "task": task, "status": status}
    selected = records
    for field, expected in filters.items():
        if expected is not None:
            selected = [item for item in selected if str(item.get(field) or "").casefold() == str(expected).strip().casefold()]
    selected = list(reversed(selected))[:limit]
    requested_paths = set(_relative_paths(paths))
    requested_terms = _feature_terms(str(summary or ""))
    candidates: list[dict[str, Any]] = []
    if requested_paths or requested_terms:
        for record in reversed(records):
            record_paths = set(record.get("paths") or [])
            path_overlap = sorted(requested_paths & record_paths)
            record_terms = _feature_terms(f"{record.get('feature', '')} {record.get('summary', '')}")
            union = requested_terms | record_terms
            term_overlap = sorted(requested_terms & record_terms)
            jaccard = len(term_overlap) / len(union) if union else 0.0
            if not path_overlap and jaccard < 0.35:
                continue
            reasons = []
            if path_overlap:
                reasons.append("owned-path-overlap")
            if jaccard >= 0.35:
                reasons.append("feature-term-overlap")
            candidates.append(
                {
                    "record_id": record["record_id"],
                    "classification": "candidate-only",
                    "branch": record["branch"],
                    "commit": record["commit"],
                    "task": record["task"],
                    "status": record["status"],
                    "path_overlap": path_overlap,
                    "term_overlap": term_overlap[:20],
                    "term_jaccard": round(jaccard, 6),
                    "reasons": reasons,
                    "automatic_duplicate_decision": False,
                }
            )
            if len(candidates) >= limit:
                break
    return {
        "schema_version": FRESHNESS_SCHEMA_VERSION,
        "status": "ready",
        "records": selected,
        "record_count": len(selected),
        "duplicate_candidates": candidates,
        "candidate_boundary": "candidate-only-not-a-duplicate-decision",
    }


def attach_freshness_to_retrieval(output: Path, retrieval: dict[str, Any], freshness: dict[str, Any]) -> dict[str, Any]:
    """Attach currentness evidence and prepend a compact machine-pack guard."""

    result = dict(retrieval)
    public_freshness = {
        key: freshness.get(key)
        for key in (
            "schema_version",
            "state",
            "stable_state",
            "observed_at_utc",
            "trigger",
            "bound_commit",
            "current_head",
            "branch",
            "dirty",
            "change_summary",
            "migration",
            "overlay",
            "cache_hit",
            "stable_facts_current",
            "next_action",
            "error",
            "state_file",
        )
    }
    result["fact_freshness"] = public_freshness
    result["current_source_grounded"] = bool(result.get("source_grounded")) and freshness.get("state") == "current"
    pack_value = result.get("pack")
    if isinstance(pack_value, str) and Path(pack_value).is_file():
        pack_path = Path(pack_value)
        existing = pack_path.read_text(encoding="utf-8-sig")
        state = freshness.get("state")
        if state == "current":
            guard = (
                "# 源码事实新鲜度\n\n"
                "状态：`current`。当前仓库与固定事实绑定提交一致，可复用本阅读包中的稳定事实。\n\n"
            )
        else:
            guard = (
                "# 源码事实新鲜度\n\n"
                f"状态：`{state}`；稳定层状态：`{freshness.get('stable_state')}`。"
                "本阅读包中的固定源码事实只可作为已绑定提交的历史基线；在完成当前源码核验或显式切换已通过门的 staging 前，不得据此形成当前确定性结论。\n\n"
            )
        if not existing.startswith("# 源码事实新鲜度"):
            pack_path.write_text(guard + existing, encoding="utf-8", newline="\n")
        record_value = result.get("record")
        if isinstance(record_value, str) and Path(record_value).is_file():
            record = json_load(Path(record_value))
            if isinstance(record, dict):
                record["fact_freshness"] = public_freshness
                record["current_source_grounded"] = result["current_source_grounded"]
                json_write(Path(record_value), record)
    return result
