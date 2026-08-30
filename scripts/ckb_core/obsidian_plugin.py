"""Deterministic registration and vault deployment for the separate Obsidian package."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
from typing import Any
import zipfile

from .common import CkbError, json_load, json_write, safe_rmtree, utc_now


PLUGIN_ID = "code-knowledge-builder-companion"
REQUIRED_FILES = ("main.js", "manifest.json", "styles.css", "LICENSE", "NOTICE.md")
OPTIONAL_FILES = ("build-record.json", "deploy.py")


def default_obsidian_plugin_registry() -> Path:
    return Path.home() / ".ckb" / "obsidian-plugin.json"


def obsidian_plugin_installation(vault: Path) -> dict[str, Any]:
    """Inspect this vault only; a global package registration is not installation."""
    vault = vault.resolve()
    destination = vault / ".obsidian" / "plugins" / PLUGIN_ID
    community_path = vault / ".obsidian" / "community-plugins.json"
    community = json_load(community_path) if community_path.is_file() else []
    enabled = isinstance(community, list) and PLUGIN_ID in community
    present_files = [name for name in (*REQUIRED_FILES, *OPTIONAL_FILES) if (destination / name).is_file()]
    missing_files = [name for name in REQUIRED_FILES if not (destination / name).is_file()]
    return {
        "plugin_id": PLUGIN_ID,
        "vault": str(vault),
        "destination": str(destination),
        "directory_present": destination.is_dir(),
        "installed": destination.is_dir() and not missing_files,
        "enabled": enabled,
        "present_files": present_files,
        "missing_files": missing_files,
    }


def _payload_from_package(package: Path, temporary: Path) -> Path:
    package = package.expanduser().resolve()
    if package.is_dir():
        return package
    if not package.is_file() or package.suffix.casefold() != ".zip":
        raise CkbError(f"Obsidian plugin package must be a directory or ZIP: {package}")
    with zipfile.ZipFile(package) as archive:
        if archive.testzip():
            raise CkbError(f"Obsidian plugin ZIP CRC failed: {package}")
        names = set(archive.namelist())
        prefix = ""
        if "manifest.json" not in names:
            candidates = sorted(name for name in names if name.endswith("/manifest.json"))
            if len(candidates) != 1:
                raise CkbError("Obsidian plugin ZIP must contain one manifest.json")
            prefix = candidates[0][:-len("manifest.json")]
        for name in REQUIRED_FILES:
            member = prefix + name
            if member not in names:
                raise CkbError(f"Obsidian plugin ZIP is missing {name}")
            target = temporary / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
        for name in OPTIONAL_FILES:
            member = prefix + name
            if member in names:
                (temporary / name).write_bytes(archive.read(member))
    return temporary


def _validate_payload(root: Path) -> dict[str, Any]:
    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    if missing:
        raise CkbError(f"Obsidian plugin payload is incomplete: {missing}")
    manifest = json_load(root / "manifest.json")
    if manifest.get("id") != PLUGIN_ID:
        raise CkbError(f"unexpected Obsidian plugin id: {manifest.get('id')}")
    version = str(manifest.get("version") or "").strip()
    if not version:
        raise CkbError("Obsidian plugin manifest has no version")
    return manifest


def register_obsidian_plugin(package: Path, registry: Path | None = None) -> dict[str, Any]:
    registry = (registry or default_obsidian_plugin_registry()).expanduser().resolve()
    with tempfile.TemporaryDirectory(prefix="ckb-obsidian-plugin-") as value:
        payload = _payload_from_package(package, Path(value))
        manifest = _validate_payload(payload)
        cache = registry.parent / "obsidian-plugins" / PLUGIN_ID / str(manifest["version"])
        if cache.exists():
            safe_rmtree(cache, registry.parent)
        cache.mkdir(parents=True, exist_ok=True)
        for name in (*REQUIRED_FILES, *OPTIONAL_FILES):
            source = payload / name
            if source.is_file():
                shutil.copy2(source, cache / name)
    result = {
        "schema_version": 1,
        "status": "registered",
        "plugin_id": PLUGIN_ID,
        "version": manifest["version"],
        "payload": str(cache),
        "registry": str(registry),
        "registered_at_utc": utc_now(),
    }
    json_write(registry, result)
    return result


def _registered_payload(registry: Path | None = None) -> tuple[dict[str, Any], Path]:
    registry = (registry or default_obsidian_plugin_registry()).expanduser().resolve()
    if not registry.is_file():
        raise CkbError("no active Obsidian plugin package is registered; run obsidian-plugin register")
    record = json_load(registry)
    payload = Path(str(record.get("payload") or "")).resolve()
    manifest = _validate_payload(payload)
    if str(manifest["version"]) != str(record.get("version")):
        raise CkbError("registered Obsidian plugin payload version drifted")
    return record, payload


def deploy_obsidian_plugin_to_vault(vault: Path, registry: Path | None = None) -> dict[str, Any]:
    vault = vault.resolve()
    record, payload = _registered_payload(registry)
    config = vault / ".obsidian"
    config.mkdir(parents=True, exist_ok=True)
    plugins = config / "plugins"
    plugins.mkdir(parents=True, exist_ok=True)
    destination = plugins / PLUGIN_ID
    staging = plugins / f".{PLUGIN_ID}.staging"
    if staging.exists():
        safe_rmtree(staging, plugins)
    staging.mkdir(parents=True)
    for name in (*REQUIRED_FILES, *OPTIONAL_FILES):
        source = payload / name
        if source.is_file():
            shutil.copy2(source, staging / name)
    _validate_payload(staging)
    install_mode = "atomic-replace"
    use_in_place_copy = False
    if destination.exists():
        try:
            safe_rmtree(destination, plugins)
        except PermissionError:
            use_in_place_copy = True
    if not use_in_place_copy:
        try:
            staging.replace(destination)
        except PermissionError:
            use_in_place_copy = True
    if use_in_place_copy:
        # Obsidian can keep a Windows handle on the plugin directory while the
        # vault is open. Individual files remain replaceable, so keep the
        # verified staging payload and copy only the declared plugin files.
        destination.mkdir(parents=True, exist_ok=True)
        for name in (*REQUIRED_FILES, *OPTIONAL_FILES):
            source = staging / name
            target = destination / name
            if source.is_file():
                shutil.copy2(source, target)
            elif target.is_file():
                target.unlink()
        _validate_payload(destination)
        install_mode = "in-place-copy"
        try:
            safe_rmtree(staging, plugins)
        except PermissionError:
            pass
    community_path = config / "community-plugins.json"
    community = json_load(community_path) if community_path.is_file() else []
    if not isinstance(community, list):
        raise CkbError(f"Obsidian community-plugins.json must contain a list: {community_path}")
    enabled = list(dict.fromkeys([*[str(value) for value in community], PLUGIN_ID]))
    json_write(community_path, enabled)
    result = {
        "schema_version": 1,
        "status": "deployed",
        "plugin_id": PLUGIN_ID,
        "version": record["version"],
        "install_mode": install_mode,
        "vault": str(vault),
        "destination": str(destination),
        "community_plugins": str(community_path),
        "files": [name for name in (*REQUIRED_FILES, *OPTIONAL_FILES) if (destination / name).is_file()],
        "deployed_at_utc": utc_now(),
    }
    return result


def deploy_obsidian_plugin(output: Path, registry: Path | None = None) -> dict[str, Any]:
    output = output.resolve()
    vault = output / "human"
    if not (output / "state.json").is_file() or not vault.is_dir():
        raise CkbError(f"CKB output with a human vault is required: {output}")
    result = deploy_obsidian_plugin_to_vault(vault, registry)
    from .output_contract import project_output_contract

    result["output_contract"] = project_output_contract(output, vault)
    json_write(output / "workspace-meta" / "obsidian-plugin.json", result)
    return result


def obsidian_plugin_status(output: Path | None = None, registry: Path | None = None) -> dict[str, Any]:
    registry_path = (registry or default_obsidian_plugin_registry()).expanduser().resolve()
    registered = json_load(registry_path) if registry_path.is_file() else None
    deployed = None
    if output is not None:
        output = output.resolve()
        path = output / "workspace-meta" / "obsidian-plugin.json"
        deployed = json_load(path) if path.is_file() else None
        vault = output / "human"
        destination = vault / ".obsidian" / "plugins" / PLUGIN_ID
        if deployed and (not destination.is_dir() or any(not (destination / name).is_file() for name in REQUIRED_FILES)):
            deployed = {**deployed, "status": "drifted"}
        from .output_contract import audit_output_contract

        contract = audit_output_contract(output, vault)
    else:
        contract = None
    return {
        "schema_version": 1,
        "status": "ready" if registered else "unregistered",
        "registry": str(registry_path),
        "registered": registered,
        "deployed": deployed,
        "output_contract": contract,
    }


def remove_obsidian_plugin(output: Path) -> dict[str, Any]:
    output = output.resolve()
    vault = output / "human"
    destination = vault / ".obsidian" / "plugins" / PLUGIN_ID
    if destination.exists():
        safe_rmtree(destination, vault / ".obsidian" / "plugins")
    community_path = vault / ".obsidian" / "community-plugins.json"
    if community_path.is_file():
        community = json_load(community_path)
        if isinstance(community, list):
            json_write(community_path, [value for value in community if value != PLUGIN_ID])
    (output / "workspace-meta" / "obsidian-plugin.json").unlink(missing_ok=True)
    from .output_contract import remove_output_contract

    remove_output_contract(vault)
    return {"schema_version": 1, "status": "removed", "plugin_id": PLUGIN_ID, "output": str(output)}


def deploy_registered_plugin_if_available(vault: Path, output: Path | None = None) -> dict[str, Any]:
    registry = default_obsidian_plugin_registry()
    if not registry.is_file():
        return {"status": "not-registered"}
    result = deploy_obsidian_plugin_to_vault(vault, registry)
    if output is not None:
        from .output_contract import project_output_contract

        result["output_contract"] = project_output_contract(output, vault)
    return result
