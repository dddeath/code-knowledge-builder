"""Explicit, bounded contracts for the optional LLM keyword fallback."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Sequence

from .common import CkbError


KEYWORD_FALLBACK_SCHEMA_VERSION = 1
KEYWORD_PROMPT_SCHEMA = "ckb-keyword-fallback-v1"
MAX_KEYWORDS = 16
MAX_ANCHORS = 12
MAX_REWRITES = 4
MAX_KEYWORD_CHARS = 80
MAX_ANCHOR_CHARS = 160
MAX_REWRITE_CHARS = 320

_MACHINE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_KEYWORD_TEXT = re.compile(r"^[\w\u3400-\u9fff./:+# -]+$", flags=re.UNICODE)
_ANCHOR_TEXT = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:(?:::|\.)[A-Za-z_][A-Za-z0-9_]*)*$"
)
_REWRITE_TEXT = re.compile(r"^[\w\u3400-\u9fff\s./:+#(),（）-]+$", flags=re.UNICODE)
_PROMPT_INJECTION = re.compile(
    r"(?:"
    r"(?:ignore|disregard).{0,24}(?:previous|system|instruction)|"
    r"system\s*(?:prompt|message)|developer\s*message|jailbreak|"
    r"<\s*/?(?:script|system)|"
    r"忽略.{0,12}(?:之前|以上|系统|指令)|系统提示|开发者消息|越狱"
    r")",
    flags=re.IGNORECASE,
)
_FAILURE_TYPES = {
    "invalid-json",
    "invalid-output",
    "missing-credentials",
    "process-failed",
    "rate-limit",
    "timeout",
    "unavailable",
}


@dataclass(frozen=True)
class KeywordProviderConfig:
    """Public identity and bounded execution settings for one provider adapter."""

    command: tuple[str, ...]
    provider: str
    model: str
    version: str
    timeout_seconds: float = 20.0
    retries: int = 1
    required_environment: tuple[str, ...] = ()


def keyword_input_hash(question: str) -> str:
    return hashlib.sha256(question.encode("utf-8")).hexdigest()


def keyword_request_id(question: str) -> str:
    return f"keyword-{keyword_input_hash(question)[:24]}"


def canonical_keyword_request(question: str) -> dict[str, Any]:
    """Build the only request shape accepted by command/stdio providers."""

    return {
        "schema_version": KEYWORD_FALLBACK_SCHEMA_VERSION,
        "prompt_schema": KEYWORD_PROMPT_SCHEMA,
        "request_id": keyword_request_id(question),
        "input_hash": keyword_input_hash(question),
        "question": question,
        "limits": {
            "keywords": MAX_KEYWORDS,
            "anchors": MAX_ANCHORS,
            "rewrites": MAX_REWRITES,
            "keyword_chars": MAX_KEYWORD_CHARS,
            "anchor_chars": MAX_ANCHOR_CHARS,
            "rewrite_chars": MAX_REWRITE_CHARS,
        },
    }


def _machine_token(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _MACHINE_TOKEN.fullmatch(value):
        raise CkbError(f"keyword provider {name} must be a bounded machine token")
    return value


def validate_provider_config(config: KeywordProviderConfig) -> None:
    if not config.command or any(not isinstance(value, str) or not value for value in config.command):
        raise CkbError("keyword provider command must contain at least one non-empty argument")
    _machine_token(config.provider, "provider")
    _machine_token(config.model, "model")
    _machine_token(config.version, "version")
    if not 0.1 <= config.timeout_seconds <= 300.0:
        raise CkbError("keyword provider timeout must be between 0.1 and 300 seconds")
    if config.retries not in {0, 1}:
        raise CkbError("keyword provider retries must be zero or one")
    for name in config.required_environment:
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", name):
            raise CkbError("keyword provider required environment names must be bounded identifiers")


def _bounded_strings(
    value: Any,
    *,
    name: str,
    maximum_items: int,
    maximum_chars: int,
    pattern: re.Pattern[str],
) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum_items:
        raise CkbError(f"keyword provider {name} must be an array with at most {maximum_items} items")
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise CkbError(f"keyword provider {name} items must be strings")
        normalized = item.strip()
        if not normalized or len(normalized) > maximum_chars:
            raise CkbError(f"keyword provider {name} items must contain 1 to {maximum_chars} characters")
        if not pattern.fullmatch(normalized):
            raise CkbError(f"keyword provider {name} contains unsupported characters")
        if _PROMPT_INJECTION.search(normalized):
            raise CkbError(f"keyword provider {name} contains prompt-injection text")
        identity = normalized.casefold()
        if identity in seen:
            raise CkbError(f"keyword provider {name} contains duplicate items")
        seen.add(identity)
        result.append(normalized)
    return result


def _usage(value: Any) -> dict[str, Any]:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise CkbError("keyword provider usage must be an object")
    allowed = {"input_tokens", "output_tokens", "total_tokens", "cost_usd"}
    if set(value) - allowed:
        raise CkbError("keyword provider usage contains unsupported fields")
    result: dict[str, Any] = {}
    for name in ("input_tokens", "output_tokens", "total_tokens"):
        item = value.get(name, 0)
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise CkbError(f"keyword provider usage {name} must be a non-negative integer")
        result[name] = item
    cost = value.get("cost_usd", 0.0)
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0:
        raise CkbError("keyword provider usage cost_usd must be a non-negative number")
    result["cost_usd"] = round(float(cost), 8)
    if result["total_tokens"] and result["total_tokens"] != result["input_tokens"] + result["output_tokens"]:
        raise CkbError("keyword provider usage total_tokens does not match input plus output")
    return result


def validate_provider_response(
    value: Any,
    *,
    question: str,
    config: KeywordProviderConfig,
) -> dict[str, Any]:
    """Validate and normalize model output before it reaches deterministic retrieval."""

    validate_provider_config(config)
    if not isinstance(value, dict):
        raise CkbError("keyword provider response must be a JSON object")
    allowed = {
        "schema_version",
        "status",
        "failure_type",
        "request_id",
        "provider",
        "model",
        "version",
        "keywords",
        "anchors",
        "rewrites",
        "usage",
    }
    if set(value) - allowed:
        raise CkbError("keyword provider response contains unsupported fields")
    if value.get("schema_version") != KEYWORD_FALLBACK_SCHEMA_VERSION:
        raise CkbError("keyword provider schema version mismatch")
    status = value.get("status")
    if status != "passed":
        failure_type = value.get("failure_type")
        if status != "failed" or failure_type not in _FAILURE_TYPES:
            raise CkbError("keyword provider failure response is not canonical")
        return {
            "schema_version": KEYWORD_FALLBACK_SCHEMA_VERSION,
            "status": "failed",
            "failure_type": failure_type,
            "request_id": keyword_request_id(question),
            "provider": config.provider,
            "model": config.model,
            "version": config.version,
            "keywords": [],
            "anchors": [],
            "rewrites": [],
            "usage": _usage(value.get("usage")),
        }
    identity = {
        "request_id": keyword_request_id(question),
        "provider": config.provider,
        "model": config.model,
        "version": config.version,
    }
    for name, expected in identity.items():
        if value.get(name) != expected:
            raise CkbError(f"keyword provider {name} does not match the request configuration")
    return {
        "schema_version": KEYWORD_FALLBACK_SCHEMA_VERSION,
        "status": "passed",
        **identity,
        "keywords": _bounded_strings(
            value.get("keywords"),
            name="keywords",
            maximum_items=MAX_KEYWORDS,
            maximum_chars=MAX_KEYWORD_CHARS,
            pattern=_KEYWORD_TEXT,
        ),
        "anchors": _bounded_strings(
            value.get("anchors"),
            name="anchors",
            maximum_items=MAX_ANCHORS,
            maximum_chars=MAX_ANCHOR_CHARS,
            pattern=_ANCHOR_TEXT,
        ),
        "rewrites": _bounded_strings(
            value.get("rewrites"),
            name="rewrites",
            maximum_items=MAX_REWRITES,
            maximum_chars=MAX_REWRITE_CHARS,
            pattern=_REWRITE_TEXT,
        ),
        "usage": _usage(value.get("usage")),
    }


def parse_provider_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CkbError("keyword provider returned invalid JSON") from exc


def unique_casefold(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        identity = normalized.casefold()
        if normalized and identity not in seen:
            seen.add(identity)
            result.append(normalized)
    return result
