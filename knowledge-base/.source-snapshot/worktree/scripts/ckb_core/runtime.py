from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any

from .common import CkbError, DependencyError, json_load, json_write, safe_rmtree, sha256_file, utc_now
from .providers import private_runtime_root


def skill_root() -> Path:
    return Path(__file__).resolve().parents[2]


def lock_document() -> dict[str, Any]:
    return json_load(skill_root() / "toolchain.lock.json")


def payload_path() -> Path:
    return skill_root() / "assets" / "runtime" / "win-x64" / "payload.zip"


def deployment_plan() -> dict[str, Any]:
    lock = lock_document()
    payload = payload_path()
    destination = private_runtime_root() / lock["lock_id"]
    payload_lock = lock.get("payload")
    deployed_record = (
        json_load(destination / "deployed.json")
        if destination.is_dir() and (destination / "deployed.json").is_file()
        else {}
    )
    required_members = payload_lock.get("required_members", []) if isinstance(payload_lock, dict) else []
    deployment_matches = (
        isinstance(payload_lock, dict)
        and deployed_record.get("status") == "ready"
        and deployed_record.get("lock_id") == lock.get("lock_id")
        and deployed_record.get("payload_sha256") == payload_lock.get("sha256")
        and (destination / "payload-files.json").is_file()
        and isinstance(required_members, list)
        and bool(required_members)
        and all((destination / member).is_file() for member in required_members)
    )
    if deployment_matches:
        status = "ready"
    elif not payload.is_file():
        status = "payload-missing"
    elif not isinstance(payload_lock, dict):
        status = "payload-unlocked"
    elif payload.stat().st_size != int(payload_lock.get("size", -1)) or sha256_file(payload) != payload_lock.get("sha256"):
        status = "payload-invalid"
    else:
        status = "permission-required"
    return {
        "status": status,
        "lock_id": lock["lock_id"],
        "components": lock["components"],
        "payload": str(payload.resolve()),
        "payload_size": payload.stat().st_size if payload.is_file() else None,
        "payload_sha256": sha256_file(payload) if payload.is_file() else None,
        "expected_payload": payload_lock,
        "destination": str(destination.resolve()),
        "rollback": f"runtime remove --lock-id {lock['lock_id']}",
    }


def deploy(accept: bool) -> dict[str, Any]:
    plan = deployment_plan()
    if plan["status"] == "ready":
        return plan
    if plan["status"] != "permission-required":
        raise DependencyError(json.dumps(plan, ensure_ascii=False))
    if not accept:
        raise DependencyError(json.dumps(plan, ensure_ascii=False))
    payload = Path(plan["payload"])
    destination = Path(plan["destination"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".deploying")
    if temporary.exists():
        safe_rmtree(temporary, destination.parent)
    temporary.mkdir()
    host_snapshot = _host_snapshot()
    with zipfile.ZipFile(payload) as archive:
        for member in archive.infolist():
            target = (temporary / member.filename).resolve()
            try:
                target.relative_to(temporary.resolve())
            except ValueError as exc:
                raise CkbError(f"runtime archive path escapes destination: {member.filename}") from exc
        archive.extractall(temporary)
    files_manifest_path = temporary / "payload-files.json"
    if not files_manifest_path.is_file():
        safe_rmtree(temporary, destination.parent)
        raise CkbError("runtime payload lacks payload-files.json")
    files_manifest = json_load(files_manifest_path)
    for item in files_manifest.get("files", []):
        member_path = (temporary / item["path"]).resolve()
        try:
            member_path.relative_to(temporary.resolve())
        except ValueError as exc:
            safe_rmtree(temporary, destination.parent)
            raise CkbError(f"runtime manifest path escapes destination: {item['path']}") from exc
        if not member_path.is_file() or member_path.stat().st_size != int(item["size"]) or sha256_file(member_path) != item["sha256"]:
            safe_rmtree(temporary, destination.parent)
            raise CkbError(f"runtime payload member verification failed: {item['path']}")
    json_write(
        temporary / "deployed.json",
        {
            "status": "ready",
            "lock_id": plan["lock_id"],
            "payload_sha256": plan["payload_sha256"],
            "deployed_at_utc": utc_now(),
            "host_snapshot_before": host_snapshot,
        },
    )
    if destination.exists():
        safe_rmtree(destination, destination.parent)
    os.replace(temporary, destination)
    plan["status"] = "ready"
    return plan


def remove(lock_id: str) -> dict[str, Any]:
    root = private_runtime_root().resolve()
    target = (root / lock_id).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise CkbError("runtime lock ID resolves outside the private runtime root") from exc
    existed = target.exists()
    deployment = json_load(target / "deployed.json") if (target / "deployed.json").is_file() else {}
    if existed:
        safe_rmtree(target, root)
    current_snapshot = _host_snapshot()
    expected_snapshot = deployment.get("host_snapshot_before")
    return {
        "status": "removed",
        "lock_id": lock_id,
        "path": str(target),
        "existed": existed,
        "host_snapshot_before": expected_snapshot,
        "host_snapshot_after": current_snapshot,
        "host_environment_restored": expected_snapshot is None or expected_snapshot == current_snapshot,
    }


def _host_snapshot() -> dict[str, Any]:
    commands = ["python", "node", "git", "pyright-langserver", "typescript-language-server", "clangd", "csharp-ls", "dotnet", "logseq"]
    return {"path": os.environ.get("PATH", ""), "commands": {name: shutil.which(name) for name in commands}}
