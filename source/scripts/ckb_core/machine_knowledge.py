"""Comprehensive SQLite knowledge layer and deterministic Agent retrieval.

The human Markdown projection is intentionally small.  This module indexes the
complete reviewed fact graph, source files, relations, evidence, working notes,
and human ownership mapping without applying human page quotas.
"""

from __future__ import annotations

from collections import defaultdict, deque
import datetime
import json
import math
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterable
from urllib.parse import quote

from .common import CkbError, json_load, json_write, sha256_file, utc_now
from .keyword_fallback import (
    KeywordFallbackOptions,
    run_keyword_provider,
    unique_casefold,
    write_keyword_fallback_record,
)
from .obsidian import NOTE_DIRECTORIES
from .query_terms import build_fts_query, explicit_anchors, index_terms, search_terms
from .source_links import SourceLinkRenderer, source_markdown_link


MACHINE_SCHEMA_VERSION = 3
MACHINE_PATH = Path("machine/knowledge.sqlite")
FAST_RETRIEVAL_OVERSCAN = 32
PRECISE_RETRIEVAL_OVERSCAN = 64
IMPLEMENTATION_TEST_DISCOUNT = 0.42
_RETRIEVAL_STATIC_CACHE: dict[str, Any] = {}
RELATION_WEIGHTS: dict[str, float] = {
    "tested-by": 1.55,
    "implements": 1.50,
    "inherits": 1.45,
    "calls": 1.40,
    "invokes": 1.40,
    "references": 1.20,
    "imports": 1.15,
    "depends-on": 1.15,
    "uses": 1.05,
    "partial-fragment": 1.00,
    "contains": 0.82,
    "contains-file": 0.72,
    "contains-module": 0.68,
}


def estimated_tokens(text: str) -> int:
    return math.ceil(len(text.encode("utf-8")) / 3)


def contains_chinese_narrative(value: Any, minimum_han: int = 2) -> bool:
    """Require Chinese prose while allowing identifiers and foreign terms."""
    if not isinstance(value, str) or len(value.strip()) < 4:
        return False
    return len(re.findall(r"[\u3400-\u9fff]", value)) >= minimum_han


def _fts_query(question: str) -> str | None:
    return build_fts_query(question)


def _fts_query_values(values: Iterable[str]) -> str | None:
    values = [term for term in values if len(term) >= 3][:16]
    if not values:
        return None
    return " OR ".join('"' + value.replace('"', '""') + '"' for value in values)


def _human_projection(output: Path) -> tuple[dict[str, Any], Path]:
    for root in (output / "human", output / "markdown"):
        path = root / "projection.json"
        if path.is_file():
            return json_load(path), root
    logseq = output / "logseq-db/projection.json"
    if logseq.is_file():
        return json_load(logseq), output / "logseq-db"
    raise CkbError("machine knowledge requires a completed human projection")


def _note_documents(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir():
        return []
    result: list[dict[str, Any]] = []
    kinds = {
        "analysis": "analysis",
        "changes": "change",
        "pitfalls": "pitfall",
        "experiments": "experiment",
        "sessions": "session",
    }
    for directory in NOTE_DIRECTORIES:
        for path in sorted((root / directory).glob("*.md")):
            content = path.read_text(encoding="utf-8")
            title = content.splitlines()[0].removeprefix("# ").strip() if content else path.stem
            tag = next(iter(re.findall(r"#类型/[\w\u3400-\u9fff-]+", content)), "")
            result.append(
                {
                    "id": f"note:{directory}:{path.stem}",
                    "kind": kinds[directory],
                    "title": title,
                    "tag": tag,
                    "relative_path": path.relative_to(root).as_posix(),
                    "content": content,
                    "links": re.findall(r"\[\[([^\]|#]+)", content),
                }
            )
    return result


def _review_paths(output: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    state_path = output / "state.json"
    if not state_path.is_file():
        return result
    state = json_load(state_path)
    for pack in state.get("review_packs", []):
        path = pack.get("review_path")
        if not path or not Path(path).is_file():
            continue
        for item in json_load(Path(path)).get("reviews", []):
            result[str(item.get("entity_id"))] = str(Path(path).resolve())
    return result


def _source_texts(output: Path, graph: dict[str, Any]) -> dict[str, str]:
    state = json_load(output / "state.json")
    snapshot = state.get("source_snapshot") or {}
    root = Path(snapshot.get("root", ""))
    texts: dict[str, str] = {}
    for path in sorted({str(entity["path"]) for entity in graph.get("entities", [])}):
        source = root / Path(path)
        if source.is_file():
            texts[path] = source.read_text(encoding="utf-8", errors="replace")
    return texts


def _description(entity: dict[str, Any]) -> str:
    if entity.get("classification") == "appendix":
        return str(entity.get("description_zh") or "").strip()
    return " ".join(
        str(entity.get(field) or "").strip()
        for field in ("meaning_zh", "role_zh", "change_when_zh")
        if str(entity.get(field) or "").strip()
    )


def _human_map(logical: dict[str, Any], projection: dict[str, Any]) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    owners = dict(logical.get("entity_owner_pages", {})) if logical else dict(projection.get("entity_owner_pages", {}))
    pages = {str(page["id"]): page for page in projection.get("pages", [])}
    return owners, pages


def _sections_for_entity(entity: dict[str, Any], excerpt: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    if entity.get("classification") == "appendix":
        sections.append(("中文作用", str(entity.get("description_zh") or "").strip()))
    else:
        sections.extend(
            [
                ("中文含义", str(entity.get("meaning_zh") or "").strip()),
                ("中文职责", str(entity.get("role_zh") or "").strip()),
                ("什么时候需要修改", str(entity.get("change_when_zh") or "").strip()),
            ]
        )
    sections.append(("来源核对", str(entity.get("evidence_note") or "").strip()))
    if entity.get("kind") != "file" and excerpt.strip():
        bounded = excerpt.strip()
        if len(bounded) > 3600:
            bounded = bounded[:3600].rstrip() + "\n\n……源码摘录已截断；完整文件保存在机器库 source_files 表中。"
        sections.append(("固定源码摘录", bounded))
    return [(heading, content) for heading, content in sections if content]


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys=ON;
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE files(
            file_id TEXT PRIMARY KEY,
            path TEXT NOT NULL UNIQUE,
            language TEXT NOT NULL,
            module TEXT NOT NULL,
            commit_id TEXT NOT NULL,
            blob_id TEXT NOT NULL,
            source_text TEXT NOT NULL
        );
        CREATE TABLE entities(
            entity_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            name TEXT NOT NULL,
            qualified_name TEXT NOT NULL,
            language TEXT NOT NULL,
            source_path TEXT NOT NULL,
            parent_id TEXT,
            classification TEXT NOT NULL,
            owner_page_id TEXT,
            module TEXT NOT NULL,
            meaning_zh TEXT NOT NULL,
            role_zh TEXT NOT NULL,
            change_when_zh TEXT NOT NULL,
            description_zh TEXT NOT NULL,
            evidence_note TEXT NOT NULL,
            review_status TEXT NOT NULL,
            commit_id TEXT NOT NULL,
            blob_id TEXT NOT NULL
        );
        CREATE INDEX entities_name ON entities(name COLLATE NOCASE);
        CREATE INDEX entities_qname ON entities(qualified_name COLLATE NOCASE);
        CREATE INDEX entities_path ON entities(source_path COLLATE NOCASE);
        CREATE TABLE source_ranges(
            entity_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
            start_byte INTEGER NOT NULL,
            end_byte INTEGER NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL
        );
        CREATE TABLE relations(
            relation_id TEXT PRIMARY KEY,
            source_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
            target_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
            relation TEXT NOT NULL,
            weight REAL NOT NULL,
            provider TEXT NOT NULL,
            cross_chunk INTEGER NOT NULL
        );
        CREATE INDEX relations_source ON relations(source_entity_id);
        CREATE INDEX relations_target ON relations(target_entity_id);
        CREATE INDEX relations_type ON relations(relation);
        CREATE TABLE relation_evidence(
            relation_id TEXT PRIMARY KEY REFERENCES relations(relation_id),
            evidence_json TEXT NOT NULL
        );
        CREATE TABLE providers(
            provider_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            language TEXT NOT NULL,
            status TEXT NOT NULL,
            precision TEXT NOT NULL,
            diagnostic_count INTEGER NOT NULL,
            evidence_json TEXT NOT NULL
        );
        CREATE TABLE diagnostics(
            diagnostic_id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER NOT NULL REFERENCES providers(provider_id),
            severity TEXT NOT NULL,
            content TEXT NOT NULL
        );
        CREATE TABLE reviews(
            entity_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
            status TEXT NOT NULL,
            evidence_note TEXT NOT NULL,
            review_file TEXT
        );
        CREATE TABLE modules(module TEXT PRIMARY KEY, entity_count INTEGER NOT NULL);
        CREATE TABLE communities(community_id INTEGER PRIMARY KEY, label TEXT NOT NULL, member_count INTEGER NOT NULL, cohesion REAL NOT NULL);
        CREATE TABLE community_members(community_id INTEGER NOT NULL REFERENCES communities(community_id), entity_id TEXT NOT NULL REFERENCES entities(entity_id), PRIMARY KEY(community_id,entity_id));
        CREATE TABLE boundaries(entity_id TEXT PRIMARY KEY REFERENCES entities(entity_id), reason TEXT NOT NULL);
        CREATE TABLE human_projection(
            entity_id TEXT PRIMARY KEY REFERENCES entities(entity_id),
            human_page_id TEXT,
            title TEXT,
            page_file TEXT,
            display_mode TEXT NOT NULL
        );
        CREATE TABLE reference_sources(
            reference_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            origin TEXT NOT NULL,
            author TEXT,
            license TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_file TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            status TEXT NOT NULL,
            revision INTEGER NOT NULL,
            supersedes TEXT,
            human_file TEXT
        );
        CREATE TABLE research_gaps(
            gap_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            status TEXT NOT NULL,
            summary_zh TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            updated_at_utc TEXT NOT NULL,
            resolution_zh TEXT,
            resolution_evidence_json TEXT NOT NULL
        );
        CREATE TABLE documents(
            document_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            tag TEXT NOT NULL,
            human_file TEXT,
            source_entity_id TEXT REFERENCES entities(entity_id),
            content TEXT NOT NULL,
            token_estimate INTEGER NOT NULL
        );
        CREATE TABLE sections(
            section_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL REFERENCES documents(document_id),
            ordinal INTEGER NOT NULL,
            heading TEXT NOT NULL,
            content TEXT NOT NULL,
            token_estimate INTEGER NOT NULL,
            source_path TEXT,
            start_line INTEGER,
            end_line INTEGER
        );
        CREATE INDEX sections_document ON sections(document_id,ordinal);
        CREATE TABLE section_sources(section_id TEXT NOT NULL REFERENCES sections(section_id), entity_id TEXT NOT NULL REFERENCES entities(entity_id), PRIMARY KEY(section_id,entity_id));
        CREATE TABLE document_links(source_document_id TEXT NOT NULL REFERENCES documents(document_id), target_document_id TEXT, target_title TEXT NOT NULL, relation TEXT NOT NULL, PRIMARY KEY(source_document_id,target_title,relation));
        CREATE TABLE terms(term TEXT NOT NULL, entity_id TEXT NOT NULL REFERENCES entities(entity_id), weight REAL NOT NULL, PRIMARY KEY(term,entity_id));
        CREATE INDEX terms_term ON terms(term);
        CREATE TABLE workspace_changes(path TEXT PRIMARY KEY, change_type TEXT NOT NULL, detail_json TEXT NOT NULL);
        CREATE VIRTUAL TABLE entity_fts USING fts5(
            entity_id UNINDEXED,
            name,
            qualified_name,
            meaning_zh,
            role_zh,
            change_when_zh,
            description_zh,
            source_path,
            tokenize='trigram'
        );
        CREATE VIRTUAL TABLE section_fts USING fts5(
            section_id UNINDEXED,
            document_id UNINDEXED,
            heading,
            content,
            source_path,
            tokenize='trigram'
        );
        CREATE VIRTUAL TABLE source_fts USING fts5(
            source_path UNINDEXED,
            content,
            tokenize='trigram'
        );
        """
    )


def build_machine_knowledge(
    output: Path,
    graph: dict[str, Any] | None = None,
    logical: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output = output.resolve()
    graph = graph or json_load(output / "graph.json")
    projection, human_root = _human_projection(output)
    owners, pages = _human_map(logical or {}, projection)
    source_texts = _source_texts(output, graph)
    review_paths = _review_paths(output)
    machine_root = output / "machine"
    machine_root.mkdir(parents=True, exist_ok=True)
    target = machine_root / "knowledge.sqlite"
    temporary = machine_root / "knowledge.sqlite.tmp"
    temporary.unlink(missing_ok=True)
    connection = sqlite3.connect(temporary)
    try:
        _create_schema(connection)
        connection.executemany(
            "INSERT INTO meta(key,value) VALUES(?,?)",
            [
                ("schema_version", str(MACHINE_SCHEMA_VERSION)),
                ("status", "ready"),
                ("built_at_utc", utc_now()),
                ("repository_commit", str(graph["repository"]["commit"])),
                ("graph_sha256", sha256_file(output / "graph.json")),
                ("language_contract", "所有说明使用简体中文，允许英文专有名词和代码标识符"),
                ("retrieval", "sqlite-exact-fts5-sections-deterministic-weighted-graph"),
            ],
        )
        entities = list(graph.get("entities", []))
        entity_by_id = {str(entity["id"]): entity for entity in entities}
        files = [entity for entity in entities if entity.get("kind") == "file"]
        for entity in files:
            path = str(entity["path"])
            connection.execute(
                "INSERT INTO files VALUES(?,?,?,?,?,?,?)",
                (
                    entity["id"],
                    path,
                    entity.get("language") or "unknown",
                    path.split("/", 1)[0] if "/" in path else ".",
                    entity["commit"],
                    entity["blob"],
                    source_texts.get(path, ""),
                ),
            )
            connection.execute("INSERT INTO source_fts(source_path,content) VALUES(?,?)", (path, source_texts.get(path, "")))
        modules: dict[str, int] = defaultdict(int)
        for entity in entities:
            path = str(entity["path"])
            module = path.split("/", 1)[0] if "/" in path else "."
            modules[module] += 1
            meaning = str(entity.get("meaning_zh") or "")
            role = str(entity.get("role_zh") or "")
            change_when = str(entity.get("change_when_zh") or "")
            description = str(entity.get("description_zh") or "")
            connection.execute(
                "INSERT INTO entities VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    entity["id"], entity.get("kind") or "unknown", entity.get("name") or "", entity.get("qualified_name") or entity.get("name") or "",
                    entity.get("language") or "unknown", path, entity.get("parent_id"), entity.get("classification") or "unknown", entity.get("owner_page_id"), module,
                    meaning, role, change_when, description, str(entity.get("evidence_note") or ""), entity.get("review_status") or "", entity["commit"], entity["blob"],
                ),
            )
            source_range = entity["range"]
            connection.execute(
                "INSERT INTO source_ranges VALUES(?,?,?,?,?)",
                (entity["id"], source_range["start_byte"], source_range["end_byte"], source_range["start_line"], source_range["end_line"]),
            )
            connection.execute(
                "INSERT INTO reviews VALUES(?,?,?,?)",
                (entity["id"], entity.get("review_status") or "", str(entity.get("evidence_note") or ""), review_paths.get(str(entity["id"]))),
            )
            if entity.get("classification") == "boundary":
                connection.execute("INSERT INTO boundaries VALUES(?,?)", (entity["id"], "局部扫描的一跳范围边界"))
            owner = owners.get(str(entity["id"])) or entity.get("owner_page_id")
            page = pages.get(str(owner)) if owner else None
            display_mode = "page" if entity.get("classification") == "page" else ("appendix" if entity.get("classification") == "appendix" else "boundary")
            connection.execute(
                "INSERT INTO human_projection VALUES(?,?,?,?,?)",
                (entity["id"], owner, page.get("title") if page else None, page.get("file") if page else None, display_mode),
            )
            connection.execute(
                "INSERT INTO entity_fts VALUES(?,?,?,?,?,?,?,?)",
                (entity["id"], entity.get("name") or "", entity.get("qualified_name") or "", meaning, role, change_when, description, path),
            )
            weighted: dict[str, float] = {}
            for value, weight in (
                (entity.get("qualified_name") or "", 10.0),
                (entity.get("name") or "", 9.0),
                (path, 6.0),
                (_description(entity), 4.0),
            ):
                for term in index_terms(str(value)):
                    weighted[term] = max(weighted.get(term, 0.0), weight)
            connection.executemany(
                "INSERT INTO terms VALUES(?,?,?)",
                [(term, entity["id"], weight) for term, weight in sorted(weighted.items())],
            )
            source = source_texts.get(path, "").encode("utf-8")
            start = int(source_range["start_byte"])
            end = int(source_range["end_byte"])
            excerpt = source[start:end].decode("utf-8", errors="replace") if 0 <= start <= end <= len(source) else ""
            document_id = f"entity:{entity['id']}"
            title = str(entity.get("qualified_name") or entity.get("name") or entity["id"])
            document_content = _description(entity)
            connection.execute(
                "INSERT INTO documents VALUES(?,?,?,?,?,?,?,?)",
                (document_id, "entity", title, "#类型/机器事实", page.get("file") if page else None, entity["id"], document_content, estimated_tokens(document_content)),
            )
            for ordinal, (heading, content) in enumerate(_sections_for_entity(entity, excerpt)):
                section_id = f"{document_id}:{ordinal}"
                connection.execute(
                    "INSERT INTO sections VALUES(?,?,?,?,?,?,?,?,?)",
                    (section_id, document_id, ordinal, heading, content, estimated_tokens(content), path, source_range["start_line"], source_range["end_line"]),
                )
                connection.execute("INSERT INTO section_sources VALUES(?,?)", (section_id, entity["id"]))
                connection.execute("INSERT INTO section_fts VALUES(?,?,?,?,?)", (section_id, document_id, heading, content, path))
        connection.executemany("INSERT INTO modules VALUES(?,?)", sorted(modules.items()))
        for link in graph.get("links", []):
            if link.get("source") not in entity_by_id or link.get("target") not in entity_by_id:
                continue
            relation = str(link.get("type") or "references")
            connection.execute(
                "INSERT INTO relations VALUES(?,?,?,?,?,?,?)",
                (link["id"], link["source"], link["target"], relation, RELATION_WEIGHTS.get(relation, 1.0), str(link.get("provider") or ""), 1 if link.get("cross_chunk") else 0),
            )
            connection.execute("INSERT INTO relation_evidence VALUES(?,?)", (link["id"], json.dumps(link.get("evidence") or {}, ensure_ascii=False, sort_keys=True)))
        for provider in graph.get("providers", []):
            cursor = connection.execute(
                "INSERT INTO providers(name,language,status,precision,diagnostic_count,evidence_json) VALUES(?,?,?,?,?,?)",
                (provider.get("name") or "", provider.get("language") or "", provider.get("status") or "", provider.get("precision") or "", int(provider.get("diagnostic_count", 0)), json.dumps(provider, ensure_ascii=False, sort_keys=True)),
            )
            provider_id = int(cursor.lastrowid)
            for severity, values in (("fatal", provider.get("fatal_diagnostics", [])), ("stderr", provider.get("fatal_stderr", []))):
                for value in values:
                    connection.execute("INSERT INTO diagnostics(provider_id,severity,content) VALUES(?,?,?)", (provider_id, severity, json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value))
        communities_path = output / "graphify-out/communities.json"
        if communities_path.is_file():
            for community in json_load(communities_path).get("communities", []):
                community_id = int(community["id"])
                connection.execute(
                    "INSERT INTO communities VALUES(?,?,?,?)",
                    (community_id, str(community.get("label") or ""), int(community.get("member_count", len(community.get("members", [])))), float(community.get("cohesion", 0.0))),
                )
                connection.executemany(
                    "INSERT INTO community_members VALUES(?,?)",
                    [(community_id, member) for member in community.get("members", []) if member in entity_by_id],
                )
        title_to_document: dict[str, str] = {}
        for note in _note_documents(human_root):
            content = str(note["content"])
            connection.execute(
                "INSERT INTO documents VALUES(?,?,?,?,?,?,?,?)",
                (note["id"], note["kind"], note["title"], note["tag"], note["relative_path"], None, content, estimated_tokens(content)),
            )
            title_to_document[note["title"]] = note["id"]
            chunks = _markdown_sections(content)
            for ordinal, (heading, section_content) in enumerate(chunks):
                section_id = f"{note['id']}:{ordinal}"
                connection.execute(
                    "INSERT INTO sections VALUES(?,?,?,?,?,?,?,?,?)",
                    (section_id, note["id"], ordinal, heading, section_content, estimated_tokens(section_content), None, None, None),
                )
                connection.execute("INSERT INTO section_fts VALUES(?,?,?,?,?)", (section_id, note["id"], heading, section_content, ""))
            for target_title in note["links"]:
                connection.execute(
                    "INSERT OR IGNORE INTO document_links VALUES(?,?,?,?)",
                    (note["id"], None, target_title, "wikilink"),
                )
        from .reference_documents import reference_machine_records

        reference_records = reference_machine_records(output)
        for source in reference_records["sources"]:
            connection.execute(
                "INSERT INTO reference_sources VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    source["reference_id"], source["title"], source["origin"], source.get("author"),
                    source["license"], source["source_type"], source["source_file"], source["source_sha256"],
                    source["status"], int(source.get("revision", 1)), source.get("supersedes"), source.get("human_file"),
                ),
            )
        for document in reference_records["documents"]:
            content = str(document["content"])
            connection.execute(
                "INSERT INTO documents VALUES(?,?,?,?,?,?,?,?)",
                (
                    document["document_id"], document["kind"], document["title"], document["tag"],
                    document["human_file"], None, content, estimated_tokens(content),
                ),
            )
            title_to_document[document["title"]] = document["document_id"]
            for ordinal, section in enumerate(document["sections"]):
                section_id = f"{document['document_id']}:{ordinal}"
                section_content = str(section["content"])
                connection.execute(
                    "INSERT INTO sections VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        section_id, document["document_id"], ordinal, section["heading"], section_content,
                        estimated_tokens(section_content), document["raw_file"], section["start_line"], section["end_line"],
                    ),
                )
                connection.execute(
                    "INSERT INTO section_fts VALUES(?,?,?,?,?)",
                    (section_id, document["document_id"], section["heading"], section_content, document["raw_file"]),
                )
            for target_title in document["links"]:
                connection.execute(
                    "INSERT OR IGNORE INTO document_links VALUES(?,?,?,?)",
                    (document["document_id"], None, target_title, "wikilink"),
                )
        from .research_gaps import gap_machine_records

        gap_records = gap_machine_records(output)
        for item in gap_records["records"]:
            connection.execute(
                "INSERT INTO research_gaps VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    item["gap_id"], item["kind"], item["status"], item["summary_zh"],
                    json.dumps(item["evidence_paths"], ensure_ascii=False), item["created_at_utc"],
                    item["updated_at_utc"], item.get("resolution_zh"),
                    json.dumps(item.get("resolution_evidence_paths", []), ensure_ascii=False),
                ),
            )
        for document in gap_records["documents"]:
            content = str(document["content"])
            connection.execute(
                "INSERT INTO documents VALUES(?,?,?,?,?,?,?,?)",
                (
                    document["document_id"], document["kind"], document["title"], document["tag"],
                    None, None, content, estimated_tokens(content),
                ),
            )
            section_id = f"{document['document_id']}:0"
            connection.execute(
                "INSERT INTO sections VALUES(?,?,?,?,?,?,?,?,?)",
                (section_id, document["document_id"], 0, document["section_heading"], content, estimated_tokens(content), None, None, None),
            )
            connection.execute(
                "INSERT INTO section_fts VALUES(?,?,?,?,?)",
                (section_id, document["document_id"], document["section_heading"], content, ""),
            )
        overlay = output / "workspace-meta/working-overlay.json"
        if overlay.is_file():
            value = json_load(overlay)
            for path in value.get("changed_paths", []):
                connection.execute("INSERT OR REPLACE INTO workspace_changes VALUES(?,?,?)", (path, "changed", json.dumps(value, ensure_ascii=False, sort_keys=True)))
            for path in value.get("untracked_paths", []):
                connection.execute("INSERT OR REPLACE INTO workspace_changes VALUES(?,?,?)", (path, "untracked", json.dumps(value, ensure_ascii=False, sort_keys=True)))
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        if integrity != "ok" or foreign_keys:
            raise CkbError(f"machine knowledge integrity failed: integrity={integrity}; foreign_keys={foreign_keys}")
    finally:
        connection.close()
    temporary.replace(target)
    return audit_machine_knowledge(output, graph)


def _markdown_sections(content: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    heading = "正文"
    buffer: list[str] = []
    in_fence = False
    for line in content.replace("\r\n", "\n").splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        match = None if in_fence else re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            if any(value.strip() for value in buffer):
                result.append((heading, "\n".join(buffer).strip()))
            heading = match.group(1).strip()
            buffer = []
        else:
            buffer.append(line)
    if any(value.strip() for value in buffer):
        result.append((heading, "\n".join(buffer).strip()))
    return result or [("正文", content.strip())]


def audit_machine_knowledge(output: Path, graph: dict[str, Any] | None = None) -> dict[str, Any]:
    output = output.resolve()
    graph = graph or json_load(output / "graph.json")
    path = output / MACHINE_PATH
    errors: list[dict[str, Any]] = []
    if not path.is_file():
        return {"schema_version": MACHINE_SCHEMA_VERSION, "status": "failed", "path": str(path), "errors": [{"reason": "machine-sqlite-missing"}]}
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        counts = {
            name: connection.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
            for name in ("files", "entities", "source_ranges", "relations", "reviews", "documents", "sections", "human_projection", "workspace_changes", "reference_sources", "research_gaps")
        }
        meta = dict(connection.execute("SELECT key,value FROM meta"))
        language_errors = [
            row[0]
            for row in connection.execute(
                """
                SELECT entity_id FROM entities
                WHERE (classification='appendix' AND description_zh NOT GLOB '*[一-龥]*')
                   OR (classification<>'appendix' AND (meaning_zh NOT GLOB '*[一-龥]*' OR role_zh NOT GLOB '*[一-龥]*' OR change_when_zh NOT GLOB '*[一-龥]*'))
                   OR evidence_note NOT GLOB '*[一-龥]*'
                """
            )
        ]
        fts_counts = {
            "entity_fts": connection.execute("SELECT count(*) FROM entity_fts").fetchone()[0],
            "section_fts": connection.execute("SELECT count(*) FROM section_fts").fetchone()[0],
            "source_fts": connection.execute("SELECT count(*) FROM source_fts").fetchone()[0],
        }
    finally:
        connection.close()
    expected_entities = len(graph.get("entities", []))
    expected_files = len([entity for entity in graph.get("entities", []) if entity.get("kind") == "file"])
    expected_relations = len(graph.get("links", []))
    from .reference_documents import reference_machine_records
    from .research_gaps import gap_machine_records

    reference_records = reference_machine_records(output)
    gap_records = gap_machine_records(output)
    if integrity != "ok": errors.append({"reason": "sqlite-integrity", "detail": integrity})
    if foreign_keys: errors.append({"reason": "foreign-key-errors", "detail": foreign_keys})
    for name, actual, expected in (
        ("entities", counts["entities"], expected_entities),
        ("source_ranges", counts["source_ranges"], expected_entities),
        ("reviews", counts["reviews"], expected_entities),
        ("human_projection", counts["human_projection"], expected_entities),
        ("files", counts["files"], expected_files),
        ("relations", counts["relations"], expected_relations),
        ("entity_fts", fts_counts["entity_fts"], expected_entities),
        ("source_fts", fts_counts["source_fts"], expected_files),
    ):
        if actual != expected:
            errors.append({"reason": f"{name}-count-mismatch", "actual": actual, "expected": expected})
    if fts_counts["section_fts"] != counts["sections"]:
        errors.append({"reason": "section-fts-count-mismatch", "actual": fts_counts["section_fts"], "expected": counts["sections"]})
    if counts["reference_sources"] != len(reference_records["sources"]):
        errors.append({"reason": "reference-source-count-mismatch", "actual": counts["reference_sources"], "expected": len(reference_records["sources"])})
    if counts["research_gaps"] != len(gap_records["records"]):
        errors.append({"reason": "research-gap-count-mismatch", "actual": counts["research_gaps"], "expected": len(gap_records["records"])})
    reference_documents = counts["documents"] - expected_entities - len(_note_documents(_human_projection(output)[1])) - len(gap_records["documents"])
    if reference_documents != len(reference_records["documents"]):
        errors.append({"reason": "reference-document-count-mismatch", "actual": reference_documents, "expected": len(reference_records["documents"])})
    if language_errors:
        errors.append({"reason": "chinese-description-contract", "entities": language_errors})
    if meta.get("schema_version") != str(MACHINE_SCHEMA_VERSION) or meta.get("status") != "ready":
        errors.append({"reason": "machine-meta-incompatible", "meta": meta})
    result = {
        "schema_version": MACHINE_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "path": str(path.resolve()),
        "integrity": integrity,
        "counts": counts,
        "fts_counts": fts_counts,
        "language_contract": meta.get("language_contract"),
        "retrieval": meta.get("retrieval"),
        "errors": errors,
    }
    json_write(output / "machine/audit.json", result)
    return result


def _adjacency(connection: sqlite3.Connection) -> tuple[dict[str, list[tuple[str, float, str]]], dict[str, int]]:
    adjacency: dict[str, list[tuple[str, float, str]]] = defaultdict(list)
    degree: dict[str, int] = defaultdict(int)
    for source, target, relation, weight in connection.execute("SELECT source_entity_id,target_entity_id,relation,weight FROM relations ORDER BY relation_id"):
        adjacency[source].append((target, float(weight), relation))
        adjacency[target].append((source, float(weight) * 0.72, relation))
        degree[source] += 1
        degree[target] += 1
    for values in adjacency.values():
        values.sort(key=lambda item: (item[0], item[2]))
    return adjacency, degree


def _fast_graph_scores(
    seeds: list[str],
    seed_scores: dict[str, float],
    adjacency: dict[str, list[tuple[str, float, str]]],
    degree: dict[str, int],
) -> dict[str, float]:
    result: dict[str, float] = defaultdict(float)
    frontier = {seed: seed_scores[seed] for seed in seeds}
    for depth in (1, 2):
        next_frontier: dict[str, float] = defaultdict(float)
        for source in sorted(frontier):
            source_score = frontier[source]
            outgoing = adjacency.get(source, [])
            total = sum(weight for _target, weight, _relation in outgoing) or 1.0
            for target, weight, _relation in outgoing:
                contribution = source_score * (0.28 if depth == 1 else 0.10) * weight / total / math.sqrt(max(1, degree.get(target, 1)))
                if contribution > next_frontier[target]:
                    next_frontier[target] = contribution
                result[target] += contribution
        frontier = next_frontier
    return dict(result)


def _deterministic_ppr(
    seeds: list[str],
    seed_scores: dict[str, float],
    adjacency: dict[str, list[tuple[str, float, str]]],
    degree: dict[str, int],
    iterations: int = 24,
    restart: float = 0.22,
) -> dict[str, float]:
    if not seeds:
        return {}
    total_seed = sum(max(seed_scores[value], 0.0) for value in seeds) or float(len(seeds))
    personalization = {value: max(seed_scores[value], 0.0) / total_seed for value in seeds}
    scores = dict(personalization)
    for _ in range(iterations):
        updated: dict[str, float] = defaultdict(float)
        dangling = 0.0
        for source in sorted(scores):
            source_score = scores[source]
            outgoing = adjacency.get(source, [])
            if not outgoing:
                dangling += source_score
                continue
            normalized = [
                (target, weight / math.sqrt(max(1, degree.get(target, 1))))
                for target, weight, _relation in outgoing
            ]
            total = sum(weight for _target, weight in normalized) or 1.0
            for target, weight in normalized:
                updated[target] += (1.0 - restart) * source_score * weight / total
        for seed, probability in personalization.items():
            updated[seed] += restart * probability + (1.0 - restart) * dangling * probability
        scores = {key: updated[key] for key in sorted(updated)}
    return scores


def _next_pack_path(output: Path) -> tuple[Path, Path]:
    directory = output / "machine/agent-packs"
    directory.mkdir(parents=True, exist_ok=True)
    prefix = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    for counter in range(1, 1000):
        markdown = directory / f"pack-{prefix}-{counter:02d}.md"
        record = markdown.with_suffix(".json")
        if not markdown.exists() and not record.exists():
            return markdown, record
    raise CkbError("machine pack name space is exhausted")


def _sql_placeholders(values: Iterable[Any]) -> str:
    items = list(values)
    if not items:
        raise CkbError("SQL placeholder list must not be empty")
    return ",".join("?" for _ in items)


def _utf8_prefix(value: str, maximum_bytes: int) -> str:
    if maximum_bytes <= 0:
        return ""
    data = value.encode("utf-8")[:maximum_bytes]
    while data:
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            data = data[: exc.start]
    return ""


def _bulk_entity_context(
    connection: sqlite3.Connection,
    entity_ids: list[str],
) -> tuple[dict[str, sqlite3.Row], dict[str, list[sqlite3.Row]]]:
    if not entity_ids:
        return {}, {}
    placeholders = _sql_placeholders(entity_ids)
    entity_rows = {
        row["entity_id"]: row
        for row in connection.execute(
            f"SELECT e.*,r.start_line,r.end_line,h.title AS human_title,h.page_file,h.display_mode "
            f"FROM entities e JOIN source_ranges r USING(entity_id) LEFT JOIN human_projection h USING(entity_id) "
            f"WHERE e.entity_id IN ({placeholders})",
            entity_ids,
        )
    }
    sections: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in connection.execute(
        f"SELECT d.source_entity_id,s.* FROM sections s JOIN documents d ON d.document_id=s.document_id "
        f"WHERE d.source_entity_id IN ({placeholders}) ORDER BY d.source_entity_id,s.ordinal",
        entity_ids,
    ):
        sections[row["source_entity_id"]].append(row)
    return entity_rows, sections


def _diverse_candidates(
    ordered_ids: list[str],
    entity_rows: dict[str, sqlite3.Row],
    limit: int,
) -> list[str]:
    selected: list[str] = []
    selected_set: set[str] = set()
    paths: set[str] = set()
    for entity_id in ordered_ids:
        row = entity_rows.get(entity_id)
        if row is None or row["source_path"] in paths:
            continue
        selected.append(entity_id)
        selected_set.add(entity_id)
        paths.add(row["source_path"])
        if len(selected) >= limit:
            return selected
    for entity_id in ordered_ids:
        if entity_id in selected_set or entity_id not in entity_rows:
            continue
        selected.append(entity_id)
        if len(selected) >= limit:
            break
    return selected


def _compact_entity_block(
    entity: sqlite3.Row,
    sections: list[sqlite3.Row],
    section_scores: dict[str, float],
    reason_values: list[str],
    source_link: str,
    allocation_bytes: int,
    profile: str,
) -> tuple[str, list[str]]:
    unique_reasons = list(dict.fromkeys(reason_values))[:4]
    reason_text = "；".join(unique_reasons)
    lines = [
        f"## {entity['qualified_name']}",
        "",
        f"选择原因：{reason_text}",
        "",
        f"源码：{source_link}",
        "",
    ]
    if entity["human_title"]:
        lines.extend([f"人类知识页：[[{entity['human_title']}]]（{entity['display_mode']}）", ""])
    mandatory = "\n".join(lines).rstrip() + "\n"
    if len(mandatory.encode("utf-8")) > allocation_bytes:
        short_reason = "；".join(unique_reasons[:2])
        mandatory = (
            f"## {entity['qualified_name']}\n\n"
            f"选择原因：{short_reason}\n\n"
            f"源码：{source_link}\n"
        )
    remaining = max(0, allocation_bytes - len(mandatory.encode("utf-8")) - 2)
    ranked = sorted(
        sections,
        key=lambda row: (-section_scores.get(row["section_id"], 0.0), row["ordinal"]),
    )[: (4 if profile == "fast" else 7)]
    chunks: list[str] = []
    included: list[str] = []
    for section in ranked:
        prefix = f"\n### {section['heading']}\n\n"
        prefix_bytes = len(prefix.encode("utf-8"))
        if prefix_bytes + 12 > remaining:
            break
        content = str(section["content"]).strip()
        available = remaining - prefix_bytes
        if len(content.encode("utf-8")) > available:
            content = _utf8_prefix(content, max(0, available - len("\n\n> 本节已按预算截断。".encode("utf-8")))).rstrip()
            content += "\n\n> 本节已按预算截断。"
        chunk = prefix + content + "\n"
        encoded = len(chunk.encode("utf-8"))
        if encoded > remaining:
            break
        chunks.append(chunk)
        included.append(section["heading"])
        remaining -= encoded
    block = mandatory + "".join(chunks)
    if len(block.encode("utf-8")) > allocation_bytes:
        block = _utf8_prefix(block, allocation_bytes).rstrip() + "\n"
    return block.rstrip() + "\n\n", included


def _static_retrieval_key(database: Path, output: Path) -> str:
    """Return a cheap fingerprint for immutable retrieval data.

    ``retrieve`` already receives normalized output/database paths, so resolving
    them again would add filesystem work to every warm query. Size and mtime
    invalidate a replaced machine database; the opener mtime invalidates cached
    source URIs when the source-view configuration changes.
    """

    openers_path = output / "local-openers.json"
    database_stat = database.stat()
    opener_mtime = openers_path.stat().st_mtime_ns if openers_path.is_file() else 0
    return f"{database.absolute()}:{database_stat.st_size}:{database_stat.st_mtime_ns}:{opener_mtime}"


def _static_retrieval_context(
    connection: sqlite3.Connection,
    output: Path,
    entity_columns: set[str],
    key: str,
) -> dict[str, Any] | None:
    required_columns = {
        "entity_id",
        "kind",
        "name",
        "qualified_name",
        "source_path",
        "meaning_zh",
        "role_zh",
        "change_when_zh",
        "description_zh",
    }
    tables = {
        str(row[0])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    if not required_columns.issubset(entity_columns) or not {"source_ranges", "human_projection", "sections", "documents"}.issubset(tables):
        return None
    metadata_rows = [
        dict(row)
        for row in connection.execute(
            "SELECT entity_id,kind,name,qualified_name,source_path,meaning_zh,role_zh,change_when_zh,description_zh FROM entities"
        )
    ]
    entity_rows = {
        row["entity_id"]: dict(row)
        for row in connection.execute(
            "SELECT e.*,r.start_line,r.end_line,h.title AS human_title,h.page_file,h.display_mode "
            "FROM entities e JOIN source_ranges r USING(entity_id) LEFT JOIN human_projection h USING(entity_id)"
        )
    }
    sections: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in connection.execute(
        "SELECT d.source_entity_id,s.* FROM sections s JOIN documents d ON d.document_id=s.document_id "
        "WHERE d.source_entity_id IS NOT NULL ORDER BY d.source_entity_id,s.ordinal"
    ):
        sections[row["source_entity_id"]].append(dict(row))
    adjacency, degree = _adjacency(connection)
    value = {
        "metadata_rows": metadata_rows,
        "entity_rows": entity_rows,
        "sections": dict(sections),
        "adjacency": adjacency,
        "degree": degree,
        "linker": SourceLinkRenderer(_openers(output), trusted_relative_paths=True),
        "entity_columns": entity_columns,
    }
    _RETRIEVAL_STATIC_CACHE.clear()
    _RETRIEVAL_STATIC_CACHE[key] = value
    return value


def _openers(output: Path) -> dict[str, Any]:
    path = output / "local-openers.json"
    if path.is_file():
        return json_load(path)
    state = json_load(output / "state.json")
    return {
        "source_editor": "vscode",
        "working_repo_root": state["repository"]["root"],
        "baseline_snapshot_root": (state.get("source_snapshot") or {}).get("root"),
        "source_view": "working",
        "show_source_range": True,
        "custom_template": None,
    }


def _matching_documents(connection: sqlite3.Connection, fts: str | None, limit: int = 8) -> list[dict[str, Any]]:
    if not fts:
        return []
    tables = {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
    if not {"section_fts", "sections", "documents"}.issubset(tables):
        return []
    rows = connection.execute(
        "SELECT d.document_id,d.title,d.kind,d.human_file,s.heading,s.content,s.source_path,s.start_line,s.end_line,"
        "bm25(section_fts,0.0,0.0,6.0,2.0,1.0) AS rank "
        "FROM section_fts JOIN sections s ON s.section_id=section_fts.section_id "
        "JOIN documents d ON d.document_id=section_fts.document_id "
        "WHERE section_fts MATCH ? AND d.kind<>'entity' ORDER BY rank,d.document_id,s.ordinal LIMIT 80",
        (fts,),
    ).fetchall()
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if row["document_id"] in seen:
            continue
        seen.add(row["document_id"])
        result.append(dict(row))
        if len(result) >= limit:
            break
    return result


def _document_source_link(row: dict[str, Any]) -> str | None:
    source_path = str(row.get("source_path") or "")
    start_line = row.get("start_line")
    if not source_path or not isinstance(start_line, int):
        return None
    path = Path(source_path)
    if not path.is_absolute():
        return None
    uri = f"vscode://file/{quote(path.resolve().as_posix(), safe='/:')}:{start_line}:1"
    end_line = row.get("end_line")
    label = f"原文第 {start_line} 行" if end_line == start_line else f"原文第 {start_line}–{end_line} 行"
    return f"[{label}]({uri})"


def _document_block(row: dict[str, Any], allocation_bytes: int) -> str:
    kind_label = "已审阅参考资料" if row["kind"] == "reference" else "待验证研究缺口" if row["kind"] == "gap" else "已审阅知识记录"
    lines = [f"## {row['title']}", "", f"类型：{kind_label}", ""]
    if row.get("human_file"):
        lines.extend([f"人类知识页：[[{row['title']}]]", ""])
    source_link = _document_source_link(row)
    if source_link:
        lines.extend([f"来源：{source_link}", ""])
    lines.extend([f"### {row['heading']}", "", str(row["content"]).strip(), ""])
    text = "\n".join(lines)
    if len(text.encode("utf-8")) > allocation_bytes:
        suffix = "\n\n> 本节已按预算截断。\n"
        text = _utf8_prefix(text, max(0, allocation_bytes - len(suffix.encode("utf-8")))).rstrip() + suffix
    return text.rstrip() + "\n\n"


def _retrieve_machine_deterministic(
    output: Path,
    question: str,
    budget: int = 1500,
    entity_limit: int = 8,
    profile: str = "fast",
    *,
    extra_terms: Iterable[str] = (),
    extra_anchors: Iterable[str] = (),
    rewrite_queries: Iterable[str] = (),
) -> dict[str, Any]:
    if profile not in {"fast", "precise"}:
        raise CkbError("machine retrieval profile must be fast or precise")
    if budget < 200:
        raise CkbError("retrieve budget must be at least 200")
    path = output / MACHINE_PATH
    if not path.is_file():
        raise CkbError("machine knowledge is missing; run finalize or machine-reindex")
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    scores: dict[str, float] = defaultdict(float)
    breakdown: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    reasons: dict[str, list[str]] = defaultdict(list)
    section_scores: dict[str, float] = {}
    original_terms = search_terms(question)
    original_anchors = explicit_anchors(question)
    extra_term_values = unique_casefold(list(extra_terms))
    extra_anchor_values = unique_casefold([value.casefold() for value in extra_anchors])
    rewrite_values = unique_casefold(list(rewrite_queries))
    terms = unique_casefold([*original_terms, *extra_term_values])
    anchors = unique_casefold([*original_anchors, *extra_anchor_values])
    from .automation import search_automation
    from .feedback import search_feedback

    automation_intent = bool(
        re.search(
            r"(?:会话自动化|会话记录|对话记录|修改记录|实验记录|踩坑记录|待审阅|自动化记录|session|conversation|pending review)",
            question,
            flags=re.IGNORECASE,
        )
    )
    automation_rows = search_automation(output, question, 8) if automation_intent else []
    feedback_intent = bool(
        re.search(
            r"(?:人工反馈|页面反馈|知识纠错|待处理反馈|开放反馈|已解决反馈|audit|feedback)",
            question,
            flags=re.IGNORECASE,
        )
    )
    feedback_rows = search_feedback(output, question, 8) if feedback_intent else []
    document_matches: list[dict[str, Any]] = []

    def add(entity_id: str, value: float, stage: str, reason: str) -> None:
        scores[entity_id] += value
        breakdown[entity_id][stage] += value
        reasons[entity_id].append(reason)

    try:
        exact_rows = connection.execute(
            "SELECT entity_id,name,qualified_name,source_path FROM entities WHERE name=? COLLATE NOCASE OR qualified_name=? COLLATE NOCASE OR source_path=? COLLATE NOCASE",
            (question, question, question),
        ).fetchall()
        for row in exact_rows:
            add(row["entity_id"], 1000.0, "exact", f"精确命中 `{row['qualified_name']}`")
        if anchors:
            placeholders = _sql_placeholders(anchors)
            for row in connection.execute(
                f"SELECT entity_id,name,qualified_name FROM entities "
                f"WHERE name COLLATE NOCASE IN ({placeholders}) OR qualified_name COLLATE NOCASE IN ({placeholders}) "
                "ORDER BY entity_id LIMIT 200",
                [*anchors, *anchors],
            ):
                matched = next(
                    anchor
                    for anchor in anchors
                    if anchor == str(row["name"]).casefold() or anchor == str(row["qualified_name"]).casefold()
                )
                add(row["entity_id"], 500.0, "anchor", f"保留显式标识符 `{matched}`")
        if terms:
            placeholders = _sql_placeholders(terms)
            for row in connection.execute(
                f"SELECT term,entity_id,weight FROM terms WHERE term IN ({placeholders}) ORDER BY term,entity_id",
                terms,
            ):
                add(row["entity_id"], float(row["weight"]), "term", f"确定性词项 `{row['term']}`")
        if extra_term_values or extra_anchor_values or rewrite_values:
            rewrite_terms = search_terms(" ".join(rewrite_values))
            fts = _fts_query_values(
                unique_casefold([*extra_term_values, *extra_anchor_values, *rewrite_terms, *original_terms])
            )
        else:
            fts = _fts_query(question)
        if fts:
            document_matches = _matching_documents(connection, fts, 8)
            for row in connection.execute(
                "SELECT entity_id,bm25(entity_fts,0.0,10.0,9.0,4.0,4.0,3.0,3.0,5.0) AS rank FROM entity_fts WHERE entity_fts MATCH ? ORDER BY rank LIMIT ?",
                (fts, 80 if profile == "fast" else 240),
            ):
                add(row["entity_id"], 120.0 / (1.0 + abs(float(row["rank"]))), "entity-fts", "机器实体全文命中")
            for row in connection.execute(
                "SELECT section_fts.section_id,section_fts.document_id,d.source_entity_id,"
                "bm25(section_fts,0.0,0.0,6.0,2.0,1.0) AS rank "
                "FROM section_fts JOIN documents d ON d.document_id=section_fts.document_id "
                "WHERE section_fts MATCH ? ORDER BY rank LIMIT ?",
                (fts, 100 if profile == "fast" else 320),
            ):
                section_scores[row["section_id"]] = 90.0 / (1.0 + abs(float(row["rank"])))
                if row["source_entity_id"]:
                    add(row["source_entity_id"], section_scores[row["section_id"]], "section-fts", "中文章节全文命中")
            if profile == "precise":
                for row in connection.execute(
                    "SELECT e.entity_id,source_fts.source_path,bm25(source_fts) AS rank "
                    "FROM source_fts JOIN entities e ON e.source_path=source_fts.source_path "
                    "WHERE source_fts MATCH ? ORDER BY rank LIMIT 640",
                    (fts,),
                ):
                    add(row["entity_id"], 24.0 / (1.0 + abs(float(row["rank"]))), "source-fts", "固定源码全文命中")
        static_key = _static_retrieval_key(path, output)
        static_context = _RETRIEVAL_STATIC_CACHE.get(static_key)
        static_cache_hit = static_context is not None
        if static_context is not None:
            entity_columns = static_context["entity_columns"]
        else:
            entity_columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(entities)")}
            static_context = _static_retrieval_context(connection, output, entity_columns, static_key)

        def entity_column(name: str) -> str:
            return name if name in entity_columns else f"'' AS {name}"

        metadata_rows = (
            static_context["metadata_rows"]
            if static_context is not None
            else connection.execute(
                "SELECT "
                + ",".join(
                    entity_column(name)
                    for name in (
                        "entity_id",
                        "kind",
                        "name",
                        "qualified_name",
                        "source_path",
                        "meaning_zh",
                        "role_zh",
                        "change_when_zh",
                        "description_zh",
                    )
                )
                + " FROM entities"
            ).fetchall()
        )
        metadata_by_id = {row["entity_id"]: row for row in metadata_rows}
        high_signal_terms = [
            term.casefold()
            for term in terms
            if len(term) >= 3 or (len(term) >= 2 and re.search(r"[a-z0-9_]", term, flags=re.IGNORECASE))
        ]
        for row in metadata_rows:
            name = str(row["name"]).casefold()
            qualified = str(row["qualified_name"]).casefold()
            source_path = str(row["source_path"]).casefold()
            narrative = " ".join(
                str(row[field] or "").casefold()
                for field in ("meaning_zh", "role_zh", "change_when_zh", "description_zh")
            )
            contribution = 0.0
            for term in high_signal_terms:
                if term == name or term == qualified:
                    contribution += 52.0
                elif term in name or term in qualified:
                    contribution += 30.0
                elif term in source_path:
                    contribution += 22.0
                elif term in narrative:
                    contribution += 12.0 if len(term) >= 4 else 5.0
            if contribution:
                if row["kind"] == "file":
                    contribution += 20.0
                add(row["entity_id"], contribution, "metadata", "文件、标识符和中文职责确定性匹配")
        test_intent = bool(re.search(r"(?:测试|验收|test|fixture|spec)", question, flags=re.IGNORECASE))
        if not test_intent:
            for entity_id in sorted(scores):
                row = metadata_by_id.get(entity_id)
                if row is None:
                    continue
                is_test = str(row["source_path"]).casefold().startswith("tests/") or str(row["name"]).casefold().startswith("test")
                if not is_test or breakdown[entity_id].get("exact") or breakdown[entity_id].get("anchor"):
                    continue
                original = scores[entity_id]
                discounted = original * IMPLEMENTATION_TEST_DISCOUNT
                add(entity_id, discounted - original, "test-discount", "实现定位查询对测试实体应用固定折扣")
        if not scores and not automation_rows and not feedback_rows and not document_matches:
            return {
                "schema_version": MACHINE_SCHEMA_VERSION,
                "status": "needs-source-read",
                "question": question,
                "profile": profile,
                "terms": terms,
                "anchors": anchors,
                "reason": "机器知识库没有来源绑定的候选，请按 scope 或源码路径继续读取。",
            }
        if not scores and (automation_rows or feedback_rows or document_matches):
            pack_path, record_path = _next_pack_path(output)
            pack = (
                f"# Agent 机器知识阅读包\n\n问题：{question}\n\n检索档位：{profile}\n\n"
                "本阅读包只命中工作记录或人工反馈；会话记录仍按状态接受来源审阅，反馈按锚点状态处理。\n\n"
            )
            related = []
            for row in document_matches:
                block = _document_block(row, max(420, budget * 2))
                if estimated_tokens(pack + block) > budget:
                    continue
                pack += block
                related.append(
                    {
                        "document_id": row["document_id"],
                        "title": row["title"],
                        "kind": row["kind"],
                        "status": "agent-reviewed",
                        "human_file": row.get("human_file"),
                        "source_path": row.get("source_path"),
                        "start_line": row.get("start_line"),
                        "end_line": row.get("end_line"),
                    }
                )
            for row in automation_rows:
                paths = "、".join(f"`{path}`" for path in row.get("changed_paths", [])) or "无项目文件变化"
                block = (
                    f"## {row['title']}\n\n"
                    f"状态：{row['status']}\n\n"
                    f"类型：{row['kind']}\n\n"
                    f"修改范围：{paths}\n\n"
                    f"{row['content'].strip()}\n\n"
                )
                if estimated_tokens(pack + block) > budget:
                    continue
                pack += block
                related.append(
                    {
                        "document_id": f"automation:{row['review_id']}",
                        "title": row["title"],
                        "kind": row["kind"],
                        "human_file": row.get("human_file"),
                        "status": row["status"],
                    }
                )
            for row in feedback_rows:
                resolution = f"\n\n处理结果：{row['resolution'].strip()}" if row.get("resolution") else ""
                block = (
                    f"## {row['title']}\n\n"
                    f"状态：{row['status']}\n\n"
                    f"严重程度：{row['severity']}\n\n"
                    f"目标：`{row['target']}`\n\n"
                    f"{row['comment'].strip()}{resolution}\n\n"
                )
                if estimated_tokens(pack + block) > budget:
                    continue
                pack += block
                related.append(
                    {
                        "document_id": f"feedback:{row['feedback_id']}",
                        "title": row["title"],
                        "kind": "feedback",
                        "human_file": row.get("human_file"),
                        "status": row["status"],
                        "severity": row["severity"],
                        "target": row["target"],
                    }
                )
            if not related:
                raise CkbError("retrieve budget is too small for the matching work record or feedback")
            pack_path.write_text(pack.rstrip() + "\n", encoding="utf-8", newline="\n")
            result = {
                "schema_version": MACHINE_SCHEMA_VERSION,
                "status": "passed",
                "question": question,
                "profile": profile,
                "budget": budget,
                "estimated_tokens": estimated_tokens(pack),
                "terms": terms,
                "anchors": anchors,
                "seed_entity_ids": [],
                "selected_entities": [],
                "related_documents": related,
                "pack": str(pack_path.resolve()),
                "record": str(record_path.resolve()),
                "retrieval": "sqlite-reviewed-document-work-record-feedback-deterministic",
                "deterministic": True,
                "source_grounded": any(item["kind"] == "reference" for item in related),
                "pending_agent_review": any(item.get("status") == "pending-agent-review" for item in related),
                "open_feedback": sum(1 for item in related if item["kind"] == "feedback" and item["status"] == "open"),
                "grep_fallback_required": False,
            }
            json_write(record_path, result)
            return result
        lexical_order = sorted(scores, key=lambda entity_id: (-scores[entity_id], entity_id))
        seeds = lexical_order[:5]
        seed_scores = {entity_id: scores[entity_id] for entity_id in seeds}
        if static_context is not None:
            adjacency, degree = static_context["adjacency"], static_context["degree"]
        else:
            adjacency, degree = _adjacency(connection)
        graph_scores = (
            _fast_graph_scores(seeds, seed_scores, adjacency, degree)
            if profile == "fast"
            else _deterministic_ppr(seeds, seed_scores, adjacency, degree)
        )
        maximum_seed = max(seed_scores.values()) or 1.0
        for entity_id, value in sorted(graph_scores.items()):
            contribution = (value if profile == "fast" else value * maximum_seed * 0.55)
            if contribution <= 0:
                continue
            add(entity_id, contribution, "graph", "查询相关种子的确定性图扩展")
        ordered = sorted(scores, key=lambda entity_id: (-scores[entity_id], entity_id))
        overscan_limit = FAST_RETRIEVAL_OVERSCAN if profile == "fast" else PRECISE_RETRIEVAL_OVERSCAN
        overscan_ids = ordered[:overscan_limit]
        if static_context is not None:
            entity_rows = {
                entity_id: static_context["entity_rows"][entity_id]
                for entity_id in overscan_ids
                if entity_id in static_context["entity_rows"]
            }
            sections_by_entity = {
                entity_id: static_context["sections"].get(entity_id, [])
                for entity_id in overscan_ids
            }
        else:
            entity_rows, sections_by_entity = _bulk_entity_context(connection, overscan_ids)
        budgeted_entity_limit = max(1, min(entity_limit, max(1, (budget - 80) // 180)))
        selected_ids = _diverse_candidates(overscan_ids, entity_rows, budgeted_entity_limit)
        pack_path, record_path = _next_pack_path(output)
        pack = f"# Agent 机器知识阅读包\n\n问题：{question}\n\n检索档位：{profile}\n\n所有说明使用简体中文；代码标识符保持源码形式。\n\n"
        included_documents: list[dict[str, Any]] = []
        document_budget = max(480, int(budget * 3 * 0.34))
        for row in document_matches[:3]:
            block = _document_block(row, max(360, document_budget // max(1, min(3, len(document_matches)))))
            if estimated_tokens(pack + block) > budget:
                continue
            pack += block
            included_documents.append(
                {
                    "document_id": row["document_id"],
                    "title": row["title"],
                    "kind": row["kind"],
                    "status": "pending-evidence" if row["kind"] == "gap" else "agent-reviewed",
                    "human_file": row.get("human_file"),
                    "source_path": row.get("source_path"),
                    "start_line": row.get("start_line"),
                    "end_line": row.get("end_line"),
                }
            )
        selected: list[dict[str, Any]] = []
        linker = static_context["linker"] if static_context is not None else SourceLinkRenderer(_openers(output), trusted_relative_paths=True)
        for index, entity_id in enumerate(selected_ids):
            entity = entity_rows[entity_id]
            remaining_bytes = max(0, budget * 3 - len(pack.encode("utf-8")) - 16)
            remaining_slots = max(1, len(selected_ids) - index)
            allocation = max(180, remaining_bytes // remaining_slots)
            source_link = linker.markdown_link(
                entity["source_path"],
                int(entity["start_line"]),
                int(entity["end_line"]),
            )
            block, included_sections = _compact_entity_block(
                entity,
                sections_by_entity.get(entity_id, []),
                section_scores,
                reasons[entity_id],
                source_link,
                allocation,
                profile,
            )
            available = max(0, budget * 3 - len(pack.encode("utf-8")) - 4)
            if len(block.encode("utf-8")) > available:
                block = _utf8_prefix(block, available).rstrip() + "\n"
            pack += block
            selected.append(
                {
                    "entity_id": entity_id,
                    "name": entity["name"],
                    "qualified_name": entity["qualified_name"],
                    "kind": entity["kind"],
                    "source_path": entity["source_path"],
                    "start_line": entity["start_line"],
                    "end_line": entity["end_line"],
                    "human_page_title": entity["human_title"],
                    "human_page_file": entity["page_file"],
                    "display_mode": entity["display_mode"],
                    "score": round(scores[entity_id], 8),
                    "score_breakdown": {key: round(value, 8) for key, value in sorted(breakdown[entity_id].items())},
                    "reasons": list(dict.fromkeys(reasons[entity_id])),
                    "sections": included_sections,
                }
            )
        note_rows = list(included_documents)
        for row in feedback_rows:
            note_rows.append(
                {
                    "document_id": f"feedback:{row['feedback_id']}",
                    "title": row["title"],
                    "kind": "feedback",
                    "human_file": row.get("human_file"),
                    "status": row["status"],
                    "severity": row["severity"],
                    "target": row["target"],
                    "content_excerpt": row["comment"][:240],
                }
            )
            if len(note_rows) >= 8:
                break
        if fts:
            seen_documents: set[str] = {row["document_id"] for row in note_rows}
            for row in connection.execute(
                "SELECT d.document_id,d.title,d.kind,d.human_file,bm25(section_fts,0.0,0.0,6.0,2.0,1.0) AS rank FROM section_fts JOIN documents d ON d.document_id=section_fts.document_id WHERE section_fts MATCH ? AND d.kind<>'entity' ORDER BY rank LIMIT 40",
                (fts,),
            ):
                if len(note_rows) >= 8:
                    break
                if row["document_id"] in seen_documents:
                    continue
                seen_documents.add(row["document_id"])
                note_rows.append({"document_id": row["document_id"], "title": row["title"], "kind": row["kind"], "human_file": row["human_file"]})
                if len(note_rows) >= 8:
                    break
        seen_document_ids = {row["document_id"] for row in note_rows}
        for row in automation_rows:
            if len(note_rows) >= 8:
                break
            document_id = f"automation:{row['review_id']}"
            if document_id in seen_document_ids:
                continue
            note_rows.append(
                {
                    "document_id": document_id,
                    "title": row["title"],
                    "kind": row["kind"],
                    "human_file": row.get("human_file"),
                    "status": row["status"],
                }
            )
            if len(note_rows) >= 8:
                break
    finally:
        connection.close()
    if not selected and not included_documents:
        raise CkbError("retrieve budget is too small for the highest-ranked machine entity or reviewed document")
    pack_path.write_text(pack.rstrip() + "\n", encoding="utf-8", newline="\n")
    result = {
        "schema_version": MACHINE_SCHEMA_VERSION,
        "status": "passed",
        "question": question,
        "profile": profile,
        "budget": budget,
        "estimated_tokens": estimated_tokens(pack),
        "terms": terms,
        "anchors": anchors,
        "seed_entity_ids": seeds,
        "selected_entities": selected,
        "related_documents": note_rows,
        "open_feedback": sum(1 for item in note_rows if item.get("kind") == "feedback" and item.get("status") == "open"),
        "retrieval_stats": {
            "scored_entities": len(scores),
            "overscan_limit": overscan_limit,
            "materialized_candidates": len(overscan_ids),
            "selected_entities": len(selected),
            "budgeted_entity_limit": budgeted_entity_limit,
            "selected_source_paths": len({item["source_path"] for item in selected}),
            "batched_entity_queries": 2,
            "source_link_cache_entries": linker.cache_size,
            "static_cache_hit": static_cache_hit,
        },
        "pack": str(pack_path.resolve()),
        "record": str(record_path.resolve()),
        "retrieval": "sqlite-exact-fts5-sections-deterministic-weighted-graph",
        "deterministic": True,
        "source_grounded": True,
        "grep_fallback_required": False,
    }
    json_write(record_path, result)
    return result


def _provider_record(provider: dict[str, Any]) -> dict[str, Any]:
    return {
        key: provider.get(key)
        for key in (
            "status",
            "failure_type",
            "request_id",
            "provider",
            "model",
            "version",
            "usage",
            "cached_usage",
            "attempts",
            "latency_ms",
            "cache_hit",
            "cache_key",
            "missing_environment",
        )
        if provider.get(key) is not None
    }


def _attach_keyword_fallback(
    output: Path,
    question: str,
    result: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    record_path = write_keyword_fallback_record(output, question, metadata)
    metadata = {**metadata, "record": str(record_path.resolve())}
    result = {**result, "keyword_fallback": metadata, "keyword_fallback_record": str(record_path.resolve())}
    retrieval_record = result.get("record")
    if isinstance(retrieval_record, str) and Path(retrieval_record).is_file():
        persisted = json_load(Path(retrieval_record))
        if isinstance(persisted, dict):
            persisted["keyword_fallback"] = metadata
            persisted["keyword_fallback_record"] = str(record_path.resolve())
            json_write(Path(retrieval_record), persisted)
    return result


def retrieve_machine(
    output: Path,
    question: str,
    budget: int = 1500,
    entity_limit: int = 8,
    profile: str = "fast",
    *,
    keyword_fallback: KeywordFallbackOptions | None = None,
) -> dict[str, Any]:
    """Run deterministic retrieval and, only when explicit, one keyword fallback."""

    original = _retrieve_machine_deterministic(output, question, budget, entity_limit, profile)
    if keyword_fallback is None:
        return original
    trigger = "forced" if keyword_fallback.force else "needs-source-read"
    if original.get("status") != "needs-source-read" and not keyword_fallback.force:
        metadata = {
            "schema_version": 1,
            "status": "skipped",
            "trigger": trigger,
            "original": {
                "status": original.get("status"),
                "terms": original.get("terms", []),
                "anchors": original.get("anchors", []),
            },
            "provider": {
                "status": "not-started",
                "provider": keyword_fallback.config.provider,
                "model": keyword_fallback.config.model,
                "version": keyword_fallback.config.version,
            },
            "model_candidates": {"keywords": [], "anchors": [], "rewrites": []},
            "validated_extensions": {"terms": [], "anchors": [], "rewrites": []},
            "final": {"status": original.get("status"), "deterministic_selection": True},
        }
        return _attach_keyword_fallback(output, question, original, metadata)
    provider = run_keyword_provider(
        output,
        question,
        keyword_fallback.config,
        use_cache=keyword_fallback.use_cache,
    )
    original_terms = list(original.get("terms") or search_terms(question))
    original_anchors = list(original.get("anchors") or explicit_anchors(question))
    candidates = {
        "keywords": list(provider.get("keywords") or []),
        "anchors": list(provider.get("anchors") or []),
        "rewrites": list(provider.get("rewrites") or []),
    }
    extension_terms = unique_casefold(
        [
            term
            for value in [*candidates["keywords"], *candidates["rewrites"]]
            for term in search_terms(value)
        ]
    )
    original_term_ids = {value.casefold() for value in original_terms}
    extension_terms = [value for value in extension_terms if value.casefold() not in original_term_ids]
    original_anchor_ids = {value.casefold() for value in original_anchors}
    extension_anchors = [
        value.casefold()
        for value in unique_casefold(candidates["anchors"])
        if value.casefold() not in original_anchor_ids
    ]
    extensions = {
        "terms": extension_terms,
        "anchors": extension_anchors,
        "rewrites": candidates["rewrites"],
    }
    if provider.get("status") != "passed" or not any(extensions.values()):
        provider_record = _provider_record(provider)
        if provider.get("status") == "passed":
            provider_record = {**provider_record, "status": "failed", "failure_type": "invalid-output"}
        metadata = {
            "schema_version": 1,
            "status": "fallback",
            "trigger": trigger,
            "original": {"status": original.get("status"), "terms": original_terms, "anchors": original_anchors},
            "provider": provider_record,
            "model_candidates": candidates,
            "validated_extensions": extensions,
            "final": {"status": original.get("status"), "deterministic_selection": True},
        }
        return _attach_keyword_fallback(output, question, original, metadata)
    final = _retrieve_machine_deterministic(
        output,
        question,
        budget,
        entity_limit,
        profile,
        extra_terms=extension_terms,
        extra_anchors=extension_anchors,
        rewrite_queries=candidates["rewrites"],
    )
    metadata = {
        "schema_version": 1,
        "status": "passed" if final.get("status") == "passed" else "no-quality-gain",
        "trigger": trigger,
        "original": {"status": original.get("status"), "terms": original_terms, "anchors": original_anchors},
        "provider": _provider_record(provider),
        "model_candidates": candidates,
        "validated_extensions": extensions,
        "final": {
            "status": final.get("status"),
            "deterministic_selection": True,
            "selected_entities": len(final.get("selected_entities") or []),
            "estimated_tokens": final.get("estimated_tokens"),
        },
    }
    return _attach_keyword_fallback(output, question, final, metadata)


def coverage(output: Path) -> dict[str, Any]:
    audit = audit_machine_knowledge(output)
    path = output / MACHINE_PATH
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        reviewed = connection.execute("SELECT count(*) FROM reviews WHERE status='agent-reviewed'").fetchone()[0]
        chinese = connection.execute(
            "SELECT count(*) FROM entities WHERE (classification='appendix' AND description_zh GLOB '*[一-龥]*') OR (classification<>'appendix' AND meaning_zh GLOB '*[一-龥]*' AND role_zh GLOB '*[一-龥]*' AND change_when_zh GLOB '*[一-龥]*')"
        ).fetchone()[0]
        total = connection.execute("SELECT count(*) FROM entities").fetchone()[0]
    finally:
        connection.close()
    return {
        "schema_version": MACHINE_SCHEMA_VERSION,
        "status": "passed" if audit.get("status") == "passed" and reviewed == total and chinese == total else "failed",
        "entities": total,
        "agent_reviewed": reviewed,
        "chinese_descriptions": chinese,
        "coverage_ratio": 1.0 if total == 0 else chinese / total,
        "audit": audit,
    }


def entity_lookup(output: Path, selector: str) -> dict[str, Any]:
    path = output / MACHINE_PATH
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT e.*,r.start_line,r.end_line,h.title AS human_title,h.page_file,h.display_mode FROM entities e JOIN source_ranges r USING(entity_id) LEFT JOIN human_projection h USING(entity_id) WHERE e.entity_id=? OR e.name=? COLLATE NOCASE OR e.qualified_name=? COLLATE NOCASE ORDER BY e.qualified_name LIMIT 20",
            (selector, selector, selector),
        ).fetchall()
    finally:
        connection.close()
    return {"schema_version": MACHINE_SCHEMA_VERSION, "status": "passed" if rows else "not-found", "selector": selector, "candidates": [dict(row) for row in rows]}


def neighbor_lookup(output: Path, selector: str, depth: int = 1, relation: str | None = None, limit: int = 50) -> dict[str, Any]:
    if depth < 1 or depth > 6:
        raise CkbError("neighbor depth must be in [1, 6]")
    found = entity_lookup(output, selector)
    if len(found["candidates"]) != 1:
        return {**found, "reason": "selector must match exactly one entity"}
    root_id = found["candidates"][0]["entity_id"]
    path = output / MACHINE_PATH
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        visited = {root_id}
        frontier = {root_id}
        rows: list[dict[str, Any]] = []
        for current_depth in range(1, depth + 1):
            next_frontier: set[str] = set()
            for entity_id in sorted(frontier):
                query = "SELECT * FROM relations WHERE (source_entity_id=? OR target_entity_id=?)"
                params: list[Any] = [entity_id, entity_id]
                if relation:
                    query += " AND relation=?"
                    params.append(relation)
                query += " ORDER BY relation_id"
                for row in connection.execute(query, params):
                    target = row["target_entity_id"] if row["source_entity_id"] == entity_id else row["source_entity_id"]
                    entity = connection.execute("SELECT name,qualified_name,source_path FROM entities WHERE entity_id=?", (target,)).fetchone()
                    rows.append({"depth": current_depth, "from": entity_id, "entity_id": target, "relation": row["relation"], "direction": "outgoing" if row["source_entity_id"] == entity_id else "incoming", **dict(entity)})
                    if target not in visited:
                        visited.add(target)
                        next_frontier.add(target)
                    if len(rows) >= limit:
                        break
                if len(rows) >= limit:
                    break
            frontier = next_frontier
            if not frontier or len(rows) >= limit:
                break
    finally:
        connection.close()
    return {"schema_version": MACHINE_SCHEMA_VERSION, "status": "passed", "selector": selector, "root_entity_id": root_id, "depth": depth, "relation": relation, "neighbors": rows}


def source_lookup(output: Path, selector: str, context_lines: int = 3) -> dict[str, Any]:
    found = entity_lookup(output, selector)
    if len(found["candidates"]) != 1:
        return {**found, "reason": "selector must match exactly one entity"}
    entity = found["candidates"][0]
    path = output / MACHINE_PATH
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        row = connection.execute("SELECT source_text FROM files WHERE path=?", (entity["source_path"],)).fetchone()
    finally:
        connection.close()
    if row is None:
        return {"schema_version": MACHINE_SCHEMA_VERSION, "status": "not-found", "selector": selector, "reason": "source file is absent from the fixed snapshot"}
    lines = row[0].splitlines()
    start = max(1, int(entity["start_line"]) - context_lines)
    end = min(len(lines), int(entity["end_line"]) + context_lines)
    excerpt = "\n".join(f"{index:>6}  {lines[index - 1]}" for index in range(start, end + 1))
    return {"schema_version": MACHINE_SCHEMA_VERSION, "status": "passed", "selector": selector, "entity_id": entity["entity_id"], "source_path": entity["source_path"], "start_line": start, "end_line": end, "excerpt": excerpt}


def change_documents(output: Path, kind: str | None = None, limit: int = 20) -> dict[str, Any]:
    path = output / MACHINE_PATH
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        query = "SELECT document_id,kind,title,human_file,token_estimate FROM documents WHERE kind<>'entity'"
        params: list[Any] = []
        if kind:
            query += " AND kind=?"
            params.append(kind)
        query += " ORDER BY document_id DESC LIMIT ?"
        params.append(limit)
        rows = [dict(row) for row in connection.execute(query, params)]
    finally:
        connection.close()
    from .automation import automation_documents

    automated = automation_documents(output, kind, limit)
    combined = rows + automated
    combined.sort(key=lambda item: str(item.get("document_id", "")), reverse=True)
    return {"schema_version": MACHINE_SCHEMA_VERSION, "status": "passed", "kind": kind, "documents": combined[:limit]}


def sync_workspace_changes(output: Path) -> dict[str, Any]:
    path = output / MACHINE_PATH
    overlay = output / "workspace-meta/working-overlay.json"
    if not path.is_file() or not overlay.is_file():
        return {"schema_version": MACHINE_SCHEMA_VERSION, "status": "skipped", "reason": "machine database or working overlay is absent"}
    value = json_load(overlay)
    connection = sqlite3.connect(path)
    try:
        connection.execute("DELETE FROM workspace_changes")
        detail = json.dumps(value, ensure_ascii=False, sort_keys=True)
        for changed in value.get("changed_paths", []):
            connection.execute("INSERT INTO workspace_changes VALUES(?,?,?)", (changed, "changed", detail))
        for untracked in value.get("untracked_paths", []):
            connection.execute("INSERT INTO workspace_changes VALUES(?,?,?)", (untracked, "untracked", detail))
        connection.commit()
    finally:
        connection.close()
    return {"schema_version": MACHINE_SCHEMA_VERSION, "status": "passed", "changed": len(value.get("changed_paths", [])), "untracked": len(value.get("untracked_paths", []))}
