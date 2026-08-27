#!/usr/bin/env python3
"""Build and verify the reproducible private-runtime payload archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


FIXED_TIME = (2026, 8, 23, 0, 0, 0)
MANIFEST_NAME = "payload-files.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative_files(root: Path) -> list[Path]:
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and path.name != MANIFEST_NAME),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def build(root: Path, output: Path) -> dict[str, object]:
    root = root.resolve()
    output = output.resolve()
    if not root.is_dir():
        raise RuntimeError(f"runtime root is absent: {root}")
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise RuntimeError("payload output must be outside the staged runtime root")

    files = relative_files(root)
    manifest = {
        "schema_version": 1,
        "platform": "win-x64",
        "lock_id": "win-x64-2.0.0",
        "files": [
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in files
        ],
    }
    manifest_path = root / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    archive_files = [manifest_path, *files]
    archive_files.sort(key=lambda path: path.relative_to(root).as_posix())

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in archive_files:
            relative = PurePosixPath(path.relative_to(root).as_posix())
            info = zipfile.ZipInfo(str(relative), date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    with zipfile.ZipFile(output) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"payload CRC failed: {bad_member}")
        archived_manifest = json.loads(archive.read(MANIFEST_NAME))
        if archived_manifest != manifest:
            raise RuntimeError("archived payload manifest differs from staging manifest")
        names = set(archive.namelist())
        expected_names = {path.relative_to(root).as_posix() for path in archive_files}
        if names != expected_names:
            raise RuntimeError("payload member set differs from the staged runtime set")

    return {
        "status": "passed",
        "root": str(root),
        "output": str(output),
        "size": output.stat().st_size,
        "sha256": sha256(output),
        "file_count": len(archive_files),
        "manifest": str(manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build(args.root, args.output)
    except RuntimeError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 5
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
