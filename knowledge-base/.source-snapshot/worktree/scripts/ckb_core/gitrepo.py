from __future__ import annotations

import fnmatch
import io
import os
from pathlib import Path, PurePosixPath
import shutil
from typing import Any
import subprocess

from .common import CkbError, DependencyError, StaleSourceError, background_process_options, run, stable_id


LANGUAGE_BY_SUFFIX = {
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".py": "python",
    ".cs": "csharp",
}

DEFAULT_EXCLUDED_PARTS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "vendor",
    "vendors",
    "_vendor",
    "third_party",
    "third-party",
    "dist",
    "build",
    "bin",
    "obj",
    "out",
    "target",
    "coverage",
    "__pycache__",
    ".venv",
    "venv",
}

GENERATED_PATTERNS = (
    "*.min.js",
    "*.generated.*",
    "*_generated.*",
    "*.pb.c",
    "*.pb.h",
    "*.g.cs",
    "*.g.i.cs",
    "*.Designer.cs",
    "*.AssemblyInfo.cs",
)

CSHARP_PROJECT_SUFFIXES = {".csproj", ".sln", ".slnx", ".props", ".targets"}
CSHARP_PROJECT_NAMES = {
    "global.json",
    "Directory.Build.props",
    "Directory.Build.targets",
    "Directory.Packages.props",
    "NuGet.Config",
    "nuget.config",
}

DEFAULT_INITIAL_COMMIT_MESSAGE = "chore: initialize repository for code-knowledge-builder"
DEFAULT_INITIAL_AUTHOR_NAME = "Code Knowledge Builder"
DEFAULT_INITIAL_AUTHOR_EMAIL = "code-knowledge-builder@local.invalid"


def git(repo: Path, *args: str, check: bool = True) -> str:
    completed = run(["git", "-C", str(repo), *args])
    if check and completed.returncode:
        message = (completed.stderr or completed.stdout).strip()
        raise CkbError(f"git {' '.join(args)} failed: {message}")
    return completed.stdout


def _git_probe(repo: Path, *args: str):
    return run(["git", "-C", str(repo), *args])


def _identity_value(repo: Path, key: str) -> str | None:
    completed = _git_probe(repo, "config", "--get", key)
    value = completed.stdout.strip() if completed.returncode == 0 else ""
    return value or None


def prepare_git_repository(
    repo: Path,
    *,
    initialize_git: bool = False,
    initial_commit_message: str = DEFAULT_INITIAL_COMMIT_MESSAGE,
    git_author_name: str | None = None,
    git_author_email: str | None = None,
) -> dict[str, Any]:
    """Confirm a usable Git commit, or create exactly one initial commit on opt-in."""
    repo = repo.resolve()
    if not repo.exists():
        raise CkbError(f"repository path does not exist: {repo}")
    if not repo.is_dir():
        raise CkbError(f"repository path is not a directory: {repo}")
    if not shutil.which("git"):
        raise DependencyError("Git is required; run doctor to inspect the toolchain")
    if not initial_commit_message.strip():
        raise CkbError("--initial-commit-message must not be empty")
    if git_author_name is not None and not git_author_name.strip():
        raise CkbError("--git-author-name must not be empty")
    if git_author_email is not None and not git_author_email.strip():
        raise CkbError("--git-author-email must not be empty")

    root_probe = _git_probe(repo, "rev-parse", "--show-toplevel")
    repository_created = False
    if root_probe.returncode == 0:
        root = Path(root_probe.stdout.strip()).resolve()
    else:
        if not initialize_git:
            raise CkbError(
                f"path is not a Git repository: {repo}; rerun the same init/run command with "
                "--init-git to initialize it and create one initial commit"
            )
        initialized = _git_probe(repo, "init")
        if initialized.returncode:
            detail = (initialized.stderr or initialized.stdout).strip()
            raise CkbError(f"git init failed: {detail}")
        repository_created = True
        root = Path(_git_probe(repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve()

    head_probe = _git_probe(root, "rev-parse", "--verify", "HEAD")
    initial_commit_created = False
    author: dict[str, str] | None = None
    if head_probe.returncode != 0:
        if not initialize_git:
            raise CkbError(
                f"Git repository has no commit: {root}; rerun the same init/run command with "
                "--init-git to stage the current files and create one initial commit"
            )
        added = _git_probe(root, "add", "-A")
        if added.returncode:
            detail = (added.stderr or added.stdout).strip()
            raise CkbError(f"git add -A failed while creating the initial commit: {detail}")
        configured_name = _identity_value(root, "user.name")
        configured_email = _identity_value(root, "user.email")
        author_name = (git_author_name or configured_name or DEFAULT_INITIAL_AUTHOR_NAME).strip()
        author_email = (git_author_email or configured_email or DEFAULT_INITIAL_AUTHOR_EMAIL).strip()
        name_source = "argument" if git_author_name else ("git-config" if configured_name else "local-fallback")
        email_source = "argument" if git_author_email else ("git-config" if configured_email else "local-fallback")
        committed = _git_probe(
            root,
            "-c",
            f"user.name={author_name}",
            "-c",
            f"user.email={author_email}",
            "commit",
            "--allow-empty",
            "-m",
            initial_commit_message,
        )
        if committed.returncode:
            detail = (committed.stderr or committed.stdout).strip()
            raise CkbError(f"initial Git commit failed: {detail}")
        initial_commit_created = True
        author = {
            "name": author_name,
            "email": author_email,
            "name_source": name_source,
            "email_source": email_source,
        }
        head_probe = _git_probe(root, "rev-parse", "--verify", "HEAD")

    commit = head_probe.stdout.strip()
    commit_count_text = _git_probe(root, "rev-list", "--count", "HEAD").stdout.strip()
    return {
        "requested": initialize_git,
        "performed": repository_created or initial_commit_created,
        "repository_created": repository_created,
        "initial_commit_created": initial_commit_created,
        "root": str(root),
        "commit": commit,
        "commit_count": int(commit_count_text),
        "commit_message": initial_commit_message if initial_commit_created else None,
        "author": author,
    }


def preflight(
    repo: Path,
    *,
    initialize_git: bool = False,
    initial_commit_message: str = DEFAULT_INITIAL_COMMIT_MESSAGE,
    git_author_name: str | None = None,
    git_author_email: str | None = None,
) -> dict[str, Any]:
    bootstrap = prepare_git_repository(
        repo,
        initialize_git=initialize_git,
        initial_commit_message=initial_commit_message,
        git_author_name=git_author_name,
        git_author_email=git_author_email,
    )
    root = Path(bootstrap["root"]).resolve()
    if root != repo.resolve():
        repo = root
    status = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    if status.strip():
        raise StaleSourceError("repository worktree is not clean; commit or remove every tracked and untracked change")
    commit = git(repo, "rev-parse", "HEAD").strip()
    tree = git(repo, "rev-parse", f"{commit}^{{tree}}").strip()
    return {"root": str(repo), "commit": commit, "tree": tree, "git_bootstrap": bootstrap}


def assert_unchanged(repository: dict[str, Any]) -> None:
    repo = Path(repository["root"])
    current = preflight(repo)
    if current["commit"] != repository["commit"] or current["tree"] != repository["tree"]:
        raise StaleSourceError(
            f"repository changed: expected {repository['commit']} / {repository['tree']}, "
            f"found {current['commit']} / {current['tree']}"
        )


def create_source_snapshot(repository: dict[str, Any], output: Path) -> dict[str, Any]:
    """Create one detached fixed-commit worktree for all semantic providers.

    The canonical parser continues to read Git blobs.  Language servers read
    this worktree instead of the user's mutable worktree, so the caller may
    start editing after initialization without changing the baseline build.
    """
    repo = Path(repository["root"]).resolve()
    snapshot_root = (output / ".source-snapshot" / "worktree").resolve()
    snapshot_root.parent.mkdir(parents=True, exist_ok=True)
    if snapshot_root.exists():
        raise CkbError(f"source snapshot already exists: {snapshot_root}")
    added = run(
        ["git", "-C", str(repo), "worktree", "add", "--detach", "--force", str(snapshot_root), repository["commit"]],
        timeout=300,
    )
    if added.returncode:
        raise CkbError(f"fixed source snapshot creation failed: {(added.stderr or added.stdout).strip()}")
    snapshot = {
        "status": "snapshot-ready",
        "root": str(snapshot_root),
        "repository_root": str(repo),
        "commit": repository["commit"],
        "tree": repository["tree"],
        "mode": "detached-git-worktree",
    }
    assert_source_snapshot(repository, snapshot)
    return snapshot


def assert_source_snapshot(repository: dict[str, Any], snapshot: dict[str, Any]) -> None:
    """Verify the immutable baseline while allowing the user's HEAD/worktree to move."""
    repo = Path(repository["root"]).resolve()
    root = Path(snapshot.get("root", "")).resolve()
    if not root.is_dir():
        raise StaleSourceError(f"fixed source snapshot is missing: {root}")
    object_probe = run(["git", "-C", str(repo), "cat-file", "-e", f"{repository['commit']}^{{commit}}"], timeout=30)
    if object_probe.returncode:
        raise StaleSourceError(f"baseline commit object is unavailable: {repository['commit']}")
    head = run(["git", "-C", str(root), "rev-parse", "HEAD"], timeout=30)
    tree = run(["git", "-C", str(root), "rev-parse", "HEAD^{tree}"], timeout=30)
    status = run(["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=no"], timeout=30)
    if head.returncode or head.stdout.strip() != repository["commit"]:
        raise StaleSourceError(f"fixed source snapshot commit drifted: {root}")
    if tree.returncode or tree.stdout.strip() != repository["tree"]:
        raise StaleSourceError(f"fixed source snapshot tree drifted: {root}")
    if status.returncode or status.stdout.strip():
        raise StaleSourceError(f"fixed source snapshot worktree drifted: {root}")


def tracked_sources(
    repository: dict[str, Any],
    include_patterns: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    repo = Path(repository["root"])
    commit = repository["commit"]
    raw = git(repo, "ls-tree", "-r", "-z", "--long", commit)
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    overrides = include_patterns or []
    for item in raw.split("\0"):
        if not item:
            continue
        meta, path = item.split("\t", 1)
        mode, kind, blob, size_text = meta.split()
        suffix = PurePosixPath(path).suffix
        language = LANGUAGE_BY_SUFFIX.get(suffix)
        if not language:
            continue
        parts = set(PurePosixPath(path).parts)
        override = any(fnmatch.fnmatch(path, pattern) for pattern in overrides)
        reason = None
        if not override and parts.intersection(DEFAULT_EXCLUDED_PARTS):
            reason = "dependency-build-or-generated-directory"
        elif not override and any(fnmatch.fnmatch(PurePosixPath(path).name, p) for p in GENERATED_PATTERNS):
            reason = "generated-file-pattern"
        record = {
            "id": stable_id("file", commit, path, blob),
            "path": path,
            "language": language,
            "blob": blob,
            "size": int(size_text),
            "mode": mode,
        }
        if reason:
            excluded.append({**record, "reason": reason})
        else:
            included.append(record)
    return included, excluded


def tracked_csharp_project_files(repository: dict[str, Any]) -> list[dict[str, Any]]:
    """Return tracked C# project metadata without treating it as source entities."""
    repo = Path(repository["root"])
    commit = repository["commit"]
    raw = git(repo, "ls-tree", "-r", "-z", "--long", commit)
    result: list[dict[str, Any]] = []
    for item in raw.split("\0"):
        if not item:
            continue
        meta, path = item.split("\t", 1)
        mode, kind, blob, size_text = meta.split()
        posix = PurePosixPath(path)
        if posix.suffix.lower() not in CSHARP_PROJECT_SUFFIXES and posix.name not in CSHARP_PROJECT_NAMES:
            continue
        result.append(
            {
                "id": stable_id("project-file", commit, path, blob),
                "path": path,
                "blob": blob,
                "size": int(size_text),
                "mode": mode,
                "role": "csharp-project-metadata",
            }
        )
    return sorted(result, key=lambda value: value["path"])


def blob_bytes(repository: dict[str, Any], path: str) -> bytes:
    repo = Path(repository["root"])
    commit = repository["commit"]
    # Binary mode preserves arbitrary bytes and avoids a redundant text-mode Git process.
    binary = subprocess.run(
        ["git", "-C", str(repo), "show", f"{commit}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **background_process_options(),
    )
    if binary.returncode:
        raise StaleSourceError(binary.stderr.decode("utf-8", errors="replace"))
    return binary.stdout


def blob_bytes_many(repository: dict[str, Any], files: list[dict[str, Any]]) -> dict[str, bytes]:
    """Read a set of fixed Git blob objects through one binary cat-file session."""
    if not files:
        return {}
    repo = Path(repository["root"])
    unique_oids = list(dict.fromkeys(str(item["blob"]) for item in files))
    query = ("\n".join(unique_oids) + "\n").encode("ascii")
    completed = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        input=query,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **background_process_options(),
    )
    if completed.returncode:
        raise StaleSourceError(completed.stderr.decode("utf-8", errors="replace"))
    stream = io.BytesIO(completed.stdout)
    values: dict[str, bytes] = {}
    for requested in unique_oids:
        header = stream.readline().decode("ascii", errors="replace").strip()
        parts = header.split()
        if len(parts) != 3 or parts[1] != "blob":
            raise StaleSourceError(f"Git object is unavailable or is not a blob: {requested}: {header}")
        actual, _kind, size_text = parts
        size = int(size_text)
        content = stream.read(size)
        delimiter = stream.read(1)
        if len(content) != size or delimiter != b"\n" or actual != requested:
            raise StaleSourceError(f"Git cat-file returned an invalid frame for blob: {requested}")
        values[requested] = content
    return {item["path"]: values[str(item["blob"])] for item in files}


def object_exists(repository: dict[str, Any], object_id: str) -> bool:
    completed = run(["git", "-C", repository["root"], "cat-file", "-e", object_id])
    return completed.returncode == 0


def resolve_scope_paths(all_files: list[dict[str, Any]], values: list[str]) -> set[str]:
    if not values:
        return {item["path"] for item in all_files}
    normalized: list[str] = []
    for value in values:
        path = value.replace("\\", "/").strip("/")
        if not path or path == "." or path.startswith("../") or "/../" in f"/{path}/":
            raise CkbError(f"invalid --scope-path: {value}")
        normalized.append(path)
    selected = {
        item["path"]
        for item in all_files
        if any(item["path"] == prefix or item["path"].startswith(prefix + "/") for prefix in normalized)
    }
    missing = [prefix for prefix in normalized if not any(p == prefix or p.startswith(prefix + "/") for p in selected)]
    if missing:
        raise CkbError(f"scope paths contain no supported tracked source: {missing}")
    return selected
