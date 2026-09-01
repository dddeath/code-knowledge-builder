"""Fixed, auditable benchmark for the optional keyword fallback."""

from __future__ import annotations

import os
from pathlib import Path
import re
import time
from typing import Any

from .common import CkbError, json_load, json_write
from .keyword_fallback import (
    KeywordFallbackOptions,
    KeywordProviderConfig,
    keyword_cache_path,
    keyword_input_hash,
)
from .machine_knowledge import retrieve_machine


KEYWORD_BENCHMARK_SCHEMA_VERSION = 1
MAX_BENCHMARK_CASES = 100
_CASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}")


def _text_list(value: Any, name: str, maximum: int = 32) -> list[str]:
    if not isinstance(value, list) or not value or len(value) > maximum:
        raise CkbError(f"keyword benchmark {name} must contain 1 to {maximum} strings")
    if any(not isinstance(item, str) or not item.strip() or len(item) > 512 for item in value):
        raise CkbError(f"keyword benchmark {name} contains an invalid string")
    return [item.strip() for item in value]


def load_keyword_benchmark(path: Path) -> list[dict[str, Any]]:
    value = json_load(path.resolve())
    if not isinstance(value, dict) or set(value) != {"schema_version", "cases"}:
        raise CkbError("keyword benchmark file must contain only schema_version and cases")
    if value.get("schema_version") != KEYWORD_BENCHMARK_SCHEMA_VERSION:
        raise CkbError("keyword benchmark schema version mismatch")
    cases = value.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_BENCHMARK_CASES:
        raise CkbError(f"keyword benchmark must contain 1 to {MAX_BENCHMARK_CASES} cases")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in cases:
        if not isinstance(item, dict):
            raise CkbError("keyword benchmark cases must be objects")
        allowed = {"id", "question", "expected_names", "expected_source_paths", "budget", "max_pages", "profile"}
        if set(item) - allowed:
            raise CkbError("keyword benchmark case contains unsupported fields")
        case_id = item.get("id")
        if not isinstance(case_id, str) or not _CASE_ID.fullmatch(case_id) or case_id in seen:
            raise CkbError("keyword benchmark case id must be unique and bounded")
        seen.add(case_id)
        question = item.get("question")
        if not isinstance(question, str) or not question.strip() or len(question) > 12_000:
            raise CkbError("keyword benchmark question must contain 1 to 12000 characters")
        budget = item.get("budget", 1800)
        max_pages = item.get("max_pages", 8)
        profile = item.get("profile", "fast")
        if isinstance(budget, bool) or not isinstance(budget, int) or not 200 <= budget <= 1_000_000:
            raise CkbError("keyword benchmark budget must be an integer in [200, 1000000]")
        if isinstance(max_pages, bool) or not isinstance(max_pages, int) or not 1 <= max_pages <= 32:
            raise CkbError("keyword benchmark max_pages must be an integer in [1, 32]")
        if profile not in {"fast", "precise"}:
            raise CkbError("keyword benchmark profile must be fast or precise")
        normalized.append(
            {
                "id": case_id,
                "question": question.strip(),
                "expected_names": _text_list(item.get("expected_names"), "expected_names"),
                "expected_source_paths": _text_list(item.get("expected_source_paths"), "expected_source_paths"),
                "budget": budget,
                "max_pages": max_pages,
                "profile": profile,
            }
        )
    return normalized


def _location(result: dict[str, Any], expected_names: list[str], expected_paths: list[str]) -> dict[str, Any]:
    selected = result.get("selected_entities") or []
    names = {
        str(value).casefold()
        for item in selected
        for value in (item.get("name"), item.get("qualified_name"))
        if value
    }
    paths = {str(item.get("source_path")).casefold() for item in selected if item.get("source_path")}
    expected_name_ids = {value.casefold() for value in expected_names}
    expected_path_ids = {value.replace("\\", "/").casefold() for value in expected_paths}
    matched_names = sorted(value for value in expected_names if value.casefold() in names)
    matched_paths = sorted(
        value
        for value in expected_paths
        if value.replace("\\", "/").casefold() in {path.replace("\\", "/") for path in paths}
    )
    total = len(expected_name_ids) + len(expected_path_ids)
    matched = len(matched_names) + len(matched_paths)
    return {
        "score": round(matched / total, 6) if total else 0.0,
        "matched_names": matched_names,
        "matched_source_paths": matched_paths,
        "selected_entities": len(selected),
        "selected_source_paths": len(paths),
        "estimated_tokens": result.get("estimated_tokens"),
        "status": result.get("status"),
    }


def _timed_retrieval(
    output: Path,
    case: dict[str, Any],
    options: KeywordFallbackOptions | None,
) -> tuple[dict[str, Any], float]:
    started = time.perf_counter_ns()
    result = retrieve_machine(
        output,
        case["question"],
        case["budget"],
        case["max_pages"],
        case["profile"],
        keyword_fallback=options,
    )
    elapsed = round((time.perf_counter_ns() - started) / 1_000_000, 6)
    return result, elapsed


def _restore_cache(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".benchmark-restore")
    temporary.write_bytes(previous)
    os.replace(temporary, path)


def run_keyword_benchmark(
    output: Path,
    cases_path: Path,
    report_path: Path,
    config: KeywordProviderConfig,
) -> dict[str, Any]:
    """Compare baseline/cold/hot retrieval without leaving benchmark cache state."""

    output = output.resolve()
    cases_path = cases_path.resolve()
    report_path = report_path.resolve()
    cases = load_keyword_benchmark(cases_path)
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    for case in cases:
        cache_path = keyword_cache_path(output, case["question"], config)
        previous_cache = cache_path.read_bytes() if cache_path.is_file() else None
        cache_path.unlink(missing_ok=True)
        try:
            baseline, baseline_ms = _timed_retrieval(output, case, None)
            cold, cold_ms = _timed_retrieval(
                output,
                case,
                KeywordFallbackOptions(config=config, force=True, use_cache=True),
            )
            hot, hot_ms = _timed_retrieval(
                output,
                case,
                KeywordFallbackOptions(config=config, force=True, use_cache=True),
            )
        finally:
            _restore_cache(cache_path, previous_cache)
        baseline_location = _location(baseline, case["expected_names"], case["expected_source_paths"])
        cold_location = _location(cold, case["expected_names"], case["expected_source_paths"])
        cold_fallback = cold.get("keyword_fallback") or {}
        hot_fallback = hot.get("keyword_fallback") or {}
        cold_provider = cold_fallback.get("provider") or {}
        hot_provider = hot_fallback.get("provider") or {}
        case_errors: list[str] = []
        if cold_fallback.get("status") != "passed":
            case_errors.append(f"cold fallback status is {cold_fallback.get('status')}")
        if hot_fallback.get("status") != "passed" or not hot_provider.get("cache_hit"):
            case_errors.append("hot fallback did not use the validated cache")
        quality_delta = round(cold_location["score"] - baseline_location["score"], 6)
        results.append(
            {
                "id": case["id"],
                "input_hash": keyword_input_hash(case["question"]),
                "profile": case["profile"],
                "budget": case["budget"],
                "baseline": {"elapsed_ms": baseline_ms, "location": baseline_location},
                "cold": {
                    "elapsed_ms": cold_ms,
                    "provider_latency_ms": cold_provider.get("latency_ms"),
                    "location": cold_location,
                    "usage": cold_provider.get("usage"),
                },
                "hot": {
                    "elapsed_ms": hot_ms,
                    "provider_latency_ms": hot_provider.get("latency_ms"),
                    "cache_hit": bool(hot_provider.get("cache_hit")),
                    "usage": hot_provider.get("usage"),
                    "cached_usage": hot_provider.get("cached_usage"),
                },
                "quality_delta": quality_delta,
                "quality_gain": quality_delta > 0,
                "errors": case_errors,
            }
        )
        errors.extend(f"{case['id']}: {error}" for error in case_errors)
    mean_delta = round(sum(item["quality_delta"] for item in results) / len(results), 6)
    report = {
        "schema_version": KEYWORD_BENCHMARK_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "benchmark": "ckb-keyword-fallback-fixed-v1",
        "cases_file": str(cases_path),
        "provider": {"provider": config.provider, "model": config.model, "version": config.version},
        "cases": results,
        "summary": {
            "cases": len(results),
            "quality_gain_cases": sum(1 for item in results if item["quality_gain"]),
            "mean_quality_delta": mean_delta,
            "quality_claim": "measured-gain" if mean_delta > 0 else "not-demonstrated",
            "errors": errors,
        },
        "report": str(report_path),
    }
    json_write(report_path, report)
    return report
