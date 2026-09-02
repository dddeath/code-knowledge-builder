from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable
import unicodedata


HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")


class FanoutError(ValueError):
    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FanoutError("INVALID_JSON", f"{label}: {exc}") from exc
    if not isinstance(value, dict):
        raise FanoutError("INVALID_SCHEMA", f"{label} 根必须为对象")
    return value


def exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FanoutError("INVALID_SCHEMA", f"{label} 必须为对象")
    actual = set(value)
    if actual != expected:
        raise FanoutError(
            "INVALID_SCHEMA",
            f"{label} missing={sorted(expected - actual)} unknown={sorted(actual - expected)}",
        )
    return value


def positive_integer(value: Any, label: str, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
        raise FanoutError("INVALID_POLICY", f"{label} 必须为 1..{maximum} 的整数")
    return value


def validate_relative_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 240:
        raise FanoutError("INVALID_PATH", f"{label} 必须为 1..240 字符的相对路径")
    if "\\" in value or ":" in value or "\x00" in value or value.startswith("/"):
        raise FanoutError("INVALID_PATH", f"{label} 必须为 POSIX 相对路径")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise FanoutError("INVALID_PATH", f"{label} 含非法路径段")
    return str(path)


def validate_identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise FanoutError("INVALID_IDENTIFIER", f"{label} 格式非法")
    return value


def ensure_within(path: Path, root: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise FanoutError("PATH_OUTSIDE_WORKSPACE", f"{label} 不在 workspace-root 内") from exc
    return resolved


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise FanoutError("TEMPORARY_EXISTS", str(temporary))
    temporary.write_bytes(canonical_json_bytes(value))
    json.loads(temporary.read_text(encoding="utf-8"))
    temporary.replace(path)
    json.loads(path.read_text(encoding="utf-8"))


def tree_manifest(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise FanoutError("TREE_NOT_FOUND", str(root))
    files = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        files.append({"path": relative, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    digest = sha256_bytes(canonical_json_bytes(files))
    return {"sha256": digest, "file_count": len(files), "total_bytes": sum(item["bytes"] for item in files), "files": files}


def normalize_topic(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def has_chinese(value: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in value)


def utf8_size(values: Iterable[str]) -> int:
    return sum(len(value.encode("utf-8")) for value in values)


def validate_contract(value: dict[str, Any]) -> dict[str, Any]:
    exact_keys(
        value,
        {
            "schema_version",
            "scope",
            "baseline_commit",
            "frozen_at_utc",
            "arms",
            "fanout_policy",
            "current_compatibility",
            "cost_formula",
            "recommendation_thresholds",
        },
        "contract",
    )
    if value["schema_version"] != 1 or value["scope"] != "isolated-page-fanout-benchmark":
        raise FanoutError("INVALID_CONTRACT", "schema_version/scope 非法")
    if not isinstance(value["baseline_commit"], str) or not HEX40.fullmatch(value["baseline_commit"]):
        raise FanoutError("INVALID_CONTRACT", "baseline_commit 非法")
    if value["arms"] != {"arm_a": "conservative", "arm_b": "fanout"}:
        raise FanoutError("INVALID_CONTRACT", "arms 必须固定为盲化 A/B 映射")
    policy = exact_keys(
        value["fanout_policy"],
        {
            "candidate_source",
            "term_rule",
            "claim_rule",
            "max_pages_per_document",
            "max_links_per_page",
            "max_total_new_pages",
            "duplicate_topic_similarity_threshold",
            "duplicate_normalization",
            "overflow_action",
        },
        "fanout_policy",
    )
    if policy["candidate_source"] != "frozen-explicit-candidate-manifest":
        raise FanoutError("INVALID_POLICY", "candidate_source 非法")
    if policy["term_rule"] != "term-must-occur-in-exact-source-range":
        raise FanoutError("INVALID_POLICY", "term_rule 非法")
    if policy["claim_rule"] != "claim-zh-must-equal-exact-source-text":
        raise FanoutError("INVALID_POLICY", "claim_rule 非法")
    if policy["overflow_action"] != "reject-with-stable-reason":
        raise FanoutError("INVALID_POLICY", "overflow_action 非法")
    if policy["duplicate_normalization"] != "unicode-nfkc-casefold-alnum-only":
        raise FanoutError("INVALID_POLICY", "duplicate_normalization 非法")
    positive_integer(policy["max_pages_per_document"], "max_pages_per_document", 32)
    positive_integer(policy["max_links_per_page"], "max_links_per_page", 32)
    positive_integer(policy["max_total_new_pages"], "max_total_new_pages", 128)
    threshold = policy["duplicate_topic_similarity_threshold"]
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not 0.8 <= threshold <= 1.0:
        raise FanoutError("INVALID_POLICY", "duplicate_topic_similarity_threshold 必须为 0.8..1.0")
    return value
