#!/usr/bin/env python3
"""Create reproducible core and Obsidian-plugin archives with strict boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path, PurePosixPath


VERSION = "5.4.0"
ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
CORE_EXCLUDED_TOP_LEVEL = {"plugins"}
RUNTIME_PREFIX = ("assets", "runtime", "win-x64")
PLUGIN_ROOT = ROOT / "plugins" / "obsidian-code-knowledge-builder"
PLUGIN_FILES = ("main.js", "manifest.json", "styles.css", "LICENSE", "NOTICE.md", "build-record.json", "deploy.py")
CORE_REQUIRED_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "scripts/ckb.py",
    "scripts/ckb_core/__init__.py",
    "references/workflow.md",
    "references/runtime.md",
    "toolchain.lock.json",
    "THIRD_PARTY_NOTICES.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_files(include_runtime: bool) -> list[Path]:
    result: list[Path] = []
    for current, directories, filenames in os.walk(ROOT):
        directory = Path(current)
        retained_directories: list[str] = []
        for name in sorted(directories):
            relative = (directory / name).relative_to(ROOT)
            if any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            if relative.parts and relative.parts[0] in CORE_EXCLUDED_TOP_LEVEL:
                continue
            if not include_runtime and relative.parts[:3] == RUNTIME_PREFIX:
                continue
            retained_directories.append(name)
        directories[:] = retained_directories
        for name in sorted(filenames):
            path = directory / name
            relative = path.relative_to(ROOT)
            if path.suffix in {".pyc", ".pyo"}:
                continue
            result.append(path)
    return sorted(result, key=lambda item: item.relative_to(ROOT).as_posix())


def core_capabilities(kind: str) -> dict[str, bool]:
    return {
        "source_scanning": True,
        "machine_sqlite_knowledge": True,
        "deterministic_retrieval": True,
        "human_markdown_obsidian_vault": True,
        "logseq_projection": True,
        "local_scope_and_segmented_build": True,
        "agent_review_and_audit": True,
        "automation_adapters": True,
        "bundled_offline_runtime": kind == "full-win-x64",
        "obsidian_companion_plugin": False,
    }


def validate_core_boundary() -> None:
    lite = {path.relative_to(ROOT).as_posix() for path in source_files(False)}
    full = {path.relative_to(ROOT).as_posix() for path in source_files(True)}
    missing = sorted(set(CORE_REQUIRED_FILES) - lite)
    if missing:
        raise RuntimeError(f"lite core capability files are absent: {missing}")
    if any(path == "plugins" or path.startswith("plugins/") for path in lite | full):
        raise RuntimeError("core distributions must not contain plugins/")
    if not lite < full:
        raise RuntimeError("full-win-x64 must strictly extend lite")
    unexpected = sorted(
        path for path in full - lite
        if not path.startswith("assets/runtime/win-x64/")
    )
    if unexpected:
        raise RuntimeError(f"full-win-x64 adds non-runtime files: {unexpected}")


def validate_full_payload(lock: dict) -> Path:
    payload_lock = lock.get("payload")
    if not isinstance(payload_lock, dict):
        raise RuntimeError("full payload lock is pending")
    relative = payload_lock.get("path")
    if not isinstance(relative, str):
        raise RuntimeError("full payload path is absent from the lock")
    path = (ROOT / relative).resolve()
    if not path.is_file():
        raise RuntimeError(f"full payload is absent: {path}")
    if path.stat().st_size != int(payload_lock.get("size", -1)):
        raise RuntimeError("full payload size differs from toolchain.lock.json")
    actual_hash = sha256(path)
    if actual_hash != payload_lock.get("sha256"):
        raise RuntimeError("full payload SHA-256 differs from toolchain.lock.json")
    for required in payload_lock.get("required_members", []):
        with zipfile.ZipFile(path) as archive:
            if required not in archive.namelist():
                raise RuntimeError(f"full payload member is absent: {required}")
    return path


def build_core(kind: str, dist: Path) -> dict:
    lock = json.loads((ROOT / "toolchain.lock.json").read_text(encoding="utf-8"))
    validate_core_boundary()
    include_runtime = kind == "full-win-x64"
    if include_runtime:
        validate_full_payload(lock)
    files = source_files(include_runtime)
    manifest = {
        "schema_version": 1,
        "name": "code-knowledge-builder",
        "version": VERSION,
        "distribution": kind,
        "category": "core",
        "capabilities": core_capabilities(kind),
        "extends": "lite" if include_runtime else None,
        "forbidden_prefixes": ["plugins/"],
        "only_adds_prefix": "assets/runtime/win-x64/" if include_runtime else None,
        "toolchain_lock_id": lock["lock_id"],
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in files
        ],
    }
    dist.mkdir(parents=True, exist_ok=True)
    archive_path = dist / f"code-knowledge-builder-{kind}-{VERSION}.zip"
    if archive_path.exists():
        archive_path.unlink()
    prefix = PurePosixPath("code-knowledge-builder")
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = PurePosixPath(path.relative_to(ROOT).as_posix())
            info = zipfile.ZipInfo(str(prefix / relative), date_time=(2026, 8, 26, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        manifest_info = zipfile.ZipInfo(str(prefix / "distribution" / "release-manifest.json"), date_time=(2026, 8, 26, 0, 0, 0))
        manifest_info.compress_type = zipfile.ZIP_DEFLATED
        manifest_info.external_attr = 0o100644 << 16
        archive.writestr(manifest_info, json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    with zipfile.ZipFile(archive_path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"ZIP CRC failed: {bad_member}")
        archived_manifest = json.loads(archive.read(str(prefix / "distribution" / "release-manifest.json")))
        if archived_manifest != manifest:
            raise RuntimeError("archived release manifest differs from the generated manifest")
    result = {
        "status": "passed",
        "distribution": kind,
        "archive": str(archive_path.resolve()),
        "size": archive_path.stat().st_size,
        "sha256": sha256(archive_path),
        "file_count": len(files),
    }
    (dist / f"code-knowledge-builder-{kind}-{VERSION}.manifest.json").write_text(
        json.dumps({**result, "content": manifest}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result


def validate_plugin_dist() -> tuple[str, list[Path], dict]:
    dist = PLUGIN_ROOT / "dist"
    files = [dist / name for name in PLUGIN_FILES]
    missing = [path.name for path in files if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(f"Obsidian plugin dist files are absent: {missing}")
    manifest = json.loads((dist / "manifest.json").read_text(encoding="utf-8"))
    version = manifest.get("version")
    if not isinstance(version, str) or not version.strip():
        raise RuntimeError("Obsidian plugin version is absent from manifest.json")
    build_record = json.loads((dist / "build-record.json").read_text(encoding="utf-8"))
    if build_record.get("status") != "passed":
        raise RuntimeError("Obsidian plugin build-record.json has not passed")
    recorded = {item["path"]: item for item in build_record.get("files", [])}
    for path in files:
        if path.name == "build-record.json":
            continue
        item = recorded.get(path.name)
        if not item:
            raise RuntimeError(f"Obsidian plugin build record is missing: {path.name}")
        if int(item.get("size", -1)) != path.stat().st_size or item.get("sha256") != sha256(path):
            raise RuntimeError(f"Obsidian plugin dist differs from build record: {path.name}")
    return version, files, build_record


def build_plugin(dist: Path) -> dict:
    version, files, build_record = validate_plugin_dist()
    manifest = {
        "schema_version": 1,
        "name": "code-knowledge-builder-obsidian",
        "version": version,
        "distribution": "obsidian-plugin",
        "category": "plugin",
        "requires": {
            "knowledge_base": "CKB output with machine/knowledge.sqlite",
            "core_package": "installed separately",
        },
        "bundled_core": False,
        "bundled_offline_runtime": False,
        "agent_deploy": {
            "standalone": "python deploy.py deploy --vault VAULT",
            "core": "ckb.py obsidian-plugin register/deploy/status/remove",
            "auto_deploy_after_registration": True,
        },
        "files": [
            {"path": path.name, "size": path.stat().st_size, "sha256": sha256(path)}
            for path in files
        ],
        "upstream_commit": build_record.get("claudian_commit"),
    }
    dist.mkdir(parents=True, exist_ok=True)
    archive_path = dist / f"code-knowledge-builder-obsidian-{version}.zip"
    if archive_path.exists():
        archive_path.unlink()
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.name, date_time=(2026, 8, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(archive_path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"Obsidian plugin ZIP CRC failed: {bad_member}")
        if archive.namelist() != list(PLUGIN_FILES):
            raise RuntimeError("Obsidian plugin ZIP member set or order differs")
        for path in files:
            if archive.read(path.name) != path.read_bytes():
                raise RuntimeError(f"Obsidian plugin ZIP bytes differ: {path.name}")
    result = {
        "status": "passed",
        "distribution": "obsidian-plugin",
        "archive": str(archive_path.resolve()),
        "size": archive_path.stat().st_size,
        "sha256": sha256(archive_path),
        "file_count": len(files),
    }
    (dist / f"code-knowledge-builder-obsidian-{version}.manifest.json").write_text(
        json.dumps({**result, "content": manifest}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result


def build(kind: str, dist: Path) -> dict:
    if kind == "obsidian-plugin":
        return build_plugin(dist)
    return build_core(kind, dist)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kind",
        choices=("lite", "full-win-x64", "obsidian-plugin", "both", "all"),
        required=True,
    )
    parser.add_argument("--dist", type=Path, required=True)
    args = parser.parse_args()
    if args.kind == "both":
        kinds = ("lite", "full-win-x64")
    elif args.kind == "all":
        kinds = ("lite", "full-win-x64", "obsidian-plugin")
    else:
        kinds = (args.kind,)
    results = []
    try:
        for kind in kinds:
            results.append(build(kind, args.dist.resolve()))
    except RuntimeError as exc:
        print(json.dumps({"status": "pending", "reason": str(exc), "completed": results}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 3
    print(json.dumps({"status": "passed", "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
