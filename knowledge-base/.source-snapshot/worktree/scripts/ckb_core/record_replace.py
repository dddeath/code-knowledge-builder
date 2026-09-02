"""Transactional replacement and rollback for one reviewed work-record body."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import socket
import sys
import time
from typing import Any, Iterator
import uuid

from .agent_index import audit_agent_index
from .agent_protocol_batch import (
    _descriptor_bytes as _owner_descriptor_bytes,
    _descriptor_lock as _owner_descriptor_lock,
    _descriptor_unlock as _owner_descriptor_unlock,
    _process_start_identity,
    _same_lock_file as _same_owner_lock_file,
    _write_lock_descriptor as _write_owner_lock_descriptor,
)
from .common import CkbError, json_load, json_write, safe_title, sha256_file, stable_id, utc_now
from .machine_knowledge import _markdown_sections, estimated_tokens
from .obsidian import NOTE_DIRECTORIES
from .operation_journal import record_operation
from .source_links import obsidian_open_uri
from .work_record_index import audit_work_record_index, refresh_work_record_index
from .workspace_notes import (
    DIRECTORY_BY_KIND,
    TAG_BY_KIND,
    _markdown_root,
    _resolve_page_titles,
    _source_links_for_titles,
    audit_notes,
    read_note_body,
    render_note_text,
)


RECORD_REPLACE_SCHEMA_VERSION = 1
REPLACE_LOCK_SCHEMA_VERSION = 1
REPLACE_LOCK_TIMEOUT_SECONDS = 30.0
REPLACE_LOCK_STALE_SECONDS = 120.0
REPLACE_LOCK_FIELDS = frozenset(
    {"schema_version", "owner_pid", "owner_token", "owner_process_start", "owner_host", "created_at_utc"}
)
REPLACE_OWNER_TOKEN_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_FILE_ROLES = (
    "human-note",
    "markdown-note",
    "note-metadata",
    "human-records",
    "markdown-records",
    "work-record-index-audit",
)


class RecordReplaceLockError(CkbError):
    def __init__(self, category: str, message: str):
        super().__init__(f"{category}: {message}")
        self.category = category


def _json_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _body_digest(body: str) -> str:
    return hashlib.sha256((body.rstrip() + "\n").encode("utf-8")).hexdigest()


def _token_estimate(text: str) -> int:
    return math.ceil(len(text.encode("utf-8")) / 3)


def _operation_root(output: Path) -> Path:
    return output.resolve() / "workspace-meta/record-replace"


def _journal_evidence(output: Path, manifest_path: Path) -> str:
    return manifest_path.resolve().relative_to(output.resolve()).as_posix()


def _new_replace_lock_record(owner_token: str) -> dict[str, Any]:
    state, identity = _process_start_identity(os.getpid())
    if state != "alive" or not identity:
        raise RecordReplaceLockError(
            "record-replace-lock-owner-identity-unavailable",
            f"current process identity is unavailable for record replacement lock: {os.getpid()}",
        )
    return {
        "schema_version": REPLACE_LOCK_SCHEMA_VERSION,
        "owner_pid": os.getpid(),
        "owner_token": owner_token,
        "owner_process_start": identity,
        "owner_host": socket.gethostname(),
        "created_at_utc": utc_now(),
    }


def _parse_replace_lock(value: bytes) -> tuple[dict[str, Any] | None, str | None]:
    try:
        record = json.loads(value.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "record-replace-lock-record-invalid"
    if not isinstance(record, dict) or set(record) != REPLACE_LOCK_FIELDS:
        return None, "record-replace-lock-record-invalid"
    if record.get("schema_version") != REPLACE_LOCK_SCHEMA_VERSION:
        return None, "record-replace-lock-record-invalid"
    if not isinstance(record.get("owner_pid"), int) or record["owner_pid"] < 1:
        return None, "record-replace-lock-record-invalid"
    if not isinstance(record.get("owner_token"), str) or not REPLACE_OWNER_TOKEN_PATTERN.fullmatch(record["owner_token"]):
        return None, "record-replace-lock-record-invalid"
    for field in ("owner_process_start", "owner_host", "created_at_utc"):
        if not isinstance(record.get(field), str) or not record[field] or len(record[field]) > 128:
            return None, "record-replace-lock-record-invalid"
    return record, None


def _replace_lock_owner_state(record: dict[str, Any]) -> str:
    if record["owner_host"] != socket.gethostname():
        return "record-replace-lock-owner-unverifiable"
    state, identity = _process_start_identity(int(record["owner_pid"]))
    if state == "dead":
        return "record-replace-lock-owner-dead"
    if state != "alive" or not identity:
        return "record-replace-lock-owner-unverifiable"
    if identity != record["owner_process_start"]:
        return "record-replace-lock-owner-pid-reused"
    return "record-replace-lock-owner-live"


def _release_replace_lock(lock: Path, descriptor: int, owner_token: str) -> None:
    category: str | None = None
    try:
        if not _same_owner_lock_file(lock, descriptor):
            category = "record-replace-lock-release-file-replaced"
        else:
            record, invalid = _parse_replace_lock(_owner_descriptor_bytes(descriptor))
            if invalid or record is None or record.get("owner_token") != owner_token:
                category = "record-replace-lock-release-owner-token-drift"
    finally:
        _owner_descriptor_unlock(descriptor)
        os.close(descriptor)
    if category is None:
        try:
            record, invalid = _parse_replace_lock(lock.read_bytes())
        except FileNotFoundError:
            category = "record-replace-lock-release-missing"
        else:
            if invalid or record is None or record.get("owner_token") != owner_token:
                category = "record-replace-lock-release-owner-token-drift"
            else:
                lock.unlink()
    if category:
        raise RecordReplaceLockError(category, f"record replacement lock ownership changed before release: {lock}")


@contextmanager
def _replace_lock(output: Path) -> Iterator[dict[str, Any]]:
    root = _operation_root(output)
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".lock"
    deadline = time.monotonic() + REPLACE_LOCK_TIMEOUT_SECONDS
    owner_token = uuid.uuid4().hex
    descriptor: int | None = None
    recovered_category: str | None = None
    last_category = "concurrent-record-replace-lock"
    while descriptor is None:
        created = False
        try:
            candidate = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            created = True
            os.write(candidate, b" ")
        except FileExistsError:
            try:
                candidate = os.open(lock, os.O_RDWR)
            except FileNotFoundError:
                continue
        if not _owner_descriptor_lock(candidate):
            os.close(candidate)
            last_category = "concurrent-record-replace-lock"
        elif not _same_owner_lock_file(lock, candidate):
            _owner_descriptor_unlock(candidate)
            os.close(candidate)
            continue
        elif created:
            _write_owner_lock_descriptor(candidate, _new_replace_lock_record(owner_token))
            descriptor = candidate
        else:
            age = max(0.0, time.time() - os.fstat(candidate).st_mtime)
            record, invalid = _parse_replace_lock(_owner_descriptor_bytes(candidate))
            if invalid or record is None:
                last_category = invalid or "record-replace-lock-record-invalid"
                recover = False
            else:
                last_category = _replace_lock_owner_state(record)
                recover = age > REPLACE_LOCK_STALE_SECONDS and last_category in {
                    "record-replace-lock-owner-dead",
                    "record-replace-lock-owner-pid-reused",
                }
                recovered_category = last_category if recover else None
            if recover:
                _write_owner_lock_descriptor(candidate, _new_replace_lock_record(owner_token))
                descriptor = candidate
            else:
                _owner_descriptor_unlock(candidate)
                os.close(candidate)
        if descriptor is None:
            if time.monotonic() >= deadline:
                raise RecordReplaceLockError(last_category, f"record replacement is busy: {lock}")
            time.sleep(0.05)
    body_error = False
    try:
        yield {
            "schema_version": REPLACE_LOCK_SCHEMA_VERSION,
            "owner_pid": os.getpid(),
            "owner_token": owner_token,
            "recovered_category": recovered_category,
            "_descriptor": descriptor,
        }
    except BaseException:
        body_error = True
        raise
    finally:
        try:
            _release_replace_lock(lock, descriptor, owner_token)
        except RecordReplaceLockError:
            if not body_error:
                raise


def _rollback_argv(output: Path, manifest: Path) -> list[str]:
    return [
        str(Path(sys.executable).resolve()),
        str(Path(sys.argv[0]).resolve()),
        "record-rollback",
        "--out",
        str(output.resolve()),
        "--manifest",
        str(manifest.resolve()),
    ]


def _powershell_command(argv: list[str]) -> str:
    escaped = [value.replace("'", "''") for value in argv]
    return "& " + " ".join(f"'{value}'" for value in escaped)


def _new_operation(output: Path, kind: str, title: str) -> tuple[str, Path, Path, dict[str, Any]]:
    operation_id = stable_id("record-replace", str(output.resolve()), kind, title, time.time_ns(), os.getpid())
    directory = _operation_root(output) / operation_id
    directory.mkdir(parents=True, exist_ok=False)
    manifest_path = directory / "manifest.json"
    rollback_argv = _rollback_argv(output, manifest_path)
    manifest = {
        "schema_version": RECORD_REPLACE_SCHEMA_VERSION,
        "operation_id": operation_id,
        "operation": "record-replace",
        "status": "preparing",
        "output": str(output.resolve()),
        "kind": kind,
        "title": title,
        "created_at_utc": utc_now(),
        "rollback_manifest": str(manifest_path.resolve()),
        "rollback_argv": rollback_argv,
        "rollback_command": _powershell_command(rollback_argv),
        "roles": [],
    }
    json_write(manifest_path, manifest)
    return operation_id, directory, manifest_path, manifest


def _read_title(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CkbError(f"managed knowledge note must be valid UTF-8: {path}: {exc}") from exc
    return text.splitlines()[0].removeprefix("# ").strip() if text else ""


def _locate_existing(output: Path, kind: str, title: str) -> tuple[Path, Path, Path, dict[str, Any]]:
    filename = safe_title(title) + ".md"
    relative = Path(DIRECTORY_BY_KIND[kind]) / filename
    markdown = output / "markdown" / relative
    human = output / "human" / relative
    metadata = output / "workspace-meta/notes" / (safe_title(title) + ".json")
    if not markdown.is_file() or not human.is_file():
        for other_kind, directory in DIRECTORY_BY_KIND.items():
            for root_name in ("markdown", "human"):
                candidate = output / root_name / directory / filename
                if candidate.is_file() and _read_title(candidate) == title:
                    if other_kind != kind:
                        raise CkbError(
                            f"record replace kind mismatch for exact title {title}: existing={other_kind}; requested={kind}"
                        )
        raise CkbError(f"record replace target does not exist for exact kind and title: kind={kind}; title={title}")
    if _read_title(markdown) != title or _read_title(human) != title:
        raise CkbError(f"record replace target title differs from the requested exact title: {title}")
    if markdown.read_bytes() != human.read_bytes():
        raise CkbError(f"record replace baseline human/markdown mirrors differ: {relative.as_posix()}")
    if not metadata.is_file():
        raise CkbError(f"record replace metadata is missing: {metadata}")
    record = json_load(metadata)
    if record.get("title") != title:
        raise CkbError(f"record replace metadata title differs from the requested exact title: {title}")
    if record.get("kind") != kind:
        raise CkbError(
            f"record replace kind mismatch for exact title {title}: existing={record.get('kind')}; requested={kind}"
        )
    return relative, human, markdown, record


def _copy_candidate_note_roots(output: Path, candidate_output: Path) -> None:
    for root_name in ("human", "markdown"):
        source_root = output / root_name
        target_root = candidate_output / root_name
        target_root.mkdir(parents=True, exist_ok=True)
        projection = source_root / "projection.json"
        if projection.is_file():
            shutil.copy2(projection, target_root / "projection.json")
        for directory in NOTE_DIRECTORIES:
            source = source_root / directory
            target = target_root / directory
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                target.mkdir(parents=True, exist_ok=True)
    gaps = output / "workspace-meta/gaps"
    if gaps.is_dir():
        shutil.copytree(gaps, candidate_output / "workspace-meta/gaps")


def _file_state(path: Path) -> dict[str, Any]:
    return {
        "exists": path.is_file(),
        "sha256": sha256_file(path) if path.is_file() else None,
        "size": path.stat().st_size if path.is_file() else 0,
    }


def _stage_file_role(
    output: Path,
    directory: Path,
    role: str,
    relative: Path,
    candidate: Path,
) -> dict[str, Any]:
    target = output / relative
    backup = directory / "backup/files" / relative
    staged = directory / "staging/files" / relative
    if target.is_file():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
    staged.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidate, staged)
    return {
        "name": role,
        "kind": "file",
        "path": relative.as_posix(),
        "baseline": {**_file_state(target), "backup": str(backup.resolve()) if backup.is_file() else None},
        "modified": {**_file_state(staged), "candidate": str(staged.resolve())},
    }


def _agent_snapshot(connection: sqlite3.Connection, title: str) -> dict[str, Any]:
    note = connection.execute(
        "SELECT note_title,tag,note_file,content,token_estimate FROM notes WHERE note_title=?",
        (title,),
    ).fetchall()
    links = connection.execute(
        "SELECT note_title,page_title FROM note_links WHERE note_title=? ORDER BY page_title",
        (title,),
    ).fetchall()
    fts = connection.execute(
        "SELECT note_title,title,content FROM note_fts WHERE note_title=?",
        (title,),
    ).fetchall()
    return {"note": [list(row) for row in note], "links": [list(row) for row in links], "fts": [list(row) for row in fts]}


def _agent_candidate(baseline: dict[str, Any], title: str, text: str, links: list[str]) -> dict[str, Any]:
    if len(baseline.get("note", [])) != 1:
        raise CkbError(f"agent-index.sqlite must contain exactly one work record for title: {title}")
    row = list(baseline["note"][0])
    row[3] = text
    row[4] = _token_estimate(text)
    return {
        "note": [row],
        "links": [[title, value] for value in sorted(set(links))],
        "fts": [[title, title, text]],
    }


def _apply_agent_state(connection: sqlite3.Connection, title: str, state: dict[str, Any]) -> None:
    if len(state.get("note", [])) != 1:
        raise CkbError(f"invalid agent-index candidate for title: {title}")
    cursor = connection.execute(
        "UPDATE notes SET tag=?,note_file=?,content=?,token_estimate=? WHERE note_title=?",
        (state["note"][0][1], state["note"][0][2], state["note"][0][3], state["note"][0][4], title),
    )
    if cursor.rowcount != 1:
        raise CkbError(f"agent-index work record disappeared during replacement: {title}")
    connection.execute("DELETE FROM note_links WHERE note_title=?", (title,))
    connection.execute("DELETE FROM note_fts WHERE note_title=?", (title,))
    connection.executemany("INSERT INTO note_links(note_title,page_title) VALUES(?,?)", state.get("links", []))
    connection.executemany("INSERT INTO note_fts(note_title,title,content) VALUES(?,?,?)", state.get("fts", []))


def _machine_snapshot(connection: sqlite3.Connection, document_id: str) -> dict[str, Any]:
    document = connection.execute(
        "SELECT document_id,kind,title,tag,human_file,source_entity_id,content,token_estimate FROM documents WHERE document_id=?",
        (document_id,),
    ).fetchall()
    sections = connection.execute(
        "SELECT section_id,document_id,ordinal,heading,content,token_estimate,source_path,start_line,end_line "
        "FROM sections WHERE document_id=? ORDER BY ordinal,section_id",
        (document_id,),
    ).fetchall()
    section_ids = [row[0] for row in sections]
    sources: list[list[Any]] = []
    if section_ids:
        placeholders = ",".join("?" for _ in section_ids)
        sources = [
            list(row)
            for row in connection.execute(
                f"SELECT section_id,entity_id FROM section_sources WHERE section_id IN ({placeholders}) ORDER BY section_id,entity_id",
                section_ids,
            )
        ]
    links = connection.execute(
        "SELECT source_document_id,target_document_id,target_title,relation FROM document_links "
        "WHERE source_document_id=? ORDER BY target_title,relation",
        (document_id,),
    ).fetchall()
    fts = connection.execute(
        "SELECT section_id,document_id,heading,content,source_path FROM section_fts "
        "WHERE document_id=? ORDER BY rowid",
        (document_id,),
    ).fetchall()
    return {
        "document": [list(row) for row in document],
        "sections": [list(row) for row in sections],
        "section_sources": sources,
        "links": [list(row) for row in links],
        "fts": [list(row) for row in fts],
    }


def _machine_candidate(baseline: dict[str, Any], text: str, links: list[str]) -> dict[str, Any]:
    if len(baseline.get("document", [])) != 1:
        raise CkbError("machine/knowledge.sqlite must contain exactly one target work record")
    document = list(baseline["document"][0])
    document_id = str(document[0])
    document[6] = text
    document[7] = estimated_tokens(text)
    sections: list[list[Any]] = []
    fts: list[list[Any]] = []
    for ordinal, (heading, content) in enumerate(_markdown_sections(text)):
        section_id = f"{document_id}:{ordinal}"
        sections.append([section_id, document_id, ordinal, heading, content, estimated_tokens(content), None, None, None])
        fts.append([section_id, document_id, heading, content, ""])
    return {
        "document": [document],
        "sections": sections,
        "section_sources": [],
        "links": [[document_id, None, value, "wikilink"] for value in sorted(set(links))],
        "fts": fts,
    }


def _apply_machine_state(connection: sqlite3.Connection, document_id: str, state: dict[str, Any]) -> None:
    if len(state.get("document", [])) != 1:
        raise CkbError(f"invalid machine knowledge candidate for document: {document_id}")
    cursor = connection.execute(
        "UPDATE documents SET kind=?,title=?,tag=?,human_file=?,source_entity_id=?,content=?,token_estimate=? WHERE document_id=?",
        (*state["document"][0][1:], document_id),
    )
    if cursor.rowcount != 1:
        raise CkbError(f"machine work record disappeared during replacement: {document_id}")
    existing_ids = [row[0] for row in connection.execute("SELECT section_id FROM sections WHERE document_id=?", (document_id,))]
    if existing_ids:
        placeholders = ",".join("?" for _ in existing_ids)
        connection.execute(f"DELETE FROM section_sources WHERE section_id IN ({placeholders})", existing_ids)
    connection.execute("DELETE FROM section_fts WHERE document_id=?", (document_id,))
    connection.execute("DELETE FROM sections WHERE document_id=?", (document_id,))
    connection.execute("DELETE FROM document_links WHERE source_document_id=?", (document_id,))
    connection.executemany("INSERT INTO sections VALUES(?,?,?,?,?,?,?,?,?)", state.get("sections", []))
    connection.executemany("INSERT INTO section_sources VALUES(?,?)", state.get("section_sources", []))
    connection.executemany("INSERT INTO document_links VALUES(?,?,?,?)", state.get("links", []))
    connection.executemany("INSERT INTO section_fts VALUES(?,?,?,?,?)", state.get("fts", []))


def _sqlite_integrity(connection: sqlite3.Connection, label: str) -> None:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
    if integrity != "ok" or foreign_keys:
        raise CkbError(f"{label} candidate integrity failed: integrity={integrity}; foreign_keys={foreign_keys[:10]}")


def _trial_agent(path: Path, title: str, baseline: dict[str, Any], candidate: dict[str, Any]) -> None:
    connection = sqlite3.connect(path, timeout=30)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")
        if _json_digest(_agent_snapshot(connection, title)) != _json_digest(baseline):
            raise CkbError(f"agent-index target drifted before candidate validation: {title}")
        _apply_agent_state(connection, title, candidate)
        _sqlite_integrity(connection, "agent-index.sqlite")
        if _json_digest(_agent_snapshot(connection, title)) != _json_digest(candidate):
            raise CkbError(f"agent-index candidate did not reopen exactly: {title}")
        connection.rollback()
    finally:
        if connection.in_transaction:
            connection.rollback()
        connection.close()


def _trial_machine(path: Path, document_id: str, baseline: dict[str, Any], candidate: dict[str, Any]) -> None:
    connection = sqlite3.connect(path, timeout=30)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")
        if _json_digest(_machine_snapshot(connection, document_id)) != _json_digest(baseline):
            raise CkbError(f"machine knowledge target drifted before candidate validation: {document_id}")
        _apply_machine_state(connection, document_id, candidate)
        _sqlite_integrity(connection, "machine/knowledge.sqlite")
        if _json_digest(_machine_snapshot(connection, document_id)) != _json_digest(candidate):
            raise CkbError(f"machine knowledge candidate did not reopen exactly: {document_id}")
        connection.rollback()
    finally:
        if connection.in_transaction:
            connection.rollback()
        connection.close()


def _current_agent(path: Path, title: str) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        return _agent_snapshot(connection, title)
    finally:
        connection.close()


def _current_machine(path: Path, document_id: str) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        return _machine_snapshot(connection, document_id)
    finally:
        connection.close()


def _commit_agent(path: Path, title: str, expected: dict[str, Any], state: dict[str, Any]) -> None:
    connection = sqlite3.connect(path, timeout=30)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")
        if _json_digest(_agent_snapshot(connection, title)) != _json_digest(expected):
            raise CkbError(f"agent-index target drifted during promotion: {title}")
        _apply_agent_state(connection, title, state)
        _sqlite_integrity(connection, "agent-index.sqlite")
        if _json_digest(_agent_snapshot(connection, title)) != _json_digest(state):
            raise CkbError(f"agent-index promoted state did not reopen exactly: {title}")
        connection.commit()
    finally:
        if connection.in_transaction:
            connection.rollback()
        connection.close()


def _commit_machine(path: Path, document_id: str, expected: dict[str, Any], state: dict[str, Any]) -> None:
    connection = sqlite3.connect(path, timeout=30)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")
        if _json_digest(_machine_snapshot(connection, document_id)) != _json_digest(expected):
            raise CkbError(f"machine knowledge target drifted during promotion: {document_id}")
        _apply_machine_state(connection, document_id, state)
        _sqlite_integrity(connection, "machine/knowledge.sqlite")
        if _json_digest(_machine_snapshot(connection, document_id)) != _json_digest(state):
            raise CkbError(f"machine knowledge promoted state did not reopen exactly: {document_id}")
        connection.commit()
    finally:
        if connection.in_transaction:
            connection.rollback()
        connection.close()


def _cleanup_new_sqlite_sidecars(path: Path, baseline: dict[str, bool]) -> None:
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(str(path) + suffix)
        if not baseline.get(suffix, False):
            sidecar.unlink(missing_ok=True)


def _promote_file(output: Path, role: dict[str, Any], expected: str | None) -> None:
    target = output / role["path"]
    current = _file_state(target)
    if current["exists"] != role["baseline"]["exists"] or current["sha256"] != expected:
        raise CkbError(f"record replace file drifted during promotion: {role['path']}")
    candidate = Path(role["modified"]["candidate"])
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".record-replace.tmp")
    shutil.copy2(candidate, temporary)
    os.replace(temporary, target)
    if sha256_file(target) != role["modified"]["sha256"]:
        raise CkbError(f"record replace promoted file did not reopen exactly: {role['path']}")


def _restore_file(output: Path, role: dict[str, Any]) -> None:
    target = output / role["path"]
    if role["baseline"]["exists"]:
        backup = Path(role["baseline"]["backup"])
        temporary = target.with_name(target.name + ".record-rollback.tmp")
        shutil.copy2(backup, temporary)
        os.replace(temporary, target)
    else:
        target.unlink(missing_ok=True)


def _verify_roles(output: Path, roles: list[dict[str, Any]], state_name: str) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for role in roles:
        expected = role[state_name]
        if role["kind"] == "file":
            actual = _file_state(output / role["path"])
            if actual["exists"] != expected["exists"] or actual["sha256"] != expected["sha256"]:
                errors.append({"role": role["name"], "expected": expected["sha256"], "actual": actual["sha256"]})
        elif role["name"] == "agent-index-note":
            actual_digest = _json_digest(_current_agent(output / role["path"], role["selector"]))
            if actual_digest != expected["sha256"]:
                errors.append({"role": role["name"], "expected": expected["sha256"], "actual": actual_digest})
        else:
            actual_digest = _json_digest(_current_machine(output / role["path"], role["selector"]))
            if actual_digest != expected["sha256"]:
                errors.append({"role": role["name"], "expected": expected["sha256"], "actual": actual_digest})
    return errors


def _candidate_contract(candidate_output: Path, relative: Path) -> dict[str, Any]:
    human = candidate_output / "human" / relative
    markdown = candidate_output / "markdown" / relative
    records_human = candidate_output / "human/RECORDS.md"
    records_markdown = candidate_output / "markdown/RECORDS.md"
    errors = audit_notes(candidate_output)
    work_records = audit_work_record_index(candidate_output)
    if human.read_bytes() != markdown.read_bytes():
        errors.append({"reason": "candidate-note-mirror-differs", "path": relative.as_posix()})
    if records_human.read_bytes() != records_markdown.read_bytes():
        errors.append({"reason": "candidate-record-index-mirror-differs"})
    if work_records["status"] != "passed":
        errors.extend(work_records["errors"])
    if errors:
        raise CkbError(f"record replace candidate audit failed: {errors[:10]}")
    return {"status": "passed", "note_errors": [], "work_record_index": work_records}


def _prepare_replacement(
    output: Path,
    kind: str,
    title: str,
    body_path: Path,
    selectors: list[str],
    query_record: Path | None,
    directory: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    fault: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    body = read_note_body(body_path)
    _markdown_root(output)
    relative, human_target, markdown_target, previous = _locate_existing(output, kind, title)
    explicit_evidence = bool(selectors) or query_record is not None
    if explicit_evidence:
        linked_titles = _resolve_page_titles(output, selectors, query_record)
        if kind != "session" and not linked_titles:
            raise CkbError(f"{kind} notes require at least one linked knowledge page")
        source_links = _source_links_for_titles(output, linked_titles)
        query_value = str(query_record.resolve()) if query_record else None
    else:
        linked_titles = list(previous.get("linked_pages") or [])
        source_links = list(previous.get("source_links") or [])
        query_value = previous.get("query_record")
        if kind != "session" and not linked_titles:
            raise CkbError(f"record replace cannot preserve an empty reviewed evidence set: {title}")
    text = render_note_text(kind, title, body, linked_titles, source_links)
    candidate_output = directory / "candidate-output"
    _copy_candidate_note_roots(output, candidate_output)
    for root_name in ("human", "markdown"):
        target = candidate_output / root_name / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    refresh_work_record_index(candidate_output)
    if fault == "candidate-mirror-diff":
        with (candidate_output / "human" / relative).open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("候选镜像故障注入。\n")
    candidate_audit = _candidate_contract(candidate_output, relative)
    now = utc_now()
    record_id = previous.get("record_id") or stable_id("work-record", kind, title.casefold(), relative.as_posix())
    replacement = {
        "operation_id": manifest["operation_id"],
        "replaced_at_utc": now,
        "previous_page_sha256": sha256_file(markdown_target),
        "previous_body_sha256": previous.get("body_sha256") or sha256_file(markdown_target),
        "body_sha256": _body_digest(body),
    }
    metadata = {
        **previous,
        "schema_version": max(1, int(previous.get("schema_version", 1))),
        "status": "agent-reviewed",
        "record_id": record_id,
        "kind": kind,
        "title": title,
        "file": str(human_target.resolve()),
        "compatibility_file": str(markdown_target.resolve()),
        "linked_pages": linked_titles,
        "source_links": source_links,
        "query_record": query_value,
        "created_at_utc": previous.get("created_at_utc") or previous.get("updated_at_utc") or now,
        "updated_at_utc": now,
        "body_sha256": _body_digest(body),
        "replacement": replacement,
        "obsidian_uri": obsidian_open_uri(markdown_target),
    }
    metadata_candidate = candidate_output / "workspace-meta/notes" / (safe_title(title) + ".json")
    json_write(metadata_candidate, metadata)
    role_sources = (
        ("human-note", Path("human") / relative, candidate_output / "human" / relative),
        ("markdown-note", Path("markdown") / relative, candidate_output / "markdown" / relative),
        ("note-metadata", Path("workspace-meta/notes") / (safe_title(title) + ".json"), metadata_candidate),
        ("human-records", Path("human/RECORDS.md"), candidate_output / "human/RECORDS.md"),
        ("markdown-records", Path("markdown/RECORDS.md"), candidate_output / "markdown/RECORDS.md"),
        (
            "work-record-index-audit",
            Path("workspace-meta/work-record-index-audit.json"),
            candidate_output / "workspace-meta/work-record-index-audit.json",
        ),
    )
    roles = [_stage_file_role(output, directory, role, relative_path, candidate) for role, relative_path, candidate in role_sources]
    agent_path = output / "agent-index.sqlite"
    machine_path = output / "machine/knowledge.sqlite"
    if not agent_path.is_file() or not machine_path.is_file():
        raise CkbError("record replace requires both agent-index.sqlite and machine/knowledge.sqlite")
    agent_connection = sqlite3.connect(f"file:{agent_path.as_posix()}?mode=ro", uri=True)
    try:
        agent_baseline = _agent_snapshot(agent_connection, title)
    finally:
        agent_connection.close()
    agent_candidate = _agent_candidate(agent_baseline, title, text, linked_titles)
    machine_connection = sqlite3.connect(f"file:{machine_path.as_posix()}?mode=ro", uri=True)
    try:
        rows = machine_connection.execute("SELECT document_id FROM documents WHERE title=? AND kind=?", (title, kind)).fetchall()
        if len(rows) != 1:
            raise CkbError(f"machine knowledge must contain one exact kind/title record: kind={kind}; title={title}")
        document_id = str(rows[0][0])
        machine_baseline = _machine_snapshot(machine_connection, document_id)
    finally:
        machine_connection.close()
    machine_candidate = _machine_candidate(machine_baseline, text, linked_titles)
    for folder, name, value in (
        ("backup", "agent-index-note.json", agent_baseline),
        ("staging", "agent-index-note.json", agent_candidate),
        ("backup", "machine-knowledge-note.json", machine_baseline),
        ("staging", "machine-knowledge-note.json", machine_candidate),
    ):
        json_write(directory / folder / name, value)
    roles.extend(
        [
            {
                "name": "agent-index-note",
                "kind": "sqlite-logical",
                "path": "agent-index.sqlite",
                "selector": title,
                "baseline": {
                    "sha256": _json_digest(agent_baseline),
                    "backup": str((directory / "backup/agent-index-note.json").resolve()),
                },
                "modified": {
                    "sha256": _json_digest(agent_candidate),
                    "candidate": str((directory / "staging/agent-index-note.json").resolve()),
                },
            },
            {
                "name": "machine-knowledge-note",
                "kind": "sqlite-logical",
                "path": "machine/knowledge.sqlite",
                "selector": document_id,
                "baseline": {
                    "sha256": _json_digest(machine_baseline),
                    "backup": str((directory / "backup/machine-knowledge-note.json").resolve()),
                },
                "modified": {
                    "sha256": _json_digest(machine_candidate),
                    "candidate": str((directory / "staging/machine-knowledge-note.json").resolve()),
                },
            },
        ]
    )
    _trial_agent(agent_path, title, agent_baseline, agent_candidate)
    _trial_machine(machine_path, document_id, machine_baseline, machine_candidate)
    manifest.update(
        {
            "status": "prepared",
            "prepared_at_utc": utc_now(),
            "record_id": record_id,
            "relative_note": relative.as_posix(),
            "explicit_evidence_replacement": explicit_evidence,
            "linked_pages": linked_titles,
            "body_sha256": _body_digest(body),
            "candidate_audit": candidate_audit,
            "roles": roles,
            "promotion_order": [role["name"] for role in roles],
        }
    )
    json_write(manifest_path, manifest)
    shutil.rmtree(candidate_output)
    return metadata, roles, agent_candidate, machine_candidate


def _restore_promoted(
    output: Path,
    roles: list[dict[str, Any]],
    promoted: list[str],
    agent_baseline: dict[str, Any],
    machine_baseline: dict[str, Any],
) -> None:
    by_name = {role["name"]: role for role in roles}
    for name in reversed(promoted):
        role = by_name[name]
        if role["kind"] == "file":
            _restore_file(output, role)
        elif name == "agent-index-note":
            current = _current_agent(output / role["path"], role["selector"])
            _commit_agent(output / role["path"], role["selector"], current, agent_baseline)
        else:
            current = _current_machine(output / role["path"], role["selector"])
            _commit_machine(output / role["path"], role["selector"], current, machine_baseline)


def _promotion(
    output: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    roles: list[dict[str, Any]],
    fault: str | None,
) -> dict[str, Any]:
    by_name = {role["name"]: role for role in roles}
    agent_role = by_name["agent-index-note"]
    machine_role = by_name["machine-knowledge-note"]
    agent_baseline = json_load(Path(agent_role["baseline"]["backup"]))
    agent_candidate = json_load(Path(agent_role["modified"]["candidate"]))
    machine_baseline = json_load(Path(machine_role["baseline"]["backup"]))
    machine_candidate = json_load(Path(machine_role["modified"]["candidate"]))
    sidecars = {
        role["name"]: {
            suffix: Path(str(output / role["path"]) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")
        }
        for role in (agent_role, machine_role)
    }
    promoted: list[str] = []
    manifest["status"] = "promoting"
    json_write(manifest_path, manifest)
    try:
        for role in roles:
            if role["kind"] == "file":
                _promote_file(output, role, role["baseline"]["sha256"])
            elif role["name"] == "agent-index-note":
                _commit_agent(output / role["path"], role["selector"], agent_baseline, agent_candidate)
            else:
                _commit_machine(output / role["path"], role["selector"], machine_baseline, machine_candidate)
            promoted.append(role["name"])
            if fault == f"after-{role['name']}":
                raise CkbError(f"injected record replace promotion failure after {role['name']}")
        verification_errors = _verify_roles(output, roles, "modified")
        note_errors = audit_notes(output)
        record_audit = audit_work_record_index(output)
        agent_audit = audit_agent_index(output)
        if verification_errors or note_errors or record_audit["status"] != "passed" or agent_audit["status"] != "passed":
            raise CkbError(
                "record replace post-promotion verification failed: "
                f"roles={verification_errors[:5]}; notes={note_errors[:5]}; records={record_audit['errors'][:5]}; "
                f"agent={agent_audit['errors'][:5]}"
            )
        manifest.update(
            {
                "status": "completed",
                "completed_at_utc": utc_now(),
                "verification": {
                    "status": "passed",
                    "role_errors": [],
                    "note_errors": [],
                    "work_record_index": record_audit,
                    "agent_index": agent_audit,
                },
            }
        )
        json_write(manifest_path, manifest)
        journal = record_operation(output, "record", "record:replace", "replaced", [_journal_evidence(output, manifest_path)])
        manifest["operation_journal"] = journal
        json_write(manifest_path, manifest)
        return journal
    except Exception:
        _restore_promoted(output, roles, promoted, agent_baseline, machine_baseline)
        restored_errors = _verify_roles(output, roles, "baseline")
        manifest.update(
            {
                "status": "failed-restored" if not restored_errors else "failed-restore-incomplete",
                "failed_at_utc": utc_now(),
                "promoted_before_failure": promoted,
                "restore_errors": restored_errors,
            }
        )
        json_write(manifest_path, manifest)
        if restored_errors:
            raise CkbError(f"record replace failed and baseline restoration was incomplete: {restored_errors[:10]}")
        raise
    finally:
        _cleanup_new_sqlite_sidecars(output / agent_role["path"], sidecars[agent_role["name"]])
        _cleanup_new_sqlite_sidecars(output / machine_role["path"], sidecars[machine_role["name"]])


def replace_note(
    output: Path,
    kind: str,
    title: str,
    body_path: Path,
    selectors: list[str] | None = None,
    query_record: Path | None = None,
    *,
    fault: str | None = None,
) -> dict[str, Any]:
    """Replace one exact managed record and publish every dependent role atomically."""

    output = output.resolve()
    normalized_title = title.strip()
    if kind not in TAG_BY_KIND:
        raise CkbError(f"note kind must be one of: {sorted(TAG_BY_KIND)}")
    if not normalized_title:
        raise CkbError("record replace title must not be empty")
    with _replace_lock(output):
        _operation_id, directory, manifest_path, manifest = _new_operation(output, kind, normalized_title)
        try:
            metadata, roles, _agent_candidate_state, _machine_candidate_state = _prepare_replacement(
                output,
                kind,
                normalized_title,
                body_path.resolve(),
                list(selectors or []),
                query_record.resolve() if query_record else None,
                directory,
                manifest_path,
                manifest,
                fault,
            )
            journal = _promotion(output, manifest_path, manifest, roles, fault)
            return {
                **metadata,
                "status": "replaced",
                "operation_id": manifest["operation_id"],
                "manifest": str(manifest_path.resolve()),
                "rollback_manifest": str(manifest_path.resolve()),
                "rollback_command": manifest["rollback_command"],
                "rollback_argv": manifest["rollback_argv"],
                "changed_roles": [role["name"] for role in roles] + ["operation-journal"],
                "before_page_sha256": manifest["roles"][0]["baseline"]["sha256"],
                "after_page_sha256": manifest["roles"][0]["modified"]["sha256"],
                "operation_journal": journal,
                "operation_journal_recorded": True,
            }
        except Exception as exc:
            current = json_load(manifest_path) if manifest_path.is_file() else manifest
            if not str(current.get("status", "")).startswith("failed"):
                current["status"] = "failed"
            current["error"] = {"type": type(exc).__name__, "message": str(exc)}
            current["failed_at_utc"] = current.get("failed_at_utc") or utc_now()
            json_write(manifest_path, current)
            try:
                record_operation(output, "record", "record:replace", "failed", [_journal_evidence(output, manifest_path)])
            except CkbError:
                pass
            if isinstance(exc, CkbError):
                raise
            raise CkbError(f"record replace failed: {exc}") from exc


def _load_rollback_manifest(output: Path, manifest_path: Path) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    root = _operation_root(output)
    try:
        manifest_path.relative_to(root)
    except ValueError as exc:
        raise CkbError(f"record rollback manifest must be inside this OUTPUT: {manifest_path}") from exc
    if not manifest_path.is_file():
        raise CkbError(f"record rollback manifest is missing: {manifest_path}")
    manifest = json_load(manifest_path)
    if manifest.get("schema_version") != RECORD_REPLACE_SCHEMA_VERSION or manifest.get("operation") != "record-replace":
        raise CkbError(f"unsupported record rollback manifest: {manifest_path}")
    if Path(str(manifest.get("output") or "")).resolve() != output.resolve():
        raise CkbError(f"record rollback manifest OUTPUT differs from the requested OUTPUT: {manifest_path}")
    if manifest.get("status") not in {"completed", "rolled-back"}:
        raise CkbError(f"record rollback requires a completed replacement: status={manifest.get('status')}")
    return manifest


def rollback_replacement(output: Path, manifest_path: Path) -> dict[str, Any]:
    """Restore the exact file and SQLite logical state owned by one replacement."""

    output = output.resolve()
    manifest_path = manifest_path.resolve()
    with _replace_lock(output):
        manifest = _load_rollback_manifest(output, manifest_path)
        roles = list(manifest.get("roles") or [])
        if {role.get("name") for role in roles} != set(_FILE_ROLES) | {"agent-index-note", "machine-knowledge-note"}:
            raise CkbError("record rollback manifest role set is incomplete")
        baseline_errors = _verify_roles(output, roles, "baseline")
        if manifest["status"] == "rolled-back":
            if baseline_errors:
                raise CkbError(f"record rollback baseline drifted after the prior rollback: {baseline_errors[:10]}")
            journal = record_operation(output, "record", "record:rollback", "rolled-back", [_journal_evidence(output, manifest_path)])
            return {
                "schema_version": RECORD_REPLACE_SCHEMA_VERSION,
                "status": "rolled-back",
                "idempotent": True,
                "operation_id": manifest["operation_id"],
                "manifest": str(manifest_path),
                "restored_roles": [role["name"] for role in roles],
                "operation_journal": journal,
                "operation_journal_recorded": True,
            }
        modified_errors = _verify_roles(output, roles, "modified")
        if modified_errors:
            if not baseline_errors:
                manifest["status"] = "rolled-back"
                manifest["rolled_back_at_utc"] = manifest.get("rolled_back_at_utc") or utc_now()
                json_write(manifest_path, manifest)
                journal = record_operation(output, "record", "record:rollback", "rolled-back", [_journal_evidence(output, manifest_path)])
                return {
                    "schema_version": RECORD_REPLACE_SCHEMA_VERSION,
                    "status": "rolled-back",
                    "idempotent": True,
                    "operation_id": manifest["operation_id"],
                    "manifest": str(manifest_path),
                    "restored_roles": [role["name"] for role in roles],
                    "operation_journal": journal,
                    "operation_journal_recorded": True,
                }
            try:
                record_operation(output, "record", "record:rollback", "conflict", [_journal_evidence(output, manifest_path)])
            except CkbError:
                pass
            raise CkbError(f"record rollback conflict: replacement-owned objects drifted: {modified_errors[:10]}")
        by_name = {role["name"]: role for role in roles}
        restored: list[str] = []
        try:
            for role in reversed(roles):
                if role["kind"] == "file":
                    _restore_file(output, role)
                elif role["name"] == "agent-index-note":
                    _commit_agent(
                        output / role["path"],
                        role["selector"],
                        json_load(Path(role["modified"]["candidate"])),
                        json_load(Path(role["baseline"]["backup"])),
                    )
                else:
                    _commit_machine(
                        output / role["path"],
                        role["selector"],
                        json_load(Path(role["modified"]["candidate"])),
                        json_load(Path(role["baseline"]["backup"])),
                    )
                restored.append(role["name"])
            errors = _verify_roles(output, roles, "baseline")
            note_errors = audit_notes(output)
            records = audit_work_record_index(output)
            agent = audit_agent_index(output)
            if errors or note_errors or records["status"] != "passed" or agent["status"] != "passed":
                raise CkbError(
                    f"record rollback verification failed: roles={errors[:5]}; notes={note_errors[:5]}; "
                    f"records={records['errors'][:5]}; agent={agent['errors'][:5]}"
                )
        except Exception as exc:
            compensation_errors: list[dict[str, Any]] = []
            for name in reversed(restored):
                role = by_name[name]
                try:
                    if role["kind"] == "file":
                        _promote_file(output, role, role["baseline"]["sha256"])
                    elif role["name"] == "agent-index-note":
                        _commit_agent(
                            output / role["path"],
                            role["selector"],
                            json_load(Path(role["baseline"]["backup"])),
                            json_load(Path(role["modified"]["candidate"])),
                        )
                    else:
                        _commit_machine(
                            output / role["path"],
                            role["selector"],
                            json_load(Path(role["baseline"]["backup"])),
                            json_load(Path(role["modified"]["candidate"])),
                        )
                except Exception as compensation_exc:
                    compensation_errors.append(
                        {"role": name, "type": type(compensation_exc).__name__, "message": str(compensation_exc)}
                    )
            manifest["rollback_failure"] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "restored_before_failure": restored,
                "compensation_errors": compensation_errors,
            }
            json_write(manifest_path, manifest)
            try:
                record_operation(output, "record", "record:rollback", "failed", [_journal_evidence(output, manifest_path)])
            except CkbError:
                pass
            if isinstance(exc, CkbError):
                raise
            raise CkbError(f"record rollback failed: {exc}") from exc
        manifest.update(
            {
                "status": "rolled-back",
                "rolled_back_at_utc": utc_now(),
                "rollback_verification": {
                    "status": "passed",
                    "role_errors": [],
                    "note_errors": [],
                    "work_record_index": records,
                    "agent_index": agent,
                },
            }
        )
        json_write(manifest_path, manifest)
        journal = record_operation(output, "record", "record:rollback", "rolled-back", [_journal_evidence(output, manifest_path)])
        manifest["rollback_operation_journal"] = journal
        json_write(manifest_path, manifest)
        return {
            "schema_version": RECORD_REPLACE_SCHEMA_VERSION,
            "status": "rolled-back",
            "idempotent": False,
            "operation_id": manifest["operation_id"],
            "manifest": str(manifest_path),
            "restored_roles": [role["name"] for role in roles],
            "operation_journal": journal,
            "operation_journal_recorded": True,
        }
