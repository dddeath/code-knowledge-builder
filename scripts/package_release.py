#!/usr/bin/env python3
"""Create reproducible lite/full Skill archives after validating locked inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath


VERSION = "5.1.3"
ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_files(include_runtime: bool) -> list[Path]:
    result: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        relative = path.relative_to(ROOT)
        if not include_runtime and relative.parts[:3] == ("assets", "runtime", "win-x64"):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        result.append(path)
    return sorted(result, key=lambda item: item.relative_to(ROOT).as_posix())


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


def build(kind: str, dist: Path) -> dict:
    lock = json.loads((ROOT / "toolchain.lock.json").read_text(encoding="utf-8"))
    include_runtime = kind == "full-win-x64"
    if include_runtime:
        validate_full_payload(lock)
    files = source_files(include_runtime)
    manifest = {
        "schema_version": 1,
        "name": "code-knowledge-builder",
        "version": VERSION,
        "distribution": kind,
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("lite", "full-win-x64", "both"), required=True)
    parser.add_argument("--dist", type=Path, required=True)
    args = parser.parse_args()
    kinds = ("lite", "full-win-x64") if args.kind == "both" else (args.kind,)
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
