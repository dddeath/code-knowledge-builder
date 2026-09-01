"""Machine-only research gap register with one bounded human navigation entry."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from .common import CkbError, json_load, json_write, path_inside, stable_id, utc_now


GAP_SCHEMA_VERSION = 1
GAP_KINDS = ("insufficient-evidence", "conflicting-sources", "deferred-feedback")
GAP_STATUSES = ("open", "deferred", "resolved")
_RECORD_FIELDS = {
    "schema_version", "gap_id", "kind", "status", "summary_zh", "evidence_paths",
    "created_at_utc", "updated_at_utc", "resolution_zh", "resolution_evidence_paths",
}
_CHINESE = re.compile(r"[\u3400-\u9fff]")


def _root(output: Path) -> Path:
    return output.resolve() / "workspace-meta/gaps"


def _records_root(output: Path) -> Path:
    return _root(output) / "records"


def _narrative(path: Path, label: str) -> str:
    if not path.is_file():
        raise CkbError(f"{label} file does not exist: {path}")
    value = re.sub(r"\s+", " ", path.read_text(encoding="utf-8-sig")).strip()
    if len(value) < 8 or len(value) > 600 or len(_CHINESE.findall(value)) < 4:
        raise CkbError(f"{label} must be one Simplified-Chinese statement between 8 and 600 characters")
    return value


def _evidence(output: Path, values: list[str], label: str) -> list[str]:
    if not values:
        raise CkbError(f"{label} requires at least one evidence path")
    if len(values) > 12:
        raise CkbError(f"{label} accepts at most 12 evidence paths")
    result: set[str] = set()
    for value in values:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = output / candidate
        resolved = candidate.resolve()
        if not resolved.is_file() or not path_inside(resolved, output):
            raise CkbError(f"{label} evidence must be an existing file inside OUTPUT: {value}")
        result.add(resolved.relative_to(output).as_posix())
    return sorted(result)


def _record_path(output: Path, gap_id: str) -> Path:
    return _records_root(output) / f"{gap_id}.json"


def gap_records(output: Path) -> list[dict[str, Any]]:
    root = _records_root(output)
    if not root.is_dir():
        return []
    result = []
    for path in sorted(root.glob("gap-*.json")):
        value = json_load(path)
        if isinstance(value, dict):
            result.append(value)
    return result


def _index_value(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = Counter(str(item.get("status")) for item in records)
    by_kind = Counter(str(item.get("kind")) for item in records)
    return {
        "schema_version": GAP_SCHEMA_VERSION,
        "status": "ready",
        "updated_at_utc": utc_now(),
        "counts": {"total": len(records), **{name: by_status.get(name, 0) for name in GAP_STATUSES}},
        "counts_by_kind": {name: by_kind.get(name, 0) for name in GAP_KINDS},
        "gaps": [
            {
                "gap_id": item["gap_id"], "kind": item["kind"], "status": item["status"],
                "summary_zh": item["summary_zh"], "evidence_count": len(item["evidence_paths"]),
                "updated_at_utc": item["updated_at_utc"],
            }
            for item in records
        ],
    }


def _write_index(output: Path) -> dict[str, Any]:
    value = _index_value(gap_records(output))
    json_write(_root(output) / "index.json", value)
    return value


def gap_navigation_counts(root: Path) -> dict[str, int] | None:
    path = root.parent / "workspace-meta/gaps/index.json"
    if not path.is_file():
        return None
    value = json_load(path)
    counts = value.get("counts") if isinstance(value, dict) else None
    if not isinstance(counts, dict):
        return None
    return {name: int(counts.get(name, 0)) for name in ("total", *GAP_STATUSES)}


def _sync_indexes(output: Path) -> None:
    if (output / "human").is_dir() and (output / "markdown").is_dir():
        from .work_record_index import refresh_work_record_index
        refresh_work_record_index(output)
    if (output / "agent-index.sqlite").is_file():
        from .agent_index import build_agent_index
        build_agent_index(output)
    if (output / "machine/knowledge.sqlite").is_file():
        from .machine_knowledge import build_machine_knowledge
        build_machine_knowledge(output)


def create_gap(output: Path, kind: str, summary_path: Path, evidence_paths: list[str]) -> dict[str, Any]:
    output = output.resolve()
    if not (output / "state.json").is_file():
        raise CkbError(f"CKB output is required: {output}")
    if kind not in GAP_KINDS:
        raise CkbError(f"gap kind must be one of: {list(GAP_KINDS)}")
    summary = _narrative(summary_path.resolve(), "gap summary")
    evidence = _evidence(output, evidence_paths, "gap")
    gap_id = stable_id("gap", kind, summary, *evidence)
    path = _record_path(output, gap_id)
    if path.is_file():
        value = json_load(path)
        return {**value, "idempotent": True, "record": str(path.resolve()), "index": str((_root(output) / "index.json").resolve())}
    stamp = utc_now()
    value = {
        "schema_version": GAP_SCHEMA_VERSION, "gap_id": gap_id, "kind": kind,
        "status": "deferred" if kind == "deferred-feedback" else "open",
        "summary_zh": summary, "evidence_paths": evidence, "created_at_utc": stamp,
        "updated_at_utc": stamp, "resolution_zh": None, "resolution_evidence_paths": [],
    }
    json_write(path, value)
    _write_index(output)
    _sync_indexes(output)
    audit = audit_gap_register(output)
    if audit["status"] != "passed":
        raise CkbError(f"research gap audit failed: {audit['errors'][:10]}")
    return {**value, "idempotent": False, "record": str(path.resolve()), "index": str((_root(output) / "index.json").resolve()), "audit": audit}


def resolve_gap(output: Path, gap_id: str, resolution_path: Path, evidence_paths: list[str]) -> dict[str, Any]:
    output = output.resolve()
    path = _record_path(output, gap_id)
    if not path.is_file():
        raise CkbError(f"research gap does not exist: {gap_id}")
    value = json_load(path)
    if value.get("status") == "resolved":
        raise CkbError(f"research gap is already resolved: {gap_id}")
    value["status"] = "resolved"
    value["resolution_zh"] = _narrative(resolution_path.resolve(), "gap resolution")
    value["resolution_evidence_paths"] = _evidence(output, evidence_paths, "gap resolution")
    value["updated_at_utc"] = utc_now()
    json_write(path, value)
    _write_index(output)
    _sync_indexes(output)
    audit = audit_gap_register(output)
    if audit["status"] != "passed":
        raise CkbError(f"research gap audit failed: {audit['errors'][:10]}")
    return {**value, "record": str(path.resolve()), "index": str((_root(output) / "index.json").resolve()), "audit": audit}


def list_gaps(output: Path, status: str | None = None, kind: str | None = None) -> dict[str, Any]:
    if status is not None and status not in GAP_STATUSES:
        raise CkbError(f"gap status must be one of: {list(GAP_STATUSES)}")
    if kind is not None and kind not in GAP_KINDS:
        raise CkbError(f"gap kind must be one of: {list(GAP_KINDS)}")
    selected = [item for item in gap_records(output.resolve()) if (status is None or item.get("status") == status) and (kind is None or item.get("kind") == kind)]
    return {"schema_version": GAP_SCHEMA_VERSION, "status": "ready", "filters": {"status": status, "kind": kind}, "count": len(selected), "gaps": selected}


def gap_machine_records(output: Path) -> dict[str, Any]:
    records = gap_records(output)
    documents = []
    for item in records:
        status_zh = {"open": "待补证据", "deferred": "暂缓处理", "resolved": "已关闭"}[item["status"]]
        kind_zh = {"insufficient-evidence": "证据不足", "conflicting-sources": "来源冲突", "deferred-feedback": "暂缓反馈"}[item["kind"]]
        lines = [f"状态：{status_zh}", f"类型：{kind_zh}", f"待验证说明：{item['summary_zh']}", "证据路径：" + "；".join(item["evidence_paths"])]
        if item.get("resolution_zh"):
            lines.extend([f"关闭说明：{item['resolution_zh']}", "关闭证据：" + "；".join(item.get("resolution_evidence_paths", []))])
        content = "\n".join(lines)
        documents.append({"document_id": f"gap:{item['gap_id']}", "gap_id": item["gap_id"], "kind": "gap", "title": "研究缺口：" + item["summary_zh"][:80], "tag": "#类型/缺口", "human_file": None, "content": content, "section_heading": "待验证研究缺口" if item["status"] != "resolved" else "已关闭研究缺口", "record": item})
    return {"records": records, "documents": documents}


def _record_errors(output: Path, path: Path, item: dict[str, Any]) -> list[str]:
    if set(item) != _RECORD_FIELDS:
        return [f"{path.name}: fields differ from the fixed gap schema"]
    errors = []
    if item.get("schema_version") != GAP_SCHEMA_VERSION or item.get("kind") not in GAP_KINDS or item.get("status") not in GAP_STATUSES:
        errors.append(f"{path.name}: schema, kind, or status is invalid")
    summary = item.get("summary_zh")
    if not isinstance(summary, str) or len(_CHINESE.findall(summary)) < 4:
        errors.append(f"{path.name}: summary must use Simplified Chinese")
    evidence = item.get("evidence_paths")
    if not isinstance(evidence, list) or not evidence or len(evidence) > 12:
        errors.append(f"{path.name}: evidence_paths must contain one to twelve files")
    else:
        for value in evidence:
            relative = PurePosixPath(str(value))
            if relative.is_absolute() or ".." in relative.parts or not (output / Path(str(value))).is_file():
                errors.append(f"{path.name}: invalid or missing evidence path: {value}")
    expected_id = stable_id("gap", item.get("kind"), item.get("summary_zh"), *(item.get("evidence_paths") or []))
    if item.get("gap_id") != expected_id or path.stem != expected_id:
        errors.append(f"{path.name}: stable gap id mismatch")
    if item.get("status") == "resolved":
        resolution = item.get("resolution_zh")
        resolution_evidence = item.get("resolution_evidence_paths")
        if not isinstance(resolution, str) or len(_CHINESE.findall(resolution)) < 4:
            errors.append(f"{path.name}: resolved gap requires a Chinese resolution")
        if not isinstance(resolution_evidence, list) or not resolution_evidence:
            errors.append(f"{path.name}: resolved gap requires closure evidence")
        else:
            for value in resolution_evidence:
                relative = PurePosixPath(str(value))
                if relative.is_absolute() or ".." in relative.parts or not (output / Path(str(value))).is_file():
                    errors.append(f"{path.name}: invalid or missing closure evidence: {value}")
    elif item.get("resolution_zh") is not None or item.get("resolution_evidence_paths") != []:
        errors.append(f"{path.name}: unresolved gap must not contain resolution fields")
    return errors


def audit_gap_register(output: Path) -> dict[str, Any]:
    output = output.resolve()
    root = _root(output)
    if not root.is_dir():
        return {"schema_version": GAP_SCHEMA_VERSION, "status": "passed", "initialized": False, "counts": {"total": 0, "open": 0, "deferred": 0, "resolved": 0}, "errors": []}
    errors: list[str] = []
    records = gap_records(output)
    for path in sorted(_records_root(output).glob("gap-*.json")):
        item = json_load(path)
        if not isinstance(item, dict):
            errors.append(f"{path.name}: gap record must be an object")
            continue
        errors.extend(_record_errors(output, path, item))
    index_path = root / "index.json"
    index = json_load(index_path) if index_path.is_file() else {}
    if not index_path.is_file():
        errors.append("gap index is missing")
    expected = _index_value(records)
    for key in ("schema_version", "status", "counts", "counts_by_kind", "gaps"):
        if index.get(key) != expected.get(key):
            errors.append(f"gap index mismatch: {key}")
    if (output / "human/gaps").exists() or (output / "markdown/gaps").exists():
        errors.append("research gaps must not create one human page per gap")
    for human_root in (output / "human", output / "markdown"):
        if human_root.is_dir():
            records_page = human_root / "RECORDS.md"
            text = records_page.read_text(encoding="utf-8-sig") if records_page.is_file() else ""
            if text.count("## 研究缺口与待补来源") != 1:
                errors.append(f"single research-gap navigation entry is missing: {records_page}")
    database = output / "machine/knowledge.sqlite"
    if database.is_file():
        import sqlite3
        with sqlite3.connect(database) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "research_gaps" not in tables:
                errors.append("machine knowledge research_gaps table is missing")
            elif connection.execute("SELECT count(*) FROM research_gaps").fetchone()[0] != len(records):
                errors.append("machine gap count mismatch")
    counts = Counter(str(item.get("status")) for item in records)
    return {"schema_version": GAP_SCHEMA_VERSION, "status": "passed" if not errors else "failed", "initialized": True, "counts": {"total": len(records), **{name: counts.get(name, 0) for name in GAP_STATUSES}}, "index": str(index_path.resolve()), "errors": errors}
