"""Canonical facts and separated human Markdown projection helpers."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any

from .common import CkbError, json_load, json_write, safe_rmtree, sha256_file, utc_now
from .machine_knowledge import contains_chinese_narrative
from .obsidian import NOTE_DIRECTORIES


FACTS_SCHEMA_VERSION = 1
HUMAN_SCHEMA_VERSION = 1


def _source_manifest(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [
            {
                "entity_id": entity["id"],
                "commit": entity["commit"],
                "blob": entity["blob"],
                "path": entity["path"],
                "start_byte": entity["range"]["start_byte"],
                "end_byte": entity["range"]["end_byte"],
                "start_line": entity["range"]["start_line"],
                "end_line": entity["range"]["end_line"],
            }
            for entity in graph.get("entities", [])
        ],
        key=lambda item: item["entity_id"],
    )


def build_facts_layer(output: Path, graph: dict[str, Any]) -> dict[str, Any]:
    """Write a rebuildable canonical facts directory beside compatibility files."""
    root = output / "facts"
    root.mkdir(parents=True, exist_ok=True)
    graph_path = root / "graph.json"
    graph_path.write_bytes((output / "graph.json").read_bytes())
    source_manifest = _source_manifest(graph)
    json_write(root / "source-manifest.json", source_manifest)
    state = json_load(output / "state.json")
    reviews = []
    for pack in state.get("review_packs", []):
        reviews.append(
            {
                "pack_id": pack["id"],
                "kind": pack.get("kind"),
                "status": pack.get("status"),
                "entity_ids": list(pack.get("entity_ids", [])),
                "review_path": pack.get("review_path"),
                "audit_path": pack.get("audit_path"),
            }
        )
    json_write(root / "review-manifest.json", reviews)
    manifest = {
        "schema_version": FACTS_SCHEMA_VERSION,
        "status": "ready",
        "repository": graph["repository"],
        "graph": str(graph_path.resolve()),
        "graph_sha256": sha256_file(graph_path),
        "source_manifest": str((root / "source-manifest.json").resolve()),
        "review_manifest": str((root / "review-manifest.json").resolve()),
        "counts": {
            "entities": len(graph.get("entities", [])),
            "relations": len(graph.get("links", [])),
            "providers": len(graph.get("providers", [])),
            "review_packs": len(reviews),
        },
        "language_contract": "所有实体说明使用简体中文，允许英文专有名词、路径和代码标识符。",
        "built_at_utc": utc_now(),
    }
    json_write(root / "manifest.json", manifest)
    return audit_facts_layer(output, graph)


def audit_facts_layer(output: Path, graph: dict[str, Any] | None = None) -> dict[str, Any]:
    graph = graph or json_load(output / "graph.json")
    root = output / "facts"
    errors: list[dict[str, Any]] = []
    required = ("graph.json", "source-manifest.json", "review-manifest.json", "manifest.json")
    for name in required:
        if not (root / name).is_file():
            errors.append({"reason": "facts-file-missing", "path": name})
    if not errors:
        if (root / "graph.json").read_bytes() != (output / "graph.json").read_bytes():
            errors.append({"reason": "facts-graph-differs-from-root-graph"})
        source_manifest = json_load(root / "source-manifest.json")
        if source_manifest != _source_manifest(graph):
            errors.append({"reason": "facts-source-manifest-mismatch"})
        manifest = json_load(root / "manifest.json")
        expected_counts = {
            "entities": len(graph.get("entities", [])),
            "relations": len(graph.get("links", [])),
            "providers": len(graph.get("providers", [])),
            "review_packs": len(json_load(root / "review-manifest.json")),
        }
        if manifest.get("counts") != expected_counts:
            errors.append({"reason": "facts-count-mismatch", "actual": manifest.get("counts"), "expected": expected_counts})
    result = {
        "schema_version": FACTS_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "root": str(root.resolve()),
        "errors": errors,
    }
    json_write(root / "audit.json", result)
    return result


def _copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _generated_files(markdown: Path) -> list[str]:
    ownership = markdown / ".ckb-generated-files.json"
    if not ownership.is_file():
        raise CkbError("Markdown generated ownership is missing")
    return [str(value) for value in json_load(ownership).get("files", [])]


def sync_human_layer(output: Path, graph: dict[str, Any]) -> dict[str, Any]:
    """Mirror the audited Markdown vault into the dedicated human layer.

    The legacy ``markdown`` path stays byte-compatible.  Agent notes written by
    the CLI are mirrored in both directions by workspace_notes.
    """
    markdown = output / "markdown"
    if not markdown.is_dir():
        raise CkbError("human projection requires OUTPUT/markdown")
    human = output / "human"
    human.mkdir(parents=True, exist_ok=True)
    previous_ownership = human / ".ckb-generated-files.json"
    if previous_ownership.is_file():
        for relative in json_load(previous_ownership).get("files", []):
            path = human / str(relative)
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                safe_rmtree(path, human)
    generated = _generated_files(markdown)
    copied: list[str] = []
    for relative in generated:
        source = markdown / relative
        if source.is_file():
            _copy_file(source, human / relative)
            copied.append(relative)
    _copy_file(markdown / ".ckb-generated-files.json", human / ".ckb-generated-files.json")
    for directory in NOTE_DIRECTORIES:
        (human / directory).mkdir(parents=True, exist_ok=True)
        for note in sorted((markdown / directory).glob("*.md")):
            _copy_file(note, human / directory / note.name)
    # Preserve user-owned Obsidian workspace/config additions while refreshing
    # the generator-owned app/plugin/snippet files from the compatibility vault.
    if (markdown / ".obsidian").is_dir():
        for source in sorted((markdown / ".obsidian").rglob("*")):
            if source.is_file():
                relative = source.relative_to(markdown)
                _copy_file(source, human / relative)
                if relative.as_posix() not in copied:
                    copied.append(relative.as_posix())
    manifest = {
        "schema_version": HUMAN_SCHEMA_VERSION,
        "status": "ready",
        "vault_root": str(human.resolve()),
        "compatibility_vault": str(markdown.resolve()),
        "generated_files": sorted(set(copied)),
        "note_directories": list(NOTE_DIRECTORIES),
        "language": "zh-CN",
        "language_contract": "正文说明使用简体中文；英文仅用于专有名词、代码符号、路径和必要术语。",
        "built_at_utc": utc_now(),
    }
    json_write(human / "manifest.json", manifest)
    ownership = json_load(human / ".ckb-generated-files.json")
    ownership["files"] = sorted(set(ownership.get("files", [])) | {"manifest.json", "audit.json"})
    json_write(human / ".ckb-generated-files.json", ownership)
    return audit_human_layer(output, graph)


def audit_human_layer(output: Path, graph: dict[str, Any] | None = None) -> dict[str, Any]:
    graph = graph or json_load(output / "graph.json")
    markdown = output / "markdown"
    human = output / "human"
    errors: list[dict[str, Any]] = []
    if not human.is_dir():
        errors.append({"reason": "human-root-missing"})
    elif not (human / "manifest.json").is_file():
        errors.append({"reason": "human-manifest-missing"})
    if not errors:
        for relative in _generated_files(markdown):
            left = markdown / relative
            right = human / relative
            if left.is_file() and (not right.is_file() or left.read_bytes() != right.read_bytes()):
                errors.append({"reason": "human-markdown-parity", "path": relative})
        for directory in NOTE_DIRECTORIES:
            markdown_notes = {path.name: path.read_bytes() for path in (markdown / directory).glob("*.md")}
            human_notes = {path.name: path.read_bytes() for path in (human / directory).glob("*.md")}
            if markdown_notes != human_notes:
                errors.append({"reason": "human-note-parity", "directory": directory})
        readability = json_load(human / "readability-audit.json") if (human / "readability-audit.json").is_file() else {}
        if readability.get("status") != "passed":
            errors.append({"reason": "human-readability-not-passed", "detail": readability})
    language_errors: list[dict[str, Any]] = []
    for entity in graph.get("entities", []):
        if entity.get("classification") == "appendix":
            if not contains_chinese_narrative(entity.get("description_zh")):
                language_errors.append({"entity_id": entity["id"], "field": "description_zh"})
        else:
            for field in ("meaning_zh", "role_zh", "change_when_zh"):
                if not contains_chinese_narrative(entity.get(field)):
                    language_errors.append({"entity_id": entity["id"], "field": field})
    if language_errors:
        errors.append({"reason": "human-chinese-description-contract", "detail": language_errors})
    result = {
        "schema_version": HUMAN_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "root": str(human.resolve()),
        "compatibility_root": str(markdown.resolve()),
        "language": "zh-CN",
        "errors": errors,
    }
    if human.is_dir():
        json_write(human / "audit.json", result)
    return result


def mirror_note(output: Path, relative: Path) -> None:
    """Copy one Agent/user note between the legacy and dedicated human roots."""
    markdown = output / "markdown" / relative
    human = output / "human" / relative
    if markdown.is_file():
        _copy_file(markdown, human)
    elif human.is_file():
        _copy_file(human, markdown)
