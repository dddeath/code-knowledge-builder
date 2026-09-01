from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from .common import CkbError


PAGE_CONFIG_SCHEMA_VERSION = 1

# Keep one embedded default so a lite installation can validate and start even
# when the caller does not supply a configuration file.  The packaged
# references/page-config.default.json is byte-compared with this value by tests.
DEFAULT_PAGE_CONFIG: dict[str, Any] = {
    "schema_version": PAGE_CONFIG_SCHEMA_VERSION,
    "page_limits": {
        "ordinary_file": 1,
        "core_file": 4,
        "adjacent_file": 1,
        "core_per_entry": 4,
        "adjacent_per_entry": 3,
    },
    "content": {
        "code_page_sections": [
            "overview",
            "change_when",
            "source_location",
            "partial_fragments",
            "related_code",
            "backlinks",
            "tests",
            "hidden_relation_hint",
            "appendix",
        ],
        "aggregate_page_sections": [
            "overview",
            "related_code",
            "backlinks",
            "tests",
            "hidden_relation_hint",
        ],
        "boundary_page_sections": [
            "overview",
            "boundary_details",
            "related_code",
            "backlinks",
            "hidden_relation_hint",
        ],
        "overview_fields": ["meaning", "role"],
        "appendix_mode": "collapsed",
        "headings": {
            "change_when": "什么时候需要修改",
            "source_location": "在代码中的位置",
            "boundary_details": "本次未继续展开的代码",
            "related_code": "相关代码",
            "backlinks": "谁会来到这里",
            "tests": "相关测试",
            "appendix": "内部细节",
        },
    },
    "relation_limits": {
        "direct": 20,
        "aggregate": 10,
        "test": 8,
        "boundary": 8,
    },
    "context": {
        "module_max_tokens": 80_000,
        "task_max_tokens": 20_000,
        "total_max_tokens": 100_000,
        "reserved_agent_tokens": 20_000,
        "bytes_per_token": 3,
    },
    "review_packs": {
        "page": {"max_files": 12, "max_items": 20, "max_tokens": 20_000},
        "appendix": {"max_files": 8, "max_items": 120, "max_tokens": 15_000},
    },
}

_CODE_SECTIONS = {
    "overview",
    "change_when",
    "source_location",
    "partial_fragments",
    "related_code",
    "backlinks",
    "tests",
    "hidden_relation_hint",
    "appendix",
}
_AGGREGATE_SECTIONS = {"overview", "related_code", "backlinks", "tests", "hidden_relation_hint"}
_BOUNDARY_SECTIONS = {"overview", "boundary_details", "related_code", "backlinks", "hidden_relation_hint"}
_REQUIRED_SECTIONS = {
    "code_page_sections": {"overview", "source_location", "appendix"},
    "aggregate_page_sections": {"overview"},
    "boundary_page_sections": {"overview", "boundary_details"},
}
_SECTION_SETS = {
    "code_page_sections": _CODE_SECTIONS,
    "aggregate_page_sections": _AGGREGATE_SECTIONS,
    "boundary_page_sections": _BOUNDARY_SECTIONS,
}


def _merge_known(default: Any, supplied: Any, path: str) -> Any:
    if isinstance(default, dict):
        if not isinstance(supplied, dict):
            raise CkbError(f"page config {path or '<root>'} must be an object")
        unknown = sorted(set(supplied) - set(default))
        if unknown:
            raise CkbError(f"page config has unknown keys at {path or '<root>'}: {unknown}")
        return {
            key: _merge_known(value, supplied[key], f"{path}.{key}".strip(".")) if key in supplied else copy.deepcopy(value)
            for key, value in default.items()
        }
    return copy.deepcopy(supplied)


def _integer(value: Any, path: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise CkbError(f"page config {path} must be an integer in [{minimum}, {maximum}]")
    return value


def _section_list(config: dict[str, Any], name: str) -> None:
    value = config["content"][name]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise CkbError(f"page config content.{name} must be a string array")
    if len(value) != len(set(value)):
        raise CkbError(f"page config content.{name} contains duplicate sections")
    unknown = sorted(set(value) - _SECTION_SETS[name])
    if unknown:
        raise CkbError(f"page config content.{name} has unknown sections: {unknown}")
    missing = sorted(_REQUIRED_SECTIONS[name] - set(value))
    if missing:
        raise CkbError(
            f"page config content.{name} omits audited required sections: {missing}"
        )


def normalize_page_config(value: dict[str, Any]) -> dict[str, Any]:
    """Merge a partial user JSON with defaults and enforce the audit contract."""
    if not isinstance(value, dict):
        raise CkbError("page config root must be a JSON object")
    if value.get("schema_version") != PAGE_CONFIG_SCHEMA_VERSION:
        raise CkbError(
            f"page config schema_version must be {PAGE_CONFIG_SCHEMA_VERSION}"
        )
    config = _merge_known(DEFAULT_PAGE_CONFIG, value, "")

    limits = config["page_limits"]
    for key in ("ordinary_file", "core_file", "adjacent_file"):
        limits[key] = _integer(limits[key], f"page_limits.{key}", 0, 32)
    for key in ("core_per_entry", "adjacent_per_entry"):
        limits[key] = _integer(limits[key], f"page_limits.{key}", 0, 64)

    for name in _SECTION_SETS:
        _section_list(config, name)
    fields = config["content"]["overview_fields"]
    if (
        not isinstance(fields, list)
        or not fields
        or len(fields) != len(set(fields))
        or any(value not in {"meaning", "role"} for value in fields)
    ):
        raise CkbError(
            "page config content.overview_fields must contain one or both of: meaning, role"
        )
    if config["content"]["appendix_mode"] not in {"collapsed", "expanded"}:
        raise CkbError("page config content.appendix_mode must be collapsed or expanded")
    headings = config["content"]["headings"]
    for key, heading in headings.items():
        if not isinstance(heading, str) or not heading.strip() or len(heading) > 64 or "\n" in heading or "\r" in heading:
            raise CkbError(f"page config content.headings.{key} must be one non-empty line of at most 64 characters")
        headings[key] = heading.strip()

    relation_limits = config["relation_limits"]
    for key in ("direct", "aggregate", "test", "boundary"):
        relation_limits[key] = _integer(relation_limits[key], f"relation_limits.{key}", 0, 200)

    context = config["context"]
    context["module_max_tokens"] = _integer(context["module_max_tokens"], "context.module_max_tokens", 1_000, 1_000_000)
    context["task_max_tokens"] = _integer(context["task_max_tokens"], "context.task_max_tokens", 500, 1_000_000)
    context["total_max_tokens"] = _integer(context["total_max_tokens"], "context.total_max_tokens", 1_000, 2_000_000)
    context["reserved_agent_tokens"] = _integer(context["reserved_agent_tokens"], "context.reserved_agent_tokens", 0, 1_000_000)
    context["bytes_per_token"] = _integer(context["bytes_per_token"], "context.bytes_per_token", 1, 16)
    if context["task_max_tokens"] > context["module_max_tokens"]:
        raise CkbError("page config context.task_max_tokens must not exceed module_max_tokens")
    if context["module_max_tokens"] + context["reserved_agent_tokens"] > context["total_max_tokens"]:
        raise CkbError(
            "page config context.module_max_tokens plus reserved_agent_tokens must not exceed total_max_tokens"
        )

    review = config["review_packs"]
    for kind in ("page", "appendix"):
        review[kind]["max_files"] = _integer(review[kind]["max_files"], f"review_packs.{kind}.max_files", 1, 200)
        review[kind]["max_items"] = _integer(review[kind]["max_items"], f"review_packs.{kind}.max_items", 1, 5_000)
        review[kind]["max_tokens"] = _integer(review[kind]["max_tokens"], f"review_packs.{kind}.max_tokens", 500, 1_000_000)
        if review[kind]["max_tokens"] > context["total_max_tokens"] - context["reserved_agent_tokens"]:
            raise CkbError(
                f"page config review_packs.{kind}.max_tokens exceeds the non-Agent context budget"
            )
    return config


def load_page_config(path: Path | None) -> tuple[dict[str, Any], str]:
    if path is None:
        return copy.deepcopy(DEFAULT_PAGE_CONFIG), "builtin-default"
    resolved = path.resolve()
    if not resolved.is_file():
        raise CkbError(f"page config does not exist: {resolved}")
    try:
        supplied = json.loads(resolved.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CkbError(f"page config is not valid JSON: {resolved}: {exc}") from exc
    return normalize_page_config(supplied), str(resolved)


def page_config_bytes(config: dict[str, Any]) -> bytes:
    normalized = normalize_page_config(config)
    return (json.dumps(normalized, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def page_config_sha256(config: dict[str, Any]) -> str:
    return hashlib.sha256(page_config_bytes(config)).hexdigest()


def write_page_config(path: Path, config: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved.exists() and not overwrite:
        raise CkbError(f"page config output already exists: {resolved}; use --force to replace it")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    content = page_config_bytes(config)
    resolved.write_bytes(content)
    return {
        "schema_version": PAGE_CONFIG_SCHEMA_VERSION,
        "path": str(resolved),
        "sha256": hashlib.sha256(content).hexdigest(),
        "status": "passed",
    }
