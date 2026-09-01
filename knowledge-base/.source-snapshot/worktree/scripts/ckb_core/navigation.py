from __future__ import annotations

from collections import defaultdict, deque
from math import ceil
from pathlib import PurePosixPath
from typing import Any

from .common import AuditError, stable_id
from .page_config import DEFAULT_PAGE_CONFIG


PAGE_CLASSIFICATIONS = {"page", "appendix", "boundary"}
# Human pages are deliberately limited to executable/code-shaping units.  A
# property, enum, field, namespace, accessor, or other small declaration stays
# in the nearest class/function/file aggregation instead of becoming a page.
HUMAN_CODE_UNIT_KINDS = {
    "class",
    "struct",
    "interface",
    "record",
    "function",
    "method",
    "constructor",
    "destructor",
}
MODULE_CONTEXT_LIMIT = 80_000
TASK_CONTEXT_LIMIT = 20_000
TOTAL_CONTEXT_BUDGET = 100_000
TOKEN_BYTES_DIVISOR = 3

DIRECT_RELATION_LIMIT = 20
AGGREGATE_RELATION_LIMIT = 10
TEST_RELATION_LIMIT = 8
BOUNDARY_RELATION_LIMIT = 8


def module_name(path: str) -> str:
    parts = PurePosixPath(path).parts
    return parts[0] if len(parts) > 1 else "root"


def estimated_tokens(text: str | bytes, divisor: int = TOKEN_BYTES_DIVISOR) -> int:
    data = text if isinstance(text, bytes) else text.encode("utf-8")
    return ceil(len(data) / divisor)


def _test_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    stem = PurePosixPath(path).stem.lower()
    return any(part.lower() in {"test", "tests"} for part in parts) or stem.startswith("test_") or stem.endswith(("_test", ".test", "-test"))


def _graph_facts(entities: list[dict[str, Any]], links: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {entity["id"]: entity for entity in entities}
    outgoing: dict[str, set[str]] = defaultdict(set)
    incoming: dict[str, set[str]] = defaultdict(set)
    cross_degree: dict[str, int] = defaultdict(int)
    total_degree: dict[str, int] = defaultdict(int)
    test_related: set[str] = set()
    for link in links:
        if link.get("type") == "contains":
            continue
        source = by_id.get(link.get("source"))
        target = by_id.get(link.get("target"))
        if not source or not target:
            continue
        outgoing[source["id"]].add(target["id"])
        incoming[target["id"]].add(source["id"])
        total_degree[source["id"]] += 1
        total_degree[target["id"]] += 1
        if source["path"] != target["path"]:
            cross_degree[source["id"]] += 1
            cross_degree[target["id"]] += 1
        if _test_path(source["path"]) != _test_path(target["path"]):
            test_related.update((source["id"], target["id"]))
    return {
        "by_id": by_id,
        "outgoing": outgoing,
        "incoming": incoming,
        "cross_degree": cross_degree,
        "total_degree": total_degree,
        "test_related": test_related,
    }


def _ancestors(entity_id: str, by_id: dict[str, dict[str, Any]]) -> list[str]:
    result: list[str] = []
    cursor = by_id.get(entity_id)
    visited: set[str] = set()
    while cursor and cursor.get("parent_id") and cursor["parent_id"] not in visited:
        parent_id = cursor["parent_id"]
        visited.add(parent_id)
        parent = by_id.get(parent_id)
        if not parent:
            break
        result.append(parent_id)
        cursor = parent
    return result


def _eligible(entity: dict[str, Any], entry_ids: set[str]) -> bool:
    if entity.get("kind") not in HUMAN_CODE_UNIT_KINDS:
        return False
    if entity["id"] in entry_ids:
        return True
    return bool(entity.get("page_eligible"))


def _rank(
    entity: dict[str, Any],
    *,
    entry_ids: set[str],
    entry_owners: set[str],
    entry_direct: set[str],
    facts: dict[str, Any],
) -> tuple[Any, ...]:
    entity_id = entity["id"]
    # Negated numeric facts sort the highest-priority entity first.  Path/range/ID
    # provide a stable language-independent tie break.
    return (
        0 if entity_id in entry_ids else 1,
        0 if entity_id in entry_owners else 1,
        0 if entity_id in entry_direct else 1,
        0 if facts["cross_degree"].get(entity_id, 0) else 1,
        0 if entity.get("is_public_or_exported") else 1,
        -facts["cross_degree"].get(entity_id, 0),
        -facts["total_degree"].get(entity_id, 0),
        0 if entity_id in facts["test_related"] else 1,
        entity["path"],
        int(entity["range"]["start_line"]),
        entity_id,
    )


def build_navigation_plan(
    entities: list[dict[str, Any]],
    links: list[dict[str, Any]],
    entry_ids: list[str],
    page_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assign page/appendix/boundary using fixed evidence and configured quotas."""
    config = page_config or DEFAULT_PAGE_CONFIG
    page_limits = config["page_limits"]
    ordinary_file_limit = int(page_limits["ordinary_file"])
    core_file_limit = int(page_limits["core_file"])
    adjacent_file_limit = int(page_limits["adjacent_file"])
    core_entry_limit = int(page_limits["core_per_entry"])
    adjacent_entry_limit = int(page_limits["adjacent_per_entry"])
    facts = _graph_facts(entities, links)
    by_id: dict[str, dict[str, Any]] = facts["by_id"]
    entries = {value for value in entry_ids if value in by_id}
    entry_owners = {ancestor for entry in entries for ancestor in _ancestors(entry, by_id) if by_id[ancestor]["kind"] != "file"}
    entry_direct: set[str] = set()
    for entry in entries:
        entry_direct.update(facts["outgoing"].get(entry, set()))
        entry_direct.update(facts["incoming"].get(entry, set()))
    selected_pages: set[str] = {entity["id"] for entity in entities if entity["kind"] == "file"}
    boundary_ids = {entity["id"] for entity in entities if entity["kind"] == "boundary"}
    selected_pages.update(boundary_ids)
    candidates_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entity in entities:
        if _eligible(entity, entries):
            candidates_by_path[entity["path"]].append(entity)
    rank_kwargs = {"entry_ids": entries, "entry_owners": entry_owners, "entry_direct": entry_direct, "facts": facts}
    for values in candidates_by_path.values():
        values.sort(key=lambda value: _rank(value, **rank_kwargs))

    clusters: list[dict[str, Any]] = []
    core_paths: set[str] = set()
    neighbor_ids_all: set[str] = set()
    adjacent_paths: set[str] = set()
    selected_key_count_by_path: dict[str, int] = defaultdict(int)
    for entry_id in sorted(entries):
        entry = by_id[entry_id]
        if not _eligible(entry, entries):
            clusters.append({"entry_id": entry_id, "core_page_ids": [], "neighbor_page_ids": [], "landing_page_id": next((value for value in _ancestors(entry_id, by_id) if by_id[value]["kind"] == "file"), None)})
            continue
        same_path = candidates_by_path.get(entry["path"], [])
        core_pool: list[dict[str, Any]] = [entry] if _eligible(entry, entries) else []
        for ancestor_id in _ancestors(entry_id, by_id):
            ancestor = by_id[ancestor_id]
            if ancestor["kind"] != "file" and _eligible(ancestor, entries):
                core_pool.append(ancestor)
        direct_same = [by_id[value] for value in facts["outgoing"].get(entry_id, set()) | facts["incoming"].get(entry_id, set()) if value in by_id and by_id[value]["path"] == entry["path"] and _eligible(by_id[value], entries)]
        core_pool.extend(sorted(direct_same, key=lambda value: _rank(value, **rank_kwargs)))
        entry_parent = entry.get("parent_id")
        core_pool.extend(value for value in same_path if value.get("parent_id") == entry_parent)
        core_ids: list[str] = []
        for value in core_pool:
            if len(core_ids) >= core_entry_limit:
                break
            if value["id"] in core_ids:
                continue
            if value["id"] in selected_pages:
                core_ids.append(value["id"])
                continue
            if selected_key_count_by_path[value["path"]] >= core_file_limit:
                continue
            core_ids.append(value["id"])
            selected_pages.add(value["id"])
            selected_key_count_by_path[value["path"]] += 1
        core_paths.update(by_id[value]["path"] for value in core_ids)

        neighbor_pool: list[dict[str, Any]] = []
        for core_id in core_ids:
            for neighbor_id in facts["outgoing"].get(core_id, set()) | facts["incoming"].get(core_id, set()):
                neighbor = by_id.get(neighbor_id)
                if neighbor and neighbor["path"] != entry["path"] and _eligible(neighbor, entries):
                    neighbor_pool.append(neighbor)
        neighbor_pool.sort(key=lambda value: _rank(value, **rank_kwargs))
        neighbor_ids: list[str] = []
        for value in neighbor_pool:
            if len(neighbor_ids) >= adjacent_entry_limit:
                break
            if value["id"] in neighbor_ids or value["id"] in selected_pages:
                continue
            if value["path"] in core_paths or selected_key_count_by_path[value["path"]] >= adjacent_file_limit:
                continue
            neighbor_ids.append(value["id"])
            selected_pages.add(value["id"])
            selected_key_count_by_path[value["path"]] += 1
        neighbor_ids_all.update(neighbor_ids)
        adjacent_paths.update(by_id[value]["path"] for value in neighbor_ids)
        adjacent_paths.difference_update(core_paths)
        clusters.append({"entry_id": entry_id, "core_page_ids": core_ids, "neighbor_page_ids": neighbor_ids})

    # Every non-core source file receives no more than its configured ordinary
    # or adjacent quota.  Ranking and tie breaks remain entirely deterministic.
    for path, values in sorted(candidates_by_path.items()):
        if path in core_paths:
            continue
        limit = adjacent_file_limit if path in adjacent_paths else ordinary_file_limit
        for value in values:
            if selected_key_count_by_path[path] >= limit:
                break
            if value["id"] not in selected_pages:
                selected_pages.add(value["id"])
                selected_key_count_by_path[path] += 1

    owner_by_entity: dict[str, str] = {}
    decisions: list[dict[str, Any]] = []
    file_page_by_path = {entity["path"]: entity["id"] for entity in entities if entity["kind"] == "file"}
    for entity in entities:
        entity_id = entity["id"]
        if entity_id in boundary_ids:
            classification = "boundary"
            owner = entity_id
        elif entity_id in selected_pages:
            classification = "page"
            owner = entity_id
        else:
            classification = "appendix"
            owner = next((ancestor for ancestor in _ancestors(entity_id, by_id) if ancestor in selected_pages and by_id[ancestor]["kind"] != "file"), file_page_by_path.get(entity["path"]))
            if not owner:
                raise AuditError(f"appendix entity has no deterministic owner: {entity_id}")
        owner_by_entity[entity_id] = owner
        evidence = []
        if entity_id in entries:
            evidence.append("explicit-entry")
        if entity_id in entry_owners:
            evidence.append("entry-lexical-owner")
        if entity_id in entry_direct:
            evidence.append("entry-direct-relation")
        if facts["cross_degree"].get(entity_id, 0):
            evidence.append("cross-file-reference")
        if entity.get("is_public_or_exported"):
            evidence.append("public-or-exported")
        if entity.get("hard_exclusion"):
            evidence.append(f"hard-exclusion:{entity['hard_exclusion']}")
        decisions.append(
            {
                "entity_id": entity_id,
                "classification": classification,
                "owner_page_id": owner,
                "rank_evidence": evidence or ["fixed-order-default"],
                "cross_file_degree": facts["cross_degree"].get(entity_id, 0),
                "total_degree": facts["total_degree"].get(entity_id, 0),
            }
        )

    page_count_by_path: dict[str, int] = defaultdict(int)
    for entity_id in selected_pages - boundary_ids:
        entity = by_id[entity_id]
        if entity["kind"] != "file":
            page_count_by_path[entity["path"]] += 1
    quota_errors = []
    for path, count in sorted(page_count_by_path.items()):
        limit = core_file_limit if path in core_paths else (adjacent_file_limit if path in adjacent_paths else ordinary_file_limit)
        if count > limit:
            quota_errors.append({"path": path, "count": count, "limit": limit})
    for cluster in clusters:
        if len(cluster["core_page_ids"]) > core_entry_limit or len(cluster["neighbor_page_ids"]) > adjacent_entry_limit:
            quota_errors.append(
                {
                    "entry_id": cluster["entry_id"],
                    "reason": "entry-cluster-quota",
                    "core_count": len(cluster["core_page_ids"]),
                    "core_limit": core_entry_limit,
                    "adjacent_count": len(cluster["neighbor_page_ids"]),
                    "adjacent_limit": adjacent_entry_limit,
                }
            )
    return {
        "schema_version": 3,
        "algorithm": "human-code-unit-navigation-v3-configured",
        "page_limits": dict(page_limits),
        "classifications": sorted(PAGE_CLASSIFICATIONS),
        "decisions": decisions,
        "entity_owner_pages": owner_by_entity,
        "page_entity_ids": sorted(selected_pages - boundary_ids),
        "boundary_entity_ids": sorted(boundary_ids),
        "entry_clusters": clusters,
        "core_paths": sorted(core_paths),
        "adjacent_paths": sorted(adjacent_paths),
        "page_count_by_path": dict(sorted(page_count_by_path.items())),
        "quota_errors": quota_errors,
        "status": "passed" if not quota_errors else "failed",
    }


def apply_navigation_plan(entities: list[dict[str, Any]], plan: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = {item["entity_id"]: item for item in plan["decisions"]}
    result = []
    for entity in entities:
        decision = decisions.get(entity["id"])
        if not decision:
            raise AuditError(f"navigation plan omitted entity: {entity['id']}")
        value = dict(entity)
        value["classification"] = decision["classification"]
        value["candidate_classification"] = decision["classification"]
        value["owner_page_id"] = decision["owner_page_id"]
        value["navigation_evidence"] = decision["rank_evidence"]
        result.append(value)
    return result


def page_limit(
    scope_file_count: int,
    module_count: int,
    entry_cluster_count: int,
    boundary_group_count: int,
    page_config: dict[str, Any] | None = None,
) -> int:
    limits = (page_config or DEFAULT_PAGE_CONFIG)["page_limits"]
    ordinary = int(limits["ordinary_file"])
    core_extra = max(0, int(limits["core_per_entry"]) - ordinary)
    adjacent_extra = int(limits["adjacent_per_entry"])
    return (
        1
        + module_count
        + scope_file_count
        + scope_file_count * ordinary
        + entry_cluster_count * (core_extra + adjacent_extra)
        + boundary_group_count
    )


def context_budget_record(
    text: str,
    mode: str,
    module: str | None = None,
    page_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = (page_config or DEFAULT_PAGE_CONFIG)["context"]
    divisor = int(context["bytes_per_token"])
    tokens = estimated_tokens(text, divisor)
    limit = int(context["module_max_tokens"] if mode == "full-module" else context["task_max_tokens"])
    return {
        "mode": mode,
        "module": module,
        "utf8_bytes": len(text.encode("utf-8")),
        "estimated_tokens": tokens,
        "formula": f"ceil(utf8_bytes / {divisor})",
        "limit": limit,
        "total_context_budget": int(context["total_max_tokens"]),
        "reserved_agent_tokens": int(context["reserved_agent_tokens"]),
        "status": "passed" if tokens <= limit else "failed",
    }


def build_review_packs(
    parse_batches: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    page_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Create review units independent from machine parse batches."""
    config = page_config or DEFAULT_PAGE_CONFIG
    review_limits = config["review_packs"]
    token_divisor = int(config["context"]["bytes_per_token"])
    by_id = {entity["id"]: entity for entity in entities}
    batch_by_entity = {entity_id: batch["id"] for batch in parse_batches for entity_id in batch["entity_ids"]}
    packs: list[dict[str, Any]] = []

    def partition(kind: str, values: list[dict[str, Any]], max_files: int, max_items: int, token_limit: int) -> None:
        current: list[dict[str, Any]] = []
        current_paths: set[str] = set()
        current_estimate = 0

        def flush() -> None:
            nonlocal current, current_paths, current_estimate
            if not current:
                return
            pack_id = f"{kind}-pack-{sum(1 for value in packs if value['kind'] == kind) + 1:04d}"
            packs.append(
                {
                    "id": pack_id,
                    "kind": kind,
                    "entity_ids": [value["id"] for value in current],
                    "file_paths": sorted(current_paths),
                    "parse_batch_ids": sorted({batch_by_entity[value["id"]] for value in current if value["id"] in batch_by_entity}),
                    "estimated_input_tokens": current_estimate,
                    "token_limit": token_limit,
                    "status": "planned",
                }
            )
            current = []
            current_paths = set()
            current_estimate = 0

        for value in sorted(values, key=lambda item: (item["path"], item["range"]["start_line"], item["id"])):
            estimate = max(8, ceil((int(value["range"]["end_byte"]) - int(value["range"]["start_byte"])) / token_divisor))
            next_paths = current_paths | {value["path"]}
            if current and (len(current) + 1 > max_items or len(next_paths) > max_files or current_estimate + estimate > token_limit):
                flush()
            current.append(value)
            current_paths.add(value["path"])
            current_estimate += estimate
            if estimate > token_limit:
                # A single declaration is an auditable oversized unit.
                flush()
        flush()

    # Keep packs independent from parse batches as state objects while avoiding
    # a pack that waits on two machine batches before it can be reviewed.
    for batch in parse_batches:
        batch_ids = set(batch["entity_ids"])
        pages = [entity for entity in entities if entity["id"] in batch_ids and entity.get("classification") in {"page", "boundary"}]
        appendices = [entity for entity in entities if entity["id"] in batch_ids and entity.get("classification") == "appendix"]
        page_limits = review_limits["page"]
        appendix_limits = review_limits["appendix"]
        partition(
            "page-review",
            pages,
            max_files=int(page_limits["max_files"]),
            max_items=int(page_limits["max_items"]),
            token_limit=int(page_limits["max_tokens"]),
        )
        partition(
            "appendix-review",
            appendices,
            max_files=int(appendix_limits["max_files"]),
            max_items=int(appendix_limits["max_items"]),
            token_limit=int(appendix_limits["max_tokens"]),
        )
    return packs
