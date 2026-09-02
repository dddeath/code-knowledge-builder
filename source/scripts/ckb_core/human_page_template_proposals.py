"""Output-local human page template proposals with deterministic review gates.

The store is deliberately separate from the built-in template registry and the
human-page projection pipeline.  Submitting a document can only create a
pending proposal; later human-audit operations are the sole activation path.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Iterator, Mapping, Sequence

from .common import CkbError, json_load, json_write, stable_id, utc_now
from .human_page_templates import (
    HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    HUMAN_PAGE_TEMPLATE_REGISTRY_ID,
    HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
    human_page_template_registry_document,
    human_page_template_registry_sha256,
    list_human_page_types,
)


TEMPLATE_PROPOSAL_SCHEMA_VERSION = 3
TEMPLATE_PROPOSAL_STORE_DIRECTORY = "human-page-template-proposals"
TEMPLATE_PROPOSAL_STATUSES = ("builtin", "pending", "approved", "rejected", "superseded")
TEMPLATE_PROPOSAL_DECISIONS = ("approve", "reject", "return")

_TOP_LEVEL_FIELDS = {
    "applicability_boundary",
    "budgets",
    "evidence",
    "examples",
    "failure_examples",
    "fields",
    "links",
    "migration_impact",
    "proposer",
    "reader_task",
    "rollback",
    "schema_version",
    "sections",
    "target",
    "template_name",
    "version",
}
_PROPOSER_FIELDS = {"id", "kind"}
_TARGET_FIELDS = {"contract_version", "registry_id", "registry_sha256", "schema_version"}
_FIELD_FIELDS = {"field_id", "label", "purpose", "required", "value_type"}
_SECTION_FIELDS = {
    "allowed_content",
    "disclosure_level",
    "empty_behavior",
    "field_ids",
    "forbidden_content",
    "freshness_rule",
    "heading",
    "key_entity_budget",
    "length_budget",
    "link_budget",
    "purpose",
    "required",
    "required_content",
    "section_id",
    "source_requirements",
}
_BUDGET_FIELDS = {"key_entities", "source_links", "total_characters"}
_COUNT_BUDGET_FIELDS = {"counting_rule", "maximum", "minimum", "overflow_action", "scope"}
_CHARACTER_BUDGET_FIELDS = {"maximum", "overflow_action"}
_SECTION_LENGTH_FIELDS = {
    "counting_rule",
    "maximum_characters",
    "maximum_list_items",
    "maximum_metrics",
    "maximum_paragraphs",
    "minimum_characters",
    "overflow_action",
}
_SECTION_LINK_BUDGET_FIELDS = {"counting_rule", "maximum", "minimum", "overflow_action", "target_types"}
_LINK_FIELDS = {"allow_external", "requirements"}
_EVIDENCE_FIELDS = {"current_fact_rule", "freshness_fields", "required_fields"}
_EXAMPLE_FIELDS = {"content", "expected_result", "name"}
_FAILURE_EXAMPLE_FIELDS = {"content", "expected_errors", "name"}
_MIGRATION_FIELDS = {
    "affected_page_types",
    "compatibility",
    "requires_existing_page_migration",
    "summary",
}
_ROLLBACK_FIELDS = {"preserves_history", "steps", "summary"}
_VALUE_TYPES = {"boolean", "integer", "list", "object", "text"}
_MIGRATION_COMPATIBILITY = {"additive", "incompatible", "migration-required"}
_DISCLOSURE_LEVELS = {"L1", "L2", "L3"}
_EMPTY_BEHAVIORS = {"error", "omit", "explicit-empty"}
_LINK_TARGET_TYPES = {"internal", "external", "source", "experiment", "reference", "work-record"}
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")
_SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_STATUS_ORDER = {value: index for index, value in enumerate(TEMPLATE_PROPOSAL_STATUSES)}


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _store_root(output: Path) -> Path:
    return output.resolve() / "workspace-meta" / TEMPLATE_PROPOSAL_STORE_DIRECTORY


def _validated_output(output: Path) -> Path:
    resolved = output.resolve()
    if not (resolved / "state.json").is_file():
        raise CkbError(f"template proposals require an existing CKB output with state.json: {resolved}")
    return resolved


def _expect_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CkbError(f"template proposal {label} must be one JSON object")
    return dict(value)


def _expect_fields(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    unknown = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unknown:
        raise CkbError(f"template proposal {label} contains unknown fields: {unknown}")
    if missing:
        raise CkbError(f"template proposal {label} is missing required fields: {missing}")


def _text(value: Any, label: str, *, maximum: int = 4000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CkbError(f"template proposal {label} must be non-empty text")
    normalized = value.strip()
    if len(normalized) > maximum or "\x00" in normalized:
        raise CkbError(f"template proposal {label} exceeds its text boundary")
    return normalized


def _string_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        suffix = "a list" if allow_empty else "a non-empty list"
        raise CkbError(f"template proposal {label} must be {suffix} of text values")
    result = [_text(item, f"{label}[{index}]", maximum=1000) for index, item in enumerate(value)]
    if len(result) != len(set(result)):
        raise CkbError(f"template proposal {label} contains duplicate values")
    return result


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise CkbError(f"template proposal {label} must be boolean")
    return value


def _integer(value: Any, label: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise CkbError(f"template proposal {label} must be an integer between {minimum} and {maximum}")
    return value


def _semantic_version(value: Any, label: str = "version") -> str:
    normalized = _text(value, label, maximum=32)
    if not _SEMVER.fullmatch(normalized):
        raise CkbError(f"template proposal {label} must use MAJOR.MINOR.PATCH")
    return normalized


def _semantic_version_key(value: str) -> tuple[int, int, int]:
    matched = _SEMVER.fullmatch(value)
    if matched is None:
        raise CkbError(f"stored template proposal has an invalid version: {value}")
    return tuple(int(part) for part in matched.groups())  # type: ignore[return-value]


def _template_name(value: Any) -> str:
    normalized = _text(value, "template_name", maximum=80)
    if any(character in normalized for character in ("/", "\\", "\r", "\n", "\t")) or normalized in {".", ".."}:
        raise CkbError("template proposal template_name must be one path-independent name")
    builtin = {name.casefold(): name for name in list_human_page_types()}
    conflict = builtin.get(normalized.casefold())
    if conflict is not None:
        raise CkbError(f"template proposal cannot override or weaken builtin template: {conflict}")
    return normalized


def _target_document() -> dict[str, Any]:
    return {
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "registry_id": HUMAN_PAGE_TEMPLATE_REGISTRY_ID,
        "registry_sha256": human_page_template_registry_sha256(),
        "schema_version": HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
    }


def _validate_target(value: Any) -> dict[str, Any]:
    target = _expect_object(value, "target")
    _expect_fields(target, _TARGET_FIELDS, "target")
    expected = _target_document()
    if target != expected:
        raise CkbError(
            "template proposal target drift: expected the current read-only builtin registry "
            f"{expected}, received {target}"
        )
    return expected


def _normalize_count_budget(
    value: Any,
    label: str,
    *,
    allowed_scopes: set[str] | None = None,
) -> dict[str, Any]:
    budget = _expect_object(value, label)
    _expect_fields(budget, _COUNT_BUDGET_FIELDS, label)
    minimum = _integer(budget["minimum"], f"{label}.minimum", minimum=0, maximum=10_000)
    maximum = _integer(budget["maximum"], f"{label}.maximum", minimum=0, maximum=10_000)
    if maximum < minimum:
        raise CkbError(f"template proposal {label}.maximum must be at least minimum")
    scope = _text(budget["scope"], f"{label}.scope", maximum=32)
    allowed_scopes = allowed_scopes or {"entry", "page"}
    if scope not in allowed_scopes:
        raise CkbError(f"template proposal {label}.scope must be one of {sorted(allowed_scopes)}")
    return {
        "counting_rule": _text(budget["counting_rule"], f"{label}.counting_rule"),
        "maximum": maximum,
        "minimum": minimum,
        "overflow_action": _text(budget["overflow_action"], f"{label}.overflow_action"),
        "scope": scope,
    }


def _normalize_section_length_budget(value: Any, label: str) -> dict[str, Any]:
    budget = _expect_object(value, label)
    _expect_fields(budget, _SECTION_LENGTH_FIELDS, label)
    minimum = _integer(budget["minimum_characters"], f"{label}.minimum_characters", minimum=0, maximum=1_000_000)
    maximum = _integer(budget["maximum_characters"], f"{label}.maximum_characters", minimum=1, maximum=1_000_000)
    if maximum < minimum:
        raise CkbError(f"template proposal {label}.maximum_characters must be at least minimum_characters")
    return {
        "counting_rule": _text(budget["counting_rule"], f"{label}.counting_rule"),
        "maximum_characters": maximum,
        "maximum_list_items": _integer(budget["maximum_list_items"], f"{label}.maximum_list_items", minimum=0, maximum=10_000),
        "maximum_metrics": _integer(budget["maximum_metrics"], f"{label}.maximum_metrics", minimum=0, maximum=10_000),
        "maximum_paragraphs": _integer(budget["maximum_paragraphs"], f"{label}.maximum_paragraphs", minimum=0, maximum=10_000),
        "minimum_characters": minimum,
        "overflow_action": _text(budget["overflow_action"], f"{label}.overflow_action"),
    }


def _normalize_section_link_budget(value: Any, label: str) -> dict[str, Any]:
    budget = _expect_object(value, label)
    _expect_fields(budget, _SECTION_LINK_BUDGET_FIELDS, label)
    minimum = _integer(budget["minimum"], f"{label}.minimum", minimum=0, maximum=10_000)
    maximum = _integer(budget["maximum"], f"{label}.maximum", minimum=0, maximum=10_000)
    if maximum < minimum:
        raise CkbError(f"template proposal {label}.maximum must be at least minimum")
    target_types = _string_list(budget["target_types"], f"{label}.target_types")
    unknown = sorted(set(target_types) - _LINK_TARGET_TYPES)
    if unknown:
        raise CkbError(f"template proposal {label}.target_types contains unsupported values: {unknown}")
    return {
        "counting_rule": _text(budget["counting_rule"], f"{label}.counting_rule"),
        "maximum": maximum,
        "minimum": minimum,
        "overflow_action": _text(budget["overflow_action"], f"{label}.overflow_action"),
        "target_types": target_types,
    }


def _normalize_fields(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise CkbError("template proposal fields must be a non-empty list")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        field = _expect_object(item, f"fields[{index}]")
        _expect_fields(field, _FIELD_FIELDS, f"fields[{index}]")
        field_id = _text(field["field_id"], f"fields[{index}].field_id", maximum=64)
        if not _IDENTIFIER.fullmatch(field_id):
            raise CkbError(f"template proposal fields[{index}].field_id has an invalid identifier")
        value_type = _text(field["value_type"], f"fields[{index}].value_type", maximum=16)
        if value_type not in _VALUE_TYPES:
            raise CkbError(f"template proposal fields[{index}].value_type must be one of {sorted(_VALUE_TYPES)}")
        result.append(
            {
                "field_id": field_id,
                "label": _text(field["label"], f"fields[{index}].label", maximum=120),
                "purpose": _text(field["purpose"], f"fields[{index}].purpose"),
                "required": _boolean(field["required"], f"fields[{index}].required"),
                "value_type": value_type,
            }
        )
    identifiers = [item["field_id"] for item in result]
    if len(identifiers) != len({value.casefold() for value in identifiers}):
        raise CkbError("template proposal fields contain duplicate field_id values")
    if not any(item["required"] for item in result):
        raise CkbError("template proposal must retain at least one required field")
    return result


def _normalize_sections(value: Any, field_ids: set[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise CkbError("template proposal sections must be a non-empty list")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        section = _expect_object(item, f"sections[{index}]")
        _expect_fields(section, _SECTION_FIELDS, f"sections[{index}]")
        section_id = _text(section["section_id"], f"sections[{index}].section_id", maximum=64)
        if not _IDENTIFIER.fullmatch(section_id):
            raise CkbError(f"template proposal sections[{index}].section_id has an invalid identifier")
        section_fields = _string_list(section["field_ids"], f"sections[{index}].field_ids")
        unknown = sorted(set(section_fields) - field_ids)
        if unknown:
            raise CkbError(f"template proposal sections[{index}] references unknown fields: {unknown}")
        required = _boolean(section["required"], f"sections[{index}].required")
        disclosure_level = _text(section["disclosure_level"], f"sections[{index}].disclosure_level", maximum=8)
        if disclosure_level not in _DISCLOSURE_LEVELS:
            raise CkbError(f"template proposal sections[{index}].disclosure_level must be L1, L2, or L3")
        empty_behavior = _text(section["empty_behavior"], f"sections[{index}].empty_behavior", maximum=32)
        if empty_behavior not in _EMPTY_BEHAVIORS:
            raise CkbError(f"template proposal sections[{index}].empty_behavior is unsupported")
        if required and empty_behavior == "omit":
            raise CkbError(f"template proposal sections[{index}] required section cannot use empty_behavior=omit")
        if not required and empty_behavior == "error":
            raise CkbError(f"template proposal sections[{index}] optional section cannot use empty_behavior=error")
        result.append(
            {
                "allowed_content": _string_list(section["allowed_content"], f"sections[{index}].allowed_content"),
                "disclosure_level": disclosure_level,
                "empty_behavior": empty_behavior,
                "field_ids": section_fields,
                "forbidden_content": _string_list(section["forbidden_content"], f"sections[{index}].forbidden_content"),
                "freshness_rule": _text(section["freshness_rule"], f"sections[{index}].freshness_rule"),
                "heading": _text(section["heading"], f"sections[{index}].heading", maximum=120),
                "key_entity_budget": _normalize_count_budget(
                    section["key_entity_budget"],
                    f"sections[{index}].key_entity_budget",
                    allowed_scopes={"section"},
                ),
                "length_budget": _normalize_section_length_budget(
                    section["length_budget"], f"sections[{index}].length_budget"
                ),
                "link_budget": _normalize_section_link_budget(
                    section["link_budget"], f"sections[{index}].link_budget"
                ),
                "purpose": _text(section["purpose"], f"sections[{index}].purpose"),
                "required": required,
                "required_content": _string_list(section["required_content"], f"sections[{index}].required_content"),
                "section_id": section_id,
                "source_requirements": _string_list(section["source_requirements"], f"sections[{index}].source_requirements"),
            }
        )
    identifiers = [item["section_id"] for item in result]
    if len(identifiers) != len({value.casefold() for value in identifiers}):
        raise CkbError("template proposal sections contain duplicate section_id values")
    if not any(item["required"] for item in result):
        raise CkbError("template proposal must retain at least one required section")
    referenced = {field_id for item in result for field_id in item["field_ids"]}
    missing = sorted(field_ids - referenced)
    if missing:
        raise CkbError(f"template proposal fields must be owned by at least one section: {missing}")
    return result


def _normalize_examples(value: Any, *, failures: bool) -> list[dict[str, Any]]:
    label = "failure_examples" if failures else "examples"
    expected_fields = _FAILURE_EXAMPLE_FIELDS if failures else _EXAMPLE_FIELDS
    if not isinstance(value, list) or not value:
        raise CkbError(f"template proposal requires at least one {label}")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        example = _expect_object(item, f"{label}[{index}]")
        _expect_fields(example, expected_fields, f"{label}[{index}]")
        normalized: dict[str, Any] = {
            "content": _text(example["content"], f"{label}[{index}].content", maximum=20_000),
            "name": _text(example["name"], f"{label}[{index}].name", maximum=120),
        }
        if failures:
            normalized["expected_errors"] = _string_list(
                example["expected_errors"], f"{label}[{index}].expected_errors"
            )
        else:
            expected_result = _text(example["expected_result"], f"{label}[{index}].expected_result", maximum=32)
            if expected_result != "passed":
                raise CkbError(f"template proposal {label}[{index}].expected_result must be passed")
            normalized["expected_result"] = expected_result
        result.append(normalized)
    names = [item["name"].casefold() for item in result]
    if len(names) != len(set(names)):
        raise CkbError(f"template proposal {label} contains duplicate names")
    return result


def normalize_template_proposal(document: Any) -> dict[str, Any]:
    """Strictly validate and normalize one proposal without network or model use."""

    proposal = _expect_object(document, "document")
    _expect_fields(proposal, _TOP_LEVEL_FIELDS, "document")
    if proposal["schema_version"] != TEMPLATE_PROPOSAL_SCHEMA_VERSION:
        raise CkbError(
            "unsupported template proposal schema_version: "
            f"{proposal['schema_version']}; expected {TEMPLATE_PROPOSAL_SCHEMA_VERSION}; "
            "旧 schema 1 proposal 必须重新执行 template init 并显式补齐 V3 章节合同字段"
        )
    proposer = _expect_object(proposal["proposer"], "proposer")
    _expect_fields(proposer, _PROPOSER_FIELDS, "proposer")
    proposer_kind = _text(proposer["kind"], "proposer.kind", maximum=16)
    if proposer_kind not in {"agent", "human"}:
        raise CkbError("template proposal proposer.kind must be agent or human")
    fields = _normalize_fields(proposal["fields"])
    field_ids = {item["field_id"] for item in fields}
    budgets = _expect_object(proposal["budgets"], "budgets")
    _expect_fields(budgets, _BUDGET_FIELDS, "budgets")
    character_budget = _expect_object(budgets["total_characters"], "budgets.total_characters")
    _expect_fields(character_budget, _CHARACTER_BUDGET_FIELDS, "budgets.total_characters")
    links = _expect_object(proposal["links"], "links")
    _expect_fields(links, _LINK_FIELDS, "links")
    evidence = _expect_object(proposal["evidence"], "evidence")
    _expect_fields(evidence, _EVIDENCE_FIELDS, "evidence")
    migration = _expect_object(proposal["migration_impact"], "migration_impact")
    _expect_fields(migration, _MIGRATION_FIELDS, "migration_impact")
    compatibility = _text(migration["compatibility"], "migration_impact.compatibility", maximum=32)
    if compatibility not in _MIGRATION_COMPATIBILITY:
        raise CkbError(
            "template proposal migration_impact.compatibility must be one of "
            f"{sorted(_MIGRATION_COMPATIBILITY)}"
        )
    affected_page_types = _string_list(
        migration["affected_page_types"], "migration_impact.affected_page_types", allow_empty=True
    )
    requires_migration = _boolean(
        migration["requires_existing_page_migration"],
        "migration_impact.requires_existing_page_migration",
    )
    if requires_migration and not affected_page_types:
        raise CkbError("template proposal requiring migration must name affected_page_types")
    rollback = _expect_object(proposal["rollback"], "rollback")
    _expect_fields(rollback, _ROLLBACK_FIELDS, "rollback")
    if not _boolean(rollback["preserves_history"], "rollback.preserves_history"):
        raise CkbError("template proposal rollback must preserve proposal and audit history")
    normalized = {
        "applicability_boundary": _text(proposal["applicability_boundary"], "applicability_boundary"),
        "budgets": {
            "key_entities": _normalize_count_budget(budgets["key_entities"], "budgets.key_entities"),
            "source_links": _normalize_count_budget(budgets["source_links"], "budgets.source_links"),
            "total_characters": {
                "maximum": _integer(
                    character_budget["maximum"],
                    "budgets.total_characters.maximum",
                    minimum=1,
                    maximum=1_000_000,
                ),
                "overflow_action": _text(
                    character_budget["overflow_action"], "budgets.total_characters.overflow_action"
                ),
            },
        },
        "evidence": {
            "current_fact_rule": _text(evidence["current_fact_rule"], "evidence.current_fact_rule"),
            "freshness_fields": _string_list(evidence["freshness_fields"], "evidence.freshness_fields"),
            "required_fields": _string_list(evidence["required_fields"], "evidence.required_fields"),
        },
        "examples": _normalize_examples(proposal["examples"], failures=False),
        "failure_examples": _normalize_examples(proposal["failure_examples"], failures=True),
        "fields": fields,
        "links": {
            "allow_external": _boolean(links["allow_external"], "links.allow_external"),
            "requirements": _string_list(links["requirements"], "links.requirements"),
        },
        "migration_impact": {
            "affected_page_types": affected_page_types,
            "compatibility": compatibility,
            "requires_existing_page_migration": requires_migration,
            "summary": _text(migration["summary"], "migration_impact.summary"),
        },
        "proposer": {
            "id": _text(proposer["id"], "proposer.id", maximum=200),
            "kind": proposer_kind,
        },
        "reader_task": _text(proposal["reader_task"], "reader_task"),
        "rollback": {
            "preserves_history": True,
            "steps": _string_list(rollback["steps"], "rollback.steps"),
            "summary": _text(rollback["summary"], "rollback.summary"),
        },
        "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
        "sections": _normalize_sections(proposal["sections"], field_ids),
        "target": _validate_target(proposal["target"]),
        "template_name": _template_name(proposal["template_name"]),
        "version": _semantic_version(proposal["version"]),
    }
    return normalized


def template_proposal_skeleton(template_name: str = "output-local-template") -> dict[str, Any]:
    name = template_name.strip() or "output-local-template"
    return {
        "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
        "template_name": name,
        "version": "1.0.0",
        "proposer": {"kind": "agent", "id": "填写提议者身份"},
        "target": _target_document(),
        "reader_task": "填写读者使用本模板要完成的任务。",
        "fields": [
            {
                "field_id": "human_summary",
                "label": "人类摘要",
                "value_type": "text",
                "required": True,
                "purpose": "填写只进入 L1-L3 人类页面的摘要正文。",
            }
        ],
        "sections": [
            {
                "allowed_content": ["结论、直接结果、适用边界和少量描述性链接。"],
                "disclosure_level": "L2",
                "empty_behavior": "error",
                "field_ids": ["human_summary"],
                "forbidden_content": ["完整命令、测试总数、逐门清单、日志、完整哈希、SQLite、manifest、maintain 和回滚探针。"],
                "freshness_rule": "当前、已支持和已测试表述必须绑定机器证据与观察时间。",
                "section_id": "result",
                "heading": "结果",
                "key_entity_budget": {
                    "minimum": 0,
                    "maximum": 3,
                    "scope": "section",
                    "counting_rule": "统计本章节直接点名的关键实体。",
                    "overflow_action": "把实现明细移到职责页或机器记录。",
                },
                "length_budget": {
                    "minimum_characters": 1,
                    "maximum_characters": 600,
                    "maximum_paragraphs": 3,
                    "maximum_list_items": 6,
                    "maximum_metrics": 2,
                    "counting_rule": "统计 human_summary 的字符、段落、列表项和显式指标。",
                    "overflow_action": "保留结论和边界，把完整证据移到机器记录。",
                },
                "link_budget": {
                    "minimum": 0,
                    "maximum": 4,
                    "target_types": ["internal", "source", "experiment", "reference", "work-record"],
                    "counting_rule": "统计带阅读目的的描述性链接。",
                    "overflow_action": "只保留直接支持结论的链接。",
                },
                "required": True,
                "required_content": ["先呈现读者要获得的结果。"],
                "purpose": "先呈现读者要获得的结果。",
                "source_requirements": ["时效性事实必须绑定来源；L4 字面证据只保留引用。"],
            }
        ],
        "budgets": {
            "key_entities": {
                "minimum": 0,
                "maximum": 5,
                "scope": "page",
                "counting_rule": "填写关键实体的确定性计数规则。",
                "overflow_action": "填写超出预算时的固定动作。",
            },
            "source_links": {
                "minimum": 0,
                "maximum": 5,
                "scope": "page",
                "counting_rule": "填写来源链接的确定性计数规则。",
                "overflow_action": "填写超出预算时的固定动作。",
            },
            "total_characters": {
                "maximum": 10000,
                "overflow_action": "删除与读者任务无关的内容。",
            },
        },
        "links": {
            "requirements": ["填写链接目标、用途和存在性要求。"],
            "allow_external": False,
        },
        "evidence": {
            "required_fields": ["填写机器证据字段。"],
            "current_fact_rule": "填写时效性事实如何绑定来源与观察时间。",
            "freshness_fields": ["observed_at"],
        },
        "examples": [
            {"name": "通过样例", "content": "填写完整的合格页面样例。", "expected_result": "passed"}
        ],
        "failure_examples": [
            {
                "name": "失败样例",
                "content": "填写应被拒绝的页面样例。",
                "expected_errors": ["填写稳定失败原因。"],
            }
        ],
        "migration_impact": {
            "summary": "填写对既有页面、索引和调用方的迁移影响；没有迁移也要说明原因。",
            "compatibility": "additive",
            "affected_page_types": [],
            "requires_existing_page_migration": False,
        },
        "applicability_boundary": "填写适用输出、读者和明确排除的边界。",
        "rollback": {
            "summary": "停用扩展并从局部索引移除，不删除提议或审计历史。",
            "steps": ["运行 template rollback 撤销对应 approved extension 的启用状态。"],
            "preserves_history": True,
        },
    }


def write_template_proposal_skeleton(output: Path, target: Path, template_name: str = "output-local-template") -> dict[str, Any]:
    _validated_output(output)
    target = target.resolve()
    if target.exists():
        raise CkbError(f"template proposal skeleton target already exists: {target}")
    skeleton = template_proposal_skeleton(template_name)
    json_write(target, skeleton)
    reopened = json_load(target)
    if reopened != skeleton:
        raise CkbError(f"template proposal skeleton did not reopen with written content: {target}")
    return {
        "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
        "status": "written",
        "proposal": str(target),
        "target": skeleton["target"],
    }


def _store_schema_document() -> dict[str, Any]:
    return {
        "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
        "store_type": "output-local-human-page-template-proposals",
        "builtin_registry": {
            **_target_document(),
            "builtin_count": len(list_human_page_types()),
            "immutable": True,
        },
        "proposal_fields": sorted(_TOP_LEVEL_FIELDS),
        "proposal_statuses": list(TEMPLATE_PROPOSAL_STATUSES),
        "audit_decisions": list(TEMPLATE_PROPOSAL_DECISIONS),
        "audit_constraints": {
            "proposal_initial_status": "pending",
            "approval_reviewer_kind": "human",
            "approval_freezes": ["version", "content_hash", "migration_impact", "rollback"],
            "builtin_override": "forbidden",
            "history_deletion": "forbidden",
            "rollback_scope": "approved-extension-activation-only",
        },
    }


def _validate_store_schema(root: Path) -> dict[str, Any]:
    path = root / "schema.json"
    if not path.is_file():
        raise CkbError(f"template proposal store is missing schema.json: {root}")
    value = json_load(path)
    expected = _store_schema_document()
    if value != expected:
        raise CkbError("template proposal store schema or builtin registry target drifted")
    return value


def _prepare_store(output: Path) -> Path:
    output = _validated_output(output)
    root = _store_root(output)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _initialize_store_locked(root: Path) -> None:
    schema_path = root / "schema.json"
    if not schema_path.exists():
        json_write(schema_path, _store_schema_document())
    _validate_store_schema(root)
    for name in ("proposals", "audits", "rollbacks"):
        (root / name).mkdir(parents=True, exist_ok=True)


@contextmanager
def _store_lock(root: Path, timeout: float = 30.0) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".write-lock"
    deadline = time.monotonic() + timeout
    acquired = False
    while not acquired:
        try:
            lock.mkdir()
            (lock / "owner").write_text(str(os.getpid()), encoding="ascii")
            acquired = True
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise CkbError(f"template proposal store is busy: {lock}")
            time.sleep(0.02)
    try:
        yield
    finally:
        owner = lock / "owner"
        owner.unlink(missing_ok=True)
        try:
            lock.rmdir()
        except FileNotFoundError:
            pass


def _proposal_event_errors(event: Any, path: Path) -> list[str]:
    expected = {
        "content_hash",
        "event_id",
        "event_type",
        "payload",
        "proposal_id",
        "schema_version",
        "sequence",
        "submitted_at_utc",
    }
    if not isinstance(event, dict):
        return [f"proposal event must be an object: {path}"]
    if set(event) != expected:
        return [f"proposal event fields differ from schema: {path}"]
    errors: list[str] = []
    if event.get("schema_version") != TEMPLATE_PROPOSAL_SCHEMA_VERSION or event.get("event_type") != "proposal":
        errors.append(f"proposal event version or type mismatch: {path}")
    if event.get("event_id") != event.get("proposal_id") or path.stem != event.get("proposal_id"):
        errors.append(f"proposal event identifier mismatch: {path}")
    if not isinstance(event.get("sequence"), int) or event["sequence"] < 1:
        errors.append(f"proposal event sequence is invalid: {path}")
    try:
        normalized = normalize_template_proposal(event.get("payload"))
    except CkbError as exc:
        errors.append(f"proposal payload is invalid at {path}: {exc}")
    else:
        digest = _sha256(normalized)
        expected_id = stable_id("template-proposal", digest)
        if event.get("content_hash") != digest or event.get("proposal_id") != expected_id:
            errors.append(f"proposal content hash or stable identifier mismatch: {path}")
    return errors


def _reviewer(value: Any, label: str) -> dict[str, str]:
    reviewer = _expect_object(value, label)
    _expect_fields(reviewer, {"id", "kind"}, label)
    kind = _text(reviewer["kind"], f"{label}.kind", maximum=16)
    if kind != "human":
        raise CkbError("template audit and rollback require reviewer.kind=human")
    return {"id": _text(reviewer["id"], f"{label}.id", maximum=200), "kind": "human"}


def _audit_event_errors(event: Any, path: Path) -> list[str]:
    expected = {
        "audit_id",
        "audited_at_utc",
        "conclusion",
        "decision",
        "event_id",
        "event_type",
        "frozen_activation",
        "proposal_id",
        "reviewed_content_hash",
        "reviewed_version",
        "reviewer",
        "schema_version",
        "sequence",
        "superseded_proposal_ids",
        "target",
    }
    if not isinstance(event, dict):
        return [f"audit event must be an object: {path}"]
    if set(event) != expected:
        return [f"audit event fields differ from schema: {path}"]
    errors: list[str] = []
    if event.get("schema_version") != TEMPLATE_PROPOSAL_SCHEMA_VERSION or event.get("event_type") != "audit":
        errors.append(f"audit event version or type mismatch: {path}")
    if event.get("event_id") != event.get("audit_id") or path.stem != event.get("audit_id"):
        errors.append(f"audit event identifier mismatch: {path}")
    if not isinstance(event.get("sequence"), int) or event["sequence"] < 1:
        errors.append(f"audit event sequence is invalid: {path}")
    decision = event.get("decision")
    if decision not in TEMPLATE_PROPOSAL_DECISIONS:
        errors.append(f"audit event decision is invalid: {path}")
    try:
        reviewer = _reviewer(event.get("reviewer"), "stored reviewer")
        conclusion = _text(event.get("conclusion"), "stored conclusion")
        version = _semantic_version(event.get("reviewed_version"), "stored reviewed_version")
        target = _validate_target(event.get("target"))
    except CkbError as exc:
        errors.append(f"audit event content is invalid at {path}: {exc}")
        reviewer = {"id": "", "kind": "human"}
        conclusion = ""
        version = "0.0.0"
        target = {}
    digest = event.get("reviewed_content_hash")
    if not isinstance(digest, str) or not _HASH.fullmatch(digest):
        errors.append(f"audit event reviewed_content_hash is invalid: {path}")
    superseded = event.get("superseded_proposal_ids")
    if not isinstance(superseded, list) or any(not isinstance(item, str) for item in superseded):
        errors.append(f"audit event superseded_proposal_ids is invalid: {path}")
        superseded = []
    if len(superseded) != len(set(superseded)):
        errors.append(f"audit event superseded_proposal_ids contains duplicates: {path}")
    frozen = event.get("frozen_activation")
    if decision == "approve":
        frozen_fields = {"content_hash", "migration_impact", "rollback", "target", "version"}
        if not isinstance(frozen, dict) or set(frozen) != frozen_fields:
            errors.append(f"approved audit event lacks the fixed activation contract: {path}")
        elif (
            frozen.get("content_hash") != digest
            or frozen.get("version") != version
            or frozen.get("target") != target
            or not isinstance(frozen.get("migration_impact"), dict)
            or not isinstance(frozen.get("rollback"), dict)
        ):
            errors.append(f"approved audit event activation fields do not match reviewed content: {path}")
    elif frozen is not None or superseded:
        errors.append(f"non-approved audit event must not carry activation or supersession: {path}")
    expected_id = stable_id(
        "template-audit",
        event.get("proposal_id"),
        decision,
        reviewer["id"].casefold(),
        conclusion,
        version,
        digest,
    )
    if event.get("audit_id") != expected_id:
        errors.append(f"audit event stable identifier mismatch: {path}")
    return errors


def _rollback_event_errors(event: Any, path: Path) -> list[str]:
    expected = {
        "approval_audit_id",
        "event_id",
        "event_type",
        "expected_content_hash",
        "proposal_id",
        "reason",
        "reviewer",
        "rollback_id",
        "rolled_back_at_utc",
        "schema_version",
        "sequence",
        "target",
    }
    if not isinstance(event, dict):
        return [f"rollback event must be an object: {path}"]
    if set(event) != expected:
        return [f"rollback event fields differ from schema: {path}"]
    errors: list[str] = []
    if event.get("schema_version") != TEMPLATE_PROPOSAL_SCHEMA_VERSION or event.get("event_type") != "rollback":
        errors.append(f"rollback event version or type mismatch: {path}")
    if event.get("event_id") != event.get("rollback_id") or path.stem != event.get("rollback_id"):
        errors.append(f"rollback event identifier mismatch: {path}")
    if not isinstance(event.get("sequence"), int) or event["sequence"] < 1:
        errors.append(f"rollback event sequence is invalid: {path}")
    try:
        reviewer = _reviewer(event.get("reviewer"), "stored rollback reviewer")
        reason = _text(event.get("reason"), "stored rollback reason")
        _validate_target(event.get("target"))
    except CkbError as exc:
        errors.append(f"rollback event content is invalid at {path}: {exc}")
        reviewer = {"id": "", "kind": "human"}
        reason = ""
    digest = event.get("expected_content_hash")
    if not isinstance(digest, str) or not _HASH.fullmatch(digest):
        errors.append(f"rollback event expected_content_hash is invalid: {path}")
    expected_id = stable_id(
        "template-rollback",
        event.get("proposal_id"),
        event.get("approval_audit_id"),
        reviewer["id"].casefold(),
        reason,
        digest,
    )
    if event.get("rollback_id") != expected_id:
        errors.append(f"rollback event stable identifier mismatch: {path}")
    return errors


def _load_events(root: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    specifications = (
        ("proposals", _proposal_event_errors),
        ("audits", _audit_event_errors),
        ("rollbacks", _rollback_event_errors),
    )
    for directory, validator in specifications:
        for path in sorted((root / directory).glob("*.json")):
            event = json_load(path)
            errors = validator(event, path)
            if errors:
                raise CkbError(errors[0])
            events.append(event)
    sequences = [event["sequence"] for event in events]
    if len(sequences) != len(set(sequences)):
        raise CkbError("template proposal store contains duplicate event sequences")
    return sorted(events, key=lambda event: (event["sequence"], event["event_id"]))


def _builtin_items() -> list[dict[str, Any]]:
    registry = human_page_template_registry_document()
    result: list[dict[str, Any]] = []
    for order, contract in enumerate(registry["page_types"]):
        result.append(
            {
                "active": True,
                "builtin_order": order,
                "content_hash": human_page_template_registry_sha256(),
                "id": f"builtin:{contract['page_type']}",
                "source": "builtin",
                "status": "builtin",
                "template_name": contract["page_type"],
                "version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
            }
        )
    return result


def _item_sort_key(item: Mapping[str, Any]) -> tuple[Any, ...]:
    if item.get("source") == "builtin":
        return (0, int(item.get("builtin_order", 0)), "", (0, 0, 0), str(item.get("id")))
    return (
        1,
        _STATUS_ORDER.get(str(item.get("status")), len(_STATUS_ORDER)),
        str(item.get("template_name", "")).casefold(),
        _semantic_version_key(str(item.get("version", "0.0.0"))),
        str(item.get("id", "")),
    )


def _index_from_events(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    items = _builtin_items()
    by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        event_type = event["event_type"]
        if event_type == "proposal":
            payload = event["payload"]
            proposal_id = str(event["proposal_id"])
            if proposal_id in by_id:
                raise CkbError(f"template proposal event is duplicated: {proposal_id}")
            item = {
                "active": False,
                "activation_status": "not-approved",
                "approval_audit_id": None,
                "content_hash": event["content_hash"],
                "id": proposal_id,
                "proposer": payload["proposer"],
                "rollback_id": None,
                "sequence": event["sequence"],
                "source": "proposal",
                "status": "pending",
                "submitted_at_utc": event["submitted_at_utc"],
                "superseded_by": None,
                "template_name": payload["template_name"],
                "version": payload["version"],
            }
            items.append(item)
            by_id[proposal_id] = item
            continue
        proposal_id = str(event["proposal_id"])
        item = by_id.get(proposal_id)
        if item is None:
            raise CkbError(f"template event precedes or references an unknown proposal: {event['event_id']}")
        if event_type == "audit":
            if item["status"] != "pending":
                raise CkbError(f"template proposal has more than one terminal audit: {proposal_id}")
            if event["reviewed_content_hash"] != item["content_hash"] or event["reviewed_version"] != item["version"]:
                raise CkbError(f"template audit reviewed content differs from the proposal: {event['audit_id']}")
            decision = event["decision"]
            if decision == "approve":
                frozen = event["frozen_activation"]
                proposal_event = next(value for value in events if value["event_type"] == "proposal" and value["proposal_id"] == proposal_id)
                payload = proposal_event["payload"]
                if (
                    frozen["migration_impact"] != payload["migration_impact"]
                    or frozen["rollback"] != payload["rollback"]
                    or frozen["target"] != payload["target"]
                ):
                    raise CkbError(f"template audit activation freeze differs from the proposal: {event['audit_id']}")
                expected_superseded = sorted(
                    value["id"]
                    for value in by_id.values()
                    if value["active"] and value["template_name"].casefold() == item["template_name"].casefold()
                )
                if list(event["superseded_proposal_ids"]) != expected_superseded:
                    raise CkbError(f"template audit supersession set drifted: {event['audit_id']}")
                for old_id in expected_superseded:
                    old = by_id[old_id]
                    old["active"] = False
                    old["activation_status"] = "superseded"
                    old["status"] = "superseded"
                    old["superseded_by"] = proposal_id
                item["active"] = True
                item["activation_status"] = "active"
                item["approval_audit_id"] = event["audit_id"]
                item["status"] = "approved"
            elif decision == "reject":
                item["activation_status"] = "rejected"
                item["status"] = "rejected"
            else:
                item["activation_status"] = "returned-for-changes"
                item["status"] = "superseded"
            continue
        if event_type != "rollback":
            raise CkbError(f"unknown template event type: {event_type}")
        if item["status"] != "approved" or not item["active"]:
            raise CkbError(f"template rollback does not target an active approved extension: {event['rollback_id']}")
        if event["approval_audit_id"] != item["approval_audit_id"] or event["expected_content_hash"] != item["content_hash"]:
            raise CkbError(f"template rollback target differs from the approved activation: {event['rollback_id']}")
        item["active"] = False
        item["activation_status"] = "rolled-back"
        item["rollback_id"] = event["rollback_id"]
        item["status"] = "superseded"
    ordered = sorted(items, key=_item_sort_key)
    counts = {status: sum(1 for item in ordered if item["status"] == status) for status in TEMPLATE_PROPOSAL_STATUSES}
    return {
        "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
        "status": "ready",
        "store_type": "output-local-human-page-template-proposals",
        "builtin_registry": _target_document(),
        "event_count": len(events),
        "last_sequence": max((int(event["sequence"]) for event in events), default=0),
        "counts": counts,
        "items": ordered,
    }


def _operation_log_bytes(events: Sequence[Mapping[str, Any]]) -> bytes:
    return b"".join(_canonical_bytes(dict(event)) for event in events)


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def _rebuild_store(root: Path) -> dict[str, Any]:
    events = _load_events(root)
    index = _index_from_events(events)
    json_write(root / "index.json", index)
    _atomic_write_bytes(root / "operations.jsonl", _operation_log_bytes(events))
    if json_load(root / "index.json") != index:
        raise CkbError("template proposal index did not reopen with rebuilt content")
    if (root / "operations.jsonl").read_bytes() != _operation_log_bytes(events):
        raise CkbError("template proposal operation log did not reopen with rebuilt content")
    return index


def _load_verified_store(output: Path) -> tuple[Path | None, list[dict[str, Any]], dict[str, Any]]:
    output = _validated_output(output)
    root = _store_root(output)
    if not root.exists():
        return None, [], _index_from_events([])
    _validate_store_schema(root)
    events = _load_events(root)
    index = _index_from_events(events)
    index_path = root / "index.json"
    log_path = root / "operations.jsonl"
    if not index_path.is_file() or json_load(index_path) != index:
        raise CkbError("template proposal index drifted from replayed events")
    if not log_path.is_file() or log_path.read_bytes() != _operation_log_bytes(events):
        raise CkbError("template proposal operation log drifted from replayed events")
    return root, events, index


def _validate_local_version(normalized: Mapping[str, Any], events: Sequence[Mapping[str, Any]]) -> None:
    name = str(normalized["template_name"])
    version = str(normalized["version"])
    digest = _sha256(normalized)
    same_name = [
        event
        for event in events
        if event["event_type"] == "proposal"
        and str(event["payload"]["template_name"]).casefold() == name.casefold()
    ]
    for event in same_name:
        if event["content_hash"] == digest:
            return
        if event["payload"]["version"] == version:
            raise CkbError(f"template proposal name/version already has different content: {name} {version}")
    if same_name:
        latest = max((_semantic_version_key(str(event["payload"]["version"])) for event in same_name))
        if _semantic_version_key(version) <= latest:
            raise CkbError(f"template proposal version must advance beyond the latest local version: {name}")


def validate_template_proposal(output: Path, proposal_path: Path) -> dict[str, Any]:
    _validated_output(output)
    proposal_path = proposal_path.resolve()
    if not proposal_path.is_file():
        raise CkbError(f"template proposal input does not exist: {proposal_path}")
    try:
        document = json_load(proposal_path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CkbError(f"template proposal must be valid UTF-8 JSON: {exc}") from exc
    normalized = normalize_template_proposal(document)
    _root, events, _index = _load_verified_store(output)
    _validate_local_version(normalized, events)
    digest = _sha256(normalized)
    return {
        "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
        "status": "passed",
        "proposal": str(proposal_path),
        "proposal_id": stable_id("template-proposal", digest),
        "content_hash": digest,
        "template_name": normalized["template_name"],
        "version": normalized["version"],
        "normalized": normalized,
        "writes": 0,
    }


def propose_template(output: Path, proposal_path: Path) -> dict[str, Any]:
    output = _validated_output(output)
    proposal_path = proposal_path.resolve()
    if not proposal_path.is_file():
        raise CkbError(f"template proposal input does not exist: {proposal_path}")
    try:
        document = json_load(proposal_path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CkbError(f"template proposal must be valid UTF-8 JSON: {exc}") from exc
    normalized = normalize_template_proposal(document)
    digest = _sha256(normalized)
    proposal_id = stable_id("template-proposal", digest)
    root = _prepare_store(output)
    with _store_lock(root):
        _initialize_store_locked(root)
        events = _load_events(root)
        _validate_local_version(normalized, events)
        existing = next((event for event in events if event["proposal_id"] == proposal_id), None)
        if existing is not None:
            index = _rebuild_store(root)
            return {
                "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
                "status": "pending",
                "proposal_id": proposal_id,
                "content_hash": digest,
                "idempotent": True,
                "proposal": str((root / "proposals" / f"{proposal_id}.json").resolve()),
                "index": str((root / "index.json").resolve()),
                "operation_log": str((root / "operations.jsonl").resolve()),
                "event_count": index["event_count"],
            }
        sequence = max((int(event["sequence"]) for event in events), default=0) + 1
        event = {
            "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
            "event_type": "proposal",
            "event_id": proposal_id,
            "proposal_id": proposal_id,
            "sequence": sequence,
            "submitted_at_utc": utc_now(),
            "content_hash": digest,
            "payload": normalized,
        }
        proposal_store_path = root / "proposals" / f"{proposal_id}.json"
        json_write(proposal_store_path, event)
        index = _rebuild_store(root)
    return {
        "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
        "status": "pending",
        "proposal_id": proposal_id,
        "content_hash": digest,
        "idempotent": False,
        "proposal": str(proposal_store_path.resolve()),
        "schema": str((root / "schema.json").resolve()),
        "index": str((root / "index.json").resolve()),
        "operation_log": str((root / "operations.jsonl").resolve()),
        "event_count": index["event_count"],
        "next": "template audit requires an explicit human reviewer",
    }


def list_templates(output: Path, status: str = "all") -> dict[str, Any]:
    if status != "all" and status not in TEMPLATE_PROPOSAL_STATUSES:
        raise CkbError(f"template list status must be all or one of {list(TEMPLATE_PROPOSAL_STATUSES)}")
    root, _events, index = _load_verified_store(output)
    selected = [item for item in index["items"] if status == "all" or item["status"] == status]
    return {
        "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
        "status": "ready",
        "filter": status,
        "count": len(selected),
        "counts": index["counts"],
        "templates": selected,
        "index": str((root / "index.json").resolve()) if root else None,
    }


def show_template(output: Path, identifier: str) -> dict[str, Any]:
    lookup = _text(identifier, "identifier", maximum=200)
    root, events, index = _load_verified_store(output)
    matches = [item for item in index["items"] if str(item["id"]) == lookup]
    if not matches:
        matches = [item for item in index["items"] if str(item["template_name"]).casefold() == lookup.casefold()]
    if not matches:
        raise CkbError(f"template does not exist in builtin or output-local registry: {lookup}")
    selected = sorted(matches, key=_item_sort_key)[-1]
    if selected["source"] == "builtin":
        registry = human_page_template_registry_document()
        contract = next(item for item in registry["page_types"] if item["page_type"] == selected["template_name"])
        detail: dict[str, Any] = {**selected, "contract": contract, "history": []}
    else:
        proposal_event = next(
            item for item in events if item["event_type"] == "proposal" and item["proposal_id"] == selected["id"]
        )
        history = [item for item in events if item.get("proposal_id") == selected["id"]]
        detail = {**selected, "proposal": proposal_event["payload"], "history": history}
    return {
        "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
        "status": "ready",
        "match_count": len(matches),
        "template": detail,
        "store": str(root.resolve()) if root else None,
    }


def _event_by_id(events: Sequence[Mapping[str, Any]], event_id: str) -> Mapping[str, Any] | None:
    return next((event for event in events if event["event_id"] == event_id), None)


def _proposal_payload(events: Sequence[Mapping[str, Any]], proposal_id: str) -> Mapping[str, Any]:
    event = next(
        (
            value
            for value in events
            if value["event_type"] == "proposal" and value["proposal_id"] == proposal_id
        ),
        None,
    )
    if event is None:
        raise CkbError(f"template proposal does not exist: {proposal_id}")
    return event["payload"]


def audit_template_proposal(
    output: Path,
    proposal_id: str,
    decision: str,
    reviewer_kind: str,
    reviewer_id: str,
    conclusion: str,
    version: str,
    expected_content_hash: str,
) -> dict[str, Any]:
    """Record one explicit human decision and activate only approved content."""

    output = _validated_output(output)
    if decision not in TEMPLATE_PROPOSAL_DECISIONS:
        raise CkbError(f"template audit decision must be one of {list(TEMPLATE_PROPOSAL_DECISIONS)}")
    reviewer = _reviewer({"kind": reviewer_kind, "id": reviewer_id}, "reviewer")
    conclusion = _text(conclusion, "conclusion")
    version = _semantic_version(version, "reviewed version")
    if not _HASH.fullmatch(str(expected_content_hash)):
        raise CkbError("template audit expected_content_hash must be one lowercase SHA-256")
    root = _store_root(output)
    if not root.is_dir():
        raise CkbError("template audit requires an existing pending proposal store")
    with _store_lock(root):
        _initialize_store_locked(root)
        events = _load_events(root)
        payload = _proposal_payload(events, proposal_id)
        digest = str(expected_content_hash)
        audit_id = stable_id(
            "template-audit",
            proposal_id,
            decision,
            reviewer["id"].casefold(),
            conclusion,
            version,
            digest,
        )
        existing = _event_by_id(events, audit_id)
        if existing is not None:
            index = _rebuild_store(root)
            item = next(value for value in index["items"] if value["id"] == proposal_id)
            return {
                "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
                "status": item["status"],
                "active": item["active"],
                "proposal_id": proposal_id,
                "audit_id": audit_id,
                "idempotent": True,
                "audit": str((root / "audits" / f"{audit_id}.json").resolve()),
                "index": str((root / "index.json").resolve()),
            }
        index = _index_from_events(events)
        item = next((value for value in index["items"] if value["id"] == proposal_id), None)
        if item is None:
            raise CkbError(f"template proposal does not exist: {proposal_id}")
        if item["status"] != "pending":
            raise CkbError(f"template audit requires a pending proposal: {proposal_id}; status={item['status']}")
        if digest != item["content_hash"]:
            raise CkbError("template audit content hash drifted from the pending proposal")
        if version != item["version"] or version != payload["version"]:
            raise CkbError("template audit reviewed version drifted from the pending proposal")
        if payload["target"] != _target_document():
            raise CkbError("template audit target drifted from the current read-only builtin registry")
        superseded = sorted(
            value["id"]
            for value in index["items"]
            if value.get("source") == "proposal"
            and value["active"]
            and value["template_name"].casefold() == item["template_name"].casefold()
        ) if decision == "approve" else []
        frozen = (
            {
                "content_hash": digest,
                "migration_impact": payload["migration_impact"],
                "rollback": payload["rollback"],
                "target": payload["target"],
                "version": version,
            }
            if decision == "approve"
            else None
        )
        sequence = max((int(event["sequence"]) for event in events), default=0) + 1
        event = {
            "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
            "event_type": "audit",
            "event_id": audit_id,
            "audit_id": audit_id,
            "proposal_id": proposal_id,
            "sequence": sequence,
            "audited_at_utc": utc_now(),
            "decision": decision,
            "reviewer": reviewer,
            "conclusion": conclusion,
            "reviewed_version": version,
            "reviewed_content_hash": digest,
            "target": payload["target"],
            "frozen_activation": frozen,
            "superseded_proposal_ids": superseded,
        }
        audit_path = root / "audits" / f"{audit_id}.json"
        json_write(audit_path, event)
        index = _rebuild_store(root)
        current = next(value for value in index["items"] if value["id"] == proposal_id)
    return {
        "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
        "status": current["status"],
        "active": current["active"],
        "proposal_id": proposal_id,
        "audit_id": audit_id,
        "decision": decision,
        "reviewer": reviewer,
        "frozen_version": version if decision == "approve" else None,
        "frozen_content_hash": digest if decision == "approve" else None,
        "idempotent": False,
        "audit": str(audit_path.resolve()),
        "index": str((root / "index.json").resolve()),
        "operation_log": str((root / "operations.jsonl").resolve()),
    }


def rollback_template_extension(
    output: Path,
    proposal_id: str,
    reviewer_kind: str,
    reviewer_id: str,
    reason: str,
    expected_content_hash: str,
) -> dict[str, Any]:
    """Deactivate one active approved extension while retaining all history."""

    output = _validated_output(output)
    reviewer = _reviewer({"kind": reviewer_kind, "id": reviewer_id}, "rollback reviewer")
    reason = _text(reason, "rollback reason")
    digest = str(expected_content_hash)
    if not _HASH.fullmatch(digest):
        raise CkbError("template rollback expected_content_hash must be one lowercase SHA-256")
    root = _store_root(output)
    if not root.is_dir():
        raise CkbError("template rollback requires an existing proposal store")
    with _store_lock(root):
        _initialize_store_locked(root)
        events = _load_events(root)
        index = _index_from_events(events)
        item = next((value for value in index["items"] if value["id"] == proposal_id), None)
        approval_audit_id = str(item.get("approval_audit_id")) if item else ""
        rollback_id = stable_id(
            "template-rollback",
            proposal_id,
            approval_audit_id,
            reviewer["id"].casefold(),
            reason,
            digest,
        )
        existing = _event_by_id(events, rollback_id)
        if existing is not None:
            index = _rebuild_store(root)
            current = next(value for value in index["items"] if value["id"] == proposal_id)
            return {
                "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
                "status": "rolled-back",
                "template_status": current["status"],
                "active": current["active"],
                "proposal_id": proposal_id,
                "rollback_id": rollback_id,
                "idempotent": True,
                "rollback": str((root / "rollbacks" / f"{rollback_id}.json").resolve()),
                "index": str((root / "index.json").resolve()),
            }
        if item is None:
            raise CkbError(f"template proposal does not exist: {proposal_id}")
        if item["status"] != "approved" or not item["active"]:
            raise CkbError("template rollback can only deactivate an active approved extension")
        if digest != item["content_hash"]:
            raise CkbError("template rollback content hash drifted from the approved extension")
        payload = _proposal_payload(events, proposal_id)
        if payload["target"] != _target_document():
            raise CkbError("template rollback target drifted from the current read-only builtin registry")
        sequence = max((int(event["sequence"]) for event in events), default=0) + 1
        event = {
            "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
            "event_type": "rollback",
            "event_id": rollback_id,
            "rollback_id": rollback_id,
            "proposal_id": proposal_id,
            "approval_audit_id": item["approval_audit_id"],
            "sequence": sequence,
            "rolled_back_at_utc": utc_now(),
            "reviewer": reviewer,
            "reason": reason,
            "expected_content_hash": digest,
            "target": payload["target"],
        }
        rollback_path = root / "rollbacks" / f"{rollback_id}.json"
        json_write(rollback_path, event)
        index = _rebuild_store(root)
        current = next(value for value in index["items"] if value["id"] == proposal_id)
    return {
        "schema_version": TEMPLATE_PROPOSAL_SCHEMA_VERSION,
        "status": "rolled-back",
        "template_status": current["status"],
        "active": current["active"],
        "proposal_id": proposal_id,
        "rollback_id": rollback_id,
        "idempotent": False,
        "rollback": str(rollback_path.resolve()),
        "index": str((root / "index.json").resolve()),
        "operation_log": str((root / "operations.jsonl").resolve()),
        "history_retained": True,
    }
