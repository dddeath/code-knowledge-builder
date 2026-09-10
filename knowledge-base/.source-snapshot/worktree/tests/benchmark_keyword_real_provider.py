"""Run the frozen 12-case keyword fallback benchmark against a real Provider."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import statistics
import sys
import time
from typing import Any, Iterator


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPOSITORY_ROOT / "tests"))
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import benchmark_chinese_retrieval as effect  # noqa: E402
from ckb_core import machine_knowledge as machine  # noqa: E402
from ckb_core.keyword_fallback import (  # noqa: E402
    KeywordFallbackOptions,
    KeywordProviderConfig,
    keyword_cache_path,
)


SCHEMA_VERSION = 1
FIXTURE = REPOSITORY_ROOT / "tests" / "fixtures" / "keyword_provider.py"
REQUIRED_FAULT_MODES = {
    "irrelevant-output": None,
    "timeout": "timeout",
    "invalid-json": "invalid-json",
    "empty-output": "invalid-output",
    "too-many-keywords": "invalid-output",
    "missing-credentials": "missing-credentials",
}


def json_load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = (len(ordered) - 1) * probability
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def marker_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines()) if path.is_file() else 0


@contextmanager
def environment(values: dict[str, str | None]) -> Iterator[None]:
    previous = {name: os.environ.get(name) for name in values}
    for name, value in values.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def validate_protocol(protocol_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol_path = protocol_path.resolve()
    protocol = json_load(protocol_path)
    expected_fields = {
        "schema_version",
        "status",
        "frozen_before_run",
        "benchmark",
        "source_protocol",
        "source_protocol_sha256",
        "corpus",
        "provider",
        "runs",
        "invocation_contract",
        "fault_probes",
        "metrics",
        "quality_interpretation",
        "questions",
    }
    if set(protocol) != expected_fields:
        raise ValueError("real Provider protocol fields differ from the frozen schema")
    if protocol.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("real Provider protocol schema version mismatch")
    if protocol.get("status") != "frozen" or protocol.get("frozen_before_run") is not True:
        raise ValueError("real Provider protocol must be frozen before execution")
    source_protocol_path = REPOSITORY_ROOT / str(protocol["source_protocol"])
    if not source_protocol_path.is_file() or sha256(source_protocol_path) != protocol["source_protocol_sha256"]:
        raise ValueError("source 12-question protocol is missing or drifted")
    source_protocol = json_load(source_protocol_path)
    questions = protocol.get("questions")
    if not isinstance(questions, list) or len(questions) != 12:
        raise ValueError("real Provider protocol requires exactly 12 cases")
    source_questions = source_protocol.get("questions")
    stripped_questions = [
        {name: value for name, value in item.items() if name != "coverage"}
        for item in questions
    ]
    if stripped_questions != source_questions:
        raise ValueError("real Provider cases differ from the frozen source questions")
    if len({item.get("id") for item in questions}) != 12:
        raise ValueError("real Provider case ids must be unique")
    coverage = {tag for item in questions for tag in item.get("coverage", [])}
    if not {"chinese-natural-language", "source-identifier"}.issubset(coverage):
        raise ValueError("real Provider cases must cover Chinese natural language and source identifiers")
    fault_probes = protocol.get("fault_probes")
    if not isinstance(fault_probes, list):
        raise ValueError("real Provider fault probes must be an array")
    if {item.get("mode") for item in fault_probes} != set(REQUIRED_FAULT_MODES):
        raise ValueError("real Provider fault modes differ from the frozen matrix")
    for item in fault_probes:
        if item.get("expected_failure_type") != REQUIRED_FAULT_MODES[item["mode"]]:
            raise ValueError(f"fault probe expectation differs for {item['mode']}")
        if item.get("question_id") not in {question["id"] for question in questions}:
            raise ValueError("fault probe references an unknown question")
    runs = protocol.get("runs") or {}
    if runs != {"baseline": 1, "real_provider_cold": 1, "real_provider_hot": 1}:
        raise ValueError("real Provider run counts differ from the frozen protocol")
    provider = protocol.get("provider") or {}
    if provider.get("adapter") != "tests/fixtures/keyword_provider.py":
        raise ValueError("real Provider adapter differs from the frozen protocol")
    if provider.get("usage_source") != "codex-exec-turn.completed":
        raise ValueError("real Provider usage source differs from the frozen protocol")
    if provider.get("cost_source") != "not-reported-by-provider-cli":
        raise ValueError("real Provider cost boundary differs from the frozen protocol")
    return protocol, source_protocol


def real_config(protocol: dict[str, Any], provider_executable: str | None) -> KeywordProviderConfig | None:
    if not provider_executable:
        return None
    provider = protocol["provider"]
    return KeywordProviderConfig(
        command=(sys.executable, str(FIXTURE)),
        provider=provider["name"],
        model=provider["model"],
        version=provider["version"],
        timeout_seconds=float(provider["adapter_timeout_seconds"]),
        retries=int(provider["retries"]),
        required_environment=("CKB_REAL_KEYWORD_PROVIDER_EXECUTABLE",),
    )


def not_executed_report(
    protocol_path: Path,
    output: Path,
    protocol: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "not-executed",
        "benchmark": protocol["benchmark"],
        "protocol": str(protocol_path.resolve()),
        "protocol_sha256": sha256(protocol_path.resolve()),
        "checks": {"protocol_frozen": True, "real_provider_configured": False},
        "cases": [],
        "fault_probes": [],
        "invocation_observations": {},
        "summary": {
            "cases": 12,
            "real_provider_actual_calls": 0,
            "quality_claim": "not-executed",
            "reason_zh": reason,
        },
        "real_provider": {
            "status": "not-executed",
            "actual_calls": 0,
            "effect_claim": "not-executed",
        },
        "artifacts": {"report": str((output / "report.json").resolve())},
    }
    json_write(output / "report.json", report)
    return report


def timed_retrieval(
    corpus: Path,
    question: dict[str, Any],
    source_protocol: dict[str, Any],
    options: KeywordFallbackOptions | None = None,
) -> tuple[dict[str, Any], float]:
    started = time.perf_counter_ns()
    result = machine.retrieve_machine(
        corpus,
        question["question"],
        int(source_protocol["budget_tokens"]),
        int(source_protocol["max_results"]),
        source_protocol["profile"],
        keyword_fallback=options,
    )
    return result, round((time.perf_counter_ns() - started) / 1_000_000, 6)


def measured_result(result: dict[str, Any], elapsed_ms: float, question: dict[str, Any]) -> dict[str, Any]:
    documents = effect.unique_ranked_documents(result)
    return {
        "elapsed_ms": elapsed_ms,
        "status": result.get("status"),
        "terms": result.get("terms") or [],
        "anchors": result.get("anchors") or [],
        "selected_documents": documents,
        "quality": effect.quality_for_ranking(documents, question["relevance"]),
        "estimated_tokens": result.get("estimated_tokens", 0),
        "signature": effect.result_signature(result, documents),
    }


def fallback_observation(result: dict[str, Any]) -> dict[str, Any]:
    fallback = result.get("keyword_fallback") or {}
    provider = fallback.get("provider") or {}
    return {
        "status": fallback.get("status"),
        "trigger": fallback.get("trigger"),
        "provider": {
            key: provider.get(key)
            for key in (
                "status",
                "failure_type",
                "provider",
                "model",
                "version",
                "attempts",
                "latency_ms",
                "cache_hit",
                "usage",
                "cached_usage",
                "missing_environment",
            )
            if provider.get(key) is not None
        },
        "input_terms": {
            "terms": (fallback.get("original") or {}).get("terms") or [],
            "anchors": (fallback.get("original") or {}).get("anchors") or [],
        },
        "provider_output": fallback.get("model_candidates") or {
            "keywords": [],
            "anchors": [],
            "rewrites": [],
        },
        "validated_output": fallback.get("validated_extensions") or {
            "terms": [],
            "anchors": [],
            "rewrites": [],
        },
        "final": fallback.get("final") or {},
    }


def run_real_cases(
    corpus: Path,
    protocol: dict[str, Any],
    source_protocol: dict[str, Any],
    config: KeywordProviderConfig,
    provider_executable: str,
    marker: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    provider = protocol["provider"]
    marker.unlink(missing_ok=True)
    rows: list[dict[str, Any]] = []
    allow_observation: dict[str, Any] = {}
    with environment(
        {
            "CKB_FAKE_KEYWORD_PROVIDER_MODE": "codex-cli",
            "CKB_FAKE_KEYWORD_PROVIDER_MARKER": str(marker.resolve()),
            "CKB_FAKE_KEYWORD_PROVIDER_NAME": config.provider,
            "CKB_FAKE_KEYWORD_PROVIDER_MODEL": config.model,
            "CKB_FAKE_KEYWORD_PROVIDER_VERSION": config.version,
            "CKB_REAL_KEYWORD_PROVIDER_EXECUTABLE": provider_executable,
            "CKB_REAL_KEYWORD_PROVIDER_TIMEOUT": str(provider["cli_timeout_seconds"]),
        }
    ):
        for index, question in enumerate(protocol["questions"]):
            machine._RETRIEVAL_STATIC_CACHE.clear()
            before_default = marker_count(marker)
            baseline_result, baseline_ms = timed_retrieval(corpus, question, source_protocol)
            after_default = marker_count(marker)
            baseline = measured_result(baseline_result, baseline_ms, question)
            if index == 0:
                before_allow = marker_count(marker)
                allow_result, allow_ms = timed_retrieval(
                    corpus,
                    question,
                    source_protocol,
                    KeywordFallbackOptions(config=config, force=False, use_cache=False),
                )
                allow_observation = {
                    "input_status": baseline_result.get("status"),
                    "elapsed_ms": allow_ms,
                    "provider_process_starts": marker_count(marker) - before_allow,
                    "fallback": fallback_observation(allow_result),
                }
            cache_path = keyword_cache_path(corpus, question["question"], config)
            cache_path.unlink(missing_ok=True)
            machine._RETRIEVAL_STATIC_CACHE.clear()
            before_cold = marker_count(marker)
            cold_result, cold_ms = timed_retrieval(
                corpus,
                question,
                source_protocol,
                KeywordFallbackOptions(config=config, force=True, use_cache=True),
            )
            after_cold = marker_count(marker)
            hot_result, hot_ms = timed_retrieval(
                corpus,
                question,
                source_protocol,
                KeywordFallbackOptions(config=config, force=True, use_cache=True),
            )
            after_hot = marker_count(marker)
            cold = measured_result(cold_result, cold_ms, question)
            hot = measured_result(hot_result, hot_ms, question)
            cold_fallback = fallback_observation(cold_result)
            hot_fallback = fallback_observation(hot_result)
            quality_delta = {
                name: round(cold["quality"][name] - baseline["quality"][name], 9)
                for name in ("recall_at_8", "mrr_at_8", "ndcg_at_8")
            }
            rows.append(
                {
                    "id": question["id"],
                    "question": question["question"],
                    "coverage": question["coverage"],
                    "relevance": question["relevance"],
                    "default_provider_process_starts": after_default - before_default,
                    "cold_provider_process_starts": after_cold - before_cold,
                    "hot_provider_process_starts": after_hot - after_cold,
                    "baseline": baseline,
                    "real_provider_cold": {
                        **cold,
                        "fallback": cold_fallback,
                        "additional_latency_ms": round(cold_ms - baseline_ms, 6),
                    },
                    "real_provider_hot": {**hot, "fallback": hot_fallback},
                    "quality_delta": quality_delta,
                }
            )
    return rows, allow_observation


def fault_config(*, timeout: float = 2.0, required_environment: tuple[str, ...] = ()) -> KeywordProviderConfig:
    return KeywordProviderConfig(
        command=(sys.executable, str(FIXTURE)),
        provider="fixture",
        model="fault-matrix",
        version="1",
        timeout_seconds=timeout,
        retries=0,
        required_environment=required_environment,
    )


def fault_probe_checks(row: dict[str, Any]) -> dict[str, bool]:
    """Recompute one fault verdict from persisted, bounded benchmark fields."""

    expected_failure = row["expected_failure_type"]
    baseline = row["baseline"]
    observed = row["observed"]
    fallback = observed["fallback"]
    provider = fallback["provider"]
    if expected_failure is None:
        return {
            "provider_output_accepted": provider.get("status") == "passed",
            "retrieval_not_blocked": observed["status"] in {"passed", "needs-source-read"},
            "recall_not_regressed": observed["quality"]["recall_at_8"] >= baseline["quality"]["recall_at_8"],
        }
    return {
        "structured_failure_type": provider.get("failure_type") == expected_failure,
        "fallback_status": fallback["status"] == "fallback",
        "original_status_preserved": observed["status"] == baseline["status"],
        "original_ranking_preserved": observed["signature"] == baseline["signature"],
        "retrieval_not_blocked": True,
        "adapter_attempt_count": provider.get("attempts")
        == (0 if row["mode"] == "missing-credentials" else 1),
    }


def run_fault_probes(
    corpus: Path,
    protocol: dict[str, Any],
    source_protocol: dict[str, Any],
    marker: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    marker.unlink(missing_ok=True)
    questions = {item["id"]: item for item in protocol["questions"]}
    rows: list[dict[str, Any]] = []
    base_environment = {
        "CKB_FAKE_KEYWORD_PROVIDER_MARKER": str(marker.resolve()),
        "CKB_FAKE_KEYWORD_PROVIDER_NAME": "fixture",
        "CKB_FAKE_KEYWORD_PROVIDER_MODEL": "fault-matrix",
        "CKB_FAKE_KEYWORD_PROVIDER_VERSION": "1",
    }
    for probe in protocol["fault_probes"]:
        question = questions[probe["question_id"]]
        machine._RETRIEVAL_STATIC_CACHE.clear()
        baseline_result, baseline_ms = timed_retrieval(corpus, question, source_protocol)
        baseline = measured_result(baseline_result, baseline_ms, question)
        mode = probe["mode"]
        required_name = "CKB_TEST_KEYWORD_PROVIDER_CREDENTIAL"
        config = fault_config(
            timeout=0.1 if mode == "timeout" else 2.0,
            required_environment=(required_name,) if mode == "missing-credentials" else (),
        )
        values = {
            **base_environment,
            "CKB_FAKE_KEYWORD_PROVIDER_MODE": mode,
            required_name: None if mode == "missing-credentials" else "fixture-present",
        }
        before = marker_count(marker)
        with environment(values):
            failed_result, failed_ms = timed_retrieval(
                corpus,
                question,
                source_protocol,
                KeywordFallbackOptions(config=config, force=True, use_cache=False),
            )
        starts = marker_count(marker) - before
        observed = measured_result(failed_result, failed_ms, question)
        fallback = fallback_observation(failed_result)
        row = {
            "id": probe["id"],
            "mode": mode,
            "evidence_class": "fault-injection-fixture",
            "question_id": question["id"],
            "expected_failure_type": probe["expected_failure_type"],
            "provider_process_starts": starts,
            "baseline": baseline,
            "observed": {**observed, "fallback": fallback},
        }
        checks = fault_probe_checks(row)
        rows.append({**row, "checks": checks, "status": "passed" if all(checks.values()) else "failed"})

    trigger_question = protocol["invocation_contract"]["allow_needs_source_read_probe"]
    machine._RETRIEVAL_STATIC_CACHE.clear()
    baseline_result = machine.retrieve_machine(
        corpus,
        trigger_question,
        int(source_protocol["budget_tokens"]),
        int(source_protocol["max_results"]),
        source_protocol["profile"],
    )
    before = marker_count(marker)
    with environment({**base_environment, "CKB_FAKE_KEYWORD_PROVIDER_MODE": "passed"}):
        allow_result = machine.retrieve_machine(
            corpus,
            trigger_question,
            int(source_protocol["budget_tokens"]),
            int(source_protocol["max_results"]),
            source_protocol["profile"],
            keyword_fallback=KeywordFallbackOptions(config=fault_config(), force=False, use_cache=False),
        )
    allow_fallback = fallback_observation(allow_result)
    allow_probe = {
        "input_status": baseline_result.get("status"),
        "provider_process_starts": marker_count(marker) - before,
        "fallback": allow_fallback,
        "status": "passed"
        if baseline_result.get("status") == "needs-source-read"
        and marker_count(marker) - before == 1
        and allow_fallback.get("trigger") == "needs-source-read"
        else "failed",
    }
    return rows, allow_probe


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    names = ("recall_at_8", "mrr_at_8", "ndcg_at_8")
    baseline = {name: round(statistics.mean(row["baseline"]["quality"][name] for row in rows), 9) for name in names}
    real = {
        name: round(statistics.mean(row["real_provider_cold"]["quality"][name] for row in rows), 9)
        for name in names
    }
    delta = {name: round(real[name] - baseline[name], 9) for name in names}
    if all(value >= 0 for value in delta.values()) and any(value > 0 for value in delta.values()):
        claim = "measured-gain"
    elif all(value == 0 for value in delta.values()):
        claim = "not-demonstrated"
    else:
        claim = "regression-observed"
    cold_provider = [row["real_provider_cold"]["fallback"]["provider"] for row in rows]
    input_tokens = sum(int(item.get("usage", {}).get("input_tokens", 0)) for item in cold_provider)
    output_tokens = sum(int(item.get("usage", {}).get("output_tokens", 0)) for item in cold_provider)
    additional = [float(row["real_provider_cold"]["additional_latency_ms"]) for row in rows]
    return {
        "cases": len(rows),
        "baseline_quality": baseline,
        "real_provider_quality": real,
        "quality_delta": delta,
        "quality_claim": claim,
        "recall_gain_cases": sum(1 for row in rows if row["quality_delta"]["recall_at_8"] > 0),
        "recall_regression_cases": sum(1 for row in rows if row["quality_delta"]["recall_at_8"] < 0),
        "mrr_gain_cases": sum(1 for row in rows if row["quality_delta"]["mrr_at_8"] > 0),
        "mrr_regression_cases": sum(1 for row in rows if row["quality_delta"]["mrr_at_8"] < 0),
        "ndcg_gain_cases": sum(1 for row in rows if row["quality_delta"]["ndcg_at_8"] > 0),
        "ndcg_regression_cases": sum(1 for row in rows if row["quality_delta"]["ndcg_at_8"] < 0),
        "real_provider_actual_calls": sum(int(item.get("attempts", 0)) for item in cold_provider),
        "real_provider_successful_calls": sum(item.get("status") == "passed" for item in cold_provider),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost_usd": None,
        "cost_status": "not-reported-by-provider-cli",
        "provider_latency_ms_p50": round(percentile([float(item.get("latency_ms", 0.0)) for item in cold_provider], 0.5), 6),
        "provider_latency_ms_p95": round(percentile([float(item.get("latency_ms", 0.0)) for item in cold_provider], 0.95), 6),
        "additional_latency_ms_p50": round(percentile(additional, 0.5), 6),
        "additional_latency_ms_p95": round(percentile(additional, 0.95), 6),
        "hot_cache_hits": sum(bool(row["real_provider_hot"]["fallback"]["provider"].get("cache_hit")) for row in rows),
    }


def run_benchmark(
    protocol_path: Path,
    source_corpus: Path,
    output: Path,
    provider_executable: str | None,
    *,
    keep_corpus: bool = False,
) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    source_corpus = source_corpus.resolve()
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    protocol, source_protocol = validate_protocol(protocol_path)
    config = real_config(protocol, provider_executable)
    if config is None:
        return not_executed_report(
            protocol_path,
            output,
            protocol,
            "未传入真实 Provider 可执行文件；未启动模型，也不生成效果结论。",
        )
    executable_path = Path(provider_executable)
    if not executable_path.is_file() and shutil.which(provider_executable) is None:
        return not_executed_report(
            protocol_path,
            output,
            protocol,
            "真实 Provider 可执行文件不存在；未启动模型，也不生成效果结论。",
        )
    effect.validate_protocol(source_protocol, source_corpus)
    corpus = output / "corpus"
    corpus_info = effect.copy_corpus(source_corpus, corpus)
    real_marker = output / "real-provider-starts.log"
    fault_marker = output / "fault-provider-starts.log"
    try:
        rows, allow_passed = run_real_cases(
            corpus,
            protocol,
            source_protocol,
            config,
            provider_executable,
            real_marker,
        )
        fault_rows, allow_needs_source = run_fault_probes(
            corpus,
            protocol,
            source_protocol,
            fault_marker,
        )
        summary = summarize(rows)
        source_machine_after = sha256(source_corpus / "machine/knowledge.sqlite")
        source_legacy_after = sha256(source_corpus / "agent-index.sqlite")
        copied_machine_after = sha256(corpus / "machine/knowledge.sqlite")
        copied_legacy_after = sha256(corpus / "agent-index.sqlite")
        with sqlite3.connect(corpus / "machine/knowledge.sqlite") as connection:
            machine_integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        with sqlite3.connect(corpus / "agent-index.sqlite") as connection:
            legacy_integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        checks = {
            "protocol_frozen": True,
            "real_provider_configured": True,
            "case_count_exact": len(rows) == 12,
            "default_started_no_provider": all(row["default_provider_process_starts"] == 0 for row in rows),
            "allow_passed_started_no_provider": allow_passed.get("provider_process_starts") == 0
            and allow_passed.get("fallback", {}).get("status") == "skipped",
            "allow_needs_source_read_started_provider": allow_needs_source.get("status") == "passed",
            "force_started_once_per_case": all(row["cold_provider_process_starts"] == 1 for row in rows),
            "real_provider_calls_exact": summary["real_provider_actual_calls"] == 12,
            "real_provider_successes_exact": summary["real_provider_successful_calls"] == 12,
            "hot_cache_used_without_provider_start": summary["hot_cache_hits"] == 12
            and all(row["hot_provider_process_starts"] == 0 for row in rows),
            "fault_probe_count_exact": len(fault_rows) == len(REQUIRED_FAULT_MODES),
            "fault_probes_passed": all(row["status"] == "passed" for row in fault_rows),
            "source_corpus_unchanged": source_machine_after == corpus_info["source_machine_sha256_before"]
            and source_legacy_after == corpus_info["source_legacy_sha256_before"],
            "benchmark_indexes_unchanged": copied_machine_after == corpus_info["copied_machine_sha256"]
            and copied_legacy_after == corpus_info["copied_legacy_sha256"],
            "copied_sqlite_integrity": machine_integrity == "ok" and legacy_integrity == "ok",
        }
        raw = {
            "schema_version": SCHEMA_VERSION,
            "benchmark": protocol["benchmark"],
            "protocol": str(protocol_path),
            "protocol_sha256": sha256(protocol_path),
            "source_protocol_sha256": protocol["source_protocol_sha256"],
            "corpus": {
                **corpus_info,
                "source_machine_sha256_after": source_machine_after,
                "source_legacy_sha256_after": source_legacy_after,
                "copied_machine_sha256_after": copied_machine_after,
                "copied_legacy_sha256_after": copied_legacy_after,
                "integrity_after": {"machine": machine_integrity, "legacy": legacy_integrity},
            },
            "cases": rows,
            "fault_probes": fault_rows,
        }
        report = {
            "schema_version": SCHEMA_VERSION,
            "status": "passed" if all(checks.values()) else "failed",
            "benchmark": protocol["benchmark"],
            "protocol": str(protocol_path),
            "protocol_sha256": raw["protocol_sha256"],
            "checks": checks,
            "invocation_observations": {
                "default": {"condition": "没有显式 fallback 选项", "provider_process_starts": 0},
                "allow_after_passed": allow_passed,
                "allow_after_needs_source_read": allow_needs_source,
                "force": {"cases": 12, "provider_process_starts": marker_count(real_marker)},
            },
            "cases": rows,
            "fault_probes": fault_rows,
            "summary": summary,
            "real_provider": {
                "status": "executed",
                "name": config.provider,
                "model": config.model,
                "version": config.version,
                "actual_calls": summary["real_provider_actual_calls"],
                "effect_claim": summary["quality_claim"],
                "usage_source": protocol["provider"]["usage_source"],
                "cost_source": protocol["provider"]["cost_source"],
            },
            "environment": {
                "measured_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "platform": platform.platform(),
                "python": sys.version,
                "python_executable": sys.executable,
                "source_corpus": str(source_corpus),
                "output": str(output),
            },
            "artifacts": {
                "raw_results": str((output / "raw-results.json").resolve()),
                "report": str((output / "report.json").resolve()),
                "real_provider_starts": str(real_marker.resolve()),
                "fault_provider_starts": str(fault_marker.resolve()),
            },
        }
        json_write(output / "raw-results.json", raw)
        json_write(output / "report.json", report)
        return report
    finally:
        if not keep_corpus:
            shutil.rmtree(corpus, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--source-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provider-executable")
    parser.add_argument("--keep-corpus", action="store_true")
    arguments = parser.parse_args()
    report = run_benchmark(
        arguments.protocol,
        arguments.source_corpus,
        arguments.output,
        arguments.provider_executable,
        keep_corpus=arguments.keep_corpus,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"passed", "not-executed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
