"""Independently recompute semantic-vector benchmark aggregates from raw rows."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
from typing import Any


ARM_IDS = ("sqlite-current", "semantic-vector", "hybrid-rrf")
SUMMARY_FIELDS = (
    "questions",
    "runs",
    "recall_at_8",
    "mrr_at_8",
    "ndcg_at_8",
    "first_pack_estimated_tokens",
    "cold_latency_ms_p50",
    "cold_latency_ms_p95",
    "hot_latency_ms_p50",
    "hot_latency_ms_p95",
    "worker_process_starts",
    "peak_rss_bytes",
    "peak_extra_child_processes",
    "deterministic_question_rate",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    rank = (len(ordered) - 1) * probability
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def quality(documents: list[dict[str, Any]], labels: list[dict[str, Any]]) -> dict[str, float]:
    grades = {
        item["source_path"].replace("\\", "/").casefold(): int(item["grade"])
        for item in labels
    }
    hits = [
        (int(item["rank"]), grades[item["source_path"].replace("\\", "/").casefold()])
        for item in documents[:8]
        if item["source_path"].replace("\\", "/").casefold() in grades
    ]
    recalled = {
        item["source_path"].replace("\\", "/").casefold()
        for item in documents[:8]
        if item["source_path"].replace("\\", "/").casefold() in grades
    }
    recall = len(recalled) / len(grades)
    reciprocal_rank = 1.0 / hits[0][0] if hits else 0.0
    dcg = sum((2**grade - 1) / math.log2(rank + 1) for rank, grade in hits)
    ideal = sorted(grades.values(), reverse=True)[:8]
    idcg = sum((2**grade - 1) / math.log2(index + 2) for index, grade in enumerate(ideal))
    return {
        "recall_at_8": round(recall, 9),
        "mrr_at_8": round(reciprocal_rank, 9),
        "ndcg_at_8": round(dcg / idcg if idcg else 0.0, 9),
    }


def aggregate(
    protocol: dict[str, Any], raw: dict[str, Any], arm: str
) -> dict[str, Any]:
    rows = [item for item in raw["rows"] if item["arm"] == arm]
    resources = [item for item in raw["worker_resources"] if item["arm"] == arm]
    per_question = []
    deterministic = []
    for question in protocol["questions"]:
        question_rows = [item for item in rows if item["question_id"] == question["id"]]
        cold = next(item for item in question_rows if item["cache_state"] == "cold")
        metrics = quality(cold["selected_documents"], question["relevance"])
        per_question.append(
            {**metrics, "first_pack_estimated_tokens": cold["first_pack_estimated_tokens"]}
        )
        deterministic.append(len({item["result_signature"] for item in question_rows}) == 1)
    cold_latencies = [float(item["latency_ms"]) for item in rows if item["cache_state"] == "cold"]
    hot_latencies = [float(item["latency_ms"]) for item in rows if item["cache_state"] == "hot"]
    return {
        "questions": len(per_question),
        "runs": len(rows),
        "recall_at_8": round(statistics.mean(item["recall_at_8"] for item in per_question), 9),
        "mrr_at_8": round(statistics.mean(item["mrr_at_8"] for item in per_question), 9),
        "ndcg_at_8": round(statistics.mean(item["ndcg_at_8"] for item in per_question), 9),
        "first_pack_estimated_tokens": statistics.median(
            item["first_pack_estimated_tokens"] for item in per_question
        ),
        "cold_latency_ms_p50": round(percentile(cold_latencies, 0.50), 6),
        "cold_latency_ms_p95": round(percentile(cold_latencies, 0.95), 6),
        "hot_latency_ms_p50": round(percentile(hot_latencies, 0.50), 6),
        "hot_latency_ms_p95": round(percentile(hot_latencies, 0.95), 6),
        "worker_process_starts": len(resources),
        "peak_rss_bytes": max(item["peak_rss_bytes"] for item in resources),
        "peak_extra_child_processes": max(
            item["peak_extra_child_processes"] for item in resources
        ),
        "deterministic_question_rate": round(statistics.mean(deterministic), 9),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--reported", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    protocol = load(arguments.protocol)
    raw = load(arguments.raw)
    reported = load(arguments.reported)
    recomputed = {arm: aggregate(protocol, raw, arm) for arm in ARM_IDS}
    comparisons = {}
    for arm in ARM_IDS:
        expected = {name: reported["arms"][arm][name] for name in SUMMARY_FIELDS}
        comparisons[arm] = {
            "exact": recomputed[arm] == expected,
            "recomputed": recomputed[arm],
            "reported": expected,
        }
    expected_rows = len(protocol["questions"]) * len(ARM_IDS) * (
        int(protocol["execution"]["cold_runs"]) + int(protocol["execution"]["hot_runs"])
    )
    checks = {
        "raw_row_count_exact": len(raw["rows"]) == expected_rows,
        "all_aggregate_fields_exact": all(item["exact"] for item in comparisons.values()),
        "question_ids_exact": {item["question_id"] for item in raw["rows"]}
        == {item["id"] for item in protocol["questions"]},
        "arm_ids_exact": {item["arm"] for item in raw["rows"]} == set(ARM_IDS),
        "one_cold_five_hot_per_arm_question": all(
            len(
                [
                    row
                    for row in raw["rows"]
                    if row["arm"] == arm
                    and row["question_id"] == question["id"]
                    and row["cache_state"] == "cold"
                ]
            )
            == 1
            and len(
                [
                    row
                    for row in raw["rows"]
                    if row["arm"] == arm
                    and row["question_id"] == question["id"]
                    and row["cache_state"] == "hot"
                ]
            )
            == 5
            for arm in ARM_IDS
            for question in protocol["questions"]
        ),
    }
    result = {
        "schema_version": 1,
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "comparisons": comparisons,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(
        (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
