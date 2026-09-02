from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3
from typing import Any, Iterable

from .contracts import (
    HEX64,
    TagNavigationError,
    atomic_write_json,
    canonical_json_text,
    ensure_within,
    sha256_file,
    validate_assertion,
)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assertions (
    assertion_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    recorded_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS assertions_replay_order
ON assertions(recorded_at, assertion_id);
"""


def connect(database: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = DELETE")
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_SQL)
    connection.execute("INSERT OR REPLACE INTO metadata(key, value) VALUES('schema_version', '1')")
    connection.commit()


def read_assertion_jsonl(path: Path) -> list[dict[str, Any]]:
    assertions: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TagNavigationError("INVALID_JSONL", f"第 {line_number} 行不是 JSON") from exc
        try:
            assertions.append(validate_assertion(value))
        except TagNavigationError as exc:
            raise TagNavigationError(exc.reason, f"第 {line_number} 行: {exc.detail}") from exc
    if not assertions:
        raise TagNavigationError("EMPTY_ASSERTIONS", "assertion JSONL 为空")
    return assertions


def ingest(connection: sqlite3.Connection, assertions: Iterable[dict[str, Any]]) -> dict[str, int]:
    inserted = 0
    duplicates = 0
    connection.execute("BEGIN IMMEDIATE")
    try:
        for assertion in assertions:
            payload = canonical_json_text(assertion)
            existing = connection.execute(
                "SELECT assertion_id, payload_json FROM assertions WHERE idempotency_key = ?",
                (assertion["idempotency_key"],),
            ).fetchone()
            if existing is not None:
                if existing["assertion_id"] == assertion["assertion_id"] and existing["payload_json"] == payload:
                    duplicates += 1
                    continue
                raise TagNavigationError(
                    "IDEMPOTENCY_CONFLICT",
                    f"idempotency_key={assertion['idempotency_key']} 已绑定不同 payload",
                )
            try:
                connection.execute(
                    "INSERT INTO assertions(assertion_id, idempotency_key, recorded_at, payload_json) VALUES(?, ?, ?, ?)",
                    (
                        assertion["assertion_id"],
                        assertion["idempotency_key"],
                        assertion["recorded_at"],
                        payload,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise TagNavigationError("ASSERTION_ID_CONFLICT", assertion["assertion_id"]) from exc
            inserted += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return {"inserted": inserted, "duplicates": duplicates}


def load_assertions(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT payload_json FROM assertions ORDER BY recorded_at, assertion_id"
    ).fetchall()
    return [validate_assertion(json.loads(row["payload_json"])) for row in rows]


def integrity(connection: sqlite3.Connection) -> str:
    row = connection.execute("PRAGMA integrity_check").fetchone()
    return str(row[0])


def replay_with_rollback(
    assertion_path: Path,
    database: Path,
    rollback_manifest: Path,
) -> dict[str, Any]:
    assertions = read_assertion_jsonl(assertion_path)
    database.parent.mkdir(parents=True, exist_ok=True)
    rollback_manifest.parent.mkdir(parents=True, exist_ok=True)
    if rollback_manifest.exists():
        raise TagNavigationError("TARGET_EXISTS", f"rollback manifest 已存在: {rollback_manifest}")
    baseline_state = "present" if database.exists() else "absent"
    baseline_sha256 = sha256_file(database) if database.exists() else None
    backup_path = database.with_name(database.name + ".baseline") if database.exists() else None
    manifest_temporary = rollback_manifest.with_name(rollback_manifest.name + ".tmp")
    restore_temporary = database.with_name(database.name + ".restore.tmp")
    for owned_temporary in (manifest_temporary, restore_temporary):
        if owned_temporary.exists():
            raise TagNavigationError("TARGET_EXISTS", f"恢复临时文件已存在: {owned_temporary}")
    if backup_path is not None and backup_path.exists():
        raise TagNavigationError("TARGET_EXISTS", f"baseline 备份已存在: {backup_path}")
    try:
        if backup_path is not None:
            shutil.copy2(database, backup_path)
        connection = connect(database)
        try:
            initialize(connection)
            counts = ingest(connection, assertions)
            check = integrity(connection)
            if check != "ok":
                raise TagNavigationError("SQLITE_INTEGRITY_FAILED", check)
        finally:
            connection.close()
        generated_sha256 = sha256_file(database)
        manifest = {
            "schema_version": 1,
            "target_path": str(database.resolve()),
            "baseline_state": baseline_state,
            "baseline_sha256": baseline_sha256,
            "backup_path": str(backup_path.resolve()) if backup_path is not None else None,
            "generated_sha256": generated_sha256,
        }
        atomic_write_json(rollback_manifest, manifest)
    except Exception as original_error:
        recovery_error: Exception | None = None
        recovery_confirmed = False
        try:
            if baseline_state == "present":
                if database.exists() and sha256_file(database) == baseline_sha256:
                    recovery_confirmed = True
                elif backup_path is not None and backup_path.exists() and sha256_file(backup_path) == baseline_sha256:
                    shutil.copy2(backup_path, restore_temporary)
                    if sha256_file(restore_temporary) != baseline_sha256:
                        raise TagNavigationError("REPLAY_RECOVERY_FAILED", "restore 临时文件 hash 不等于 baseline")
                    restore_temporary.replace(database)
                    if sha256_file(database) != baseline_sha256:
                        raise TagNavigationError("REPLAY_RECOVERY_FAILED", "恢复后数据库 hash 不等于 baseline")
                    recovery_confirmed = True
                else:
                    raise TagNavigationError("REPLAY_RECOVERY_FAILED", "baseline 备份缺失或漂移")
            else:
                database.unlink(missing_ok=True)
                if database.exists():
                    raise TagNavigationError("REPLAY_RECOVERY_FAILED", "absent baseline 的数据库仍然存在")
                recovery_confirmed = True
        except Exception as exc:
            recovery_error = exc
        if recovery_confirmed:
            if backup_path is not None:
                backup_path.unlink(missing_ok=True)
            restore_temporary.unlink(missing_ok=True)
            manifest_temporary.unlink(missing_ok=True)
            rollback_manifest.unlink(missing_ok=True)
        if recovery_error is not None:
            raise TagNavigationError(
                "REPLAY_RECOVERY_FAILED",
                (
                    f"原始错误={original_error}; 恢复错误={recovery_error}; "
                    f"database={database}; backup={backup_path}; manifest={rollback_manifest}; "
                    f"manifest_temporary={manifest_temporary}; restore_temporary={restore_temporary}"
                ),
            ) from recovery_error
        raise
    return {
        "schema_version": 1,
        "status": "passed",
        "database": str(database.resolve()),
        "database_sha256": generated_sha256,
        "rollback_manifest": str(rollback_manifest.resolve()),
        "inserted": counts["inserted"],
        "duplicates": counts["duplicates"],
        "integrity_check": check,
    }


def _rollback_path_within(path: Path, workspace_root: Path, field: str) -> Path:
    try:
        return ensure_within(path, workspace_root, field)
    except TagNavigationError as exc:
        raise TagNavigationError("ROLLBACK_PATH_OUTSIDE_WORKSPACE", f"{field} 不在 workspace-root 内") from exc


def rollback(manifest_path: Path, workspace_root: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {"schema_version", "target_path", "baseline_state", "baseline_sha256", "backup_path", "generated_sha256"}
    if not isinstance(manifest, dict) or set(manifest) != expected or manifest.get("schema_version") != 1:
        raise TagNavigationError("INVALID_ROLLBACK_MANIFEST", str(manifest_path))
    target_value = manifest["target_path"]
    backup_value = manifest["backup_path"]
    baseline_state = manifest["baseline_state"]
    baseline_sha256 = manifest["baseline_sha256"]
    generated_sha256 = manifest["generated_sha256"]
    if not isinstance(target_value, str) or not target_value:
        raise TagNavigationError("INVALID_ROLLBACK_MANIFEST", "target_path 必须为非空字符串")
    if backup_value is not None and (not isinstance(backup_value, str) or not backup_value):
        raise TagNavigationError("INVALID_ROLLBACK_MANIFEST", "backup_path 必须为 null 或非空字符串")
    if not isinstance(generated_sha256, str) or not HEX64.fullmatch(generated_sha256):
        raise TagNavigationError("INVALID_ROLLBACK_MANIFEST", "generated_sha256 非法")
    if baseline_state == "absent":
        if baseline_sha256 is not None or backup_value is not None:
            raise TagNavigationError("INVALID_ROLLBACK_MANIFEST", "absent baseline 不得包含 hash 或 backup")
    elif baseline_state == "present":
        if not isinstance(baseline_sha256, str) or not HEX64.fullmatch(baseline_sha256) or backup_value is None:
            raise TagNavigationError("INVALID_ROLLBACK_MANIFEST", "present baseline 缺少合法 hash 或 backup")
    else:
        raise TagNavigationError("INVALID_ROLLBACK_MANIFEST", "baseline_state 非法")

    workspace = workspace_root.resolve()
    _rollback_path_within(manifest_path, workspace, "manifest")
    target = _rollback_path_within(Path(target_value), workspace, "target_path")
    backup = _rollback_path_within(Path(backup_value), workspace, "backup_path") if backup_value is not None else None
    if not target.exists() or sha256_file(target) != manifest["generated_sha256"]:
        raise TagNavigationError("ROLLBACK_DRIFT", "目标不存在或不再等于 generated_sha256")
    if baseline_state == "absent":
        target.unlink()
        restored = "absent"
    else:
        assert backup is not None
        if not backup.exists() or sha256_file(backup) != manifest["baseline_sha256"]:
            raise TagNavigationError("ROLLBACK_DRIFT", "baseline 备份缺失或漂移")
        shutil.copy2(backup, target)
        if sha256_file(target) != manifest["baseline_sha256"]:
            raise TagNavigationError("ROLLBACK_VERIFY_FAILED", "恢复后 hash 不等于 baseline")
        backup.unlink()
        restored = manifest["baseline_sha256"]
    return {
        "schema_version": 1,
        "status": "passed",
        "target_path": str(target),
        "restored": restored,
    }
