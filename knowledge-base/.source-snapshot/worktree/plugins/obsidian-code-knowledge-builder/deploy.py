#!/usr/bin/env python3
"""Install, inspect, or remove this extracted plugin package from an Obsidian vault."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil


PLUGIN_ID = "code-knowledge-builder-companion"
REQUIRED = ("main.js", "manifest.json", "styles.css", "LICENSE", "NOTICE.md")
CONTRACT_RELATIVE = Path(".ckb/output-contract.json")


def payload() -> Path:
    root = Path(__file__).resolve().parent
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if missing:
        raise RuntimeError(f"plugin package is incomplete: {missing}")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8-sig"))
    if manifest.get("id") != PLUGIN_ID:
        raise RuntimeError(f"unexpected plugin id: {manifest.get('id')}")
    return root


def community_file(vault: Path) -> Path:
    return vault / ".obsidian" / "community-plugins.json"


def _binding_from_agents(vault: Path, output: Path) -> tuple[Path, Path] | None:
    for candidate in (vault / "AGENTS.md", output / "AGENTS.md"):
        if not candidate.is_file():
            continue
        document = candidate.read_text(encoding="utf-8-sig")
        windows = re.search(r"&\s*'([^'\r\n]*python\.exe)'\s*'([^'\r\n]*ckb\.py)'", document, re.IGNORECASE)
        if windows:
            return Path(windows.group(1)), Path(windows.group(2))
        posix = re.search(r"(?:^|\n)\s*(\S*python(?:3(?:\.\d+)?)?)\s+[\"']?([^\"'\s]+ckb\.py)[\"']?", document, re.IGNORECASE)
        if posix:
            return Path(posix.group(1)), Path(posix.group(2))
    return None


def _resolve_contract_binding(vault: Path, output: Path | None, python: Path | None, ckb: Path | None) -> tuple[Path, Path, Path]:
    resolved_output = (output or vault.parent).expanduser().resolve()
    if not (resolved_output / "state.json").is_file():
        raise RuntimeError(f"CKB output state is missing; pass --output explicitly: {resolved_output}")
    if python is not None and ckb is not None:
        return resolved_output, python.expanduser(), ckb.expanduser()
    discovered = _binding_from_agents(vault, resolved_output)
    if discovered is None:
        raise RuntimeError("CKB runtime binding is missing; pass both --python and --ckb or project AGENTS.md first")
    return resolved_output, discovered[0], discovered[1]


def _write_contract(vault: Path, output: Path, python: Path, ckb: Path) -> Path:
    path = vault / CONTRACT_RELATIVE
    value = {
        "schema_version": 1,
        "contract": "code-knowledge-builder-output",
        "status": "ready",
        "output": str(output),
        "vault": str(vault),
        "runtime": {"python": str(python), "ckb": str(ckb)},
        "stdio": {
            "protocol": "ckb-stdio-retrieval",
            "minimum_version": 2,
            "methods": ["ping", "retrieve", "record-explanation", "shutdown"],
            "command": [str(python), str(ckb), "serve", "--out", str(output), "--stdio"],
        },
        "language": "zh-CN",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def deploy(vault: Path, output: Path | None = None, python: Path | None = None, ckb: Path | None = None) -> dict:
    source = payload()
    vault = vault.expanduser().resolve()
    resolved_output, resolved_python, resolved_ckb = _resolve_contract_binding(vault, output, python, ckb)
    target = vault / ".obsidian" / "plugins" / PLUGIN_ID
    target.mkdir(parents=True, exist_ok=True)
    for name in (*REQUIRED, "build-record.json", "deploy.py"):
        path = source / name
        if path.is_file():
            shutil.copy2(path, target / name)
    config = community_file(vault)
    enabled = json.loads(config.read_text(encoding="utf-8-sig")) if config.is_file() else []
    if not isinstance(enabled, list):
        raise RuntimeError(f"community-plugins.json must contain a list: {config}")
    enabled = list(dict.fromkeys([*[str(value) for value in enabled], PLUGIN_ID]))
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps(enabled, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    contract = _write_contract(vault, resolved_output, resolved_python, resolved_ckb)
    return {"status": "deployed", "plugin_id": PLUGIN_ID, "version": manifest["version"], "vault": str(vault), "destination": str(target), "output_contract": str(contract)}


def status(vault: Path) -> dict:
    vault = vault.expanduser().resolve()
    target = vault / ".obsidian" / "plugins" / PLUGIN_ID
    missing = [name for name in REQUIRED if not (target / name).is_file()]
    config = community_file(vault)
    enabled = json.loads(config.read_text(encoding="utf-8-sig")) if config.is_file() else []
    enabled = enabled if isinstance(enabled, list) else []
    contract = vault / CONTRACT_RELATIVE
    contract_ready = False
    if contract.is_file():
        value = json.loads(contract.read_text(encoding="utf-8-sig"))
        contract_ready = value.get("contract") == "code-knowledge-builder-output" and value.get("vault") == str(vault)
    return {"status": "ready" if not missing and PLUGIN_ID in enabled and contract_ready else "missing", "plugin_id": PLUGIN_ID, "vault": str(vault), "missing_files": missing, "enabled": PLUGIN_ID in enabled, "output_contract": str(contract), "output_contract_ready": contract_ready}


def remove(vault: Path) -> dict:
    vault = vault.expanduser().resolve()
    target = vault / ".obsidian" / "plugins" / PLUGIN_ID
    if target.is_dir():
        shutil.rmtree(target)
    config = community_file(vault)
    if config.is_file():
        value = json.loads(config.read_text(encoding="utf-8-sig"))
        if isinstance(value, list):
            config.write_text(json.dumps([item for item in value if item != PLUGIN_ID], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    contract = vault / CONTRACT_RELATIVE
    contract.unlink(missing_ok=True)
    if contract.parent.is_dir() and not any(contract.parent.iterdir()):
        contract.parent.rmdir()
    return {"status": "removed", "plugin_id": PLUGIN_ID, "vault": str(vault)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("deploy", "status", "remove"):
        command = sub.add_parser(name)
        command.add_argument("--vault", type=Path, required=True)
        if name == "deploy":
            command.add_argument("--output", type=Path)
            command.add_argument("--python", type=Path)
            command.add_argument("--ckb", type=Path)
    args = parser.parse_args()
    result = deploy(args.vault, args.output, args.python, args.ckb) if args.command == "deploy" else status(args.vault) if args.command == "status" else remove(args.vault)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "missing" else 5


if __name__ == "__main__":
    raise SystemExit(main())
