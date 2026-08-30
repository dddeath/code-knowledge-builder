"""Mutable human notes and working-tree session records layered over a baseline KB."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .common import CkbError, json_load, json_write, run, safe_title, utc_now
from .obsidian import NOTE_DIRECTORIES
from .source_links import ensure_local_openers, obsidian_open_uri, source_markdown_link
from .machine_knowledge import contains_chinese_narrative
from .work_record_index import refresh_work_record_index


TAG_BY_KIND = {
    "analysis": "#类型/分析",
    "change": "#类型/变更",
    "pitfall": "#类型/踩坑",
    "experiment": "#类型/实验",
    "session": "#类型/会话",
}
DIRECTORY_BY_KIND = dict(zip(TAG_BY_KIND, NOTE_DIRECTORIES))
LONG_HEX = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{40,}(?![0-9A-Fa-f])")


def page_tag(page_type: str) -> str:
    if page_type == "boundary":
        return "#类型/边界"
    if page_type in {"repository", "module"}:
        return "#类型/职责"
    return "#类型/代码"


def _markdown_root(output: Path) -> Path:
    root = output / "markdown"
    if not (root / "projection.json").is_file():
        raise CkbError(f"Markdown projection is required before recording knowledge notes: {root}")
    return root


def _resolve_page_titles(output: Path, selectors: list[str], query_record: Path | None) -> list[str]:
    projection = json_load(output / "markdown/projection.json")
    pages = projection.get("pages", [])
    title_by_id = {page["id"]: page["title"] for page in pages}
    titles = set(title_by_id.values())
    folded = {title.casefold(): title for title in titles}
    selected: list[str] = []
    for selector in selectors:
        exact = folded.get(selector.casefold())
        if exact:
            selected.append(exact)
            continue
        partial = sorted(title for title in titles if selector.casefold() in title.casefold())
        if len(partial) != 1:
            raise CkbError(f"knowledge-page selector must match one page: {selector}; candidates={partial[:20]}")
        selected.append(partial[0])
    if query_record:
        query = json_load(query_record)
        for page in query.get("selected_pages", []):
            title = page.get("title")
            if title in titles:
                selected.append(title)
        owners = projection.get("entity_owner_pages", {})
        for node in query.get("nodes", []):
            node_id = node.get("id")
            page_id = owners.get(node_id) or (node_id if node_id in title_by_id else None)
            if page_id in title_by_id:
                selected.append(title_by_id[page_id])
        for entity in query.get("selected_entities", []):
            title = entity.get("human_page_title")
            if title in titles:
                selected.append(title)
    return list(dict.fromkeys(selected))


def _source_links_for_titles(output: Path, titles: list[str]) -> list[str]:
    projection = json_load(output / "markdown/projection.json")
    graph = json_load(output / "graph.json")
    page_by_title = {page["title"]: page for page in projection.get("pages", [])}
    entity_by_id = {entity["id"]: entity for entity in graph.get("entities", [])}
    state = json_load(output / "state.json")
    snapshot = state.get("source_snapshot") or {}
    openers = ensure_local_openers(
        output,
        Path(state["repository"]["root"]),
        Path(snapshot["root"]) if snapshot.get("root") else None,
    )
    links = []
    for title in titles:
        page = page_by_title.get(title)
        entity = entity_by_id.get(page.get("id")) if page else None
        if not entity or not entity.get("path") or not entity.get("range"):
            continue
        links.append(
            source_markdown_link(
                openers,
                entity["path"],
                int(entity["range"]["start_line"]),
                int(entity["range"]["end_line"]),
            )
        )
    return links


def record_note(
    output: Path,
    kind: str,
    title: str,
    body_path: Path,
    selectors: list[str] | None = None,
    query_record: Path | None = None,
    append: bool = False,
    reindex: bool = True,
) -> dict[str, Any]:
    if kind not in TAG_BY_KIND:
        raise CkbError(f"note kind must be one of: {sorted(TAG_BY_KIND)}")
    if not body_path.is_file():
        raise CkbError(f"note body does not exist: {body_path}")
    body = body_path.read_text(encoding="utf-8-sig").strip()
    if not body:
        raise CkbError("note body must not be empty")
    if not contains_chinese_narrative(body):
        raise CkbError("knowledge note descriptions must use Simplified Chinese; English proper nouns and code identifiers are allowed")
    if body.startswith("---\n") or LONG_HEX.search(body):
        raise CkbError("human knowledge notes must omit frontmatter and hash-like identifiers")
    root = _markdown_root(output)
    linked_titles = _resolve_page_titles(output, selectors or [], query_record)
    if kind != "session" and not linked_titles:
        raise CkbError(f"{kind} notes require at least one linked knowledge page")
    source_links = _source_links_for_titles(output, linked_titles)
    filename = safe_title(title) + ".md"
    directory = root / DIRECTORY_BY_KIND[kind]
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / filename
    if target.exists() and not append:
        raise CkbError(f"knowledge note already exists: {target}; use --append to add a revision")
    sections = [f"# {title.strip()}", "", f"标签：{TAG_BY_KIND[kind]}", "", body]
    if linked_titles:
        sections.extend(["", "## 相关知识页", "", *[f"- [[{value}]]" for value in linked_titles]])
    if source_links:
        sections.extend(["", "## 源码入口", "", *[f"- {value}" for value in source_links]])
    text = "\n".join(sections).rstrip() + "\n"
    if LONG_HEX.search(text):
        raise CkbError("generated human knowledge note contains a hash-like identifier")
    if append and target.exists():
        existing = target.read_text(encoding="utf-8")
        text = existing.rstrip() + "\n\n## 后续补充\n\n" + body + "\n"
    target.write_text(text, encoding="utf-8", newline="\n")
    from .knowledge_layers import mirror_note

    relative_note = Path(DIRECTORY_BY_KIND[kind]) / filename
    mirror_note(output, relative_note)
    human_target = output / "human" / relative_note
    meta_dir = output / "workspace-meta" / "notes"
    meta_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": 1,
        "status": "agent-reviewed",
        "kind": kind,
        "title": title.strip(),
        "file": str((human_target if human_target.is_file() else target).resolve()),
        "compatibility_file": str(target.resolve()),
        "linked_pages": linked_titles,
        "source_links": source_links,
        "query_record": str(query_record.resolve()) if query_record else None,
        "updated_at_utc": utc_now(),
        "obsidian_uri": obsidian_open_uri(target),
    }
    json_write(meta_dir / (safe_title(title) + ".json"), record)
    refresh_work_record_index(output)
    errors = audit_notes(output)
    if errors:
        raise CkbError(f"knowledge-note audit failed: {errors[:10]}")
    if reindex and (output / "agent-index.sqlite").is_file():
        from .agent_index import build_agent_index

        build_agent_index(output)
    if reindex and (output / "machine/knowledge.sqlite").is_file():
        from .machine_knowledge import build_machine_knowledge, sync_workspace_changes

        build_machine_knowledge(output)
        sync_workspace_changes(output)
    return record


def queue_pending_note(
    output: Path,
    kind: str,
    title: str,
    body: str,
    *,
    query_record: Path | None = None,
    changed_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Queue a Chinese Agent note while the human projection is still building."""
    if kind not in TAG_BY_KIND:
        raise CkbError(f"note kind must be one of: {sorted(TAG_BY_KIND)}")
    if not contains_chinese_narrative(body):
        raise CkbError("pending knowledge note descriptions must use Simplified Chinese; English proper nouns and code identifiers are allowed")
    directory = output / "workspace-meta/pending-notes"
    directory.mkdir(parents=True, exist_ok=True)
    stem = safe_title(title)
    counter = 1
    while (directory / f"{stem}-{counter:02d}.json").exists():
        counter += 1
    record_path = directory / f"{stem}-{counter:02d}.json"
    body_path = record_path.with_suffix(".md")
    body_path.write_text(body.strip() + "\n", encoding="utf-8", newline="\n")
    record = {
        "schema_version": 1,
        "status": "pending-human-projection",
        "kind": kind,
        "title": title,
        "body": str(body_path.resolve()),
        "query_record": str(query_record.resolve()) if query_record else None,
        "changed_paths": sorted(set(changed_paths or [])),
        "queued_at_utc": utc_now(),
    }
    json_write(record_path, record)
    return {**record, "record": str(record_path.resolve())}


def selectors_for_changed_paths(output: Path, changed_paths: list[str]) -> list[str]:
    """Map working-tree paths to deterministic owner pages, with repository fallback."""
    selected_paths = {value.replace("\\", "/") for value in changed_paths}
    if not selected_paths:
        return []
    projection = json_load(output / "markdown/projection.json")
    graph = json_load(output / "graph.json")
    title_by_id = {page["id"]: page["title"] for page in projection.get("pages", [])}
    owners = projection.get("entity_owner_pages", {})
    selectors: list[str] = []
    for entity in graph.get("entities", []):
        if str(entity.get("path", "")).replace("\\", "/") in selected_paths:
            owner = owners.get(entity["id"]) or (entity["id"] if entity["id"] in title_by_id else None)
            if owner in title_by_id:
                selectors.append(title_by_id[owner])
    selectors = list(dict.fromkeys(selectors))
    if selectors:
        return selectors
    repository_pages = [
        page["title"]
        for page in projection.get("pages", [])
        if page.get("page_type") == "repository"
    ]
    return repository_pages[:1]


def materialize_pending_notes(output: Path) -> list[dict[str, Any]]:
    directory = output / "workspace-meta/pending-notes"
    if not directory.is_dir():
        return []
    results: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        pending = json_load(path)
        if pending.get("status") == "materialized":
            continue
        selectors = selectors_for_changed_paths(output, list(pending.get("changed_paths", [])))
        query_record = Path(pending["query_record"]) if pending.get("query_record") else None
        if query_record and not query_record.is_file():
            query_record = None
        result = record_note(
            output,
            str(pending["kind"]),
            str(pending["title"]),
            Path(pending["body"]),
            selectors=selectors,
            query_record=query_record,
            append=False,
            reindex=False,
        )
        pending["status"] = "materialized"
        pending["materialized_file"] = result["file"]
        pending["materialized_at_utc"] = utc_now()
        json_write(path, pending)
        results.append(result)
    return results


def audit_notes(output: Path) -> list[dict[str, Any]]:
    root = output / "markdown"
    if not root.is_dir():
        return [{"reason": "markdown-vault-missing"}]
    projection = json_load(root / "projection.json")
    titles = {page["title"] for page in projection.get("pages", [])}
    notes = []
    errors: list[dict[str, Any]] = []
    for kind, directory_name in DIRECTORY_BY_KIND.items():
        directory = root / directory_name
        if not directory.is_dir():
            errors.append({"reason": "note-directory-missing", "directory": directory_name})
            continue
        for path in sorted(directory.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            note_title = text.splitlines()[0].removeprefix("# ").strip() if text else ""
            notes.append(note_title)
            expected_tag = TAG_BY_KIND[kind]
            tags = re.findall(r"#类型/[\w\u3400-\u9fff-]+", text)
            if tags != [expected_tag]:
                errors.append({"reason": "note-tag-invalid", "path": str(path), "tags": tags, "expected": expected_tag})
            if text.startswith("---\n"):
                errors.append({"reason": "note-frontmatter-visible", "path": str(path)})
            if LONG_HEX.search(text):
                errors.append({"reason": "note-hash-visible", "path": str(path)})
            narrative = "\n".join(
                line
                for line in text.splitlines()
                if not line.startswith(("#", "标签：", "- [[", "- [打开源码："))
            )
            if not contains_chinese_narrative(narrative):
                errors.append({"reason": "note-description-not-chinese", "path": str(path)})
    all_titles = titles | set(notes)
    for directory_name in NOTE_DIRECTORIES:
        for path in (root / directory_name).glob("*.md"):
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[\[([^\]|#]+)", text):
                if target not in all_titles:
                    errors.append({"reason": "note-link-dangling", "path": str(path), "target": target})
    return errors


def sync_workspace(output: Path, repo: Path) -> dict[str, Any]:
    state = json_load(output / "state.json")
    expected = Path(state["repository"]["root"]).resolve()
    actual = repo.resolve()
    if actual != expected:
        raise CkbError(f"workspace repository differs from the initialized repository: {actual}")
    status = run(["git", "-C", str(actual), "status", "--porcelain=v1", "--untracked-files=all"], timeout=60)
    if status.returncode:
        raise CkbError(f"git status failed: {status.stderr or status.stdout}")
    head = run(["git", "-C", str(actual), "rev-parse", "HEAD"], timeout=30)
    diff = run(["git", "-C", str(actual), "diff", "--no-color", "--no-ext-diff"], timeout=120)
    lines = [line for line in diff.stdout.splitlines() if not line.startswith("index ")]
    meta = output / "workspace-meta"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "working.patch").write_text("\n".join(lines).rstrip() + ("\n" if lines else ""), encoding="utf-8", newline="\n")
    changed = []
    untracked = []
    for line in status.stdout.splitlines():
        value = line[3:].strip().replace("\\", "/")
        (untracked if line.startswith("??") else changed).append(value)
    record = {
        "schema_version": 1,
        "status": "dirty" if status.stdout.strip() else "clean",
        "base_commit": state["repository"]["commit"],
        "working_head": head.stdout.strip(),
        "changed_paths": sorted(set(changed)),
        "untracked_paths": sorted(set(untracked)),
        "patch": str((meta / "working.patch").resolve()),
        "captured_at_utc": utc_now(),
    }
    json_write(meta / "working-overlay.json", record)
    if (output / "agent-index.sqlite").is_file() and (output / "markdown/projection.json").is_file():
        from .agent_index import build_agent_index

        build_agent_index(output)
    return record


def workspace_status(output: Path) -> dict[str, Any]:
    state = json_load(output / "state.json")
    overlay = output / "workspace-meta/working-overlay.json"
    return {
        "schema_version": 1,
        "status": "ready",
        "baseline": {
            "status": (state.get("source_snapshot") or {}).get("status", "legacy-live-worktree"),
            "commit": state["repository"]["commit"],
            "snapshot_root": (state.get("source_snapshot") or {}).get("root"),
        },
        "working_overlay": json_load(overlay) if overlay.is_file() else {"status": "not-synced"},
        "notes": {"status": "passed" if not audit_notes(output) else "failed"} if (output / "markdown/projection.json").is_file() else {"status": "waiting-for-markdown"},
    }
