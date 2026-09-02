from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
from statistics import median
from typing import Any

from .contracts import TagNavigationError


CONDITIONS = ("no_tag", "confirmed_tag")


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TagNavigationError("INVALID_BENCHMARK_RECORD", f"第 {line_number} 行") from exc
        records.append(value)
    return records


def recompute(fixture: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(fixture, dict) or set(fixture) != {"schema_version", "scope", "page_sets", "tasks"}:
        raise TagNavigationError("INVALID_BENCHMARK", "fixture 根字段非法")
    if fixture["schema_version"] != 1 or fixture["scope"] != "isolated-fixture":
        raise TagNavigationError("INVALID_BENCHMARK", "fixture schema/scope 非法")
    page_sets = fixture["page_sets"]
    if not isinstance(page_sets, dict) or set(page_sets) != set(CONDITIONS):
        raise TagNavigationError("INVALID_BENCHMARK", "page_sets 条件非法")
    normalized_sets = {condition: set(page_sets[condition]) for condition in CONDITIONS}
    if any(len(normalized_sets[c]) != len(page_sets[c]) for c in CONDITIONS):
        raise TagNavigationError("INVALID_BENCHMARK", "page_sets 含重复页面")
    task_map: dict[str, dict[str, Any]] = {}
    for task in fixture["tasks"]:
        if not isinstance(task, dict) or set(task) != {"task_id", "target", "accepted_routes"}:
            raise TagNavigationError("INVALID_BENCHMARK", "task 字段非法")
        if task["task_id"] in task_map or set(task["accepted_routes"]) != set(CONDITIONS):
            raise TagNavigationError("INVALID_BENCHMARK", "task ID 重复或条件非法")
        task_map[task["task_id"]] = task
    seen: set[tuple[str, str]] = set()
    rows: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or set(record) != {
            "schema_version", "task_id", "condition", "visited_pages", "conflicting_tag_count"
        }:
            raise TagNavigationError("INVALID_BENCHMARK_RECORD", "record 字段非法")
        task_id = record["task_id"]
        condition = record["condition"]
        key = (task_id, condition)
        if record["schema_version"] != 1 or task_id not in task_map or condition not in CONDITIONS or key in seen:
            raise TagNavigationError("INVALID_BENCHMARK_RECORD", f"非法或重复记录 {key}")
        seen.add(key)
        visited = record["visited_pages"]
        if not isinstance(visited, list) or not visited or any(page not in normalized_sets[condition] for page in visited):
            raise TagNavigationError("INVALID_BENCHMARK_RECORD", f"{key} visited_pages 非法")
        task = task_map[task_id]
        if visited[-1] != task["target"]:
            raise TagNavigationError("INVALID_BENCHMARK_RECORD", f"{key} 未找到目标")
        route = task["accepted_routes"][condition]
        if not isinstance(route, list) or not route or route[-1] != task["target"]:
            raise TagNavigationError("INVALID_BENCHMARK", f"{key} accepted_route 非法")
        conflicts = record["conflicting_tag_count"]
        if not isinstance(conflicts, int) or isinstance(conflicts, bool) or conflicts < 0:
            raise TagNavigationError("INVALID_BENCHMARK_RECORD", f"{key} conflict 非法")
        rows.append(
            {
                "task_id": task_id,
                "condition": condition,
                "steps": len(visited) - 1,
                "misdirected_links": sum(1 for page in visited[:-1] if page not in route),
                "page_increment": 0,
                "conflicts": conflicts,
            }
        )
    expected = {(task_id, condition) for task_id in task_map for condition in CONDITIONS}
    if seen != expected:
        raise TagNavigationError("INCOMPLETE_BENCHMARK", f"missing={sorted(expected - seen)}")
    aggregate: dict[str, dict[str, Any]] = {}
    for condition in CONDITIONS:
        condition_rows = [row for row in rows if row["condition"] == condition]
        aggregate[condition] = {
            "tasks": len(condition_rows),
            "total_steps": sum(row["steps"] for row in condition_rows),
            "median_steps": median(row["steps"] for row in condition_rows),
            "misdirected_links": sum(row["misdirected_links"] for row in condition_rows),
            "page_count": len(normalized_sets[condition]),
            "conflicts": sum(row["conflicts"] for row in condition_rows),
        }
    page_increment = len(normalized_sets["confirmed_tag"] - normalized_sets["no_tag"])
    aggregate["confirmed_tag"]["page_increment"] = page_increment
    aggregate["no_tag"]["page_increment"] = 0
    rows.sort(key=lambda row: (row["task_id"], row["condition"]))
    return {
        "schema_version": 1,
        "status": "passed",
        "scope": "isolated-fixture",
        "effect_claim": "fixture-navigation-signal-only",
        "aggregate": aggregate,
        "records": rows,
    }
