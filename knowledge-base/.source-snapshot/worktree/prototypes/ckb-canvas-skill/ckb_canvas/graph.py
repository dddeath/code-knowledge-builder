"""冻结候选选择、稳定 ID、布局、规范字节与 Canvas 验证。"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any
import unicodedata

from scripts.ckb_core.source_links import audit_source_uri

from .contracts import CanvasFailure, SchemaValidationError, validate_instance
from .freeze import FrozenInputs, SourceRange, validate_source_range


@dataclass(frozen=True)
class PageSelection:
    ordinal: int
    relative_path: str
    title: str


@dataclass(frozen=True)
class RecordSelection:
    ordinal: int
    relative_path: str


@dataclass(frozen=True)
class SourceSelection:
    owner_ordinal: int
    owner_page: str
    range: SourceRange
    uri: str


@dataclass(frozen=True)
class SelectedGraph:
    pages: tuple[PageSelection, ...]
    records: tuple[RecordSelection, ...]
    sources: tuple[SourceSelection, ...]


@dataclass(frozen=True)
class ValidationFacts:
    node_count: int
    edge_count: int
    role_counts: dict[str, int]
    backlinks: tuple[dict[str, Any], ...]
    dangling_edges: int = 0
    machine_fields_exposed: int = 0


def canonical_json_bytes(value: Any) -> bytes:
    """返回 UTF-8/NFC/key 排序/紧凑分隔符/单 LF 字节。"""

    def normalize(item: Any) -> Any:
        if isinstance(item, str):
            return unicodedata.normalize("NFC", item)
        if isinstance(item, list):
            return [normalize(value) for value in item]
        if isinstance(item, dict):
            return {unicodedata.normalize("NFC", str(key)): normalize(value) for key, value in item.items()}
        return item

    return (json.dumps(normalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_canvas_bytes(document: dict[str, Any]) -> bytes:
    return canonical_json_bytes(document)


def _safe_relative(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "\\" in value:
        return None
    return pure.as_posix()


def _budget_failure(detail: str, frozen: FrozenInputs) -> CanvasFailure:
    return CanvasFailure("budget_exceeded", "select", detail, target_path=str(frozen.target_canvas))


def select_graph(frozen: FrozenInputs) -> SelectedGraph:
    """按 record ordinal 与冻结配额选择至多 12 节点、16 边。"""

    record = frozen.record
    entities = record["selected_entities"]
    documents = record["related_documents"]
    required = frozen.value["request"]["required_entries"]

    required_page_ordinals: set[int] = set()
    required_source_ordinals: set[int] = set()
    required_record_ordinals: set[int] = set()
    for entry in required:
        ordinal = entry["ordinal"]
        if entry["kind"] == "selected_entity":
            if ordinal >= len(entities):
                raise CanvasFailure(
                    "missing_backlink", "select", f"required selected_entities[{ordinal}] is absent", target_path=str(frozen.target_canvas)
                )
            # 每个 source edge 都必须有 owning page；source 要求隐含 page 回链。
            required_page_ordinals.add(ordinal)
            if entry["require"] in {"source", "page-and-source"}:
                required_source_ordinals.add(ordinal)
        else:
            if ordinal >= len(documents):
                raise CanvasFailure(
                    "missing_backlink", "select", f"required related_documents[{ordinal}] is absent", target_path=str(frozen.target_canvas)
                )
            required_record_ordinals.add(ordinal)

    page_candidates: list[PageSelection] = []
    seen_pages: set[str] = set()
    for ordinal, entity in enumerate(entities):
        relative = _safe_relative(entity.get("human_page_file"))
        if relative and relative in frozen.human_files and relative not in seen_pages:
            seen_pages.add(relative)
            page_candidates.append(
                PageSelection(ordinal, relative, unicodedata.normalize("NFC", str(entity.get("human_page_title") or relative)))
            )
    pages_by_ordinal = {item.ordinal: item for item in page_candidates}
    missing_required_pages = sorted(required_page_ordinals - set(pages_by_ordinal))
    if missing_required_pages:
        raise CanvasFailure(
            "missing_backlink",
            "select",
            f"required entity has no frozen human page: selected_entities[{missing_required_pages[0]}]",
            target_path=str(frozen.target_canvas),
        )
    if len(required_page_ordinals) > 6:
        raise _budget_failure("required page nodes exceed 6", frozen)
    selected_pages = [pages_by_ordinal[index] for index in sorted(required_page_ordinals)]
    selected_page_paths = {item.relative_path for item in selected_pages}
    for item in page_candidates:
        if len(selected_pages) >= 6:
            break
        if item.relative_path not in selected_page_paths:
            selected_pages.append(item)
            selected_page_paths.add(item.relative_path)

    record_candidates: list[RecordSelection] = []
    seen_records: set[str] = set()
    for ordinal, document in enumerate(documents):
        relative = _safe_relative(document.get("human_file"))
        if (
            document.get("status") == "agent-reviewed"
            and relative
            and relative in frozen.human_files
            and relative not in seen_records
        ):
            seen_records.add(relative)
            record_candidates.append(RecordSelection(ordinal, relative))
    records_by_ordinal = {item.ordinal: item for item in record_candidates}
    missing_required_records = sorted(required_record_ordinals - set(records_by_ordinal))
    if missing_required_records:
        raise CanvasFailure(
            "missing_backlink",
            "select",
            f"required record has no reviewed human file: related_documents[{missing_required_records[0]}]",
            target_path=str(frozen.target_canvas),
        )
    if len(required_record_ordinals) > 2:
        raise _budget_failure("required record nodes exceed 2", frozen)
    selected_records = [records_by_ordinal[index] for index in sorted(required_record_ordinals)]
    selected_record_paths = {item.relative_path for item in selected_records}
    for item in record_candidates:
        if len(selected_records) >= 2:
            break
        if item.relative_path not in selected_record_paths:
            selected_records.append(item)
            selected_record_paths.add(item.relative_path)

    source_candidates: list[SourceSelection] = []
    seen_sources: set[tuple[str, int, int]] = set()
    for page in selected_pages:
        entity = entities[page.ordinal]
        relative = _safe_relative(entity.get("source_path"))
        if not relative or relative not in frozen.source_files:
            if page.ordinal in required_source_ordinals:
                raise CanvasFailure(
                    "missing_backlink",
                    "select",
                    f"required source is not frozen: selected_entities[{page.ordinal}]",
                    target_path=str(frozen.target_canvas),
                )
            continue
        start, end = entity.get("start_line"), entity.get("end_line")
        evidence = frozen.source_files[relative]
        try:
            source_range = validate_source_range(
                evidence.path, start, end, kind=str(entity.get("kind") or "entity"), relative_path=relative
            )
        except CanvasFailure as exc:
            exc.operation = "generate"
            exc.target_path = str(frozen.target_canvas)
            raise
        key = (relative, int(start), int(end))
        if key in seen_sources:
            continue
        seen_sources.add(key)
        uri = frozen.renderer.uri(relative, int(start), 1)
        audit_error = audit_source_uri(frozen.openers, uri, relative, int(start))
        if audit_error:
            raise CanvasFailure(
                "invalid_source_range", "select", f"source URI audit failed: {audit_error}", target_path=str(frozen.target_canvas)
            )
        source_candidates.append(SourceSelection(page.ordinal, page.relative_path, source_range, uri))
    sources_by_owner = {item.owner_ordinal: item for item in source_candidates}
    missing_required_sources = sorted(required_source_ordinals - set(sources_by_owner))
    if missing_required_sources:
        raise CanvasFailure(
            "missing_backlink",
            "select",
            f"required entity has no valid source: selected_entities[{missing_required_sources[0]}]",
            target_path=str(frozen.target_canvas),
        )
    if len(required_source_ordinals) > 3:
        raise _budget_failure("required source nodes exceed 3", frozen)
    selected_sources = [item for item in source_candidates if item.owner_ordinal in required_source_ordinals]
    selected_source_keys = {(item.range.relative_path, item.range.start_line, item.range.end_line) for item in selected_sources}
    for item in source_candidates:
        if len(selected_sources) >= 3:
            break
        key = (item.range.relative_path, item.range.start_line, item.range.end_line)
        if key not in selected_source_keys:
            selected_sources.append(item)
            selected_source_keys.add(key)

    node_count = 1 + len(selected_pages) + len(selected_records) + len(selected_sources)
    edge_count = len(selected_pages) + len(selected_records) + len(selected_sources)
    if node_count > 12 or edge_count > 16:
        raise _budget_failure(f"selected graph exceeds budget: {node_count} nodes, {edge_count} edges", frozen)
    return SelectedGraph(tuple(selected_pages), tuple(selected_records), tuple(selected_sources))


def _stable_id(kind: str, *parts: str) -> str:
    payload = (kind + "\0" + "\0".join(parts)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def layout_graph(selected: SelectedGraph, frozen: FrozenInputs) -> dict[str, Any]:
    """用冻结坐标、尺寸和数组次序生成 Canvas 对象。"""

    title = frozen.value["request"]["title"]
    focus_id = _stable_id("node", "focus", f"index:INDEX.md\0title:{title}")
    nodes: list[dict[str, Any]] = [
        {"id": focus_id, "type": "text", "x": 0, "y": 0, "width": 360, "height": 180, "text": f"# {title}\n\n[[INDEX]]"}
    ]
    page_ids: dict[str, str] = {}
    for index, page in enumerate(selected.pages):
        node_id = _stable_id("node", "page", f"file:{page.relative_path}")
        page_ids[page.relative_path] = node_id
        nodes.append(
            {"id": node_id, "type": "file", "x": 480, "y": index * 260, "width": 360, "height": 220, "file": page.relative_path}
        )
    record_ids: dict[str, str] = {}
    for index, record in enumerate(selected.records):
        node_id = _stable_id("node", "record", f"record:{record.relative_path}")
        record_ids[record.relative_path] = node_id
        nodes.append(
            {
                "id": node_id,
                "type": "file",
                "x": 480,
                "y": (len(selected.pages) + index) * 260,
                "width": 360,
                "height": 220,
                "file": record.relative_path,
            }
        )
    source_ids: dict[str, str] = {}
    for index, source in enumerate(selected.sources):
        node_id = _stable_id("node", "source", f"source:{source.uri}")
        source_ids[source.uri] = node_id
        nodes.append(
            {"id": node_id, "type": "link", "x": 960, "y": index * 260, "width": 360, "height": 160, "url": source.uri}
        )

    def edge(source_id: str, label: str, target_id: str) -> dict[str, Any]:
        return {
            "id": _stable_id("edge", source_id, label, target_id),
            "fromNode": source_id,
            "fromSide": "right",
            "fromEnd": "none",
            "toNode": target_id,
            "toSide": "left",
            "toEnd": "arrow",
            "label": label,
        }

    edges: list[dict[str, Any]] = []
    edges.extend(edge(focus_id, "检索命中", page_ids[item.relative_path]) for item in selected.pages)
    edges.extend(edge(focus_id, "相关记录", record_ids[item.relative_path]) for item in selected.records)
    edges.extend(edge(page_ids[item.owner_page], "来源核对", source_ids[item.uri]) for item in selected.sources)
    return {"nodes": nodes, "edges": edges}


FORBIDDEN_KEYS = {
    "entity_id",
    "document_id",
    "score",
    "score_breakdown",
    "terms",
    "anchors",
    "seed_entity_ids",
    "retrieval_stats",
    "token",
    "cache",
    "environment",
    "credential",
    "mcp",
}
FORBIDDEN_TEXT = (
    "entity_id",
    "document_id",
    "score_breakdown",
    "seed_entity_ids",
    "retrieval_stats",
    "depends-on",
    "calls",
    "contains",
)


def _machine_leaks(value: Any) -> int:
    count = 0
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                count += 1
            count += _machine_leaks(item)
    elif isinstance(value, list):
        count += sum(_machine_leaks(item) for item in value)
    elif isinstance(value, str):
        lowered = value.lower()
        count += sum(1 for token in FORBIDDEN_TEXT if token in lowered)
    return count


def validate_canvas(document: dict[str, Any], frozen: FrozenInputs, selected: SelectedGraph) -> ValidationFacts:
    """验证 schema、预算、ID、边闭合、回链、范围与泄露门。"""

    try:
        validate_instance("json-canvas-1.0-ckb-subset.schema.json", document)
    except SchemaValidationError as exc:
        raise CanvasFailure("invalid_canvas", "validate", f"Canvas schema failed: {exc}", target_path=str(frozen.target_canvas)) from exc
    nodes = document["nodes"]
    edges = document["edges"]
    ids = [item["id"] for item in nodes] + [item["id"] for item in edges]
    if len(ids) != len(set(ids)):
        raise CanvasFailure("duplicate_id", "validate", "node or edge stable ID collision", target_path=str(frozen.target_canvas))
    node_ids = {item["id"] for item in nodes}
    dangling = sum(1 for item in edges if item["fromNode"] not in node_ids or item["toNode"] not in node_ids)
    if dangling:
        raise CanvasFailure("dangling_edge", "validate", f"Canvas contains {dangling} dangling edges", target_path=str(frozen.target_canvas))
    role_counts = {
        "text": sum(1 for item in nodes if item["type"] == "text"),
        "page": len(selected.pages),
        "record": len(selected.records),
        "source": len(selected.sources),
    }
    budget = frozen.value["budget"]
    if (
        len(nodes) > budget["max_nodes"]
        or len(edges) > budget["max_edges"]
        or role_counts["text"] > budget["max_text_nodes"]
        or role_counts["page"] > budget["max_page_nodes"]
        or role_counts["record"] > budget["max_record_nodes"]
        or role_counts["source"] > budget["max_source_nodes"]
    ):
        raise CanvasFailure("budget_exceeded", "validate", "Canvas exceeds a frozen hard budget", target_path=str(frozen.target_canvas))
    leaks = _machine_leaks(document)
    if leaks:
        raise CanvasFailure("invalid_canvas", "validate", f"Canvas exposes {leaks} forbidden machine fields", target_path=str(frozen.target_canvas))

    backlinks: list[dict[str, Any]] = []
    focus = nodes[0]
    index_evidence = frozen.human_files["INDEX.md"]
    backlinks.append(
        {"node_id": focus["id"], "role": "focus", "record_ref": "request.title", "target": "INDEX.md", "sha256": index_evidence.sha256, "status": "passed"}
    )
    node_by_file = {item.get("file"): item for item in nodes if item["type"] == "file"}
    for page in selected.pages:
        evidence = frozen.human_files.get(page.relative_path)
        if evidence is None or page.relative_path not in node_by_file:
            raise CanvasFailure("missing_backlink", "validate", f"page backlink is missing: {page.relative_path}", target_path=str(frozen.target_canvas))
        backlinks.append(
            {"node_id": node_by_file[page.relative_path]["id"], "role": "page", "record_ref": f"selected_entities[{page.ordinal}]", "target": page.relative_path, "sha256": evidence.sha256, "status": "passed"}
        )
    for record in selected.records:
        evidence = frozen.human_files.get(record.relative_path)
        if evidence is None or record.relative_path not in node_by_file:
            raise CanvasFailure("missing_backlink", "validate", f"record backlink is missing: {record.relative_path}", target_path=str(frozen.target_canvas))
        backlinks.append(
            {"node_id": node_by_file[record.relative_path]["id"], "role": "record", "record_ref": f"related_documents[{record.ordinal}]", "target": record.relative_path, "sha256": evidence.sha256, "status": "passed"}
        )
    node_by_url = {item.get("url"): item for item in nodes if item["type"] == "link"}
    for source in selected.sources:
        evidence = frozen.source_files[source.range.relative_path]
        node = node_by_url.get(source.uri)
        if node is None:
            raise CanvasFailure("missing_backlink", "validate", f"source backlink is missing: {source.uri}", target_path=str(frozen.target_canvas))
        backlinks.append(
            {
                "node_id": node["id"],
                "role": "source",
                "record_ref": f"selected_entities[{source.owner_ordinal}].source_path:{source.range.start_line}-{source.range.end_line}",
                "target": source.uri,
                "sha256": evidence.sha256,
                "status": "passed",
            }
        )
    return ValidationFacts(len(nodes), len(edges), role_counts, tuple(backlinks), 0, 0)
