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
    human_page_template_registry_sha256,
    validate_human_page,
)


HUMAN_PAGE_AUTHORING_SCHEMA_VERSION = 1
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
            "人类页面模板合同版本不兼容。",
            actual={"schema_version": schema_version, "contract_version": contract_version},
            expected={
                "schema_version": HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
                "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
            },
        )
    try:
        return get_human_page_template(str(page_type or "")), None
    except CkbError as exc:  # get_human_page_template owns the stable type list.
        return None, _failed(operation, "unknown-page-type", str(exc))


def _field_slot(field: str, field_type: str, purpose: str) -> dict[str, str]:
    return {"field": field, "type": field_type, "purpose": purpose}


def _section_slot(section: SectionContract) -> dict[str, str]:
    value = {"body": ""}
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
        "validation_context": {"key_entities": [], "links": [], "current_facts": []},
        "applicability_boundary": contract.applicability_boundary,
    }
    fields = [
        _field_slot(f"evidence.{field}", "non-empty", "满足页面合同的来源或验证字段。")
        for field in contract.evidence_requirements.required_fields
    ]
    if contract.key_entity_budget.minimum:
        fields.append(
            _field_slot(
                "validation_context.key_entities",
                f"array[{contract.key_entity_budget.minimum}..{contract.key_entity_budget.maximum}]",
                contract.key_entity_budget.counting_rule,
            )
        )
    if contract.source_link_budget.minimum:
        fields.append(
            _field_slot(
                "validation_context.links",
                f"array[{contract.source_link_budget.minimum}..{contract.source_link_budget.maximum}]",
                contract.source_link_budget.counting_rule,
            )
        )

    if mode == "new":
        skeleton["title"] = ""
        skeleton["sections"] = {
            section.section_id: _section_slot(section) for section in contract.required_sections
        }
        fields.insert(0, _field_slot("title", "non-empty-string", "页面唯一一级标题。"))
        fields[1:1] = [
            _field_slot(
                f"sections.{section.section_id}.body",
                "non-empty-markdown",
                section.purpose,
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
                "array[{section_id,current,replacement,source}]",
                "逐项说明要替换的当前段落、替换正文和来源。",
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
        field = f"sections.{required.section_id}.body"
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
) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    if not isinstance(value, Mapping):
        return None, _failed(operation, "field-type-invalid", "章节输入必须是对象。", field=f"sections.{section.section_id}")
    allowed = {"body", "heading"} if section.heading_pattern else {"body"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        return None, _failed(
            operation,
            "unknown-field",
            "章节输入包含未知字段。",
            fields=[f"sections.{section.section_id}.{name}" for name in unknown],
        )
    body = str(value.get("body") or "").strip()
    heading = str(value.get("heading") or section.heading).strip()
    if section.heading_pattern and heading and re.fullmatch(section.heading_pattern, heading) is None:
        return None, _failed(
            operation,
            "heading-pattern-mismatch",
            "动态章节标题不符合冻结合同。",
            field=f"sections.{section.section_id}.heading",
            pattern=section.heading_pattern,
        )
    return {"body": body, "heading": heading}, None


def _render_section(section: SectionContract, value: Mapping[str, str]) -> str:
    return f"{'#' * section.level} {value['heading']}\n\n{value['body']}"


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
    else:
        if contract.key_entity_budget.minimum and not _non_empty(context.get("key_entities")):
            missing.append("validation_context.key_entities")
        if contract.source_link_budget.minimum and not _non_empty(context.get("links")):
            missing.append("validation_context.links")
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


_CONTEXT_FIELDS = {"key_entities", "links", "current_facts"}
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
}
_BUDGET_REASONS = {"key-entity-budget", "source-link-budget"}
_LINK_REASONS = {"link-purpose-missing"}
_CURRENT_FACT_REASONS = {"current-fact-unverified"}


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
    entries = (
        ("links", {"target", "purpose", "kind"}),
        ("current_facts", {"claim", "source", "observed_at"}),
    )
    for field, allowed in entries:
        value = context.get(field, [])
        if not isinstance(value, list):
            continue
        for index, item in enumerate(value):
            if not isinstance(item, Mapping):
                continue
            unknown = sorted(set(item) - allowed)
            if unknown:
                return _failed(
                    operation,
                    "unknown-field",
                    f"validation_context.{field} 条目包含未知字段。",
                    fields=[f"validation_context.{field}[{index}].{name}" for name in unknown],
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
    unclassified = reasons - _STRUCTURE_REASONS - _BUDGET_REASONS - _LINK_REASONS - _CURRENT_FACT_REASONS - {
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
        normalized: dict[str, dict[str, str]] = {}
        for section in contract.required_sections:
            value = sections_value.get(section.section_id)
            if value is None:
                missing.append(f"sections.{section.section_id}.body")
                if section.heading_pattern:
                    missing.append(f"sections.{section.section_id}.heading")
                continue
            item, failure = _normalize_section_input("render", section, value)
            if failure:
                return failure
            assert item is not None
            if not item["body"]:
                missing.append(f"sections.{section.section_id}.body")
            if section.heading_pattern and not item["heading"]:
                missing.append(f"sections.{section.section_id}.heading")
            normalized[section.section_id] = item
        for section in contract.optional_sections:
            if section.section_id not in sections_value:
                continue
            item, failure = _normalize_section_input("render", section, sections_value[section.section_id])
            if failure:
                return failure
            assert item is not None
            if not item["body"]:
                missing.append(f"sections.{section.section_id}.body")
            normalized[section.section_id] = item
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
            if not item["body"]:
                missing.append(f"sections.{section_id}.body")
            additions.append(_render_section(section, item))
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
        normalized_revisions: list[dict[str, str]] = []
        for index, revision in enumerate(revisions):
            if not isinstance(revision, Mapping):
                return _failed(
                    "render",
                    "field-type-invalid",
                    "revisions 条目必须是对象。",
                    field=f"revisions[{index}]",
                )
            unknown = sorted(set(revision) - {"section_id", "current", "replacement", "source"})
            if unknown:
                return _failed(
                    "render",
                    "unknown-field",
                    "revisions 条目包含未知字段。",
                    fields=[f"revisions[{index}].{field}" for field in unknown],
                )
            item = {name: str(revision.get(name) or "").strip() for name in ("section_id", "current", "replacement", "source")}
            for name, value in item.items():
                if not value:
                    missing.append(f"revisions[{index}].{name}")
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
            markdown = markdown.replace(revision["current"], revision["replacement"], 1)
        if not markdown.endswith("\n"):
            markdown += "\n"

    context = payload.get("validation_context")
    assert isinstance(context, Mapping)
    validation = _candidate_validation(
        contract,
        markdown,
        evidence=payload.get("evidence"),
        context=context,
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
    return {
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "markdown": markdown,
        "markdown_sha256": _sha256_text(markdown),
        "mode": mode,
        "operation": "render",
        "page_type": contract.page_type,
        "schema_version": HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
        "source": {"path": str(source), "sha256": source_sha256} if source else None,
        "status": "ready",
        "validation": validation,
    }


_RECORD_TYPES = {"analysis", "change", "pitfall", "experiment", "session"}
_NAVIGATION_TYPES = {"INDEX", "WIKI", "RECORDS", "REFERENCES"}


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
    target, failure = _staging_target(staging_dir, workspace_root)
    if failure:
        return failure
    assert target is not None
    markdown = str(rendered["markdown"])
    markdown_sha256 = str(rendered["markdown_sha256"])
    route = _package_route(str(rendered["page_type"]))
    manifest = {
        "body": {"path": "body.md", "sha256": markdown_sha256},
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "direct_projection_write": False,
        "mode": rendered["mode"],
        "next_entry": route,
        "page_type": rendered["page_type"],
        "registry_sha256": human_page_template_registry_sha256(),
        "schema_version": HUMAN_PAGE_AUTHORING_SCHEMA_VERSION,
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
    return {
        "artifacts": {
            "body": str(target / "body.md"),
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
        "status": "ready",
    }


def load_authoring_input(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, Mapping):
        raise ValueError("page-author input must be a JSON object")
    return value
