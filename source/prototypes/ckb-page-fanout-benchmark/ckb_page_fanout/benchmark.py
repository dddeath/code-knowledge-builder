from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import FanoutError, exact_keys, load_object, tree_manifest, utf8_size, validate_contract


def snapshot_read_only(root: Path) -> dict[str, Any]:
    resolved = root.resolve()
    manifest = tree_manifest(resolved)
    return {
        "schema_version": 1,
        "status": "snapshotted",
        "root": resolved.as_posix(),
        "tree_sha256": manifest["sha256"],
        "file_count": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
    }


def _validate_arm(value: dict[str, Any], arm_id: str) -> dict[str, Any]:
    exact_keys(value, {"schema_version", "status", "scope", "arm_id", "projection_tree_sha256", "page_files", "aggregate", "records"}, arm_id)
    if value["schema_version"] != 1 or value["status"] != "passed" or value["scope"] != "isolated-blinded-page-navigation-judge" or value["arm_id"] != arm_id:
        raise FanoutError("INVALID_ARM_RESULT", arm_id)
    return value


def _read_only_guard(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    fields = {"schema_version", "status", "root", "tree_sha256", "file_count", "total_bytes"}
    exact_keys(before, fields, "read-only-before")
    exact_keys(after, fields, "read-only-after")
    if before != after:
        raise FanoutError(
            "READ_ONLY_ROOT_DRIFT",
            f"before={before.get('tree_sha256')} after={after.get('tree_sha256')}",
        )
    return {
        "status": "passed",
        "root": before["root"],
        "tree_sha256": before["tree_sha256"],
        "file_count": before["file_count"],
        "total_bytes": before["total_bytes"],
    }


def _context_bytes(corpus: dict[str, Any]) -> int:
    return sum(
        utf8_size((candidate["term"], candidate["claim_zh"], candidate["source_text"]))
        for document in corpus["documents"]
        for candidate in document["candidates"]
    )


def _generated_output_bytes(conservative: dict[str, Any], fanout: dict[str, Any]) -> int:
    baseline = {item["path"]: item for item in conservative["page_files"]}
    return sum(
        item["bytes"]
        for item in fanout["page_files"]
        if item["path"] not in baseline or item["sha256"] != baseline[item["path"]]["sha256"]
    )


def _checks(thresholds: dict[str, Any], comparison: dict[str, Any], fanout: dict[str, Any]) -> list[dict[str, Any]]:
    specifications = (
        ("median-navigation-step-reduction", comparison["median_navigation_step_reduction"], ">=", thresholds["minimum_median_navigation_step_reduction"]),
        ("answer-accuracy-delta", comparison["answer_accuracy_delta"], ">=", thresholds["minimum_answer_accuracy_delta"]),
        ("source-entailment-rate", fanout["source_entailment_rate"], ">=", thresholds["minimum_source_entailment_rate"]),
        ("misleading-links", fanout["misleading_links"], "<=", thresholds["maximum_misleading_links"]),
        ("orphan-pages", fanout["orphan_page_count"], "<=", thresholds["maximum_orphan_pages"]),
        ("duplicate-topics", fanout["duplicate_topic_count"], "<=", thresholds["maximum_duplicate_topics"]),
        ("broken-links", fanout["broken_link_count"], "<=", thresholds["maximum_broken_links"]),
        ("page-increment", comparison["page_increment"], "<=", thresholds["maximum_page_increment"]),
        ("generation-context-bytes", comparison["generation_context_bytes"], "<=", thresholds["maximum_generation_context_bytes"]),
    )
    return [
        {"name": name, "actual": actual, "operator": operator, "threshold": threshold, "passed": actual >= threshold if operator == ">=" else actual <= threshold}
        for name, actual, operator, threshold in specifications
    ]


def aggregate_benchmark(
    *,
    contract_path: Path,
    corpus_path: Path,
    arm_a_path: Path,
    arm_b_path: Path,
    read_only_before_path: Path,
    read_only_after_path: Path,
) -> dict[str, Any]:
    contract = validate_contract(load_object(contract_path, "contract"))
    corpus = load_object(corpus_path, "corpus")
    conservative = _validate_arm(load_object(arm_a_path, "arm_a"), "arm_a")
    fanout = _validate_arm(load_object(arm_b_path, "arm_b"), "arm_b")
    read_only_guard = _read_only_guard(
        load_object(read_only_before_path, "read-only-before"),
        load_object(read_only_after_path, "read-only-after"),
    )
    expected_context_bytes = _context_bytes(corpus)
    if fanout["aggregate"]["reported_generation_context_bytes"] != expected_context_bytes:
        raise FanoutError("GENERATION_CONTEXT_COST_DRIFT", str(expected_context_bytes))
    output_bytes = _generated_output_bytes(conservative, fanout)
    if fanout["aggregate"]["reported_generated_output_bytes"] != output_bytes:
        raise FanoutError("GENERATED_OUTPUT_COST_DRIFT", str(output_bytes))
    conservative_pages = {item["path"] for item in conservative["page_files"]}
    fanout_pages = {item["path"] for item in fanout["page_files"]}
    aggregate_a = conservative["aggregate"]
    aggregate_b = fanout["aggregate"]
    comparison = {
        "median_navigation_step_reduction": round(aggregate_a["median_navigation_steps"] - aggregate_b["median_navigation_steps"], 6),
        "answer_accuracy_delta": round(aggregate_b["answer_accuracy"] - aggregate_a["answer_accuracy"], 6),
        "source_entailment_rate_delta": round(aggregate_b["source_entailment_rate"] - aggregate_a["source_entailment_rate"], 6),
        "page_increment": len(fanout_pages - conservative_pages),
        "page_removal": len(conservative_pages - fanout_pages),
        "page_increment_ratio_to_conservative": round(len(fanout_pages - conservative_pages) / len(conservative_pages), 6),
        "generation_context_bytes": expected_context_bytes,
        "generated_output_bytes": output_bytes,
    }
    threshold_sets = contract["recommendation_thresholds"]
    production_checks = _checks(threshold_sets["production_candidate"], comparison, aggregate_b)
    experiment_checks = _checks(threshold_sets["continue_experiment"], comparison, aggregate_b)
    if all(item["passed"] for item in production_checks):
        recommendation = "production-candidate"
        deciding_checks = production_checks
    elif all(item["passed"] for item in experiment_checks):
        recommendation = "continue-experiment"
        deciding_checks = experiment_checks
    else:
        recommendation = threshold_sets["fallback"]
        deciding_checks = experiment_checks
    records_a = {item["task_id"]: item for item in conservative["records"]}
    records_b = {item["task_id"]: item for item in fanout["records"]}
    if set(records_a) != set(records_b):
        raise FanoutError("TASK_SET_DRIFT", f"arm_a={sorted(records_a)} arm_b={sorted(records_b)}")
    tasks = [
        {
            "task_id": task_id,
            "category": records_a[task_id]["category"],
            "conservative": records_a[task_id],
            "fanout": records_b[task_id],
        }
        for task_id in sorted(records_a)
    ]
    return {
        "schema_version": 1,
        "status": "passed",
        "scope": "isolated-page-fanout-benchmark",
        "baseline_commit": contract["baseline_commit"],
        "read_only_guard": read_only_guard,
        "arms": {
            "conservative": {"arm_id": "arm_a", "aggregate": aggregate_a},
            "fanout": {"arm_id": "arm_b", "aggregate": aggregate_b},
        },
        "comparison": comparison,
        "threshold_evaluation": {
            "production_candidate": production_checks,
            "continue_experiment": experiment_checks,
            "deciding_checks": deciding_checks,
        },
        "recommendation": recommendation,
        "recommendation_reasons": [item for item in deciding_checks if not item["passed"]],
        "tasks": tasks,
    }
