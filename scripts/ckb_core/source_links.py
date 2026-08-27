"""Machine-local clickable links for source files and Obsidian notes."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, unquote, urlparse

from .common import CkbError, json_load, json_write, path_inside


SOURCE_EDITORS = {"vscode", "vscode-insiders", "file", "custom-template"}


class SourceLinkRenderer:
    """Validate one opener config and cache resolved repository paths.

    Retrieval may render several entities from the same file.  The public
    one-shot helpers below intentionally preserve their old behavior, while a
    long-lived renderer avoids repeating Windows ``resolve`` and
    ``_getfinalpathname`` work for every candidate.
    """

    def __init__(self, config: dict[str, Any], *, trusted_relative_paths: bool = False) -> None:
        self.config = validate_local_openers(config)
        root_value = self.config.get("working_repo_root")
        if self.config.get("source_view") == "baseline" and self.config.get("baseline_snapshot_root"):
            root_value = self.config["baseline_snapshot_root"]
        self.root = Path(str(root_value)).resolve()
        self.trusted_relative_paths = trusted_relative_paths
        self._absolute_paths: dict[str, Path] = {}

    @property
    def cache_size(self) -> int:
        return len(self._absolute_paths)

    def absolute_path(self, relative_path: str) -> Path:
        cached = self._absolute_paths.get(relative_path)
        if cached is not None:
            return cached
        relative = PurePosixPath(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise CkbError(f"source path is outside the repository: {relative_path}")
        joined = self.root.joinpath(*relative.parts)
        if self.trusted_relative_paths:
            # Machine retrieval only supplies paths from the audited source
            # manifest.  Absolute and parent components were rejected above,
            # so the lexical path is repository-bounded without another
            # filesystem canonicalization for every selected entity.
            path = joined
        else:
            path = joined.resolve()
            if not path_inside(path, self.root):
                raise CkbError(f"source path is outside the selected source root: {relative_path}")
        self._absolute_paths[relative_path] = path
        return path

    def uri(self, relative_path: str, line: int, column: int = 1) -> str:
        absolute = self.absolute_path(relative_path)
        encoded = quote(absolute.as_posix(), safe="/:")
        editor = self.config["source_editor"]
        if editor == "vscode":
            return f"vscode://file/{encoded}:{int(line)}:{int(column)}"
        if editor == "vscode-insiders":
            return f"vscode-insiders://file/{encoded}:{int(line)}:{int(column)}"
        if editor == "file":
            prefix = "file:///" if os.name == "nt" else "file://"
            return prefix + encoded
        return str(self.config["custom_template"]).format(
            absolute_path=encoded,
            line=int(line),
            column=int(column),
        )

    def markdown_link(self, relative_path: str, start_line: int, end_line: int) -> str:
        uri = self.uri(relative_path, start_line, 1)
        label = f"打开源码：{relative_path} 第 {start_line} 行"
        suffix = f"  `{relative_path}:{start_line}-{end_line}`" if self.config.get("show_source_range", True) else ""
        return f"[{label}]({uri}){suffix}"


def default_openers(repository_root: Path, snapshot_root: Path | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source_editor": "vscode" if os.name == "nt" else "file",
        "working_repo_root": str(repository_root.resolve()),
        "baseline_snapshot_root": str(snapshot_root.resolve()) if snapshot_root else None,
        "source_view": "working",
        "show_source_range": True,
        "custom_template": None,
    }


def ensure_local_openers(output: Path, repository_root: Path, snapshot_root: Path | None = None) -> dict[str, Any]:
    path = output / "local-openers.json"
    if path.is_file():
        return validate_local_openers(json_load(path))
    value = default_openers(repository_root, snapshot_root)
    json_write(path, value)
    return value


def validate_local_openers(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise CkbError("local-openers.json must use schema_version 1")
    editor = value.get("source_editor")
    if editor not in SOURCE_EDITORS:
        raise CkbError(f"unsupported source editor: {editor}")
    root = Path(str(value.get("working_repo_root", ""))).resolve()
    if not root.is_dir():
        raise CkbError(f"working repository root is missing: {root}")
    source_view = value.get("source_view", "working")
    if source_view not in {"working", "baseline"}:
        raise CkbError("source_view must be working or baseline")
    template = value.get("custom_template")
    if editor == "custom-template" and (
        not isinstance(template, str)
        or "{absolute_path}" not in template
        or "{line}" not in template
        or "{column}" not in template
    ):
        raise CkbError("custom source-link template requires {absolute_path}, {line}, and {column}")
    return {
        "schema_version": 1,
        "source_editor": editor,
        "working_repo_root": str(root),
        "baseline_snapshot_root": value.get("baseline_snapshot_root"),
        "source_view": source_view,
        "show_source_range": bool(value.get("show_source_range", True)),
        "custom_template": template,
    }


def update_local_openers(
    output: Path,
    repository_root: Path,
    *,
    editor: str = "vscode",
    source_view: str = "working",
    custom_template: str | None = None,
) -> dict[str, Any]:
    state_path = output / "state.json"
    if not state_path.is_file():
        raise CkbError(f"state.json does not exist: {state_path}")
    state = json_load(state_path)
    snapshot_root = (state.get("source_snapshot") or {}).get("root")
    value = default_openers(repository_root, Path(snapshot_root) if snapshot_root else None)
    value.update({"source_editor": editor, "source_view": source_view, "custom_template": custom_template})
    value = validate_local_openers(value)
    json_write(output / "local-openers.json", value)
    return value


def source_absolute_path(config: dict[str, Any], relative_path: str) -> Path:
    return SourceLinkRenderer(config).absolute_path(relative_path)


def source_uri(config: dict[str, Any], relative_path: str, line: int, column: int = 1) -> str:
    return SourceLinkRenderer(config).uri(relative_path, line, column)


def source_markdown_link(config: dict[str, Any], relative_path: str, start_line: int, end_line: int) -> str:
    return SourceLinkRenderer(config).markdown_link(relative_path, start_line, end_line)


def obsidian_open_uri(path: Path) -> str:
    return "obsidian://open?path=" + quote(str(path.resolve()), safe="")


def audit_source_uri(config: dict[str, Any], uri: str, relative_path: str, line: int) -> str | None:
    expected = source_uri(config, relative_path, line, 1)
    if uri != expected:
        return "source-uri-does-not-match-source-location"
    parsed = urlparse(uri)
    if parsed.scheme not in {"vscode", "vscode-insiders", "file", "cursor", "idea"}:
        return "source-uri-scheme-is-not-allowed"
    if parsed.scheme.startswith("vscode"):
        decoded = unquote(parsed.path)
        if f":{int(line)}:1" not in decoded:
            return "source-uri-line-is-missing"
    return None
