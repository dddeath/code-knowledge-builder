from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess


def _host_path(value: str, base: Path) -> Path:
    text = value.strip()
    if os.name == "nt":
        match = re.fullmatch(r"/mnt/([A-Za-z])(?:/(.*))?", text.replace("\\", "/"))
        if match:
            suffix = match.group(2) or ""
            return Path(f"{match.group(1).upper()}:/{suffix}").resolve()
    path = Path(text)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def resolve_checkout_git_dir(root: Path) -> Path:
    marker = root.resolve() / ".git"
    if marker.is_dir():
        return marker.resolve()
    if marker.is_file():
        first = marker.read_text(encoding="utf-8-sig").splitlines()[0].strip()
        if not first.casefold().startswith("gitdir:"):
            raise RuntimeError(f"checkout .git file has no gitdir binding: {marker}")
        git_dir = _host_path(first.split(":", 1)[1], root.resolve())
        if git_dir.is_dir():
            return git_dir
        raise RuntimeError(f"checkout gitdir binding is missing: {git_dir}")
    raise RuntimeError(f"checkout has no .git directory or gitdir file: {root}")


def resolve_git_common_dir(root: Path) -> Path:
    root = root.resolve()
    direct = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if direct.returncode == 0 and direct.stdout.strip():
        common = _host_path(direct.stdout.strip(), root)
    else:
        git_dir = resolve_checkout_git_dir(root)
        commondir = git_dir / "commondir"
        common = _host_path(commondir.read_text(encoding="utf-8-sig").strip(), git_dir) if commondir.is_file() else git_dir
    if not common.is_dir():
        raise RuntimeError(f"resolved Git common directory is missing: {common}")
    verified = subprocess.run(
        ["git", f"--git-dir={common}", "rev-parse", "--git-common-dir"],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if verified.returncode:
        raise RuntimeError(f"resolved Git common directory failed rev-parse: {common}: {verified.stderr.strip()}")
    return common.resolve()
