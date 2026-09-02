from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Iterable


EXIT_OK = 0
EXIT_INPUT = 2
EXIT_DEPENDENCY = 3
EXIT_REVIEW = 4
EXIT_AUDIT = 5
EXIT_STALE = 6


class CkbError(RuntimeError):
    exit_code = EXIT_INPUT


class DependencyError(CkbError):
    exit_code = EXIT_DEPENDENCY


class ReviewRequired(CkbError):
    exit_code = EXIT_REVIEW


class AuditError(CkbError):
    exit_code = EXIT_AUDIT


class StaleSourceError(CkbError):
    exit_code = EXIT_STALE


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_id(prefix: str, *parts: Any) -> str:
    text = "\0".join(str(part) for part in parts)
    value = uuid.uuid5(uuid.NAMESPACE_URL, text).hex
    return f"{prefix}-{value}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def background_process_options(*, visible: bool = False) -> dict[str, Any]:
    """Hide non-interactive Windows child consoles without changing I/O semantics."""
    if visible or os.name != "nt":
        return {}
    creation_flag = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return {"creationflags": creation_flag} if creation_flag else {}


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = False,
    timeout: int | None = None,
    visible: bool = False,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        **background_process_options(visible=visible),
    )
    if check and completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise CkbError(f"command failed ({completed.returncode}): {' '.join(command)}\n{detail}")
    return completed


def command_version(executable: str, args: Iterable[str] = ("--version",)) -> dict[str, Any]:
    resolved = shutil.which(executable)
    if not resolved:
        return {"status": "missing", "command": executable, "path": None, "version": None}
    completed = run([resolved, *args], timeout=20)
    text = (completed.stdout or completed.stderr).strip().splitlines()
    return {
        "status": "ready" if completed.returncode == 0 else "broken",
        "command": executable,
        "path": str(Path(resolved).resolve()),
        "version": text[0] if text else None,
        "exit_status": completed.returncode,
    }


def clear_markers(output: Path) -> None:
    for name in (
        ".pending-agent-review",
        ".failed",
        ".complete",
        ".machine.complete",
        ".human.complete",
    ):
        (output / name).unlink(missing_ok=True)


def write_marker(output: Path, name: str, payload: dict[str, Any]) -> None:
    clear_markers(output)
    json_write(output / name, payload)


def safe_title(text: str, limit: int = 120) -> str:
    value = re.sub(r"[\\/:*?\"<>|\[\]]+", "-", text).strip(" .-")
    return (value[:limit] or "untitled").strip()


def path_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def safe_rmtree(path: Path, root: Path) -> None:
    """Remove one verified descendant without ever accepting the root itself."""
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    if resolved_path == resolved_root or not path_inside(resolved_path, resolved_root):
        raise CkbError(f"recursive removal target is outside its declared root: {resolved_path}")
    if resolved_path.exists():
        shutil.rmtree(resolved_path)


def temp_directory(prefix: str = "ckb-"):
    return tempfile.TemporaryDirectory(prefix=prefix)
