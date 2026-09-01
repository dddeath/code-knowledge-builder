"""Plugin-gated machine-readable binding between one CKB output and an Obsidian vault."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .common import json_load, json_write


OUTPUT_CONTRACT_SCHEMA_VERSION = 1
OUTPUT_CONTRACT_RELATIVE = Path(".ckb/output-contract.json")
STDIO_PROTOCOL = "ckb-stdio-retrieval"
STDIO_MINIMUM_VERSION = 2
STDIO_METHODS = ("ping", "retrieve", "record-explanation", "shutdown")


def _default_ckb() -> Path:
    return (Path(__file__).resolve().parents[1] / "ckb.py").resolve()


def _runtime_binding(output: Path) -> tuple[Path, Path]:
    record_path = output / "workspace-meta/agent-protocol.json"
    record = json_load(record_path) if record_path.is_file() else {}
    python = Path(str(record.get("python") or sys.executable)).resolve()
    ckb = Path(str(record.get("ckb") or _default_ckb())).resolve()
    return python, ckb


def expected_output_contract(output: Path, vault: Path) -> dict[str, Any]:
    output = output.resolve()
    vault = vault.resolve()
    python, ckb = _runtime_binding(output)
    return output_contract_for_runtime(output, vault, python, ckb)


def output_contract_for_runtime(output: Path, vault: Path, python: Path, ckb: Path) -> dict[str, Any]:
    """Render one exact contract for an already validated runtime binding."""
    output = output.resolve()
    vault = vault.resolve()
    python = python.resolve()
    ckb = ckb.resolve()
    return {
        "schema_version": OUTPUT_CONTRACT_SCHEMA_VERSION,
        "contract": "code-knowledge-builder-output",
        "status": "ready",
        "output": str(output),
        "vault": str(vault),
        "runtime": {"python": str(python), "ckb": str(ckb)},
        "stdio": {
            "protocol": STDIO_PROTOCOL,
            "minimum_version": STDIO_MINIMUM_VERSION,
            "methods": list(STDIO_METHODS),
            "command": [str(python), str(ckb), "serve", "--out", str(output), "--stdio"],
        },
        "language": "zh-CN",
    }


def _update_ownership(vault: Path, *, present: bool) -> None:
    ownership_path = vault / ".ckb-generated-files.json"
    if not ownership_path.is_file():
        return
    ownership = json_load(ownership_path)
    files = {str(value) for value in ownership.get("files", [])}
    relative = OUTPUT_CONTRACT_RELATIVE.as_posix()
    if present:
        files.add(relative)
    else:
        files.discard(relative)
    ownership["files"] = sorted(files)
    json_write(ownership_path, ownership)


def project_output_contract(output: Path, vault: Path) -> dict[str, Any]:
    """Write the contract only when this exact vault has the companion installed."""
    from .obsidian_plugin import obsidian_plugin_installation

    output = output.resolve()
    vault = vault.resolve()
    installation = obsidian_plugin_installation(vault)
    path = vault / OUTPUT_CONTRACT_RELATIVE
    if not installation["installed"]:
        path.unlink(missing_ok=True)
        _update_ownership(vault, present=False)
        return {
            "schema_version": OUTPUT_CONTRACT_SCHEMA_VERSION,
            "status": "not-required",
            "required": False,
            "vault": str(vault),
            "path": str(path),
        }
    value = expected_output_contract(output, vault)
    json_write(path, value)
    _update_ownership(vault, present=True)
    return {**value, "required": True, "path": str(path)}


def remove_output_contract(vault: Path) -> dict[str, Any]:
    vault = vault.resolve()
    path = vault / OUTPUT_CONTRACT_RELATIVE
    path.unlink(missing_ok=True)
    parent = path.parent
    if parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
    _update_ownership(vault, present=False)
    return {"schema_version": OUTPUT_CONTRACT_SCHEMA_VERSION, "status": "removed", "path": str(path)}


def audit_output_contract(output: Path, vault: Path) -> dict[str, Any]:
    """Require exact contract parity only for vaults that actually contain the plugin."""
    from .obsidian_plugin import obsidian_plugin_installation

    output = output.resolve()
    vault = vault.resolve()
    path = vault / OUTPUT_CONTRACT_RELATIVE
    installation = obsidian_plugin_installation(vault)
    if not installation["installed"]:
        return {
            "schema_version": OUTPUT_CONTRACT_SCHEMA_VERSION,
            "status": "not-required",
            "required": False,
            "vault": str(vault),
            "path": str(path),
            "errors": [],
        }
    errors: list[dict[str, Any]] = []
    if not path.is_file():
        errors.append({"reason": "plugin-output-contract-missing", "path": str(path)})
    else:
        actual = json_load(path)
        expected = expected_output_contract(output, vault)
        if actual != expected:
            errors.append({"reason": "plugin-output-contract-drift", "path": str(path)})
    return {
        "schema_version": OUTPUT_CONTRACT_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "required": True,
        "vault": str(vault),
        "path": str(path),
        "errors": errors,
    }
