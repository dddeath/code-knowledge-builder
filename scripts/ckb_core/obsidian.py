"""Minimal, plugin-free Obsidian vault projection and ownership tracking."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .common import CkbError, json_load, json_write, safe_rmtree


NOTE_DIRECTORIES = ("analysis", "changes", "pitfalls", "experiments", "sessions")
FEEDBACK_DIRECTORIES = ("feedback/open", "feedback/resolved")
GENERATED_TOP_LEVEL = (
    "INDEX.md",
    "WIKI.md",
    "RECORDS.md",
    "normalized.edn",
    "projection.json",
    "context-budget.json",
    "readability-audit.json",
)


def prepare_vault(root: Path, output: Path) -> None:
    """Remove only generator-owned files and preserve Agent/user notes."""
    root.mkdir(parents=True, exist_ok=True)
    ownership = root / ".ckb-generated-files.json"
    if ownership.is_file():
        record = json_load(ownership)
        for relative in record.get("files", []):
            path = root / str(relative)
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                safe_rmtree(path, root)
    else:
        for name in GENERATED_TOP_LEVEL:
            (root / name).unlink(missing_ok=True)
        for name in ("pages", "logseq"):
            path = root / name
            if path.exists():
                safe_rmtree(path, root)
    for name in (*NOTE_DIRECTORIES, *FEEDBACK_DIRECTORIES):
        (root / name).mkdir(parents=True, exist_ok=True)


def install_obsidian(root: Path, output: Path | None = None) -> dict[str, Any]:
    config = root / ".obsidian"
    snippets = config / "snippets"
    snippets.mkdir(parents=True, exist_ok=True)
    app = {
        "newLinkFormat": "shortest",
        "useMarkdownLinks": False,
        "alwaysUpdateLinks": True,
        "attachmentFolderPath": "attachments",
        "showUnsupportedFiles": True,
        "defaultViewMode": "preview",
        "userIgnoreFilters": [
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
            ".github/",
            ".cursor/",
        ],
    }
    plugins = [
        "file-explorer",
        "global-search",
        "switcher",
        "graph",
        "backlink",
        "outgoing-link",
        "tag-pane",
        "page-preview",
        "outline",
        "command-palette",
    ]
    appearance = {"enabledCssSnippets": ["ckb"]}
    css = """/* Code Knowledge Builder: restrained source links and appendices. */
/* Generated Markdown already has one portable H1.  Obsidian's filename-based
   inline title would repeat that heading, so the vault shows only the H1. */
body .inline-title { display: none; }
.external-link[href^="vscode://"],
.external-link[href^="vscode-insiders://"] { color: var(--text-accent); }
.markdown-rendered table { width: 100%; }
.markdown-rendered details { border-left: 2px solid var(--background-modifier-border); padding-left: 0.8rem; }
.nav-file-title[data-path="AGENTS.md"],
.nav-file-title[data-path="CLAUDE.md"],
.nav-file-title[data-path="GEMINI.md"] { display: none; }
"""
    json_write(config / "app.json", app)
    json_write(config / "core-plugins.json", plugins)
    json_write(config / "appearance.json", appearance)
    (snippets / "ckb.css").write_text(css, encoding="utf-8", newline="\n")
    from .obsidian_plugin import deploy_registered_plugin_if_available

    companion = deploy_registered_plugin_if_available(root, output) if output is not None else {"status": "not-requested"}
    return {
        "status": "ready",
        "vault_root": str(root.resolve()),
        "config_root": str(config.resolve()),
        "core_plugins": plugins,
        "home": "INDEX.md",
        "note_directories": list(NOTE_DIRECTORIES),
        "feedback_directories": list(FEEDBACK_DIRECTORIES),
        "companion_plugin": companion,
    }


def write_generated_ownership(root: Path, generated: list[Path]) -> dict[str, Any]:
    files = sorted(path.relative_to(root).as_posix() for path in generated if path.is_file())
    record = {"schema_version": 1, "status": "ready", "files": files}
    json_write(root / ".ckb-generated-files.json", record)
    return record


def audit_obsidian(root: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required = (
        ".obsidian/app.json",
        ".obsidian/core-plugins.json",
        ".obsidian/appearance.json",
        ".obsidian/snippets/ckb.css",
        ".ckb-generated-files.json",
        "INDEX.md",
        "WIKI.md",
        "RECORDS.md",
    )
    for relative in required:
        if not (root / relative).is_file():
            errors.append({"reason": "obsidian-vault-file-missing", "path": relative})
    for name in (*NOTE_DIRECTORIES, *FEEDBACK_DIRECTORIES):
        if not (root / name).is_dir():
            errors.append({"reason": "obsidian-note-directory-missing", "path": name})
    ownership = root / ".ckb-generated-files.json"
    if ownership.is_file() and ".obsidian/workspace.json" in json_load(ownership).get("files", []):
        errors.append({"reason": "machine-specific-obsidian-workspace-owned-by-generator"})
    try:
        plugins = json_load(root / ".obsidian/core-plugins.json")
        for plugin in ("backlink", "outgoing-link", "tag-pane", "graph", "global-search"):
            if plugin not in plugins:
                errors.append({"reason": "obsidian-core-plugin-missing", "plugin": plugin})
    except (OSError, json.JSONDecodeError, CkbError) as exc:
        errors.append({"reason": "obsidian-config-invalid", "detail": str(exc)})
    css_path = root / ".obsidian/snippets/ckb.css"
    if css_path.is_file():
        css = css_path.read_text(encoding="utf-8")
        if "body .inline-title { display: none; }" not in css:
            errors.append({"reason": "obsidian-inline-title-not-hidden"})
    from .obsidian_plugin import PLUGIN_ID, obsidian_plugin_installation

    installation = obsidian_plugin_installation(root)
    if installation["directory_present"] or installation["enabled"]:
        if not installation["installed"]:
            for name in installation["missing_files"]:
                errors.append({"reason": "obsidian-companion-file-missing", "plugin": PLUGIN_ID, "path": name})
        if not installation["enabled"]:
            errors.append({"reason": "obsidian-companion-not-enabled", "plugin": PLUGIN_ID})
        output = root.parent if (root.parent / "state.json").is_file() else None
        if output is not None:
            from .output_contract import audit_output_contract

            errors.extend(audit_output_contract(output, root)["errors"])
    return errors
