#!/usr/bin/env python3
"""Restore the exact pre-cutover stable knowledge directory and Agent adapters."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


ACTIVE = Path(r"E:\knowledge_builder\self-workspace\knowledge-base")
CANDIDATE = Path(r"E:\knowledge_builder\self-workspace\kb-stg-89eac148")
ORIGIN = Path(r"E:\knowledge_builder\self-workspace\kb-batch-backups\cutover-origin-2d1ddc4-8654b04b")
QUARANTINE = Path(r"E:\knowledge_builder\self-workspace\kb-batch-quarantine\rollback-target-150a1ce")
PROTOCOL_BACKUP = Path(r"E:\knowledge_builder\self-workspace\kb-batch-backups\protocol-before-cutover-150a1ce")
WORKSPACE = Path(r"E:\knowledge_builder")
RESULT = Path(r"E:\knowledge_builder\artifacts\verification\stable-kb-sync-89eac148\rollback-result.json")
SKILL_ACTIVE = Path(r"C:\Users\19739\.codex\skills\code-knowledge-builder")
SKILL_BACKUP = Path(r"C:\Users\19739\.codex\skills\.ckb-backups\code-knowledge-builder-pre-150a1ce")
SKILL_QUARANTINE = Path(r"C:\Users\19739\.codex\skills\.ckb-backups\code-knowledge-builder-target-150a1ce")
ORIGIN_COMMIT = "2d1ddc4de65c36c2ebe244e3d0556d4b613b2d3d"
TARGET_COMMIT = "150a1ce8ea3fca0f7ce2f56c731d42a9973ee0e3"


def state_commit(path: Path) -> str | None:
    state = path / "state.json"
    if not state.is_file():
        return None
    return json.loads(state.read_text(encoding="utf-8"))["repository"]["commit"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight() -> dict:
    active_commit = state_commit(ACTIVE)
    candidate_commit = state_commit(CANDIDATE)
    origin_commit = state_commit(ORIGIN)
    phase = "before-cutover" if active_commit == ORIGIN_COMMIT and candidate_commit == TARGET_COMMIT else "rollback-ready" if active_commit == TARGET_COMMIT and origin_commit == ORIGIN_COMMIT else "unknown"
    result = {
        "schema_version": 1,
        "status": "passed",
        "mode": "preflight",
        "active": str(ACTIVE),
        "phase": phase,
        "active_commit": active_commit,
        "candidate": str(CANDIDATE),
        "candidate_commit": candidate_commit,
        "origin_commit": origin_commit,
        "origin_destination_absent": not ORIGIN.exists(),
        "rollback_quarantine_absent": not QUARANTINE.exists(),
        "protocol_backup_present": (PROTOCOL_BACKUP / "manifest.json").is_file(),
        "skill_backup_present": (SKILL_BACKUP / "scripts" / "ckb.py").is_file(),
        "skill_quarantine_absent": not SKILL_QUARANTINE.exists(),
    }
    before_cutover = active_commit == ORIGIN_COMMIT and candidate_commit == TARGET_COMMIT and result["origin_destination_absent"]
    rollback_ready = active_commit == TARGET_COMMIT and origin_commit == ORIGIN_COMMIT
    passed = (before_cutover or rollback_ready) and result["rollback_quarantine_absent"] and result["protocol_backup_present"] and result["skill_backup_present"] and result["skill_quarantine_absent"]
    result["status"] = "passed" if passed else "failed"
    return result


def restore_protocol() -> list[dict]:
    manifest = json.loads((PROTOCOL_BACKUP / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for item in manifest["files"]:
        relative = item["relative"]
        target = WORKSPACE / relative
        if item["exists"]:
            source = PROTOCOL_BACKUP / "files" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            rows.append({"relative": relative, "restored": True, "sha256": sha256(target), "expected_sha256": item["sha256"]})
        elif target.exists():
            target.unlink()
            rows.append({"relative": relative, "restored": True, "removed": True})
        else:
            rows.append({"relative": relative, "restored": True, "already_absent": True})
    return rows


def rollback() -> dict:
    if state_commit(ACTIVE) != TARGET_COMMIT:
        raise RuntimeError("active knowledge output is not the cutover target")
    if state_commit(ORIGIN) != ORIGIN_COMMIT:
        raise RuntimeError("exact origin directory is missing or has the wrong commit")
    if QUARANTINE.exists():
        raise RuntimeError("rollback quarantine destination already exists")
    ACTIVE.rename(QUARANTINE)
    try:
        ORIGIN.rename(ACTIVE)
    except Exception:
        QUARANTINE.rename(ACTIVE)
        raise
    protocol = restore_protocol()
    if not (SKILL_BACKUP / "scripts" / "ckb.py").is_file() or SKILL_QUARANTINE.exists():
        raise RuntimeError("installed Skill rollback paths are not ready")
    SKILL_ACTIVE.rename(SKILL_QUARANTINE)
    try:
        SKILL_BACKUP.rename(SKILL_ACTIVE)
    except Exception:
        SKILL_QUARANTINE.rename(SKILL_ACTIVE)
        raise
    skill = {
        "restored": (SKILL_ACTIVE / "scripts" / "ckb.py").is_file(),
        "active": str(SKILL_ACTIVE),
        "quarantined_target": str(SKILL_QUARANTINE),
    }
    result = {
        "schema_version": 1,
        "status": "passed" if state_commit(ACTIVE) == ORIGIN_COMMIT and all(item.get("sha256") in {None, item.get("expected_sha256")} for item in protocol) else "failed",
        "mode": "rollback",
        "active": str(ACTIVE),
        "restored_commit": state_commit(ACTIVE),
        "quarantined_target": str(QUARANTINE),
        "protocol": protocol,
        "skill": skill,
    }
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    result = preflight() if args.preflight else rollback()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 5


if __name__ == "__main__":
    raise SystemExit(main())
