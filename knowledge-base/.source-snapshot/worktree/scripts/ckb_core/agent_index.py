"""SQLite page-first retrieval index for bounded Agent context packs."""

from __future__ import annotations

from collections import defaultdict
import datetime
import json
import math
from pathlib import Path
import re
import sqlite3
from typing import Any

from .common import CkbError, json_load, json_write, utc_now
from .obsidian import NOTE_DIRECTORIES
from .query_terms import build_fts_query, index_terms, search_terms
from .source_links import ensure_local_openers, source_markdown_link


INDEX_SCHEMA_VERSION = 1
DEFAULT_PAGE_LIMIT = 8


def _tokens(text: str) -> int:
    return math.ceil(len(text.encode("utf-8")) / 3)


def _note_documents(markdown_root: Path) -> list[dict[str, Any]]:
    documents = []
    for directory in NOTE_DIRECTORIES:
        for path in sorted((markdown_root / directory).glob("*.md")):
            text = path.read_text(encoding="utf-8")
            title = text.splitlines()[0].removeprefix("# ").strip() if text else path.stem
            tag_match = re.search(r"#类型/[\w\u3400-\u9fff-]+", text)
            documents.append(
                {
                    "title": title,
                    "tag": tag_match.group(0) if tag_match else "",
                    "file": path.relative_to(markdown_root).as_posix(),
                    "content": text,
                    "links": re.findall(r"\[\[([^\]|#]+)", text),
                }
            )
    return documents


def _projection(output: Path) -> tuple[dict[str, Any], str]:
    """Select the richest completed human projection without requiring Markdown."""
    state_path = output / "state.json"
    if state_path.is_file() and json_load(state_path).get("format") == "logseq-db":
        logseq = output / "logseq-db/projection.json"
        if logseq.is_file():
            return json_load(logseq), "logseq-db"
    markdown = output / "markdown/projection.json"
    if markdown.is_file():
        return json_load(markdown), "markdown"
    logseq = output / "logseq-db/projection.json"
    if logseq.is_file():
        return json_load(logseq), "logseq-db"
    raise CkbError("Agent index requires a finalized Markdown or Logseq DB projection")


def _page_documents(
    output: Path,
    projection: dict[str, Any],
    projection_format: str,
    graph: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return readable page documents for either projection.

    Markdown pages are indexed byte-for-byte.  A DB-only build has no page
    files, so the same reviewed source facts are rendered into a compact
    index-only narrative.  This keeps retrieval format-neutral without adding
    another visible knowledge-base projection.
    """
    page_by_id = {page["id"]: page for page in projection.get("pages", [])}
    title_by_id = {page_id: page["title"] for page_id, page in page_by_id.items()}
    owner_by_entity = projection.get("entity_owner_pages", {})
    entity_by_id = {entity["id"]: entity for entity in graph.get("entities", [])}
    owned: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entity in graph.get("entities", []):
        owner = owner_by_entity.get(entity["id"]) or (entity["id"] if entity["id"] in page_by_id else None)
        if owner in page_by_id:
            owned[owner].append(entity)

    state = json_load(output / "state.json")
    snapshot = state.get("source_snapshot") or {}
    openers = ensure_local_openers(
        output,
        Path(state["repository"]["root"]),
        Path(snapshot["root"]) if snapshot.get("root") else None,
    )
    documents: dict[str, dict[str, Any]] = {}
    for page_id, page in page_by_id.items():
        entity = entity_by_id.get(page_id)
        if projection_format == "markdown":
            relative = Path("markdown") / page["file"]
            content = (output / relative).read_text(encoding="utf-8")
        else:
            relative = Path("logseq-db/normalized.edn")
            lines = [f"# {page['title']}", "", f"标签：{page.get('tag') or ''}", ""]
            if entity:
                overview = " ".join(
                    value.strip()
                    for value in (str(entity.get("meaning_zh", "")), str(entity.get("role_zh", "")))
                    if value.strip()
                )
                if overview:
                    lines.extend([f"> {overview}", ""])
                if entity.get("change_when_zh"):
                    lines.extend(["## 什么时候需要修改", "", str(entity["change_when_zh"]), ""])
                if entity.get("path") and entity.get("range"):
                    lines.extend(
                        [
                            "## 源码位置",
                            "",
                            source_markdown_link(
                                openers,
                                str(entity["path"]),
                                int(entity["range"]["start_line"]),
                                int(entity["range"]["end_line"]),
                            ),
                            "",
                        ]
                    )
            else:
                lines.extend(["> 这是由相关类、函数和辅助实现组成的职责导航页。", ""])
            appendix = [item for item in owned.get(page_id, []) if item.get("classification") == "appendix"]
            if appendix:
                lines.extend(["## 内部细节", ""])
                for item in sorted(appendix, key=lambda value: (value.get("path", ""), value.get("range", {}).get("start_line", 0), value.get("qualified_name", ""))):
                    lines.append(f"- `{item.get('qualified_name') or item.get('name')}`：{item.get('description_zh') or item.get('role_zh') or '承担局部辅助处理。'}")
                lines.append("")
            neighbors = []
            for link in projection.get("links", []):
                if link.get("source") == page_id and link.get("target") in title_by_id:
                    neighbors.append(title_by_id[link["target"]])
                elif link.get("target") == page_id and link.get("source") in title_by_id:
                    neighbors.append(title_by_id[link["source"]])
            if neighbors:
                lines.extend(["## 相关代码", "", *[f"- [[{title}]]" for title in sorted(set(neighbors))], ""])
            content = "\n".join(lines).rstrip() + "\n"
        summary = next(
            (
                line.removeprefix("> ").strip()
                for line in content.splitlines()
                if line.startswith("> ") and line.removeprefix("> ").strip()
            ),
            page["title"],
        )
        source_range = entity.get("range", {}) if entity else {}
        documents[page_id] = {
            "content": content,
            "summary": summary,
            "page_file": relative.as_posix(),
            "source_path": entity.get("path") if entity else None,
            "start_line": source_range.get("start_line"),
            "end_line": source_range.get("end_line"),
        }
    return documents


def build_agent_index(output: Path) -> dict[str, Any]:
    markdown_root = output / "markdown"
    projection, projection_format = _projection(output)
    graph = json_load(output / "graph.json")
    pages = projection.get("pages", [])
    documents = _page_documents(output, projection, projection_format, graph)
    page_by_id = {page["id"]: page for page in pages}
    owner_by_entity = projection.get("entity_owner_pages", {})
    symbols_by_page: dict[str, list[str]] = defaultdict(list)
    for entity in graph.get("entities", []):
        owner = owner_by_entity.get(entity["id"]) or (entity["id"] if entity["id"] in page_by_id else None)
        if owner in page_by_id:
            for value in (entity.get("name"), entity.get("qualified_name")):
                if value:
                    symbols_by_page[owner].append(str(value))
    index = output / "agent-index.sqlite"
    temporary = output / "agent-index.sqlite.tmp"
    temporary.unlink(missing_ok=True)
    connection = sqlite3.connect(temporary)
    try:
        connection.executescript(
            """
            PRAGMA foreign_keys=ON;
            CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE pages(
                page_id TEXT PRIMARY KEY,
                title TEXT NOT NULL UNIQUE,
                page_type TEXT NOT NULL,
                tag TEXT NOT NULL,
                page_file TEXT NOT NULL,
                source_path TEXT,
                start_line INTEGER,
                end_line INTEGER,
                summary TEXT NOT NULL,
                content TEXT NOT NULL,
                token_estimate INTEGER NOT NULL
            );
            CREATE TABLE symbols(
                symbol TEXT NOT NULL,
                qualified_name TEXT NOT NULL,
                owner_page_id TEXT NOT NULL REFERENCES pages(page_id),
                source_path TEXT,
                start_line INTEGER,
                end_line INTEGER
            );
            CREATE INDEX symbols_name ON symbols(symbol COLLATE NOCASE);
            CREATE INDEX symbols_qname ON symbols(qualified_name COLLATE NOCASE);
            CREATE TABLE edges(
                source_page_id TEXT NOT NULL REFERENCES pages(page_id),
                target_page_id TEXT NOT NULL REFERENCES pages(page_id),
                relation TEXT NOT NULL,
                weight REAL NOT NULL,
                PRIMARY KEY(source_page_id,target_page_id,relation)
            );
            CREATE INDEX edges_target ON edges(target_page_id);
            CREATE TABLE terms(
                term TEXT NOT NULL,
                page_id TEXT NOT NULL REFERENCES pages(page_id),
                weight REAL NOT NULL,
                PRIMARY KEY(term,page_id)
            );
            CREATE INDEX terms_term ON terms(term);
            CREATE TABLE notes(
                note_title TEXT PRIMARY KEY,
                tag TEXT NOT NULL,
                note_file TEXT NOT NULL,
                content TEXT NOT NULL,
                token_estimate INTEGER NOT NULL
            );
            CREATE TABLE note_links(
                note_title TEXT NOT NULL REFERENCES notes(note_title),
                page_title TEXT NOT NULL,
                PRIMARY KEY(note_title,page_title)
            );
            CREATE VIRTUAL TABLE page_fts USING fts5(
                page_id UNINDEXED,
                title,
                summary,
                symbols,
                source_path,
                tokenize='trigram'
            );
            CREATE VIRTUAL TABLE note_fts USING fts5(
                note_title UNINDEXED,
                title,
                content,
                tokenize='trigram'
            );
            """
        )
        connection.executemany(
            "INSERT INTO meta(key,value) VALUES(?,?)",
            [
                ("schema_version", str(INDEX_SCHEMA_VERSION)),
                ("status", "ready"),
                ("built_at_utc", utc_now()),
                ("page_count", str(len(pages))),
                ("projection_format", projection_format),
            ],
        )
        entity_by_id = {entity["id"]: entity for entity in graph.get("entities", [])}
        for page in pages:
            document = documents[page["id"]]
            content = document["content"]
            summary = document["summary"]
            source_path = document["source_path"]
            symbols = sorted(set(symbols_by_page.get(page["id"], [])))
            connection.execute(
                "INSERT INTO pages VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    page["id"],
                    page["title"],
                    page["page_type"],
                    page.get("tag") or "",
                    document["page_file"],
                    source_path,
                    document["start_line"],
                    document["end_line"],
                    summary,
                    content,
                    _tokens(content),
                ),
            )
            connection.execute(
                "INSERT INTO page_fts(page_id,title,summary,symbols,source_path) VALUES(?,?,?,?,?)",
                (page["id"], page["title"], summary, " ".join(symbols), source_path or ""),
            )
            weighted_terms: dict[str, float] = {}
            for value, weight in ((page["title"], 8.0), (" ".join(symbols), 6.0), (summary, 3.0), (source_path or "", 2.0)):
                for term in index_terms(value):
                    weighted_terms[term] = max(weighted_terms.get(term, 0.0), weight)
            connection.executemany(
                "INSERT INTO terms(term,page_id,weight) VALUES(?,?,?)",
                [(term, page["id"], weight) for term, weight in sorted(weighted_terms.items())],
            )
        for entity in graph.get("entities", []):
            owner = owner_by_entity.get(entity["id"]) or (entity["id"] if entity["id"] in page_by_id else None)
            if owner not in page_by_id:
                continue
            source_range = entity.get("range", {})
            connection.execute(
                "INSERT INTO symbols VALUES(?,?,?,?,?,?)",
                (
                    str(entity.get("name") or entity.get("qualified_name") or ""),
                    str(entity.get("qualified_name") or entity.get("name") or ""),
                    owner,
                    entity.get("path"),
                    source_range.get("start_line"),
                    source_range.get("end_line"),
                ),
            )
        relation_weight = {"tested-by": 1.4, "calls": 1.3, "invokes": 1.3, "depends-on": 1.2, "uses": 1.1, "contains": 0.8}
        for link in projection.get("links", []):
            if link["source"] not in page_by_id or link["target"] not in page_by_id:
                continue
            connection.execute(
                "INSERT OR REPLACE INTO edges VALUES(?,?,?,?)",
                (link["source"], link["target"], link["type"], relation_weight.get(link["type"], 1.0)),
            )
        for note in _note_documents(markdown_root) if projection_format == "markdown" else []:
            connection.execute(
                "INSERT INTO notes VALUES(?,?,?,?,?)",
                (note["title"], note["tag"], note["file"], note["content"], _tokens(note["content"])),
            )
            connection.execute(
                "INSERT INTO note_fts(note_title,title,content) VALUES(?,?,?)",
                (note["title"], note["title"], note["content"]),
            )
            for title in note["links"]:
                connection.execute("INSERT OR IGNORE INTO note_links VALUES(?,?)", (note["title"], title))
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        if integrity != "ok" or foreign_keys:
            raise CkbError(f"Agent index integrity failed: integrity={integrity}; foreign_keys={foreign_keys}")
    finally:
        connection.close()
    temporary.replace(index)
    return audit_agent_index(output)


def audit_agent_index(output: Path) -> dict[str, Any]:
    index = output / "agent-index.sqlite"
    if not index.is_file():
        return {"schema_version": 1, "status": "failed", "errors": [{"reason": "agent-index-missing"}]}
    projection, projection_format = _projection(output)
    expected_notes = len(_note_documents(output / "markdown")) if projection_format == "markdown" else 0
    connection = sqlite3.connect(f"file:{index.as_posix()}?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        counts = {
            "pages": connection.execute("SELECT count(*) FROM pages").fetchone()[0],
            "symbols": connection.execute("SELECT count(*) FROM symbols").fetchone()[0],
            "edges": connection.execute("SELECT count(*) FROM edges").fetchone()[0],
            "terms": connection.execute("SELECT count(*) FROM terms").fetchone()[0],
            "notes": connection.execute("SELECT count(*) FROM notes").fetchone()[0],
        }
        meta = dict(connection.execute("SELECT key,value FROM meta").fetchall())
        forbidden_columns = []
        for table in ("pages", "symbols", "edges", "notes", "meta"):
            for row in connection.execute(f"PRAGMA table_info({table})"):
                if "hash" in str(row[1]).casefold():
                    forbidden_columns.append(f"{table}.{row[1]}")
    finally:
        connection.close()
    errors = []
    if integrity != "ok":
        errors.append({"reason": "sqlite-integrity", "detail": integrity})
    if foreign_keys:
        errors.append({"reason": "foreign-key-errors", "detail": foreign_keys})
    if counts["pages"] != len(projection.get("pages", [])):
        errors.append({"reason": "page-count-mismatch", "actual": counts["pages"], "expected": len(projection.get("pages", []))})
    if counts["notes"] != expected_notes:
        errors.append({"reason": "note-count-mismatch", "actual": counts["notes"], "expected": expected_notes})
    if forbidden_columns:
        errors.append({"reason": "new-index-hash-column-present", "columns": forbidden_columns})
    if meta.get("projection_format") != projection_format:
        errors.append({"reason": "projection-format-mismatch", "actual": meta.get("projection_format"), "expected": projection_format})
    return {
        "schema_version": INDEX_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "path": str(index.resolve()),
        "integrity": integrity,
        "counts": counts,
        "projection_format": projection_format,
        "errors": errors,
    }


def _agent_index_ready(output: Path) -> None:
    index = output / "agent-index.sqlite"
    if not index.is_file():
        raise CkbError("Agent index is missing; run reindex or finalize")
    connection = sqlite3.connect(f"file:{index.as_posix()}?mode=ro", uri=True)
    try:
        meta = dict(connection.execute("SELECT key,value FROM meta").fetchall())
    except sqlite3.DatabaseError as exc:
        raise CkbError(f"Agent index metadata is unavailable: {exc}") from exc
    finally:
        connection.close()
    if meta.get("status") != "ready" or meta.get("schema_version") != str(INDEX_SCHEMA_VERSION):
        raise CkbError(f"Agent index metadata is incompatible: {meta}")


def _fts_query(question: str) -> str | None:
    return build_fts_query(question, 12)


def _next_pack_path(output: Path) -> tuple[Path, Path]:
    directory = output / "agent-packs"
    directory.mkdir(parents=True, exist_ok=True)
    prefix = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    counter = 1
    while True:
        stem = f"pack-{prefix}-{counter:02d}"
        markdown = directory / f"{stem}.md"
        record = directory / f"{stem}.json"
        if not markdown.exists() and not record.exists():
            return markdown, record
        counter += 1


def retrieve(output: Path, question: str, budget: int = 1500, page_limit: int = DEFAULT_PAGE_LIMIT) -> dict[str, Any]:
    if budget < 200:
        raise CkbError("retrieve budget must be at least 200")
    if page_limit < 1 or page_limit > 32:
        raise CkbError("retrieve page limit must be in [1, 32]")
    _agent_index_ready(output)
    index = output / "agent-index.sqlite"
    connection = sqlite3.connect(f"file:{index.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    scores: dict[str, float] = defaultdict(float)
    reasons: dict[str, list[str]] = defaultdict(list)
    terms = search_terms(question)
    try:
        for row in connection.execute("SELECT page_id,title FROM pages WHERE title=? COLLATE NOCASE", (question,)):
            scores[row["page_id"]] += 160
            reasons[row["page_id"]].append("页面标题精确匹配")
        for term in terms:
            for row in connection.execute(
                "SELECT owner_page_id,symbol,qualified_name FROM symbols WHERE symbol=? COLLATE NOCASE OR qualified_name=? COLLATE NOCASE LIMIT 20",
                (term, term),
            ):
                scores[row["owner_page_id"]] += 120
                reasons[row["owner_page_id"]].append(f"符号精确匹配：{row['qualified_name']}")
            for row in connection.execute("SELECT page_id,weight FROM terms WHERE term=? LIMIT 50", (term,)):
                scores[row["page_id"]] += float(row["weight"])
                reasons[row["page_id"]].append(f"索引词匹配：{term}")
        fts = _fts_query(question)
        if fts:
            for row in connection.execute(
                "SELECT page_id,bm25(page_fts,8.0,3.0,6.0,2.0) AS rank FROM page_fts WHERE page_fts MATCH ? ORDER BY rank LIMIT 30",
                (fts,),
            ):
                scores[row["page_id"]] += 40.0 / (1.0 + abs(float(row["rank"])))
                reasons[row["page_id"]].append("全文索引匹配")
        if not scores:
            return {
                "schema_version": INDEX_SCHEMA_VERSION,
                "status": "needs-grep",
                "question": question,
                "budget": budget,
                "grep_terms": terms[:12],
                "reason": "Agent index found no page candidate",
            }
        seeds = [page_id for page_id, _score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:3]]
        for seed in seeds:
            for row in connection.execute(
                "SELECT source_page_id,target_page_id,relation,weight FROM edges WHERE source_page_id=? OR target_page_id=?",
                (seed, seed),
            ):
                neighbor = row["target_page_id"] if row["source_page_id"] == seed else row["source_page_id"]
                scores[neighbor] += 18.0 * float(row["weight"])
                reasons[neighbor].append(f"与高相关页面一跳关联：{row['relation']}")
        ordered = sorted(scores, key=lambda page_id: (-scores[page_id], page_id))
        pack_path, record_path = _next_pack_path(output)
        header = ["# Agent 阅读包", "", f"问题：{question}", "", "按顺序阅读以下页面；源码链接可以直接打开对应位置。", ""]
        selected = []
        pack = "\n".join(header)
        for page_id in ordered:
            if len(selected) >= page_limit:
                break
            row = connection.execute("SELECT * FROM pages WHERE page_id=?", (page_id,)).fetchone()
            if row is None:
                continue
            reason_text = "；".join(dict.fromkeys(reasons[page_id]))
            block = (
                f"## {row['title']}\n\n"
                f"选择原因：{reason_text}\n\n"
                f"知识页：`{row['page_file']}`\n\n"
                f"{row['content'].strip()}\n\n"
            )
            candidate = pack + block
            if _tokens(candidate) > budget:
                if selected:
                    continue
                allowed_bytes = max(0, budget * 3 - len((pack + f"## {row['title']}\n\n选择原因：{reason_text}\n\n").encode("utf-8")) - 80)
                content_bytes = row["content"].encode("utf-8")[:allowed_bytes]
                while True:
                    try:
                        truncated = content_bytes.decode("utf-8")
                        break
                    except UnicodeDecodeError as exc:
                        content_bytes = content_bytes[: exc.start]
                block = f"## {row['title']}\n\n选择原因：{reason_text}\n\n{truncated.rstrip()}\n\n> 页面内容已按预算截断。\n\n"
                candidate = pack + block
            if _tokens(candidate) <= budget:
                pack = candidate
                selected.append(
                    {
                        "page_id": page_id,
                        "title": row["title"],
                        "page_file": str((output / row["page_file"]).resolve()),
                        "tag": row["tag"],
                        "source_path": row["source_path"],
                        "start_line": row["start_line"],
                        "end_line": row["end_line"],
                        "page_tokens": row["token_estimate"],
                        "score": round(scores[page_id], 6),
                        "reasons": list(dict.fromkeys(reasons[page_id])),
                    }
                )
        note_rows = []
        if fts:
            for row in connection.execute(
                "SELECT note_title,bm25(note_fts,8.0,2.0) AS rank FROM note_fts WHERE note_fts MATCH ? ORDER BY rank LIMIT 5",
                (fts,),
            ):
                note = connection.execute("SELECT * FROM notes WHERE note_title=?", (row["note_title"],)).fetchone()
                if note:
                    note_rows.append({"title": note["note_title"], "file": str((output / "markdown" / note["note_file"]).resolve()), "tag": note["tag"]})
    finally:
        connection.close()
    if not selected:
        raise CkbError("retrieve budget is too small for the highest-ranked page")
    pack_path.write_text(pack.rstrip() + "\n", encoding="utf-8", newline="\n")
    result = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "status": "passed",
        "question": question,
        "budget": budget,
        "estimated_tokens": _tokens(pack),
        "selected_pages": selected,
        "related_notes": note_rows,
        "pack": str(pack_path.resolve()),
        "record": str(record_path.resolve()),
        "retrieval": "sqlite-exact-terms-fts5-trigram-plus-one-hop-graph",
        "grep_fallback_required": False,
    }
    json_write(record_path, result)
    return result
