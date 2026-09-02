"""Deterministic staging guidance for CKB human-readable page contracts.

This module never writes the human/markdown projections or either SQLite
index.  It reads one bounded source draft when supplementing or revising and
renders an in-memory candidate that is immediately checked by the frozen
``human_page_templates`` registry.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import os
import shutil
from typing import Any, Mapping, Sequence

from .common import CkbError
from .human_page_templates import (
    HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
    HumanPageTemplateContract,
    SectionContract,
    get_human_page_template,
    human_page_section_document,
    human_page_template_registry_sha256,
    validate_human_page,
)


HUMAN_PAGE_AUTHORING_SCHEMA_VERSION = 3
HUMAN_PAGE_AUTHORING_MODES = ("new", "supplement", "revise")


_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMON_FIELDS = {
    "schema_version",
    "contract_version",
    "page_type",
    "mode",
    "evidence",
    "validation_context",
    "applicability_boundary",
}
_MODE_FIELDS = {
    "new": _COMMON_FIELDS | {"title", "sections"},
    "supplement": _COMMON_FIELDS | {"source_path", "source_sha256", "sections", "title"},
    "revise": _COMMON_FIELDS | {"source_path", "source_sha256", "revisions"},
}


def _error(reason: str, message: str, **fields: Any) -> dict[str, Any]:
    return {"reason": reason, "message": message, **fields}


def _failed(operation: str, reason: str, message: str, **fields: Any) -> dict[str, Any]:
    return {
        "errors": [_error(reason, message, **fields)],
        "operation": operation,
        "schema_version": HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
        "status": "failed",
    }


def _missing(operation: str, page_type: str, mode: str, fields: Sequence[str]) -> dict[str, Any]:
    return {
        "missing_fields": sorted(set(fields)),
        "mode": mode,
        "operation": operation,
        "page_type": page_type,
        "schema_version": HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
        "status": "missing-fields",
    }


def _contract_result(
    operation: str,
    page_type: object,
    mode: object,
    *,
    contract_version: object = HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    schema_version: object = HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
) -> tuple[HumanPageTemplateContract | None, dict[str, Any] | None]:
    mode_text = str(mode or "").strip()
    if mode_text not in HUMAN_PAGE_AUTHORING_MODES:
        return None, _failed(
            operation,
            "unknown-mode",
            f"未知人类页面编写模式：{mode_text}。",
            available=list(HUMAN_PAGE_AUTHORING_MODES),
        )
    try:
        contract_schema = int(schema_version)
    except (TypeError, ValueError):
        contract_schema = -1
    if (
        contract_schema != HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION
        or str(contract_version) != HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION
    ):
        return None, _failed(
            operation,
            "contract-version-incompatible",
            "人类页面模板合同版本不兼容；旧 1.0.0 输入必须显式按 V3 章节重写。",
            actual={"schema_version": schema_version, "contract_version": contract_version},
            expected={
                "schema_version": HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
                "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
            },
            migration={"from": "1.0.0", "to": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION, "mode": "explicit-rewrite"},
        )
    try:
        return get_human_page_template(str(page_type or "")), None
    except CkbError as exc:  # get_human_page_template owns the stable type list.
        return None, _failed(operation, "unknown-page-type", str(exc))


def _field_slot(field: str, field_type: str, purpose: str) -> dict[str, str]:
    return {"field": field, "type": field_type, "purpose": purpose}


def _section_slot(section: SectionContract) -> dict[str, Any]:
    value: dict[str, Any] = {
        "human_summary": "",
        "key_entities": [],
        "links": [],
        "metrics": [],
        "source_refs": [],
        "machine_evidence_refs": [],
    }
    if section.heading_pattern:
        value["heading"] = ""
    return value


def init_page_author(
    page_type: str,
    mode: str,
    *,
    contract_version: str = HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    schema_version: int = HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Return only the minimum typed fields for one page type and mode."""

    contract, failure = _contract_result(
        "init",
        page_type,
        mode,
        contract_version=contract_version,
        schema_version=schema_version,
    )
    if failure:
        return failure
    assert contract is not None

    skeleton: dict[str, Any] = {
        "schema_version": HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "page_type": contract.page_type,
        "mode": mode,
        "evidence": {field: "" for field in contract.evidence_requirements.required_fields},
        "validation_context": {"sections": {}, "current_facts": []},
        "applicability_boundary": contract.applicability_boundary,
    }
    fields = [
        _field_slot(f"evidence.{field}", "non-empty", "满足页面合同的来源或验证字段。")
        for field in contract.evidence_requirements.required_fields
    ]

    if mode == "new":
        skeleton["title"] = ""
        skeleton["sections"] = {
            section.section_id: _section_slot(section) for section in contract.required_sections
        }
        fields.insert(0, _field_slot("title", "non-empty-string", "页面唯一一级标题。"))
        fields[1:1] = [
            _field_slot(
                f"sections.{section.section_id}.human_summary",
                "non-empty-human-markdown",
                "只填写人类可见摘要；完整命令、日志、哈希、SQLite、manifest、maintain 和回滚探针写入 machine_evidence_refs。",
            )
            for section in contract.required_sections
        ]
        for section in contract.required_sections:
            if section.heading_pattern:
                fields.append(
                    _field_slot(
                        f"sections.{section.section_id}.heading",
                        f"regex:{section.heading_pattern}",
                        "为动态章节提供满足冻结合同的标题。",
                    )
                )
    elif mode == "supplement":
        skeleton.update({"source_path": "", "source_sha256": "", "sections": {}})
        fields[0:0] = [
            _field_slot("source_path", "workspace-relative-path", "只读打开现有草稿或受管页面。"),
            _field_slot("source_sha256", "sha256", "防止 inspect 后目标内容漂移。"),
            _field_slot("sections", "missing-section-map", "只填写 inspect 返回的缺失章节。"),
        ]
    else:
        skeleton.update({"source_path": "", "source_sha256": "", "revisions": []})
        fields[0:0] = [
            _field_slot("source_path", "workspace-relative-path", "只读打开现有草稿或受管页面。"),
            _field_slot("source_sha256", "sha256", "防止 inspect 后目标内容漂移。"),
            _field_slot(
                "revisions",
                "array[{section_id,current,human_summary,source_refs,machine_evidence_refs,key_entities,links,metrics}]",
                "逐项说明要替换的当前段落、人类摘要、来源与不投影的 L4 机器证据引用。",
            ),
        ]

    return {
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "fields": fields,
        "mode": mode,
        "operation": "init",
        "page_type": contract.page_type,
        "registry_sha256": human_page_template_registry_sha256(),
        "schema_version": HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
        "section_constraints": {
            section.section_id: human_page_section_document(section)
            for section in contract.required_sections + contract.optional_sections
        },
        "skeleton": skeleton,
        "status": "ready",
    }


def _resolve_within(path_value: str | Path, workspace_root: str | Path) -> tuple[Path | None, dict[str, Any] | None]:
    root = Path(workspace_root).resolve()
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if candidate != root and root not in candidate.parents:
        return None, _failed(
            "inspect",
            "path-outside-workspace",
            "页面路径越过 workspace_root。",
            path=str(candidate),
            workspace_root=str(root),
        )
    if not candidate.is_file():
        return None, _failed("inspect", "source-not-found", "页面来源不是可读取文件。", path=str(candidate))
    return candidate, None


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _document_sections(markdown: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lines = markdown.splitlines()
    headings: list[dict[str, Any]] = []
    fence: str | None = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in {"```", "~~~"}:
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            continue
        if fence is not None:
            continue
        match = _HEADING_RE.match(line.strip())
        if match:
            headings.append(
                {"level": len(match.group(1)), "text": match.group(2).strip(), "line": index + 1, "index": index}
            )
    sections: list[dict[str, Any]] = []
    for position, heading in enumerate(headings):
        end = len(lines)
        for following in headings[position + 1 :]:
            if int(following["level"]) <= int(heading["level"]):
                end = int(following["index"])
                break
        body = "\n".join(lines[int(heading["index"]) + 1 : end]).strip()
        sections.append({**heading, "body": body, "end_index": end})
    return headings, sections


def _matches(section: SectionContract, heading: Mapping[str, Any]) -> bool:
    if int(heading["level"]) != section.level:
        return False
    text = str(heading["text"])
    if section.heading_pattern:
        return re.fullmatch(section.heading_pattern, text) is not None
    return text == section.heading


def _managed_source(path: Path, workspace_root: Path) -> bool:
    relative = path.resolve().relative_to(workspace_root.resolve())
    return bool({"human", "markdown"} & set(relative.parts)) or path.suffix.casefold() in {
        ".sqlite",
        ".db",
    }


def inspect_page_author(
    page_type: str,
    mode: str,
    source_path: str | Path,
    *,
    workspace_root: str | Path,
    expected_sha256: str | None = None,
    contract_version: str = HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    schema_version: int = HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Read one bounded source and report contract fields without editing it."""

    contract, failure = _contract_result(
        "inspect",
        page_type,
        mode,
        contract_version=contract_version,
        schema_version=schema_version,
    )
    if failure:
        return failure
    assert contract is not None
    source, failure = _resolve_within(source_path, workspace_root)
    if failure:
        return failure
    assert source is not None
    try:
        markdown = source.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return _failed("inspect", "source-unreadable", f"页面来源读取失败：{exc}", path=str(source))
    digest = _sha256_text(markdown)
    if expected_sha256 is not None and expected_sha256.casefold() != digest:
        return _failed(
            "inspect",
            "target-drift",
            "页面来源在 inspect 前后发生漂移。",
            expected_sha256=expected_sha256,
            actual_sha256=digest,
        )

    headings, sections = _document_sections(markdown)
    satisfied: list[str] = []
    missing: list[str] = []
    conflicts: list[dict[str, Any]] = []
    h1 = [heading for heading in headings if heading["level"] == 1]
    if len(h1) == 1:
        satisfied.append("title")
    else:
        missing.append("title")
        conflicts.append({"field": "title", "reason": "title-heading-count", "count": len(h1)})
    for required in contract.required_sections:
        matches = [section for section in sections if _matches(required, section)]
        field = f"sections.{required.section_id}.human_summary"
        if len(matches) == 1 and str(matches[0]["body"]).strip():
            satisfied.append(field)
        else:
            missing.append(field)
        if len(matches) > 1 and not required.repeatable:
            conflicts.append(
                {
                    "field": field,
                    "reason": "duplicate-heading",
                    "lines": [item["line"] for item in matches],
                }
            )
        if len(matches) == 1 and not str(matches[0]["body"]).strip():
            conflicts.append({"field": field, "reason": "section-empty", "line": matches[0]["line"]})

    root = Path(workspace_root).resolve()
    managed = _managed_source(source, root)
    actions = ["render", "validate", "package"]
    return {
        "allowed_actions": actions,
        "conflict_fields": conflicts,
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "managed_page": managed,
        "missing_fields": missing,
        "mode": mode,
        "operation": "inspect",
        "page_type": contract.page_type,
        "satisfied_fields": satisfied,
        "schema_version": HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
        "source": {
            "path": str(source),
            "relative_path": source.relative_to(root).as_posix(),
            "sha256": digest,
        },
        "status": "conflicted" if conflicts else "ready",
    }


def _non_empty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return value is not None


def _validate_top_level(payload: Mapping[str, Any], mode: str) -> dict[str, Any] | None:
    unknown = sorted(set(payload) - _MODE_FIELDS[mode])
    if unknown:
        return _failed(
            "render",
            "unknown-field",
            "schema 化输入包含未知字段。",
            fields=unknown,
        )
    return None


def _section_by_id(contract: HumanPageTemplateContract) -> dict[str, SectionContract]:
    return {section.section_id: section for section in contract.required_sections + contract.optional_sections}


def _normalize_section_input(
    operation: str,
    section: SectionContract,
    value: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not isinstance(value, Mapping):
        return None, _failed(operation, "field-type-invalid", "章节输入必须是对象。", field=f"sections.{section.section_id}")
    allowed = {
        "human_summary",
        "key_entities",
        "links",
        "metrics",
        "source_refs",
        "machine_evidence_refs",
    }
    if section.heading_pattern:
        allowed.add("heading")
    unknown = sorted(set(value) - allowed)
    if unknown:
        return None, _failed(
            operation,
            "unknown-field",
            "章节输入包含未知字段。",
            fields=[f"sections.{section.section_id}.{name}" for name in unknown],
        )
    human_summary = str(value.get("human_summary") or "").strip()
    heading = str(value.get("heading") or section.heading).strip()
    if section.heading_pattern and heading and re.fullmatch(section.heading_pattern, heading) is None:
        return None, _failed(
            operation,
            "heading-pattern-mismatch",
            "动态章节标题不符合冻结合同。",
            field=f"sections.{section.section_id}.heading",
            pattern=section.heading_pattern,
        )
    lists: dict[str, list[Any]] = {}
    for field in ("key_entities", "links", "metrics", "source_refs", "machine_evidence_refs"):
        item = value.get(field, [])
        if not isinstance(item, list):
            return None, _failed(
                operation,
                "field-type-invalid",
                "章节的实体、指标、链接和证据引用字段必须是数组。",
                field=f"sections.{section.section_id}.{field}",
            )
        lists[field] = list(item)
    return {"human_summary": human_summary, "heading": heading, **lists}, None


def _render_section(section: SectionContract, value: Mapping[str, Any]) -> str:
    return f"{'#' * section.level} {value['heading']}\n\n{value['human_summary']}"


def _section_validation_context(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        field: list(value.get(field, []))
        for field in ("key_entities", "links", "metrics", "source_refs", "machine_evidence_refs")
    }


def _canonical_reference(value: Mapping[str, Any]) -> dict[str, str]:
    result = {
        "kind": str(value.get("kind") or "").strip(),
        "purpose": str(value.get("purpose") or "").strip(),
        "target": str(value.get("target") or "").strip(),
    }
    digest = str(value.get("sha256") or "").strip().casefold()
    if digest:
        result["sha256"] = digest
    return result


def _section_evidence_document(
    contract: HumanPageTemplateContract,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    sections_value = context.get("sections", {})
    assert isinstance(sections_value, Mapping)
    sections: list[dict[str, Any]] = []
    for section in contract.required_sections + contract.optional_sections:
        value = sections_value.get(section.section_id)
        if not isinstance(value, Mapping):
            continue
        source_refs = sorted(
            (_canonical_reference(item) for item in value.get("source_refs", []) if isinstance(item, Mapping)),
            key=lambda item: (item["target"], item["kind"], item["purpose"], item.get("sha256", "")),
        )
        machine_refs = sorted(
            (
                _canonical_reference(item)
                for item in value.get("machine_evidence_refs", [])
                if isinstance(item, Mapping)
            ),
            key=lambda item: (item["target"], item["kind"], item["purpose"], item.get("sha256", "")),
        )
        sections.append(
            {
                "disclosure_level": section.disclosure_level,
                "heading": section.heading,
                "machine_evidence_refs": machine_refs,
                "section_id": section.section_id,
                "source_refs": source_refs,
            }
        )
    return {"schema_version": 1, "sections": sections}


def _base_missing_fields(payload: Mapping[str, Any], contract: HumanPageTemplateContract) -> list[str]:
    missing: list[str] = []
    evidence = payload.get("evidence")
    if not isinstance(evidence, Mapping):
        missing.append("evidence")
    else:
        for field in contract.evidence_requirements.required_fields:
            if not _non_empty(evidence.get(field)):
                missing.append(f"evidence.{field}")
    context = payload.get("validation_context")
    if not isinstance(context, Mapping):
        missing.append("validation_context")
    return missing


def _load_source_for_render(
    payload: Mapping[str, Any], workspace_root: str | Path
) -> tuple[Path | None, str | None, dict[str, Any] | None]:
    source_value = payload.get("source_path")
    expected = str(payload.get("source_sha256") or "").casefold()
    missing = []
    if not _non_empty(source_value):
        missing.append("source_path")
    if not _SHA256_RE.fullmatch(expected):
        missing.append("source_sha256")
    if missing:
        return None, None, _missing("render", str(payload.get("page_type") or ""), str(payload.get("mode") or ""), missing)
    source, failure = _resolve_within(str(source_value), workspace_root)
    if failure:
        assert failure is not None
        failure["operation"] = "render"
        return None, None, failure
    assert source is not None
    try:
        markdown = source.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return None, None, _failed("render", "source-unreadable", f"页面来源读取失败：{exc}", path=str(source))
    actual = _sha256_text(markdown)
    if actual != expected:
        return None, None, _failed(
            "render",
            "target-drift",
            "页面来源在 inspect 后发生漂移。",
            expected_sha256=expected,
            actual_sha256=actual,
        )
    return source, markdown, None


_CONTEXT_FIELDS = {"sections", "current_facts"}
_VALIDATE_FIELDS = {
    "schema_version",
    "contract_version",
    "page_type",
    "markdown",
    "evidence",
    "validation_context",
    "applicability_boundary",
}
_STRUCTURE_REASONS = {
    "page-empty",
    "title-heading-count",
    "required-section-missing",
    "duplicate-heading",
    "process-meta-copy",
    "section-empty",
    "empty-section-must-be-omitted",
}
_BUDGET_REASONS = {
    "key-entity-budget",
    "source-link-budget",
    "section-key-entity-budget",
    "section-length-budget",
    "section-link-budget",
}
_LINK_REASONS = {
    "link-purpose-missing",
    "link-context-missing",
    "link-context-unused",
    "link-target-conflict",
    "link-target-duplicate",
    "section-link-target-type",
}
_CURRENT_FACT_REASONS = {"current-fact-unverified"}
_DISCLOSURE_REASONS = {"l4-evidence-leak", "l4-machine-evidence-rendered"}


def _validate_nested_input(
    operation: str,
    contract: HumanPageTemplateContract,
    evidence: Any,
    context: Any,
) -> dict[str, Any] | None:
    if not isinstance(evidence, Mapping):
        return None
    unknown_evidence = sorted(set(evidence) - set(contract.evidence_requirements.required_fields))
    if unknown_evidence:
        return _failed(
            operation,
            "unknown-field",
            "evidence 包含当前页面类型未定义的字段。",
            fields=[f"evidence.{field}" for field in unknown_evidence],
        )
    if not isinstance(context, Mapping):
        return None
    unknown_context = sorted(set(context) - _CONTEXT_FIELDS)
    if unknown_context:
        return _failed(
            operation,
            "unknown-field",
            "validation_context 包含未知字段。",
            fields=[f"validation_context.{field}" for field in unknown_context],
        )
    current_facts = context.get("current_facts", [])
    if isinstance(current_facts, list):
        for index, item in enumerate(current_facts):
            if not isinstance(item, Mapping):
                continue
            unknown = sorted(set(item) - {"claim", "source", "observed_at", "section_id"})
            if unknown:
                return _failed(
                    operation,
                    "unknown-field",
                    "validation_context.current_facts 条目包含未知字段。",
                    fields=[f"validation_context.current_facts[{index}].{name}" for name in unknown],
                )
    sections = context.get("sections", {})
    if isinstance(sections, Mapping):
        section_ids = set(_section_by_id(contract))
        unknown_sections = sorted(set(sections) - section_ids)
        if unknown_sections:
            return _failed(
                operation,
                "unknown-field",
                "validation_context.sections 包含当前页面类型未定义的章节。",
                fields=[f"validation_context.sections.{field}" for field in unknown_sections],
            )
        allowed_section = {"key_entities", "links", "metrics", "source_refs", "machine_evidence_refs"}
        for section_id, value in sections.items():
            if not isinstance(value, Mapping):
                continue
            unknown = sorted(set(value) - allowed_section)
            if unknown:
                return _failed(
                    operation,
                    "unknown-field",
                    "validation_context 章节条目包含未知字段。",
                    fields=[f"validation_context.sections.{section_id}.{name}" for name in unknown],
                )
            for field in ("links", "source_refs", "machine_evidence_refs"):
                entries = value.get(field, [])
                if not isinstance(entries, list):
                    continue
                for index, item in enumerate(entries):
                    if not isinstance(item, Mapping):
                        continue
                    unknown_ref = sorted(set(item) - {"target", "purpose", "kind", "sha256"})
                    if unknown_ref:
                        return _failed(
                            operation,
                            "unknown-field",
                            "章节链接或证据引用包含未知字段。",
                            fields=[
                                f"validation_context.sections.{section_id}.{field}[{index}].{name}"
                                for name in unknown_ref
                            ],
                        )
    return None


def _candidate_validation(
    contract: HumanPageTemplateContract,
    markdown: str,
    *,
    evidence: Any,
    context: Any,
    declared_boundary: Any,
) -> dict[str, Any]:
    missing: list[str] = []
    if not isinstance(evidence, Mapping):
        missing.append("evidence")
        evidence = {}
    for field in contract.evidence_requirements.required_fields:
        if not _non_empty(evidence.get(field)):
            missing.append(f"evidence.{field}")
    if not isinstance(context, Mapping):
        missing.append("validation_context")
        context = {}
    if missing:
        return _missing("validate", contract.page_type, "candidate", missing)

    base = validate_human_page(
        contract.page_type,
        markdown,
        context=context,
        contract_version=HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        schema_version=HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
    )
    errors = list(base.get("errors", []))
    boundary_text = str(declared_boundary or "").strip()
    boundary_status = "passed"
    if boundary_text and boundary_text != contract.applicability_boundary:
        boundary_status = "failed"
        errors.append(
            _error(
                "applicability-boundary-drift",
                "输入适用边界与当前页面合同不一致。",
                expected=contract.applicability_boundary,
                actual=boundary_text,
            )
        )

    reasons = {str(error.get("reason")) for error in errors}

    def status_for(category: set[str]) -> str:
        return "failed" if reasons & category else "passed"

    checks = {
        "structure": {"status": status_for(_STRUCTURE_REASONS)},
        "budget": {
            "status": status_for(_BUDGET_REASONS),
            "key_entity_count": base.get("metrics", {}).get("key_entity_count"),
            "source_link_count": base.get("metrics", {}).get("source_link_count"),
        },
        "links": {"status": status_for(_LINK_REASONS)},
        "disclosure": {"status": status_for(_DISCLOSURE_REASONS)},
        "current_fact_evidence": {
            "status": status_for(_CURRENT_FACT_REASONS),
            "verified_count": base.get("metrics", {}).get("verified_current_fact_count"),
        },
        "contract_evidence": {
            "status": "passed",
            "required_fields": list(contract.evidence_requirements.required_fields),
        },
        "applicability_boundary": {
            "status": boundary_status,
            "value": contract.applicability_boundary,
        },
    }
    unclassified = reasons - _STRUCTURE_REASONS - _BUDGET_REASONS - _LINK_REASONS - _CURRENT_FACT_REASONS - _DISCLOSURE_REASONS - {
        "applicability-boundary-drift"
    }
    if unclassified:
        checks["validation_context"] = {"status": "failed", "reasons": sorted(unclassified)}
    else:
        checks["validation_context"] = {"status": "passed"}
    return {
        "checks": checks,
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "errors": errors,
        "metrics": base.get("metrics", {}),
        "operation": "validate",
        "page_type": contract.page_type,
        "registry_sha256": human_page_template_registry_sha256(),
        "schema_version": HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
    }


def validate_page_author(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate structure, budgets, links, evidence, and boundary in one result."""

    if not isinstance(payload, Mapping):
        return _failed("validate", "input-not-object", "validate 输入必须是 JSON 对象。")
    unknown = sorted(set(payload) - _VALIDATE_FIELDS)
    if unknown:
        return _failed(
            "validate",
            "unknown-field",
            "validate 输入包含未知字段。",
            fields=unknown,
        )
    contract, failure = _contract_result(
        "validate",
        payload.get("page_type"),
        "new",
        contract_version=payload.get("contract_version", HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION),
        schema_version=payload.get("schema_version", HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION),
    )
    if failure:
        return failure
    assert contract is not None
    failure = _validate_nested_input(
        "validate", contract, payload.get("evidence"), payload.get("validation_context")
    )
    if failure:
        return failure
    markdown = payload.get("markdown")
    if not isinstance(markdown, str) or not markdown.strip():
        return _missing("validate", contract.page_type, "candidate", ["markdown"])
    return _candidate_validation(
        contract,
        markdown,
        evidence=payload.get("evidence"),
        context=payload.get("validation_context"),
        declared_boundary=payload.get("applicability_boundary"),
    )


def render_page_author(payload: Mapping[str, Any], *, workspace_root: str | Path = ".") -> dict[str, Any]:
    """Render a complete candidate from schema input and validate it immediately."""

    if not isinstance(payload, Mapping):
        return _failed("render", "input-not-object", "render 输入必须是 JSON 对象。")
    contract, failure = _contract_result(
        "render",
        payload.get("page_type"),
        payload.get("mode"),
        contract_version=payload.get("contract_version", HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION),
        schema_version=payload.get("schema_version", HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION),
    )
    if failure:
        return failure
    assert contract is not None
    mode = str(payload["mode"])
    failure = _validate_top_level(payload, mode)
    if failure:
        return failure
    failure = _validate_nested_input(
        "render", contract, payload.get("evidence"), payload.get("validation_context")
    )
    if failure:
        return failure
    declared_boundary = str(payload.get("applicability_boundary") or "").strip()
    if declared_boundary and declared_boundary != contract.applicability_boundary:
        return _failed(
            "render",
            "target-drift",
            "输入适用边界与当前页面合同不一致。",
            expected=contract.applicability_boundary,
            actual=declared_boundary,
        )

    missing = _base_missing_fields(payload, contract)
    section_contracts = _section_by_id(contract)
    markdown = ""
    source: Path | None = None
    source_sha256: str | None = None
    authored_section_contexts: dict[str, dict[str, Any]] = {}

    if mode == "new":
        title = str(payload.get("title") or "").strip()
        sections_value = payload.get("sections")
        if not title:
            missing.append("title")
        if not isinstance(sections_value, Mapping):
            missing.append("sections")
            sections_value = {}
        unknown_sections = sorted(set(sections_value) - set(section_contracts))
        if unknown_sections:
            return _failed(
                "render",
                "unknown-field",
                "sections 包含当前页面类型未定义的字段。",
                fields=[f"sections.{field}" for field in unknown_sections],
            )
        normalized: dict[str, dict[str, Any]] = {}
        for section in contract.required_sections:
            value = sections_value.get(section.section_id)
            if value is None:
                missing.append(f"sections.{section.section_id}.human_summary")
                if section.heading_pattern:
                    missing.append(f"sections.{section.section_id}.heading")
                continue
            item, failure = _normalize_section_input("render", section, value)
            if failure:
                return failure
            assert item is not None
            if not item["human_summary"]:
                missing.append(f"sections.{section.section_id}.human_summary")
            if section.heading_pattern and not item["heading"]:
                missing.append(f"sections.{section.section_id}.heading")
            normalized[section.section_id] = item
            authored_section_contexts[section.section_id] = _section_validation_context(item)
        for section in contract.optional_sections:
            if section.section_id not in sections_value:
                continue
            item, failure = _normalize_section_input("render", section, sections_value[section.section_id])
            if failure:
                return failure
            assert item is not None
            if not item["human_summary"]:
                missing.append(f"sections.{section.section_id}.human_summary")
            normalized[section.section_id] = item
            authored_section_contexts[section.section_id] = _section_validation_context(item)
        if missing:
            return _missing("render", contract.page_type, mode, missing)
        rendered_sections = [
            _render_section(section, normalized[section.section_id])
            for section in contract.required_sections + contract.optional_sections
            if section.section_id in normalized
        ]
        markdown = f"# {title}\n\n" + "\n\n".join(rendered_sections) + "\n"
    elif mode == "supplement":
        if "title" in payload:
            return _failed(
                "render",
                "duplicate-title",
                "补充模式复用来源页标题，不接收或复制一级标题。",
                field="title",
            )
        source, existing, failure = _load_source_for_render(payload, workspace_root)
        if failure:
            return failure
        assert source is not None and existing is not None
        source_sha256 = _sha256_text(existing)
        sections_value = payload.get("sections")
        if not isinstance(sections_value, Mapping) or not sections_value:
            missing.append("sections")
            sections_value = {}
        unknown_sections = sorted(set(sections_value) - set(section_contracts))
        if unknown_sections:
            return _failed(
                "render",
                "unknown-field",
                "sections 包含当前页面类型未定义的字段。",
                fields=[f"sections.{field}" for field in unknown_sections],
            )
        _headings, existing_sections = _document_sections(existing)
        additions: list[str] = []
        for section_id, value in sections_value.items():
            section = section_contracts[str(section_id)]
            if any(_matches(section, item) for item in existing_sections):
                return _failed(
                    "render",
                    "field-already-satisfied",
                    "补充模式只接收当前页面缺少的章节。",
                    field=f"sections.{section_id}",
                )
            item, failure = _normalize_section_input("render", section, value)
            if failure:
                return failure
            assert item is not None
            if not item["human_summary"]:
                missing.append(f"sections.{section_id}.human_summary")
            additions.append(_render_section(section, item))
            authored_section_contexts[str(section_id)] = _section_validation_context(item)
        if missing:
            return _missing("render", contract.page_type, mode, missing)
        markdown = existing.rstrip() + "\n\n" + "\n\n".join(additions) + "\n"
    else:
        source, existing, failure = _load_source_for_render(payload, workspace_root)
        if failure:
            return failure
        assert source is not None and existing is not None
        source_sha256 = _sha256_text(existing)
        revisions = payload.get("revisions")
        if not isinstance(revisions, list) or not revisions:
            missing.append("revisions")
            revisions = []
        normalized_revisions: list[dict[str, Any]] = []
        for index, revision in enumerate(revisions):
            if not isinstance(revision, Mapping):
                return _failed(
                    "render",
                    "field-type-invalid",
                    "revisions 条目必须是对象。",
                    field=f"revisions[{index}]",
                )
            allowed_revision = {
                "section_id",
                "current",
                "human_summary",
                "key_entities",
                "links",
                "metrics",
                "source_refs",
                "machine_evidence_refs",
            }
            unknown = sorted(set(revision) - allowed_revision)
            if unknown:
                return _failed(
                    "render",
                    "unknown-field",
                    "revisions 条目包含未知字段。",
                    fields=[f"revisions[{index}].{field}" for field in unknown],
                )
            item: dict[str, Any] = {
                name: str(revision.get(name) or "").strip()
                for name in ("section_id", "current", "human_summary")
            }
            for name in ("section_id", "current", "human_summary"):
                if not item[name]:
                    missing.append(f"revisions[{index}].{name}")
            for name in ("key_entities", "links", "metrics", "source_refs", "machine_evidence_refs"):
                value = revision.get(name, [])
                if not isinstance(value, list):
                    return _failed(
                        "render",
                        "field-type-invalid",
                        "revision 的实体、链接、来源和证据引用必须是数组。",
                        field=f"revisions[{index}].{name}",
                    )
                item[name] = list(value)
            if not item["source_refs"]:
                missing.append(f"revisions[{index}].source_refs")
            if item["section_id"] and item["section_id"] not in section_contracts:
                return _failed(
                    "render",
                    "unknown-field",
                    "revision 指向当前页面类型未定义的章节。",
                    field=f"revisions[{index}].section_id",
                )
            normalized_revisions.append(item)
        if missing:
            return _missing("render", contract.page_type, mode, missing)
        markdown = existing
        _headings, existing_sections = _document_sections(existing)
        for index, revision in enumerate(normalized_revisions):
            section = section_contracts[revision["section_id"]]
            matches = [item for item in existing_sections if _matches(section, item)]
            if len(matches) != 1 or revision["current"] not in str(matches[0]["body"]):
                return _failed(
                    "render",
                    "revision-target-missing",
                    "修订目标段落未在指定章节中唯一定位。",
                    field=f"revisions[{index}].current",
                    section_id=revision["section_id"],
                )
            if markdown.count(revision["current"]) != 1:
                return _failed(
                    "render",
                    "revision-target-conflict",
                    "修订目标段落在页面中出现多次。",
                    field=f"revisions[{index}].current",
                )
            markdown = markdown.replace(revision["current"], revision["human_summary"], 1)
            authored_section_contexts[revision["section_id"]] = _section_validation_context(revision)
        if not markdown.endswith("\n"):
            markdown += "\n"

    context = payload.get("validation_context")
    assert isinstance(context, Mapping)
    merged_context = {
        "current_facts": list(context.get("current_facts", [])) if isinstance(context.get("current_facts", []), list) else context.get("current_facts"),
        "sections": dict(context.get("sections", {})) if isinstance(context.get("sections", {}), Mapping) else context.get("sections"),
    }
    if isinstance(merged_context["sections"], dict):
        merged_context["sections"].update(authored_section_contexts)
    validation = _candidate_validation(
        contract,
        markdown,
        evidence=payload.get("evidence"),
        context=merged_context,
        declared_boundary=payload.get("applicability_boundary"),
    )
    if validation["status"] != "passed":
        return {
            "errors": validation["errors"],
            "mode": mode,
            "operation": "render",
            "page_type": contract.page_type,
            "schema_version": HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
            "status": "failed",
            "validation": validation,
        }
    section_evidence = _section_evidence_document(contract, merged_context)
    section_evidence_bytes = (
        json.dumps(section_evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    return {
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "markdown": markdown,
        "markdown_sha256": _sha256_text(markdown),
        "mode": mode,
        "operation": "render",
        "page_type": contract.page_type,
        "schema_version": HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
        "section_evidence": section_evidence,
        "section_evidence_sha256": hashlib.sha256(section_evidence_bytes).hexdigest(),
        "source": {"path": str(source), "sha256": source_sha256} if source else None,
        "status": "ready",
        "validation": validation,
    }


_RECORD_TYPES = {"analysis", "change", "pitfall", "experiment", "session"}
_NAVIGATION_TYPES = {"INDEX", "WIKI", "RECORDS", "REFERENCES"}
_REFERENCE_URI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _package_route(page_type: str) -> dict[str, Any]:
    if page_type in _RECORD_TYPES:
        return {
            "entrypoint": "record",
            "command": [
                "ckb.py",
                "record",
                "--out",
                "OUTPUT",
                "--kind",
                page_type,
                "--title",
                "TITLE",
                "--body",
                "BODY.md",
                "--from-pack",
                "PACK.json",
            ],
        }
    if page_type == "reference":
        return {
            "entrypoint": "reference",
            "command": ["ckb.py", "reference", "review", "--out", "OUTPUT", "--review", "REVIEW.json"],
        }
    if page_type == "feedback":
        return {
            "entrypoint": "feedback",
            "command": [
                "ckb.py",
                "feedback",
                "create",
                "--out",
                "OUTPUT",
                "--target",
                "TARGET",
                "--start-line",
                "START",
                "--end-line",
                "END",
                "--comment",
                "BODY.md",
                "--author",
                "AUTHOR",
            ],
        }
    if page_type == "learning-note":
        return {
            "entrypoint": "learning-note-generator",
            "plugin_command": "Ask about selection and save to daily learning note",
        }
    if page_type == "README":
        return {
            "entrypoint": "README-submit",
            "submission": "提交 BODY.md 供发布包 README 人工审阅；不写生成投影。",
        }
    if page_type in _NAVIGATION_TYPES:
        return {
            "entrypoint": f"{page_type}-generator",
            "command": ["ckb.py", "human-refresh", "--out", "OUTPUT"],
        }
    if page_type == "responsibility":
        return {
            "entrypoint": "responsibility-generator",
            "command": [
                "ckb.py",
                "review-pack",
                "--out",
                "OUTPUT",
                "--pack",
                "PACK_ID",
                "--review",
                "REVIEW.json",
            ],
        }
    raise RuntimeError(f"unrouted human page type: {page_type}")


def _staging_target(
    staging_dir: str | Path, workspace_root: str | Path
) -> tuple[Path | None, dict[str, Any] | None]:
    root = Path(workspace_root).resolve()
    target = Path(staging_dir)
    if not target.is_absolute():
        target = root / target
    target = target.resolve()
    if target == root or root not in target.parents:
        return None, _failed(
            "package",
            "path-outside-workspace",
            "staging 路径必须是 workspace_root 内的新目录。",
            path=str(target),
            workspace_root=str(root),
        )
    relative = target.relative_to(root)
    forbidden = {"human", "markdown", "machine"} & {part.casefold() for part in relative.parts}
    if forbidden or target.suffix.casefold() in {".sqlite", ".db"}:
        return None, _failed(
            "package",
            "managed-target-forbidden",
            "staging 包不得写入 human、markdown、machine 或 SQLite 受管路径。",
            path=str(target),
        )
    if target.exists():
        return None, _failed(
            "package",
            "staging-target-exists",
            "staging 包目录已存在；为避免覆盖，必须使用新目录。",
            path=str(target),
        )
    return target, None


def _portable_section_evidence(
    section_evidence: Mapping[str, Any],
    workspace_root: str | Path,
) -> tuple[dict[str, Any] | None, list[tuple[Path, str, str]], dict[str, Any] | None]:
    root = Path(workspace_root).resolve()
    packaged_sections: list[dict[str, Any]] = []
    copy_plan: list[tuple[Path, str, str]] = []
    for section in section_evidence.get("sections", []):
        if not isinstance(section, Mapping):
            continue
        section_id = str(section.get("section_id") or "")
        packaged_section = {
            "disclosure_level": str(section.get("disclosure_level") or ""),
            "heading": str(section.get("heading") or ""),
            "machine_evidence_refs": [],
            "section_id": section_id,
            "source_refs": [],
        }
        for field in ("source_refs", "machine_evidence_refs"):
            values = section.get(field, [])
            if not isinstance(values, list):
                continue
            for index, item in enumerate(values):
                if not isinstance(item, Mapping):
                    continue
                target = str(item.get("target") or "").strip()
                is_windows_drive = bool(re.match(r"^[A-Za-z]:[\\/]", target))
                if _REFERENCE_URI_RE.match(target) and not is_windows_drive:
                    packaged_section[field].append({**dict(item), "target_basis": "uri"})
                    continue
                candidate = Path(target)
                if not candidate.is_absolute():
                    candidate = root / candidate
                candidate = candidate.resolve()
                if candidate != root and root not in candidate.parents:
                    return None, [], _failed(
                        "package",
                        "reference-target-outside-workspace",
                        "章节来源或机器证据路径越过 workspace_root。",
                        field=f"section_evidence.{section_id}.{field}[{index}]",
                        target=target,
                    )
                if not candidate.is_file():
                    return None, [], _failed(
                        "package",
                        "reference-target-not-found",
                        "章节来源或机器证据路径不是可读取文件。",
                        field=f"section_evidence.{section_id}.{field}[{index}]",
                        target=target,
                    )
                expected = str(item.get("sha256") or "").strip().casefold()
                if not _SHA256_RE.fullmatch(expected):
                    return None, [], _failed(
                        "package",
                        "reference-target-sha256-missing",
                        "文件型来源或机器证据引用必须提供小写 SHA-256。",
                        field=f"section_evidence.{section_id}.{field}[{index}].sha256",
                        target=target,
                    )
                actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
                if actual != expected:
                    return None, [], _failed(
                        "package",
                        "reference-target-drift",
                        "章节来源或机器证据文件与声明 SHA-256 不一致。",
                        field=f"section_evidence.{section_id}.{field}[{index}]",
                        target=target,
                        expected_sha256=expected,
                        actual_sha256=actual,
                    )
                portable_target = Path("evidence") / expected / candidate.name
                portable_value = {
                    **dict(item),
                    "original_target": target,
                    "package_owned": True,
                    "target": portable_target.as_posix(),
                    "target_basis": "manifest-parent",
                }
                packaged_section[field].append(portable_value)
                copy_plan.append((candidate, portable_target.as_posix(), expected))
        for field in ("source_refs", "machine_evidence_refs"):
            packaged_section[field] = sorted(
                packaged_section[field],
                key=lambda item: (
                    str(item.get("target") or ""),
                    str(item.get("kind") or ""),
                    str(item.get("purpose") or ""),
                    str(item.get("sha256") or ""),
                ),
            )
        packaged_sections.append(packaged_section)
    portable = {
        "schema_version": 2,
        "target_resolution": {
            "file_target_basis": "manifest-parent",
            "package_owned_directory": "evidence",
            "uri_target_basis": "uri",
        },
        "sections": packaged_sections,
    }
    unique_plan = {
        (target, digest): (source, target, digest)
        for source, target, digest in copy_plan
    }
    return portable, [unique_plan[key] for key in sorted(unique_plan)], None


def package_page_author(
    payload: Mapping[str, Any],
    staging_dir: str | Path,
    *,
    workspace_root: str | Path = ".",
) -> dict[str, Any]:
    """Write only a validated ``body.md`` and routing ``manifest.json``."""

    rendered = render_page_author(payload, workspace_root=workspace_root)
    if rendered.get("status") != "ready":
        result = dict(rendered)
        result["operation"] = "package"
        return result
    section_evidence = rendered.get("section_evidence", {})
    if not isinstance(section_evidence, Mapping):
        return _failed("package", "section-evidence-invalid", "render 未返回规范化章节证据引用。")
    packaged_section_evidence, copy_plan, failure = _portable_section_evidence(
        section_evidence, workspace_root
    )
    if failure:
        return failure
    assert packaged_section_evidence is not None
    target, failure = _staging_target(staging_dir, workspace_root)
    if failure:
        return failure
    assert target is not None
    markdown = str(rendered["markdown"])
    markdown_sha256 = str(rendered["markdown_sha256"])
    route = _package_route(str(rendered["page_type"]))
    section_evidence_bytes = (
        json.dumps(
            packaged_section_evidence,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    section_evidence_sha256 = hashlib.sha256(section_evidence_bytes).hexdigest()
    evidence_paths = sorted(target_value for _source, target_value, _digest in copy_plan)
    manifest = {
        "body": {"path": "body.md", "sha256": markdown_sha256},
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "direct_projection_write": False,
        "mode": rendered["mode"],
        "next_entry": route,
        "page_type": rendered["page_type"],
        "registry_sha256": human_page_template_registry_sha256(),
        "schema_version": HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
        "package_owned_paths": ["body.md", *evidence_paths, "manifest.json"],
        "section_evidence": packaged_section_evidence,
        "section_evidence_sha256": section_evidence_sha256,
        "source": rendered.get("source"),
        "status": "staged",
        "validation": rendered["validation"],
    }
    body_bytes = markdown.encode("utf-8")
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = target.with_name(f".{target.name}.tmp-{markdown_sha256[:12]}")
    if temporary.exists():
        return _failed(
            "package",
            "staging-temporary-exists",
            "staging 临时目录已存在，未覆盖其内容。",
            path=str(temporary),
        )
    try:
        temporary.mkdir(parents=True)
        (temporary / "body.md").write_bytes(body_bytes)
        for source_path, relative_target, expected_sha256 in copy_plan:
            evidence_target = temporary / relative_target
            evidence_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, evidence_target)
            if hashlib.sha256(evidence_target.read_bytes()).hexdigest() != expected_sha256:
                raise OSError(f"staged evidence hash verification failed: {relative_target}")
        (temporary / "manifest.json").write_bytes(manifest_bytes)
        if hashlib.sha256((temporary / "body.md").read_bytes()).hexdigest() != markdown_sha256:
            raise OSError("staged body hash verification failed")
        os.replace(temporary, target)
    except OSError as exc:
        if temporary.exists():
            shutil.rmtree(temporary)
        return _failed("package", "staging-write-failed", f"staging 包写入失败：{exc}", path=str(target))

    manifest_sha256 = hashlib.sha256((target / "manifest.json").read_bytes()).hexdigest()
    reopened_manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    if reopened_manifest != manifest:
        return _failed("package", "staging-reopen-failed", "staging manifest 重开后内容不一致。")
    for _source_path, relative_target, expected_sha256 in copy_plan:
        reopened_evidence = target / relative_target
        if not reopened_evidence.is_file() or hashlib.sha256(reopened_evidence.read_bytes()).hexdigest() != expected_sha256:
            return _failed(
                "package",
                "staging-evidence-reopen-failed",
                "staging 机器证据副本重开后缺失或哈希不一致。",
                target=relative_target,
            )
    return {
        "artifacts": {
            "body": str(target / "body.md"),
            "evidence": [str(target / value) for value in evidence_paths],
            "manifest": str(target / "manifest.json"),
        },
        "body_sha256": markdown_sha256,
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "manifest_sha256": manifest_sha256,
        "mode": rendered["mode"],
        "next_entry": route,
        "operation": "package",
        "page_type": rendered["page_type"],
        "schema_version": HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
        "section_evidence_sha256": section_evidence_sha256,
        "status": "ready",
    }


def load_authoring_input(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, Mapping):
        raise ValueError("page-author input must be a JSON object")
    return value
