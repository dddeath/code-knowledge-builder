from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any


HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
ACTOR_KEY = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
SECTION_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
ACTOR_CATEGORIES = {
    "retrieval-agent",
    "source-review-agent",
    "human-reviewer",
    "deterministic-tool",
}
SOURCE_KINDS = {"source-range", "reviewed-record", "official-document", "test-result"}


class TagNavigationError(ValueError):
    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise TagNavigationError("INVALID_TIMESTAMP", f"{field} 必须是带时区的 ISO 8601 字符串")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise TagNavigationError("INVALID_TIMESTAMP", f"{field} 不是 ISO 8601 时间") from exc
    if parsed.tzinfo is None:
        raise TagNavigationError("INVALID_TIMESTAMP", f"{field} 缺少时区")
    return parsed.astimezone(timezone.utc)


def _exact_keys(value: Any, expected: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TagNavigationError("INVALID_SCHEMA", f"{field} 必须是对象")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise TagNavigationError("INVALID_SCHEMA", f"{field} missing={missing} unknown={unknown}")
    return value


def validate_identifier(value: Any, field: str, *, actor: bool = False) -> str:
    pattern = ACTOR_KEY if actor else IDENTIFIER
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise TagNavigationError("INVALID_IDENTIFIER", f"{field} 格式非法")
    return value


def validate_relative_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 240:
        raise TagNavigationError("INVALID_PATH", f"{field} 必须是 1..240 字符的相对路径")
    if "\\" in value or ":" in value or "\x00" in value or value.startswith("/"):
        raise TagNavigationError("INVALID_PATH", f"{field} 必须使用仓库相对 POSIX 路径")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise TagNavigationError("INVALID_PATH", f"{field} 含非法路径段")
    return str(path)


def normalize_tag(value: Any) -> str:
    if not isinstance(value, str) or not (1 <= len(value) <= 80):
        raise TagNavigationError("INVALID_TAG", "tag 长度必须为 1..80")
    if value.startswith("#") or value.startswith("/") or value.endswith("/") or "//" in value:
        raise TagNavigationError("INVALID_TAG", "tag 不含 #，且层级分隔符不能位于两端或连续出现")
    if not any(character.isalpha() for character in value):
        raise TagNavigationError("INVALID_TAG", "tag 至少包含一个字母或汉字")
    if any(not (character.isalnum() or character in "_-/") for character in value):
        raise TagNavigationError("INVALID_TAG", "tag 只能包含字母、数字、汉字、_、- 和 /")
    return value.casefold()


def validate_locator(value: Any) -> dict[str, Any]:
    locator = _exact_keys(value, {"kind", "start_line", "end_line", "section_id"}, "evidence.locator")
    kind = locator["kind"]
    if kind not in {"line-range", "section", "whole-file"}:
        raise TagNavigationError("INVALID_LOCATOR", "locator.kind 非法")
    start = locator["start_line"]
    end = locator["end_line"]
    section = locator["section_id"]
    if kind == "line-range":
        if not isinstance(start, int) or isinstance(start, bool) or start < 1:
            raise TagNavigationError("INVALID_LOCATOR", "line-range.start_line 必须为正整数")
        if not isinstance(end, int) or isinstance(end, bool) or end < start:
            raise TagNavigationError("INVALID_LOCATOR", "line-range.end_line 必须不小于 start_line")
        if section is not None:
            raise TagNavigationError("INVALID_LOCATOR", "line-range.section_id 必须为 null")
    elif kind == "section":
        if start is not None or end is not None or not isinstance(section, str) or not SECTION_ID.fullmatch(section):
            raise TagNavigationError("INVALID_LOCATOR", "section 只允许规范 section_id")
    else:
        if start is not None or end is not None or section is not None:
            raise TagNavigationError("INVALID_LOCATOR", "whole-file 的定位字段必须为 null")
    return locator


def validate_evidence(value: Any) -> dict[str, Any]:
    evidence = _exact_keys(
        value,
        {"source_id", "source_kind", "path", "locator", "sha256", "commit", "observed_at"},
        "evidence",
    )
    validate_identifier(evidence["source_id"], "evidence.source_id")
    if evidence["source_kind"] not in SOURCE_KINDS:
        raise TagNavigationError("INVALID_EVIDENCE", "evidence.source_kind 非法")
    validate_relative_path(evidence["path"], "evidence.path")
    validate_locator(evidence["locator"])
    if not isinstance(evidence["sha256"], str) or not HEX64.fullmatch(evidence["sha256"]):
        raise TagNavigationError("INVALID_EVIDENCE", "evidence.sha256 非法")
    if not isinstance(evidence["commit"], str) or not HEX40.fullmatch(evidence["commit"]):
        raise TagNavigationError("INVALID_EVIDENCE", "evidence.commit 非法")
    parse_timestamp(evidence["observed_at"], "evidence.observed_at")
    return evidence


def validate_assertion(value: Any) -> dict[str, Any]:
    assertion = _exact_keys(
        value,
        {
            "schema_version",
            "assertion_id",
            "idempotency_key",
            "action",
            "tag",
            "target",
            "stance",
            "actor",
            "evidence",
            "recorded_at",
            "retracts",
        },
        "assertion",
    )
    if assertion["schema_version"] != 1:
        raise TagNavigationError("INVALID_SCHEMA", "schema_version 必须为 1")
    validate_identifier(assertion["assertion_id"], "assertion_id")
    validate_identifier(assertion["idempotency_key"], "idempotency_key")
    action = assertion["action"]
    if action not in {"propose", "vote", "retract"}:
        raise TagNavigationError("INVALID_ACTION", "action 非法")
    assertion["tag"] = normalize_tag(assertion["tag"])
    target = _exact_keys(assertion["target"], {"kind", "path"}, "target")
    if target["kind"] != "page":
        raise TagNavigationError("INVALID_TARGET", "target.kind 必须为 page")
    validate_relative_path(target["path"], "target.path")
    if not target["path"].endswith(".md"):
        raise TagNavigationError("INVALID_TARGET", "target.path 必须指向 Markdown 页面")
    actor = _exact_keys(assertion["actor"], {"category", "key"}, "actor")
    if actor["category"] not in ACTOR_CATEGORIES:
        raise TagNavigationError("INVALID_ACTOR", "actor.category 非法")
    validate_identifier(actor["key"], "actor.key", actor=True)
    parse_timestamp(assertion["recorded_at"], "recorded_at")
    if action == "vote":
        if assertion["stance"] not in {"support", "oppose"} or assertion["retracts"] is not None:
            raise TagNavigationError("INVALID_ACTION_FIELDS", "vote 必须有 stance 且不能有 retracts")
        validate_evidence(assertion["evidence"])
    elif action == "propose":
        if assertion["stance"] is not None or assertion["retracts"] is not None:
            raise TagNavigationError("INVALID_ACTION_FIELDS", "propose 的 stance/retracts 必须为 null")
        validate_evidence(assertion["evidence"])
    else:
        if assertion["stance"] is not None or assertion["evidence"] is not None:
            raise TagNavigationError("INVALID_ACTION_FIELDS", "retract 的 stance/evidence 必须为 null")
        validate_identifier(assertion["retracts"], "retracts")
    return assertion


def validate_policy(value: Any) -> dict[str, Any]:
    policy = _exact_keys(
        value,
        {
            "schema_version",
            "min_support_votes",
            "min_independent_agents",
            "min_independent_sources",
            "max_opposition_ratio",
            "max_evidence_age_days",
            "max_tags_per_page",
        },
        "policy",
    )
    if policy["schema_version"] != 1:
        raise TagNavigationError("INVALID_POLICY", "schema_version 必须为 1")
    for field in ("min_support_votes", "min_independent_agents", "min_independent_sources"):
        value = policy[field]
        if not isinstance(value, int) or isinstance(value, bool) or not 2 <= value <= 20:
            raise TagNavigationError("INVALID_POLICY", f"{field} 必须为 2..20")
    ratio = policy["max_opposition_ratio"]
    if not isinstance(ratio, (int, float)) or isinstance(ratio, bool) or not 0 <= ratio <= 0.49:
        raise TagNavigationError("INVALID_POLICY", "max_opposition_ratio 必须为 0..0.49")
    age = policy["max_evidence_age_days"]
    if not isinstance(age, int) or isinstance(age, bool) or not 1 <= age <= 365:
        raise TagNavigationError("INVALID_POLICY", "max_evidence_age_days 必须为 1..365")
    quota = policy["max_tags_per_page"]
    if not isinstance(quota, int) or isinstance(quota, bool) or not 1 <= quota <= 8:
        raise TagNavigationError("INVALID_POLICY", "max_tags_per_page 必须为 1..8")
    return policy


def ensure_within(path: Path, root: Path, field: str) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise TagNavigationError("OUTPUT_OUTSIDE_WORKSPACE", f"{field} 不在 workspace-root 内") from exc
    return resolved


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(canonical_json_bytes(value))
    json.loads(temporary.read_text(encoding="utf-8"))
    temporary.replace(path)
    json.loads(path.read_text(encoding="utf-8"))
