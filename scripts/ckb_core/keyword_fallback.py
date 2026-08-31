"""Explicit, bounded contracts for the optional LLM keyword fallback."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Sequence

from .common import CkbError, background_process_options, json_load, json_write


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
_CREDENTIAL_SHAPE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{20,}|bearer\s+[A-Za-z0-9._-]{20,})",
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
_CACHE_FIELDS = {
    "schema_version",
    "status",
    "cache_key",
    "input_hash",
    "prompt_schema",
    "provider",
    "model",
    "version",
    "response",
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


def keyword_cache_key(question: str, config: KeywordProviderConfig) -> str:
    validate_provider_config(config)
    material = {
        "input_hash": keyword_input_hash(question),
        "provider": config.provider,
        "model": config.model,
        "version": config.version,
        "prompt_schema": KEYWORD_PROMPT_SCHEMA,
    }
    serialized = json.dumps(material, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("ascii")).hexdigest()


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
        if _CREDENTIAL_SHAPE.search(normalized):
            raise CkbError(f"keyword provider {name} contains credential-shaped text")
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


def _failure(question: str, config: KeywordProviderConfig, failure_type: str) -> dict[str, Any]:
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
        "usage": _usage({}),
    }


def _cache_path(output: Path, cache_key: str) -> Path:
    return output.resolve() / "workspace-meta" / "keyword-fallback" / "cache" / f"{cache_key}.json"


def _cache_record(question: str, config: KeywordProviderConfig, response: dict[str, Any]) -> dict[str, Any]:
    cache_key = keyword_cache_key(question, config)
    return {
        "schema_version": KEYWORD_FALLBACK_SCHEMA_VERSION,
        "status": "passed",
        "cache_key": cache_key,
        "input_hash": keyword_input_hash(question),
        "prompt_schema": KEYWORD_PROMPT_SCHEMA,
        "provider": config.provider,
        "model": config.model,
        "version": config.version,
        "response": response,
    }


def _read_cache(output: Path, question: str, config: KeywordProviderConfig) -> dict[str, Any] | None:
    path = _cache_path(output, keyword_cache_key(question, config))
    if not path.is_file():
        return None
    try:
        record = json_load(path)
        expected = _cache_record(question, config, record.get("response") if isinstance(record, dict) else {})
        if not isinstance(record, dict) or set(record) != _CACHE_FIELDS:
            return None
        for name in _CACHE_FIELDS - {"response"}:
            if record.get(name) != expected.get(name):
                return None
        response = validate_provider_response(record.get("response"), question=question, config=config)
        if response.get("status") != "passed":
            return None
        return response
    except (CkbError, OSError, ValueError, TypeError):
        return None


def _write_cache(output: Path, question: str, config: KeywordProviderConfig, response: dict[str, Any]) -> Path:
    record = _cache_record(question, config, response)
    path = _cache_path(output, record["cache_key"])
    json_write(path, record)
    return path


def _transient(failure_type: str) -> bool:
    return failure_type in {"process-failed", "rate-limit", "timeout", "unavailable"}


def run_keyword_provider(
    output: Path,
    question: str,
    config: KeywordProviderConfig,
    *,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Call one explicit command/stdio adapter and return only validated fields."""

    validate_provider_config(config)
    missing = sorted(name for name in config.required_environment if not os.environ.get(name))
    if missing:
        return {
            **_failure(question, config, "missing-credentials"),
            "attempts": 0,
            "latency_ms": 0.0,
            "cache_hit": False,
            "missing_environment": missing,
        }
    if use_cache:
        cached = _read_cache(output, question, config)
        if cached is not None:
            return {
                **cached,
                "attempts": 0,
                "latency_ms": 0.0,
                "cache_hit": True,
                "cache_key": keyword_cache_key(question, config),
            }
    request = json.dumps(canonical_keyword_request(question), ensure_ascii=False, separators=(",", ":"))
    started = time.perf_counter_ns()
    attempts = 0
    response: dict[str, Any] = _failure(question, config, "unavailable")
    for attempt in range(config.retries + 1):
        attempts = attempt + 1
        failure_type: str | None = None
        try:
            completed = subprocess.run(
                list(config.command),
                input=request,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=config.timeout_seconds,
                check=False,
                **background_process_options(),
            )
            if completed.returncode:
                diagnostic = f"{completed.stdout}\n{completed.stderr}"
                failure_type = "rate-limit" if re.search(r"rate[ _-]*limit|too many requests|\b429\b", diagnostic, re.IGNORECASE) else "process-failed"
                response = _failure(question, config, failure_type)
            else:
                try:
                    parsed = parse_provider_json(completed.stdout)
                    response = validate_provider_response(parsed, question=question, config=config)
                    failure_type = response.get("failure_type") if response.get("status") != "passed" else None
                except CkbError as exc:
                    failure_type = "invalid-json" if "invalid JSON" in str(exc) else "invalid-output"
                    response = _failure(question, config, failure_type)
        except subprocess.TimeoutExpired:
            failure_type = "timeout"
            response = _failure(question, config, failure_type)
        except (FileNotFoundError, OSError):
            failure_type = "unavailable"
            response = _failure(question, config, failure_type)
        if response.get("status") == "passed" or not failure_type or not _transient(failure_type):
            break
    latency_ms = round((time.perf_counter_ns() - started) / 1_000_000, 6)
    result = {
        **response,
        "attempts": attempts,
        "latency_ms": latency_ms,
        "cache_hit": False,
        "cache_key": keyword_cache_key(question, config),
    }
    if response.get("status") == "passed" and use_cache:
        result["cache"] = str(_write_cache(output, question, config, response).resolve())
    return result


def audit_keyword_cache(output: Path) -> dict[str, Any]:
    """Check bounded cache records without reading or requiring provider secrets."""

    root = output.resolve() / "workspace-meta" / "keyword-fallback" / "cache"
    if not root.is_dir():
        return {"schema_version": 1, "status": "passed", "records": 0, "errors": []}
    errors: list[str] = []
    records = 0
    for path in sorted(root.glob("*.json")):
        records += 1
        try:
            value = json_load(path)
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name}: invalid cache JSON: {type(exc).__name__}")
            continue
        if not isinstance(value, dict) or set(value) != _CACHE_FIELDS:
            errors.append(f"{path.name}: fields differ from the fixed cache schema")
            continue
        if value.get("schema_version") != KEYWORD_FALLBACK_SCHEMA_VERSION or value.get("status") != "passed":
            errors.append(f"{path.name}: cache status or schema mismatch")
        if value.get("prompt_schema") != KEYWORD_PROMPT_SCHEMA:
            errors.append(f"{path.name}: prompt schema mismatch")
        cache_key = value.get("cache_key")
        if not isinstance(cache_key, str) or not re.fullmatch(r"[0-9a-f]{64}", cache_key) or path.stem != cache_key:
            errors.append(f"{path.name}: cache key mismatch")
        input_hash = value.get("input_hash")
        if not isinstance(input_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", input_hash):
            errors.append(f"{path.name}: input hash is invalid")
        for name in ("provider", "model", "version"):
            try:
                _machine_token(value.get(name), name)
            except CkbError as exc:
                errors.append(f"{path.name}: {exc}")
        serialized = json.dumps(value, ensure_ascii=False)
        if _CREDENTIAL_SHAPE.search(serialized):
            errors.append(f"{path.name}: cache contains credential-shaped text")
    unexpected = [path.name for path in root.iterdir() if not path.is_file() or path.suffix != ".json"]
    errors.extend(f"unexpected keyword cache entry: {name}" for name in sorted(unexpected))
    return {
        "schema_version": KEYWORD_FALLBACK_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "records": records,
        "errors": errors,
    }


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
