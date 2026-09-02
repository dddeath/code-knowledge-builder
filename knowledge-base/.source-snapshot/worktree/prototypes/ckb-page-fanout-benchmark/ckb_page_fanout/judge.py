from __future__ import annotations

from collections import deque
from difflib import SequenceMatcher
import hashlib
from pathlib import Path, PurePosixPath
import re
from statistics import median
from typing import Any

from .contracts import (
    FanoutError,
    exact_keys,
    load_object,
    normalize_topic,
    sha256_file,
    validate_relative_path,
)


WIKI_LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
TITLE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def _resolve(page: str, target: str) -> str | None:
    if ":" in target or target.startswith("#"):
        return None
    value = PurePosixPath(target)
    if value.suffix != ".md":
        value = value.with_suffix(".md")
    candidate = value.relative_to("/") if target.startswith("/") else PurePosixPath(page).parent / value
    stack: list[str] = []
    for part in candidate.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not stack:
                return None
            stack.pop()
        else:
            stack.append(part)
    return PurePosixPath(*stack).as_posix()


def _page_graph(root: Path, projection: dict[str, Any]) -> tuple[dict[str, list[str]], list[dict[str, str]], list[dict[str, Any]]]:
    declared: set[str] = set()
    page_files: list[dict[str, Any]] = []
    for item in projection["pages"]:
        exact_keys(item, {"path", "title", "kind"}, "projection.pages[]")
        relative = validate_relative_path(item["path"], "projection.pages[].path")
        if not relative.endswith(".md") or relative in declared:
            raise FanoutError("INVALID_PROJECTION", f"重复或非 Markdown 页面：{relative}")
        path = root / relative
        if not path.is_file():
            raise FanoutError("PROJECTED_PAGE_NOT_FOUND", relative)
        text = path.read_text(encoding="utf-8")
        title = TITLE.search(text)
        if not title or title.group(1).strip() != item["title"]:
            raise FanoutError("PROJECTED_TITLE_MISMATCH", relative)
        declared.add(relative)
        page_files.append(
            {
                "path": relative,
                "title": item["title"],
                "kind": item["kind"],
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*.md")}
    if actual != declared:
        raise FanoutError("PROJECTION_PAGE_SET_DRIFT", f"missing={sorted(declared-actual)} extra={sorted(actual-declared)}")
    graph: dict[str, list[str]] = {}
    broken: list[dict[str, str]] = []
    for page in sorted(declared):
        targets: list[str] = []
        text = (root / page).read_text(encoding="utf-8")
        for raw in WIKI_LINK.findall(text):
            resolved = _resolve(page, raw.strip())
            if resolved is None or resolved not in declared:
                broken.append({"page": page, "target": raw.strip(), "resolved": resolved or "outside"})
            else:
                targets.append(resolved)
        graph[page] = sorted(set(targets))
    return graph, broken, sorted(page_files, key=lambda item: item["path"])


def _shortest_path(graph: dict[str, list[str]], start: str, target: str) -> list[str] | None:
    queue: deque[list[str]] = deque([[start]])
    seen = {start}
    while queue:
        path = queue.popleft()
        if path[-1] == target:
            return path
        for neighbor in graph.get(path[-1], []):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append([*path, neighbor])
    return None


def _reachable(graph: dict[str, list[str]], start: str) -> set[str]:
    queue = deque([start])
    seen = {start}
    while queue:
        for neighbor in graph.get(queue.popleft(), []):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def _duplicate_titles(page_files: list[dict[str, Any]], threshold: float) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, left in enumerate(page_files):
        left_topic = normalize_topic(left["title"])
        for right in page_files[index + 1 :]:
            right_topic = normalize_topic(right["title"])
            score = SequenceMatcher(None, left_topic, right_topic, autojunk=False).ratio()
            if score >= threshold:
                result.append(
                    {
                        "left": left["path"],
                        "right": right["path"],
                        "similarity": round(score, 6),
                        "threshold": threshold,
                    }
                )
    return result


def _validate_judge_contract(value: dict[str, Any]) -> dict[str, Any]:
    exact_keys(value, {"schema_version", "scope", "arm_ids", "start_page", "scoring_contract", "tasks"}, "judge contract")
    if value["schema_version"] != 1 or value["scope"] != "isolated-blinded-page-navigation-judge":
        raise FanoutError("INVALID_JUDGE_CONTRACT", "schema_version/scope 非法")
    if value["arm_ids"] != ["arm_a", "arm_b"]:
        raise FanoutError("INVALID_JUDGE_CONTRACT", "arm_ids 必须为固定盲化编号")
    scoring = exact_keys(
        value["scoring_contract"],
        {
            "navigation_steps",
            "answer_correct",
            "source_entailed",
            "misleading_links",
            "duplicate_topic_similarity_threshold",
            "judge_input_excludes",
        },
        "scoring_contract",
    )
    if scoring["judge_input_excludes"] != ["strategy-name", "candidate-generation-code", "recommendation-thresholds"]:
        raise FanoutError("INVALID_JUDGE_CONTRACT", "judge_input_excludes 漂移")
    threshold = scoring["duplicate_topic_similarity_threshold"]
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not 0.8 <= threshold <= 1.0:
        raise FanoutError("INVALID_JUDGE_CONTRACT", "重复主题阈值非法")
    if not isinstance(value["tasks"], list) or not value["tasks"]:
        raise FanoutError("INVALID_JUDGE_CONTRACT", "tasks 为空")
    return value


def _source_entailed(target_text: str, task: dict[str, Any], source_root: Path) -> bool:
    source = task["expected_source"]
    exact_keys(source, {"path", "start_line", "end_line", "source_text", "source_sha256"}, "expected_source")
    relative = validate_relative_path(source["path"], "expected_source.path")
    path = source_root / relative
    if not path.is_file() or sha256_file(path) != source["source_sha256"]:
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    start = source["start_line"]
    end = source["end_line"]
    if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool) or start < 1 or end < start or end > len(lines):
        return False
    actual = "\n".join(lines[start - 1 : end])
    label = f"{start}-{end}"
    return (
        actual == source["source_text"]
        and task["expected_claim_zh"] == source["source_text"]
        and f"主张：{task['expected_claim_zh']}" in target_text
        and f"来源：`{relative}:{label}`" in target_text
        and f"原文：{source['source_text']}" in target_text
    )


def judge_arm(*, judge_contract_path: Path, projection_root: Path, source_root: Path) -> dict[str, Any]:
    contract = _validate_judge_contract(load_object(judge_contract_path, "judge contract"))
    root = projection_root.resolve()
    source = source_root.resolve()
    projection = load_object(root / "projection.json", "projection")
    required_projection = {
        "schema_version",
        "scope",
        "arm_id",
        "start_page",
        "source_count",
        "page_count",
        "new_page_count",
        "page_limit_per_source",
        "generation_context_bytes",
        "generated_output_bytes",
        "pages",
        "accepted_candidates",
        "rejected_candidates",
    }
    optional_projection = {"baseline_tree", "policy"}
    if not isinstance(projection, dict) or not required_projection.issubset(projection) or set(projection) - required_projection - optional_projection:
        raise FanoutError("INVALID_PROJECTION", "projection 根字段非法")
    arm_id = projection["arm_id"]
    if arm_id not in contract["arm_ids"]:
        raise FanoutError("INVALID_PROJECTION", "arm_id 非法")
    if projection["start_page"] != contract["start_page"]:
        raise FanoutError("INVALID_PROJECTION", "start_page 漂移")
    graph, broken, page_files = _page_graph(root, projection)
    if projection["page_count"] != len(page_files):
        raise FanoutError("INVALID_PROJECTION", "page_count 与页面集不一致")
    start = contract["start_page"]
    if start not in graph:
        raise FanoutError("INVALID_PROJECTION", "固定入口不存在")
    reachable = _reachable(graph, start)
    orphan_pages = sorted(set(graph) - reachable)
    duplicate_topics = _duplicate_titles(page_files, float(contract["scoring_contract"]["duplicate_topic_similarity_threshold"]))
    records: list[dict[str, Any]] = []
    seen_tasks: set[str] = set()
    for task in contract["tasks"]:
        exact_keys(
            task,
            {"task_id", "category", "query_zh", "expected_claim_zh", "expected_source", "expected_target", "accepted_route"},
            "task",
        )
        task_id = task["task_id"]
        if not isinstance(task_id, str) or task_id in seen_tasks:
            raise FanoutError("INVALID_JUDGE_CONTRACT", f"任务 ID 非法或重复：{task_id}")
        seen_tasks.add(task_id)
        if set(task["expected_target"]) != set(contract["arm_ids"]) or set(task["accepted_route"]) != set(contract["arm_ids"]):
            raise FanoutError("INVALID_JUDGE_CONTRACT", f"任务臂字段不完整：{task_id}")
        target = validate_relative_path(task["expected_target"][arm_id], f"{task_id}.expected_target")
        accepted_route = task["accepted_route"][arm_id]
        if not isinstance(accepted_route, list) or not accepted_route or accepted_route[0] != start or accepted_route[-1] != target:
            raise FanoutError("INVALID_JUDGE_CONTRACT", f"任务路线非法：{task_id}")
        path = _shortest_path(graph, start, target) if target in graph else None
        target_text = (root / target).read_text(encoding="utf-8") if target in graph else ""
        found = path is not None
        answer_correct = found and f"主张：{task['expected_claim_zh']}" in target_text
        source_entailed = found and _source_entailed(target_text, task, source)
        visited = path or []
        misleading = sum(1 for page in visited if page not in accepted_route)
        steps = len(visited) - 1 if found else None
        records.append(
            {
                "task_id": task_id,
                "category": task["category"],
                "target": target,
                "found": found,
                "navigation_steps": steps,
                "scored_navigation_steps": steps if steps is not None else len(graph) + 1,
                "visited_pages": visited,
                "answer_correct": answer_correct,
                "source_entailed": source_entailed,
                "misleading_links": misleading,
            }
        )
    records.sort(key=lambda item: item["task_id"])
    scored_steps = [item["scored_navigation_steps"] for item in records]
    task_count = len(records)
    aggregate = {
        "tasks": task_count,
        "found_tasks": sum(1 for item in records if item["found"]),
        "failed_navigation_tasks": sum(1 for item in records if not item["found"]),
        "total_navigation_steps": sum(scored_steps),
        "median_navigation_steps": float(median(scored_steps)),
        "answer_correct": sum(1 for item in records if item["answer_correct"]),
        "answer_accuracy": round(sum(1 for item in records if item["answer_correct"]) / task_count, 6),
        "source_entailed": sum(1 for item in records if item["source_entailed"]),
        "source_entailment_rate": round(sum(1 for item in records if item["source_entailed"]) / task_count, 6),
        "misleading_links": sum(item["misleading_links"] for item in records),
        "page_count": len(page_files),
        "new_page_count": projection["new_page_count"],
        "orphan_pages": orphan_pages,
        "orphan_page_count": len(orphan_pages),
        "duplicate_topics": duplicate_topics,
        "duplicate_topic_count": len(duplicate_topics),
        "broken_links": broken,
        "broken_link_count": len(broken),
        "reported_generation_context_bytes": projection["generation_context_bytes"],
        "reported_generated_output_bytes": projection["generated_output_bytes"],
    }
    return {
        "schema_version": 1,
        "status": "passed",
        "scope": "isolated-blinded-page-navigation-judge",
        "arm_id": arm_id,
        "projection_tree_sha256": hashlib.sha256(
            "".join(f"{item['path']}\0{item['sha256']}\n" for item in page_files).encode("utf-8")
        ).hexdigest(),
        "page_files": page_files,
        "aggregate": aggregate,
        "records": records,
    }
