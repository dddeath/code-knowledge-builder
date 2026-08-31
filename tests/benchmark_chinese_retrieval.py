"""Frozen deterministic Chinese retrieval benchmark.

The runner copies an existing completed CKB corpus before measuring it.  It
never mutates the source corpus and writes every generated pack and result below
the caller-provided output directory.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import gc
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sqlite3
import statistics
import sys
import time
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from ckb_core.agent_index import retrieve as legacy_retrieve  # noqa: E402
from ckb_core import machine_knowledge as machine  # noqa: E402


NON_KNOWLEDGE_ADAPTERS = {
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    ".cursor/rules/code-knowledge-builder.mdc",
}


def json_load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def _sqlite_backup(source: Path, target: Path) -> None:
    with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as left:
        with sqlite3.connect(target) as right:
            left.backup(right)


def copy_corpus(source: Path, target: Path) -> dict[str, Any]:
    if target.exists():
        shutil.rmtree(target)
    (target / "machine").mkdir(parents=True)
    _sqlite_backup(source / "machine/knowledge.sqlite", target / "machine/knowledge.sqlite")
    _sqlite_backup(source / "agent-index.sqlite", target / "agent-index.sqlite")
    for name in ("state.json", "local-openers.json"):
        shutil.copy2(source / name, target / name)
    shutil.copytree(source / "human", target / "human")
    # Compatibility rows may point at markdown paths.  A byte-identical human
    # mirror keeps that declared benchmark boundary isolated.
    shutil.copytree(source / "human", target / "markdown")
    integrity: dict[str, str] = {}
    for name, path in (
        ("machine", target / "machine/knowledge.sqlite"),
        ("legacy", target / "agent-index.sqlite"),
    ):
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as connection:
            integrity[name] = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    return {
        "machine_sqlite_bytes": (target / "machine/knowledge.sqlite").stat().st_size,
        "machine_sqlite_sha256": sha256(target / "machine/knowledge.sqlite"),
        "legacy_sqlite_bytes": (target / "agent-index.sqlite").stat().st_size,
        "legacy_sqlite_sha256": sha256(target / "agent-index.sqlite"),
        "integrity": integrity,
    }


def _title_and_links(text: str, path: Path) -> tuple[str, list[str]]:
    title = path.stem
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    return title, re.findall(r"\[\[([^\]|#]+)", text)


def build_manual_index(corpus: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    root = corpus / "human"
    projection = json_load(root / "projection.json")
    with sqlite3.connect(f"file:{(corpus / 'machine/knowledge.sqlite').as_posix()}?mode=ro", uri=True) as connection:
        entity_paths = {
            str(entity_id): str(source_path)
            for entity_id, source_path in connection.execute("SELECT entity_id,source_path FROM entities")
        }
    paths_by_page: dict[str, set[str]] = defaultdict(set)
    for entity_id, owner in projection["entity_owner_pages"].items():
        if entity_id in entity_paths:
            paths_by_page[owner].add(entity_paths[entity_id])
    for page in projection["pages"]:
        if page["id"] in entity_paths:
            paths_by_page[page["id"]].add(entity_paths[page["id"]])
    page_id_by_file = {Path(page["file"]).as_posix(): page["id"] for page in projection["pages"]}
    documents: list[dict[str, Any]] = []
    title_to_index: dict[str, int] = {}
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        if relative in NON_KNOWLEDGE_ADAPTERS:
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        title, links = _title_and_links(text, path)
        source_paths = set(paths_by_page.get(page_id_by_file.get(relative, ""), set()))
        source_paths.update(
            re.findall(
                r"`((?:scripts|tests)/[^`\s:]+\.(?:py|js|c|h|cpp|hpp|cs))(?::\d+(?:-\d+)?)?`",
                text,
            )
        )
        documents.append(
            {
                "path": path,
                "relative": relative,
                "bytes": len(raw),
                "title": title,
                "links": links,
                "source_paths": sorted(source_paths),
            }
        )
        title_to_index[title] = len(documents) - 1
    return documents, title_to_index


def manual_scan(
    corpus: Path,
    question: str,
    documents: list[dict[str, Any]],
    title_to_index: dict[str, int],
    max_results: int,
) -> dict[str, Any]:
    terms = [term for term in machine.search_terms(question) if len(term) >= 2]
    contents: dict[int, str] = {}
    scored: list[tuple[float, str, int]] = []
    for index, document in enumerate(documents):
        value = document["path"].read_text(encoding="utf-8", errors="replace")
        contents[index] = value
        haystack = (document["title"] + "\n" + value).casefold()
        score = 0.0
        for term in terms:
            count = haystack.count(term.casefold())
            if count:
                score += min(count, 8) * (2.0 + min(len(term), 12) / 4.0)
        if question.casefold() in haystack:
            score += 120.0
        if score > 0:
            scored.append((score, document["relative"], index))
    scored.sort(key=lambda item: (-item[0], item[1]))
    selected: list[int] = []
    seen: set[int] = set()
    for _score, _relative, index in scored[:3]:
        selected.append(index)
        seen.add(index)
    for index in list(selected):
        for title in documents[index]["links"]:
            neighbor = title_to_index.get(title)
            if neighbor is not None and neighbor not in seen and len(selected) < max_results:
                selected.append(neighbor)
                seen.add(neighbor)
    for _score, _relative, index in scored:
        if len(selected) >= max_results:
            break
        if index not in seen:
            selected.append(index)
            seen.add(index)
    index_text = (corpus / "human/INDEX.md").read_text(encoding="utf-8")
    context = index_text + "\n" + "\n".join(contents[index] for index in selected)
    return {
        "status": "passed" if selected else "needs-source-read",
        "selected": [documents[index]["relative"] for index in selected],
        "source_paths": sorted({path for index in selected for path in documents[index]["source_paths"]}),
        "symbols": [],
        "agent_visible_tokens": machine.estimated_tokens(context),
        "selected_count": len(selected),
        "retrieval_stats": {},
    }


def normalize(method: str, result: dict[str, Any]) -> dict[str, Any]:
    if method == "machine-fast":
        selected = result.get("selected_entities", [])
        return {
            "status": result["status"],
            "selected": [entity["qualified_name"] for entity in selected],
            "source_paths": sorted({entity["source_path"] for entity in selected}),
            "symbols": [entity["name"] for entity in selected] + [entity["qualified_name"] for entity in selected],
            "agent_visible_tokens": result.get("estimated_tokens", 0),
            "selected_count": len(selected),
            "retrieval_stats": result.get("retrieval_stats", {}),
            "terms": result.get("terms", []),
            "selected_candidates": [
                {
                    "entity_id": entity["entity_id"],
                    "qualified_name": entity["qualified_name"],
                    "source_path": entity["source_path"],
                    "score": entity["score"],
                    "score_breakdown": entity["score_breakdown"],
                }
                for entity in selected
            ],
        }
    if method == "legacy-page-sqlite":
        selected = result.get("selected_pages", [])
        return {
            "status": result["status"],
            "selected": [page["title"] for page in selected],
            "source_paths": sorted({page["source_path"] for page in selected if page.get("source_path")}),
            "symbols": [page["title"] for page in selected],
            "agent_visible_tokens": result.get("estimated_tokens", 0),
            "selected_count": len(selected),
            "retrieval_stats": {},
        }
    return result


def invoke(
    method: str,
    corpus: Path,
    question: str,
    documents: list[dict[str, Any]],
    title_to_index: dict[str, int],
    budget: int,
    max_results: int,
) -> dict[str, Any]:
    if method == "manual-wide-scan":
        return manual_scan(corpus, question, documents, title_to_index, max_results)
    if method == "legacy-page-sqlite":
        return normalize(method, legacy_retrieve(corpus, question, budget, max_results))
    return normalize(method, machine.retrieve_machine(corpus, question, budget, max_results, "fast"))


def result_signature(result: dict[str, Any]) -> str:
    value = {
        "status": result["status"],
        "selected": result["selected"],
        "source_paths": result["source_paths"],
        "selected_candidates": result.get("selected_candidates", []),
    }
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def validate_protocol(protocol: dict[str, Any]) -> None:
    if protocol.get("status") != "frozen" or protocol.get("frozen_before_run") is not True:
        raise ValueError("protocol must be frozen before the benchmark")
    if len(protocol.get("queries", [])) != 12:
        raise ValueError("frozen benchmark must contain exactly twelve queries")
    if protocol.get("warmups") != 1 or protocol.get("repetitions") != 9:
        raise ValueError("frozen benchmark requires one warmup and nine repetitions")
    if protocol.get("budget_tokens") != 2400 or protocol.get("max_results") != 8:
        raise ValueError("frozen benchmark requires budget=2400 and max_results=8")


def run_benchmark(protocol_path: Path, source_corpus: Path, output: Path) -> dict[str, Any]:
    protocol = json_load(protocol_path)
    validate_protocol(protocol)
    output.mkdir(parents=True, exist_ok=True)
    corpus = output / "corpus"
    corpus_info = copy_corpus(source_corpus, corpus)
    documents, title_to_index = build_manual_index(corpus)
    corpus_info.update(
        {
            "human_markdown_files": len(documents),
            "human_markdown_bytes": sum(document["bytes"] for document in documents),
        }
    )
    methods = [method["id"] for method in protocol["methods"]]
    rows: list[dict[str, Any]] = []
    cache_diagnostics: list[dict[str, Any]] = []
    for query_index, query in enumerate(protocol["queries"]):
        order = methods[query_index % len(methods) :] + methods[: query_index % len(methods)]
        for method in order:
            for _ in range(protocol["warmups"]):
                invoke(
                    method,
                    corpus,
                    query["question"],
                    documents,
                    title_to_index,
                    protocol["budget_tokens"],
                    protocol["max_results"],
                )
        for repetition in range(protocol["repetitions"]):
            for method in order:
                gc.collect()
                start = time.perf_counter_ns()
                result = invoke(
                    method,
                    corpus,
                    query["question"],
                    documents,
                    title_to_index,
                    protocol["budget_tokens"],
                    protocol["max_results"],
                )
                elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
                fts_query = machine._fts_query(query["question"]) if method == "machine-fast" else None
                terms = result.get("terms", [])
                rows.append(
                    {
                        "query_id": query["id"],
                        "question": query["question"],
                        "expected_path": query["expected_path"],
                        "expected_symbol": query["expected_symbol"],
                        "method": method,
                        "repetition": repetition + 1,
                        "latency_ms": elapsed_ms,
                        "target_source_recalled": query["expected_path"] in result["source_paths"],
                        "target_symbol_recalled": any(
                            query["expected_symbol"].casefold() in symbol.casefold() for symbol in result["symbols"]
                        ),
                        "signature": result_signature(result),
                        "term_count": len(terms) if method == "machine-fast" else None,
                        "fts_term_count": len(fts_query.split(" OR ")) if fts_query else 0 if method == "machine-fast" else None,
                        "fts_match_utf8_bytes": len((fts_query or "").encode("utf-8")) if method == "machine-fast" else None,
                        **result,
                    }
                )

        machine._RETRIEVAL_STATIC_CACHE.clear()
        cache_samples = []
        for cache_state in ("cold", "hot"):
            gc.collect()
            start = time.perf_counter_ns()
            result = invoke(
                "machine-fast",
                corpus,
                query["question"],
                documents,
                title_to_index,
                protocol["budget_tokens"],
                protocol["max_results"],
            )
            cache_samples.append(
                {
                    "cache_state": cache_state,
                    "latency_ms": (time.perf_counter_ns() - start) / 1_000_000,
                    "static_cache_hit": result["retrieval_stats"]["static_cache_hit"],
                }
            )
        cache_diagnostics.append({"query_id": query["id"], "samples": cache_samples})

    raw = {
        "schema_version": 1,
        "protocol": str(protocol_path.resolve()),
        "protocol_sha256": sha256(protocol_path),
        "source_corpus": str(source_corpus.resolve()),
        "corpus": corpus_info,
        "cache_diagnostics": cache_diagnostics,
        "rows": rows,
    }
    json_write(output / "raw-results.json", raw)
    summary = summarize(protocol, raw)
    json_write(output / "summary.json", summary)
    return summary


def summarize(protocol: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    methods = [method["id"] for method in protocol["methods"]]
    summaries: dict[str, Any] = {}
    for method in methods:
        rows = [row for row in raw["rows"] if row["method"] == method]
        per_query: dict[str, Any] = {}
        for query in protocol["queries"]:
            query_rows = [row for row in rows if row["query_id"] == query["id"]]
            per_query[query["id"]] = {
                "question": query["question"],
                "expected_path": query["expected_path"],
                "latency_ms_median": statistics.median(row["latency_ms"] for row in query_rows),
                "target_source_recalled": all(row["target_source_recalled"] for row in query_rows),
                "target_symbol_recalled": (
                    None if method == "manual-wide-scan" else all(row["target_symbol_recalled"] for row in query_rows)
                ),
                "agent_visible_tokens": statistics.median(row["agent_visible_tokens"] for row in query_rows),
                "selected_count": statistics.median(row["selected_count"] for row in query_rows),
                "fallback": any(row["status"] != "passed" for row in query_rows),
                "deterministic": len({row["signature"] for row in query_rows}) == 1,
                "result_signature": query_rows[0]["signature"],
                "source_paths": query_rows[0]["source_paths"],
                "selected": query_rows[0]["selected"],
                "term_count": query_rows[0]["term_count"] if method == "machine-fast" else None,
                "fts_term_count": query_rows[0]["fts_term_count"] if method == "machine-fast" else None,
                "fts_match_utf8_bytes": query_rows[0]["fts_match_utf8_bytes"] if method == "machine-fast" else None,
                "materialized_candidates": (
                    query_rows[0]["retrieval_stats"].get("materialized_candidates") if method == "machine-fast" else None
                ),
            }
        latencies = [row["latency_ms"] for row in rows]
        summaries[method] = {
            "latency_ms_median": statistics.median(latencies),
            "latency_ms_p95": percentile(latencies, 0.95),
            "target_source_recall_at_8": sum(item["target_source_recalled"] for item in per_query.values()) / len(per_query),
            "target_symbol_recall": (
                None
                if method == "manual-wide-scan"
                else sum(item["target_symbol_recalled"] for item in per_query.values()) / len(per_query)
            ),
            "fallback_rate": sum(item["fallback"] for item in per_query.values()) / len(per_query),
            "determinism_rate": sum(item["deterministic"] for item in per_query.values()) / len(per_query),
            "agent_visible_tokens_median": statistics.median(item["agent_visible_tokens"] for item in per_query.values()),
            "selected_documents_median": statistics.median(item["selected_count"] for item in per_query.values()),
            "queries": per_query,
        }
        if method == "machine-fast":
            summaries[method]["term_count_median"] = statistics.median(item["term_count"] for item in per_query.values())
            summaries[method]["fts_term_count_median"] = statistics.median(
                item["fts_term_count"] for item in per_query.values()
            )
            summaries[method]["fts_match_utf8_bytes_median"] = statistics.median(
                item["fts_match_utf8_bytes"] for item in per_query.values()
            )
            summaries[method]["materialized_candidates_median"] = statistics.median(
                item["materialized_candidates"] for item in per_query.values()
            )

    machine_summary = summaries["machine-fast"]
    manual_summary = summaries["manual-wide-scan"]
    gates = protocol["acceptance_gates"]
    computed = {
        "machine_target_source_recall_at_8": machine_summary["target_source_recall_at_8"],
        "machine_recall_not_below_manual": (
            machine_summary["target_source_recall_at_8"] >= manual_summary["target_source_recall_at_8"]
        ),
        "machine_fallback_rate": machine_summary["fallback_rate"],
        "machine_determinism_rate": machine_summary["determinism_rate"],
        "machine_visible_context_reduction_vs_manual": (
            1 - machine_summary["agent_visible_tokens_median"] / manual_summary["agent_visible_tokens_median"]
        ),
        "machine_engine_latency_p95_ms": machine_summary["latency_ms_p95"],
        "machine_latency_speedup_vs_manual": manual_summary["latency_ms_median"] / machine_summary["latency_ms_median"],
    }
    checks = {
        "recall_min": computed["machine_target_source_recall_at_8"] >= gates["machine_target_source_recall_at_8_min"],
        "recall_not_below_manual": computed["machine_recall_not_below_manual"],
        "fallback": computed["machine_fallback_rate"] <= gates["machine_fallback_rate_max"],
        "determinism": computed["machine_determinism_rate"] >= gates["machine_determinism_rate_min"],
        "visible_context": (
            computed["machine_visible_context_reduction_vs_manual"]
            >= gates["machine_visible_context_reduction_vs_manual_min"]
        ),
        "absolute_p95_latency": (
            computed["machine_engine_latency_p95_ms"] <= gates["machine_engine_latency_p95_ms_max"]
        ),
        "latency_speedup": (
            computed["machine_latency_speedup_vs_manual"] >= gates["machine_latency_speedup_vs_manual_min"]
        ),
    }
    cold = [sample for item in raw["cache_diagnostics"] for sample in item["samples"] if sample["cache_state"] == "cold"]
    hot = [sample for item in raw["cache_diagnostics"] for sample in item["samples"] if sample["cache_state"] == "hot"]
    return {
        "schema_version": 1,
        "status": "passed" if all(checks.values()) else "mixed",
        "protocol_status": "frozen-before-run",
        "protocol_sha256": raw["protocol_sha256"],
        "corpus": raw["corpus"],
        "summary": summaries,
        "cache_diagnostics": {
            "cold_latency_ms_median": statistics.median(sample["latency_ms"] for sample in cold),
            "cold_latency_ms_p95": percentile([sample["latency_ms"] for sample in cold], 0.95),
            "hot_latency_ms_median": statistics.median(sample["latency_ms"] for sample in hot),
            "hot_latency_ms_p95": percentile([sample["latency_ms"] for sample in hot], 0.95),
            "cold_cache_flags_exact": all(sample["static_cache_hit"] is False for sample in cold),
            "hot_cache_flags_exact": all(sample["static_cache_hit"] is True for sample in hot),
        },
        "computed": computed,
        "gate_checks": checks,
        "all_gates_passed": all(checks.values()),
    }


def verify_runs(left_path: Path, right_path: Path, output: Path) -> dict[str, Any]:
    left = json_load(left_path)
    right = json_load(right_path)
    left_machine = left["summary"]["machine-fast"]
    right_machine = right["summary"]["machine-fast"]
    left_signatures = {
        query_id: query["result_signature"] for query_id, query in left_machine["queries"].items()
    }
    right_signatures = {
        query_id: query["result_signature"] for query_id, query in right_machine["queries"].items()
    }
    checks = {
        "protocol_equal": left["protocol_sha256"] == right["protocol_sha256"],
        "corpus_equal": (
            left["corpus"]["machine_sqlite_sha256"] == right["corpus"]["machine_sqlite_sha256"]
            and left["corpus"]["legacy_sqlite_sha256"] == right["corpus"]["legacy_sqlite_sha256"]
        ),
        "both_all_seven_gates_passed": left["all_gates_passed"] and right["all_gates_passed"],
        "cross_process_result_signatures_equal": left_signatures == right_signatures,
        "cross_process_quality_and_context_equal": (
            left_machine["target_source_recall_at_8"] == right_machine["target_source_recall_at_8"]
            and left_machine["fallback_rate"] == right_machine["fallback_rate"]
            and left_machine["determinism_rate"] == right_machine["determinism_rate"]
            and left_machine["agent_visible_tokens_median"] == right_machine["agent_visible_tokens_median"]
        ),
        "cold_hot_flags_exact": (
            left["cache_diagnostics"]["cold_cache_flags_exact"]
            and left["cache_diagnostics"]["hot_cache_flags_exact"]
            and right["cache_diagnostics"]["cold_cache_flags_exact"]
            and right["cache_diagnostics"]["hot_cache_flags_exact"]
        ),
    }
    result = {
        "schema_version": 1,
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "left": str(left_path.resolve()),
        "right": str(right_path.resolve()),
        "left_summary_sha256": sha256(left_path),
        "right_summary_sha256": sha256(right_path),
    }
    json_write(output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--protocol", type=Path, required=True)
    run.add_argument("--source-corpus", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--left", type=Path, required=True)
    verify.add_argument("--right", type=Path, required=True)
    verify.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.command == "run":
        result = run_benchmark(arguments.protocol, arguments.source_corpus, arguments.output)
    else:
        result = verify_runs(arguments.left, arguments.right, arguments.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
