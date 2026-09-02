"""Three-arm Chinese retrieval effect benchmark on one fixed CKB corpus.

The benchmark copies the completed corpus before execution.  The legacy arm
binds the exact tokenizer from the parent of commit 497f2ca only for the call;
the current arm uses the checked-out defaults; and the replay arm explicitly
forces the bounded keyword fallback with a deterministic command fixture.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as dt
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import sqlite3
import statistics
import sys
import time
from typing import Any, Iterator
import unicodedata


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from ckb_core import machine_knowledge as machine  # noqa: E402
from ckb_core.keyword_fallback import (  # noqa: E402
    KeywordFallbackOptions,
    KeywordProviderConfig,
    keyword_cache_path,
)


SCHEMA_VERSION = 1
ARM_IDS = ("legacy-deterministic", "current-deterministic", "llm-replay-fallback")
REPLAY_PROVIDER = "fixture"
REPLAY_MODEL = "chinese-retrieval-replay"
REPLAY_VERSION = "1"


def json_load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    rank = (len(ordered) - 1) * probability
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def _split_camel(value: str) -> list[str]:
    return [
        part
        for part in re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value).replace("::", " ").split()
        if part
    ]


def legacy_search_terms(text: str, limit: int = 64) -> list[str]:
    """Exact pre-497f2ca mechanical CJK bigram/trigram query terms."""

    normalized = unicodedata.normalize("NFKC", text)
    terms: set[str] = set()
    for run in re.findall(r"[A-Za-z0-9_.$:/\\#+-]+", normalized):
        lowered = run.casefold().strip("._$:/\\#+-")
        if len(lowered) >= 2:
            terms.add(lowered)
        for part in re.split(r"[._$:/\\#+-]+", run):
            if len(part) >= 2:
                terms.add(part.casefold())
            for camel in _split_camel(part):
                if len(camel) >= 2:
                    terms.add(camel.casefold())
    for run in re.findall(r"[\u3400-\u9fff]+", normalized):
        if run:
            terms.add(run)
        for index in range(max(0, len(run) - 1)):
            terms.add(run[index : index + 2])
        for index in range(max(0, len(run) - 2)):
            terms.add(run[index : index + 3])
    return sorted(terms, key=lambda value: (-len(value), value))[:limit]


def legacy_build_fts_query(text: str, limit: int = 16) -> str | None:
    values = [term for term in legacy_search_terms(text) if len(term) >= 3][:limit]
    if not values:
        return None
    return " OR ".join('"' + value.replace('"', '""') + '"' for value in values)


@contextmanager
def legacy_term_binding() -> Iterator[None]:
    previous_search = machine.search_terms
    previous_builder = machine.build_fts_query
    machine.search_terms = legacy_search_terms
    machine.build_fts_query = legacy_build_fts_query
    try:
        yield
    finally:
        machine.search_terms = previous_search
        machine.build_fts_query = previous_builder


@contextmanager
def fixture_environment(mode: str, marker: Path) -> Iterator[None]:
    names = {
        "CKB_FAKE_KEYWORD_PROVIDER_MODE": mode,
        "CKB_FAKE_KEYWORD_PROVIDER_MARKER": str(marker.resolve()),
        "CKB_FAKE_KEYWORD_PROVIDER_NAME": REPLAY_PROVIDER,
        "CKB_FAKE_KEYWORD_PROVIDER_MODEL": REPLAY_MODEL,
        "CKB_FAKE_KEYWORD_PROVIDER_VERSION": REPLAY_VERSION,
    }
    previous = {name: os.environ.get(name) for name in names}
    os.environ.update(names)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def marker_count(path: Path) -> int:
    if not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8").splitlines())


def _sqlite_backup(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as left:
        with sqlite3.connect(target) as right:
            left.backup(right)


def copy_corpus(source: Path, target: Path) -> dict[str, Any]:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    source_machine = source / "machine/knowledge.sqlite"
    source_legacy = source / "agent-index.sqlite"
    _sqlite_backup(source_machine, target / "machine/knowledge.sqlite")
    _sqlite_backup(source_legacy, target / "agent-index.sqlite")
    for name in ("state.json", "local-openers.json"):
        if (source / name).is_file():
            shutil.copy2(source / name, target / name)
    shutil.copytree(source / "human", target / "human")
    shutil.copytree(source / "human", target / "markdown")
    integrity: dict[str, str] = {}
    for name, path in (
        ("machine", target / "machine/knowledge.sqlite"),
        ("legacy", target / "agent-index.sqlite"),
    ):
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as connection:
            integrity[name] = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    with sqlite3.connect(
        f"file:{(target / 'machine/knowledge.sqlite').as_posix()}?mode=ro", uri=True
    ) as connection:
        meta = dict(connection.execute("SELECT key,value FROM meta").fetchall())
    return {
        "source": str(source.resolve()),
        "repository_commit": meta.get("repository_commit"),
        "source_machine_sha256_before": sha256(source_machine),
        "copied_machine_sha256": sha256(target / "machine/knowledge.sqlite"),
        "source_legacy_sha256_before": sha256(source_legacy),
        "copied_legacy_sha256": sha256(target / "agent-index.sqlite"),
        "integrity": integrity,
    }


def validate_protocol(protocol: dict[str, Any], source_corpus: Path) -> None:
    if protocol.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("protocol schema version mismatch")
    if protocol.get("status") != "frozen" or protocol.get("frozen_before_run") is not True:
        raise ValueError("protocol must be frozen before execution")
    if tuple(arm.get("id") for arm in protocol.get("arms", [])) != ARM_IDS:
        raise ValueError("protocol must contain the three fixed arms in canonical order")
    if protocol.get("cold_runs") != 1 or protocol.get("hot_runs") != 5:
        raise ValueError("protocol requires one cold run and five hot runs")
    if protocol.get("max_results") != 8 or protocol.get("profile") != "fast":
        raise ValueError("protocol requires fast profile and max_results=8")
    questions = protocol.get("questions")
    if not isinstance(questions, list) or len(questions) != 12:
        raise ValueError("protocol requires exactly twelve questions")
    if len({item.get("id") for item in questions}) != len(questions):
        raise ValueError("question ids must be unique")
    for item in questions:
        labels = item.get("relevance")
        if not isinstance(labels, list) or not labels:
            raise ValueError(f"question {item.get('id')} requires relevance labels")
        for label in labels:
            if not isinstance(label.get("source_path"), str) or label.get("grade") not in {1, 2, 3}:
                raise ValueError(f"question {item.get('id')} has an invalid relevance label")
    expected = protocol["corpus"]
    with sqlite3.connect(
        f"file:{(source_corpus / 'machine/knowledge.sqlite').as_posix()}?mode=ro", uri=True
    ) as connection:
        meta = dict(connection.execute("SELECT key,value FROM meta").fetchall())
    if meta.get("repository_commit") != expected["repository_commit"]:
        raise ValueError("source corpus repository commit differs from the frozen protocol")
    if meta.get("graph_sha256") != expected["graph_sha256"]:
        raise ValueError("source corpus graph digest differs from the frozen protocol")
    if meta.get("schema_version") != expected["machine_schema_version"]:
        raise ValueError("source corpus machine schema differs from the frozen protocol")


def replay_config(protocol: dict[str, Any]) -> KeywordProviderConfig:
    provider = protocol["provider"]
    return KeywordProviderConfig(
        command=(sys.executable, str(REPOSITORY_ROOT / provider["adapter"])),
        provider=REPLAY_PROVIDER,
        model=REPLAY_MODEL,
        version=REPLAY_VERSION,
        timeout_seconds=float(provider["timeout_seconds"]),
        retries=int(provider["retries"]),
    )


def unique_ranked_documents(result: dict[str, Any]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entity in result.get("selected_entities") or []:
        source_path = str(entity.get("source_path") or "").replace("\\", "/")
        if not source_path or source_path.casefold() in seen:
            continue
        seen.add(source_path.casefold())
        documents.append(
            {
                "rank": len(documents) + 1,
                "source_path": source_path,
                "entity_id": entity.get("entity_id"),
                "qualified_name": entity.get("qualified_name"),
                "score": entity.get("score"),
            }
        )
    return documents


def quality_for_ranking(documents: list[dict[str, Any]], relevance: list[dict[str, Any]], k: int = 8) -> dict[str, Any]:
    grades = {item["source_path"].replace("\\", "/").casefold(): int(item["grade"]) for item in relevance}
    ranked = documents[:k]
    hits = [
        {
            "source_path": item["source_path"],
            "rank": item["rank"],
            "grade": grades[item["source_path"].casefold()],
        }
        for item in ranked
        if item["source_path"].casefold() in grades
    ]
    recalled = {item["source_path"].casefold() for item in hits}
    recall = len(recalled) / len(grades)
    reciprocal_rank = 1.0 / hits[0]["rank"] if hits else 0.0
    dcg = sum((2 ** item["grade"] - 1) / math.log2(item["rank"] + 1) for item in hits)
    ideal = sorted(grades.values(), reverse=True)[:k]
    idcg = sum((2**grade - 1) / math.log2(index + 2) for index, grade in enumerate(ideal))
    missing = []
    status_by_path = {item["source_path"].casefold() for item in ranked}
    for label in relevance:
        normalized = label["source_path"].replace("\\", "/")
        if normalized.casefold() not in recalled:
            missing.append(
                {
                    "source_path": normalized,
                    "grade": label["grade"],
                    "reason": "outside-top-8" if normalized.casefold() in status_by_path else "not-selected",
                }
            )
    return {
        "recall_at_8": round(recall, 9),
        "mrr_at_8": round(reciprocal_rank, 9),
        "ndcg_at_8": round(dcg / idcg if idcg else 0.0, 9),
        "relevant_hits": hits,
        "missing": missing,
    }


def result_signature(result: dict[str, Any], documents: list[dict[str, Any]]) -> str:
    value = {
        "status": result.get("status"),
        "terms": result.get("terms") or [],
        "anchors": result.get("anchors") or [],
        "documents": [
            (item["source_path"], item.get("entity_id"), item.get("qualified_name"), item.get("score"))
            for item in documents
        ],
    }
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def invoke_arm(
    arm: str,
    corpus: Path,
    question: dict[str, Any],
    protocol: dict[str, Any],
    config: KeywordProviderConfig,
) -> dict[str, Any]:
    arguments = (
        corpus,
        question["question"],
        int(protocol["budget_tokens"]),
        int(protocol["max_results"]),
        protocol["profile"],
    )
    if arm == "legacy-deterministic":
        with legacy_term_binding():
            return machine.retrieve_machine(*arguments)
    if arm == "current-deterministic":
        return machine.retrieve_machine(*arguments)
    return machine.retrieve_machine(
        *arguments,
        keyword_fallback=KeywordFallbackOptions(config=config, force=True, use_cache=True),
    )


def run_row(
    arm: str,
    cache_state: str,
    run_index: int,
    corpus: Path,
    question: dict[str, Any],
    protocol: dict[str, Any],
    config: KeywordProviderConfig,
    marker: Path,
) -> dict[str, Any]:
    before = marker_count(marker)
    gc.collect()
    started = time.perf_counter_ns()
    result = invoke_arm(arm, corpus, question, protocol, config)
    elapsed_ms = round((time.perf_counter_ns() - started) / 1_000_000, 6)
    after = marker_count(marker)
    documents = unique_ranked_documents(result)
    quality = quality_for_ranking(documents, question["relevance"])
    fallback = result.get("keyword_fallback") or {}
    provider = fallback.get("provider") or {}
    return {
        "question_id": question["id"],
        "question": question["question"],
        "arm": arm,
        "cache_state": cache_state,
        "run_index": run_index,
        "latency_ms": elapsed_ms,
        "status": result.get("status"),
        "terms": result.get("terms") or [],
        "anchors": result.get("anchors") or [],
        "selected_documents": documents,
        "quality": quality,
        "first_pack_estimated_tokens": result.get("estimated_tokens", 0),
        "provider_process_starts": after - before,
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
            )
            if provider.get(key) is not None
        },
        "fallback": {
            "status": fallback.get("status"),
            "trigger": fallback.get("trigger"),
            "original_terms": (fallback.get("original") or {}).get("terms") or [],
            "validated_extensions": fallback.get("validated_extensions") or {},
        }
        if fallback
        else None,
        "result_signature": result_signature(result, documents),
    }


def aggregate_arm(protocol: dict[str, Any], rows: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    arm_rows = [row for row in rows if row["arm"] == arm]
    per_question: dict[str, Any] = {}
    for question in protocol["questions"]:
        question_rows = [row for row in arm_rows if row["question_id"] == question["id"]]
        cold = next(row for row in question_rows if row["cache_state"] == "cold")
        per_question[question["id"]] = {
            "question": question["question"],
            "actual_terms": cold["terms"],
            "actual_anchors": cold["anchors"],
            "selected_documents": cold["selected_documents"],
            "relevant_hits": cold["quality"]["relevant_hits"],
            "missing": cold["quality"]["missing"],
            "recall_at_8": cold["quality"]["recall_at_8"],
            "mrr_at_8": cold["quality"]["mrr_at_8"],
            "ndcg_at_8": cold["quality"]["ndcg_at_8"],
            "first_pack_estimated_tokens": cold["first_pack_estimated_tokens"],
            "deterministic_across_cold_and_hot": len({row["result_signature"] for row in question_rows}) == 1,
            "provider_process_starts": sum(row["provider_process_starts"] for row in question_rows),
            "cold_provider_cache_hit": cold["provider"].get("cache_hit"),
            "hot_provider_cache_hits": [
                row["provider"].get("cache_hit")
                for row in question_rows
                if row["cache_state"] == "hot"
            ],
            "fallback": cold["fallback"],
        }
    latencies = [row["latency_ms"] for row in arm_rows]
    cold_latencies = [row["latency_ms"] for row in arm_rows if row["cache_state"] == "cold"]
    hot_latencies = [row["latency_ms"] for row in arm_rows if row["cache_state"] == "hot"]
    return {
        "questions": len(per_question),
        "runs": len(arm_rows),
        "recall_at_8": round(statistics.mean(item["recall_at_8"] for item in per_question.values()), 9),
        "mrr_at_8": round(statistics.mean(item["mrr_at_8"] for item in per_question.values()), 9),
        "ndcg_at_8": round(statistics.mean(item["ndcg_at_8"] for item in per_question.values()), 9),
        "first_pack_estimated_tokens": statistics.median(
            item["first_pack_estimated_tokens"] for item in per_question.values()
        ),
        "latency_ms_p50": round(percentile(latencies, 0.50), 6),
        "latency_ms_p95": round(percentile(latencies, 0.95), 6),
        "cold_latency_ms_p50": round(percentile(cold_latencies, 0.50), 6),
        "cold_latency_ms_p95": round(percentile(cold_latencies, 0.95), 6),
        "hot_latency_ms_p50": round(percentile(hot_latencies, 0.50), 6),
        "hot_latency_ms_p95": round(percentile(hot_latencies, 0.95), 6),
        "provider_process_starts": sum(row["provider_process_starts"] for row in arm_rows),
        "deterministic_question_rate": round(
            statistics.mean(item["deterministic_across_cold_and_hot"] for item in per_question.values()), 9
        ),
        "per_question": per_question,
    }


def comparison(left: dict[str, Any], right: dict[str, Any], evidence_class: str) -> dict[str, Any]:
    deltas = {
        name: round(right[name] - left[name], 9)
        for name in ("recall_at_8", "mrr_at_8", "ndcg_at_8")
    }
    if all(value >= 0 for value in deltas.values()) and any(value > 0 for value in deltas.values()):
        claim = "measured-gain"
    elif all(value == 0 for value in deltas.values()):
        claim = "not-demonstrated"
    else:
        claim = "regression-observed"
    return {"evidence_class": evidence_class, "quality_delta": deltas, "quality_claim": claim}


def run_failure_probe(
    corpus: Path,
    protocol: dict[str, Any],
    config: KeywordProviderConfig,
    marker: Path,
) -> dict[str, Any]:
    question = protocol["questions"][0]
    machine._RETRIEVAL_STATIC_CACHE.clear()
    baseline = invoke_arm("current-deterministic", corpus, question, protocol, config)
    baseline_documents = unique_ranked_documents(baseline)
    before = marker_count(marker)
    with fixture_environment("rate-limit", marker):
        failed = machine.retrieve_machine(
            corpus,
            question["question"],
            int(protocol["budget_tokens"]),
            int(protocol["max_results"]),
            protocol["profile"],
            keyword_fallback=KeywordFallbackOptions(config=config, force=True, use_cache=False),
        )
    after = marker_count(marker)
    failed_documents = unique_ranked_documents(failed)
    fallback = failed.get("keyword_fallback") or {}
    provider = fallback.get("provider") or {}
    checks = {
        "original_status_preserved": failed.get("status") == baseline.get("status"),
        "original_ranking_preserved": result_signature(failed, failed_documents)
        == result_signature(baseline, baseline_documents),
        "structured_fallback_status": fallback.get("status") == "fallback",
        "structured_failure_type": provider.get("failure_type") == "rate-limit",
        "one_provider_process_start": after - before == 1,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "provider_process_starts": after - before,
        "failure_type": provider.get("failure_type"),
    }


def run_benchmark(protocol_path: Path, source_corpus: Path, output: Path) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    source_corpus = source_corpus.resolve()
    output = output.resolve()
    protocol = json_load(protocol_path)
    validate_protocol(protocol, source_corpus)
    output.mkdir(parents=True, exist_ok=True)
    corpus = output / "corpus"
    corpus_info = copy_corpus(source_corpus, corpus)
    if corpus_info["repository_commit"] != protocol["corpus"]["repository_commit"]:
        raise ValueError("copied corpus repository commit differs from the frozen protocol")
    config = replay_config(protocol)
    marker = output / "provider-starts.log"
    marker.unlink(missing_ok=True)
    rows: list[dict[str, Any]] = []
    with fixture_environment("chinese-retrieval-replay", marker):
        for question_index, question in enumerate(protocol["questions"]):
            arm_order = list(ARM_IDS[question_index % len(ARM_IDS) :] + ARM_IDS[: question_index % len(ARM_IDS)])
            for arm in arm_order:
                machine._RETRIEVAL_STATIC_CACHE.clear()
                if arm == "llm-replay-fallback":
                    keyword_cache_path(corpus, question["question"], config).unlink(missing_ok=True)
                rows.append(run_row(arm, "cold", 1, corpus, question, protocol, config, marker))
                for run_index in range(1, int(protocol["hot_runs"]) + 1):
                    rows.append(run_row(arm, "hot", run_index, corpus, question, protocol, config, marker))
    summaries = {arm: aggregate_arm(protocol, rows, arm) for arm in ARM_IDS}
    failure_probe = run_failure_probe(corpus, protocol, config, marker)
    source_machine_after = sha256(source_corpus / "machine/knowledge.sqlite")
    source_legacy_after = sha256(source_corpus / "agent-index.sqlite")
    copied_machine_after = sha256(corpus / "machine/knowledge.sqlite")
    copied_legacy_after = sha256(corpus / "agent-index.sqlite")
    source_corpus_unchanged = (
        source_machine_after == corpus_info["source_machine_sha256_before"]
        and source_legacy_after == corpus_info["source_legacy_sha256_before"]
    )
    expected_rows = len(protocol["questions"]) * len(ARM_IDS) * (
        int(protocol["cold_runs"]) + int(protocol["hot_runs"])
    )
    checks = {
        "row_count_exact": len(rows) == expected_rows,
        "copied_sqlite_integrity": corpus_info["integrity"] == {"machine": "ok", "legacy": "ok"},
        "benchmark_index_unchanged": (
            copied_machine_after == corpus_info["copied_machine_sha256"]
            and copied_legacy_after == corpus_info["copied_legacy_sha256"]
        ),
        "source_corpus_unchanged": source_corpus_unchanged,
        "default_arms_started_no_provider": (
            summaries["legacy-deterministic"]["provider_process_starts"] == 0
            and summaries["current-deterministic"]["provider_process_starts"] == 0
        ),
        "replay_cold_started_once_per_question": (
            summaries["llm-replay-fallback"]["provider_process_starts"] == len(protocol["questions"])
        ),
        "replay_hot_used_cache": all(
            item["cold_provider_cache_hit"] is False
            and item["hot_provider_cache_hits"] == [True] * int(protocol["hot_runs"])
            for item in summaries["llm-replay-fallback"]["per_question"].values()
        ),
        "all_rankings_deterministic": all(
            summary["deterministic_question_rate"] == 1.0 for summary in summaries.values()
        ),
        "failure_falls_back_to_original": failure_probe["status"] == "passed",
    }
    raw = {
        "schema_version": SCHEMA_VERSION,
        "benchmark": protocol["benchmark"],
        "protocol": str(protocol_path),
        "protocol_sha256": sha256(protocol_path),
        "corpus": {
            **corpus_info,
            "source_machine_sha256_after": source_machine_after,
            "source_legacy_sha256_after": source_legacy_after,
            "source_drift_during_run": not source_corpus_unchanged,
            "copied_machine_sha256_after": copied_machine_after,
            "copied_legacy_sha256_after": copied_legacy_after,
        },
        "rows": rows,
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "passed" if all(checks.values()) else "failed",
        "benchmark": protocol["benchmark"],
        "protocol_sha256": raw["protocol_sha256"],
        "corpus": raw["corpus"],
        "checks": checks,
        "arms": summaries,
        "comparisons": {
            "current_vs_legacy": comparison(
                summaries["legacy-deterministic"],
                summaries["current-deterministic"],
                "same-index-deterministic",
            ),
            "replay_vs_current": comparison(
                summaries["current-deterministic"],
                summaries["llm-replay-fallback"],
                "fixed-replay-not-real-model",
            ),
        },
        "failure_probe": failure_probe,
        "real_provider": {
            "status": protocol["real_provider_without_explicit_command"],
            "actual_calls": 0,
            "reason_zh": "本任务未配置可调用的真实 LLM Provider 命令或凭据；固定回放结果不作为真实模型效果。",
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
            "raw_results": str(output / "raw-results.json"),
            "report": str(output / "report.json"),
            "provider_start_log": str(marker),
        },
    }
    json_write(output / "raw-results.json", raw)
    json_write(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--source-corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = run_benchmark(arguments.protocol, arguments.source_corpus, arguments.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
