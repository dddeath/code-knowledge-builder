from __future__ import annotations

from collections import Counter, defaultdict, deque
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
from statistics import median
from typing import Any, Iterable

from .contracts import (
    TagNavigationError,
    atomic_write_json,
    canonical_json_bytes,
    ensure_within,
    normalize_tag,
    sha256_bytes,
    sha256_file,
    validate_policy,
    validate_relative_path,
)
from .projection import build_projection
from .state_machine import audit_database
from .store import read_assertion_jsonl, replay_with_rollback


CONDITIONS = ("no_tag", "machine_tag", "confirmed_tag")
DECISIONS = {"confirmed", "candidate", "opposed", "tied"}
WIKILINK = re.compile(r"\[\[([^]]+)\]\]")
EXPERIMENT_MARKER = "<!-- ckb-tag-real-vault-study -->"
ISOLATION_EXCLUSIONS = (
    ".ckb/output-contract.json",
    ".obsidian/plugins/code-knowledge-builder-companion",
)


def _exact(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        actual = set(value) if isinstance(value, dict) else set()
        raise TagNavigationError(
            "INVALID_STUDY_PROTOCOL",
            f"{label} missing={sorted(fields - actual)} unknown={sorted(actual - fields)}",
        )
    return value


def _positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise TagNavigationError("INVALID_STUDY_PROTOCOL", f"{label} 必须为正整数")
    return value


def validate_study_protocol(value: Any) -> dict[str, Any]:
    protocol = _exact(
        value,
        {
            "schema_version",
            "study_id",
            "status",
            "frozen_before_run",
            "source",
            "conditions",
            "execution",
            "claim_boundary",
            "tasks",
        },
        "protocol",
    )
    if protocol["schema_version"] != 1 or protocol["status"] != "frozen" or protocol["frozen_before_run"] is not True:
        raise TagNavigationError("INVALID_STUDY_PROTOCOL", "协议必须在运行前冻结为 schema_version=1")
    if not isinstance(protocol["study_id"], str) or not protocol["study_id"]:
        raise TagNavigationError("INVALID_STUDY_PROTOCOL", "study_id 非法")
    source = _exact(
        protocol["source"],
        {
            "expected_commit",
            "expected_complete_sha256",
            "expected_vault_tree_sha256",
            "expected_machine_sha256",
            "expected_counts",
        },
        "source",
    )
    for field in ("expected_commit", "expected_complete_sha256", "expected_vault_tree_sha256", "expected_machine_sha256"):
        expected_length = 40 if field == "expected_commit" else 64
        item = source[field]
        if not isinstance(item, str) or len(item) != expected_length or any(ch not in "0123456789abcdef" for ch in item):
            raise TagNavigationError("INVALID_STUDY_PROTOCOL", f"source.{field} 非法")
    counts = _exact(
        source["expected_counts"],
        {"files", "markdown_files", "bytes", "pages", "entities", "relations", "machine_projected_pages"},
        "source.expected_counts",
    )
    for field, item in counts.items():
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            raise TagNavigationError("INVALID_STUDY_PROTOCOL", f"source.expected_counts.{field} 非法")
    if protocol["conditions"] != list(CONDITIONS):
        raise TagNavigationError("INVALID_STUDY_PROTOCOL", "conditions 顺序必须固定为三臂")
    execution = _exact(
        protocol["execution"],
        {"entry_page", "step_budget", "task_order", "candidate_order", "baseline_route", "tag_route", "orphan_scope_prefixes", "as_of"},
        "execution",
    )
    validate_relative_path(execution["entry_page"], "execution.entry_page")
    _positive_int(execution["step_budget"], "execution.step_budget")
    if execution["candidate_order"] != "casefolded-page-path" or execution["baseline_route"] != "directed-wikilink-shortest-path" or execution["tag_route"] != "global-tag-pane-then-casefolded-candidates":
        raise TagNavigationError("INVALID_STUDY_PROTOCOL", "导航规则不是冻结实现")
    if not isinstance(execution["task_order"], list) or not execution["task_order"]:
        raise TagNavigationError("INVALID_STUDY_PROTOCOL", "task_order 非法")
    prefixes = execution["orphan_scope_prefixes"]
    if not isinstance(prefixes, list) or not prefixes:
        raise TagNavigationError("INVALID_STUDY_PROTOCOL", "orphan_scope_prefixes 非法")
    for prefix in prefixes:
        validate_relative_path(prefix, "execution.orphan_scope_prefixes")
    if not isinstance(execution["as_of"], str) or not execution["as_of"].endswith("Z"):
        raise TagNavigationError("INVALID_STUDY_PROTOCOL", "execution.as_of 必须为 UTC 时间")
    claim = _exact(protocol["claim_boundary"], {"automation", "human"}, "claim_boundary")
    if claim != {"automation": "system-navigation-proxy-only", "human": "pending-human-validation"}:
        raise TagNavigationError("INVALID_STUDY_PROTOCOL", "claim_boundary 不得越过人类验证边界")

    tasks = protocol["tasks"]
    if not isinstance(tasks, list) or not tasks:
        raise TagNavigationError("INVALID_STUDY_PROTOCOL", "tasks 非法")
    task_ids: list[str] = []
    tag_set: set[str] = set()
    for index, item in enumerate(tasks):
        task = _exact(item, {"task_id", "prompt_zh", "target", "tag", "machine_candidates"}, f"tasks[{index}]")
        task_id = task["task_id"]
        if not isinstance(task_id, str) or not re.fullmatch(r"T[0-9]{2}", task_id) or task_id in task_ids:
            raise TagNavigationError("INVALID_STUDY_PROTOCOL", f"tasks[{index}].task_id 非法或重复")
        task_ids.append(task_id)
        if not isinstance(task["prompt_zh"], str) or not re.search(r"[\u4e00-\u9fff]", task["prompt_zh"]):
            raise TagNavigationError("INVALID_STUDY_PROTOCOL", f"{task_id}.prompt_zh 缺少中文")
        validate_relative_path(task["target"], f"{task_id}.target")
        normalized_tag = normalize_tag(task["tag"])
        if normalized_tag in tag_set:
            raise TagNavigationError("INVALID_STUDY_PROTOCOL", f"{task_id}.tag 重复")
        task["tag"] = normalized_tag
        tag_set.add(normalized_tag)
        candidates = task["machine_candidates"]
        if not isinstance(candidates, list) or not candidates:
            raise TagNavigationError("INVALID_STUDY_PROTOCOL", f"{task_id}.machine_candidates 非法")
        candidate_pages: set[str] = set()
        target_decision = None
        for candidate_index, candidate_value in enumerate(candidates):
            candidate = _exact(candidate_value, {"page", "decision", "duplicate_last_vote"}, f"{task_id}.machine_candidates[{candidate_index}]")
            page = validate_relative_path(candidate["page"], f"{task_id}.candidate.page")
            if not page.endswith(".md") or page in candidate_pages or candidate["decision"] not in DECISIONS or not isinstance(candidate["duplicate_last_vote"], bool):
                raise TagNavigationError("INVALID_STUDY_PROTOCOL", f"{task_id}.machine_candidates 非法")
            candidate_pages.add(page)
            if page == task["target"]:
                target_decision = candidate["decision"]
        if target_decision != "confirmed":
            raise TagNavigationError("INVALID_STUDY_PROTOCOL", f"{task_id}.target 必须是 confirmed 候选")
    if execution["task_order"] != task_ids:
        raise TagNavigationError("INVALID_STUDY_PROTOCOL", "task_order 必须与 tasks 完全同序")
    return protocol


def _tree_entries(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir():
        raise TagNavigationError("SOURCE_NOT_FOUND", f"目录不存在: {root}")
    entries: list[dict[str, Any]] = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        data = path.read_bytes()
        entries.append({"path": path.relative_to(root).as_posix(), "bytes": len(data), "sha256": sha256_bytes(data)})
    return entries


def tree_manifest(root: Path) -> dict[str, Any]:
    entries = _tree_entries(root)
    return {
        "schema_version": 1,
        "root": str(root.resolve()),
        "file_count": len(entries),
        "markdown_file_count": sum(item["path"].casefold().endswith(".md") for item in entries),
        "bytes": sum(item["bytes"] for item in entries),
        "tree_sha256": sha256_bytes(canonical_json_bytes(entries)),
        "entries": entries,
    }


def _machine_counts(database: Path) -> dict[str, int]:
    try:
        connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            return {
                "entities": int(connection.execute("SELECT COUNT(*) FROM entities").fetchone()[0]),
                "relations": int(connection.execute("SELECT COUNT(*) FROM relations").fetchone()[0]),
                "machine_projected_pages": int(connection.execute("SELECT COUNT(DISTINCT page_file) FROM human_projection WHERE page_file IS NOT NULL").fetchone()[0]),
            }
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise TagNavigationError("INVALID_SOURCE_DATABASE", str(exc)) from exc


def source_identity(source_output: Path) -> dict[str, Any]:
    complete_path = source_output / ".complete"
    vault = source_output / "human"
    database = source_output / "machine" / "knowledge.sqlite"
    if not complete_path.is_file() or not database.is_file():
        raise TagNavigationError("SOURCE_NOT_FOUND", f"稳定知识库结构不完整: {source_output}")
    complete = json.loads(complete_path.read_text(encoding="utf-8"))
    if not isinstance(complete, dict) or complete.get("status") != "complete":
        raise TagNavigationError("SOURCE_NOT_COMPLETE", str(complete_path))
    vault_manifest = tree_manifest(vault)
    counts = {
        "files": vault_manifest["file_count"],
        "markdown_files": vault_manifest["markdown_file_count"],
        "bytes": vault_manifest["bytes"],
        "pages": len(list((vault / "pages").glob("*.md"))),
        **_machine_counts(database),
    }
    return {
        "schema_version": 1,
        "source_output": str(source_output.resolve()),
        "source_access": "read-only",
        "commit": complete.get("commit"),
        "complete_sha256": sha256_file(complete_path),
        "vault": vault_manifest,
        "machine_sha256": sha256_file(database),
        "counts": counts,
    }


def _validate_source_identity(identity: dict[str, Any], expected: dict[str, Any]) -> None:
    checks = {
        "commit": identity["commit"] == expected["expected_commit"],
        "complete_sha256": identity["complete_sha256"] == expected["expected_complete_sha256"],
        "vault_tree_sha256": identity["vault"]["tree_sha256"] == expected["expected_vault_tree_sha256"],
        "machine_sha256": identity["machine_sha256"] == expected["expected_machine_sha256"],
        "counts": identity["counts"] == expected["expected_counts"],
    }
    if not all(checks.values()):
        raise TagNavigationError("SOURCE_DRIFT", json.dumps(checks, ensure_ascii=False, sort_keys=True))


def _page_evidence(source_output: Path, pages: Iterable[str]) -> dict[str, dict[str, Any]]:
    database = source_output / "machine" / "knowledge.sqlite"
    snapshot = source_output / ".source-snapshot" / "worktree"
    requested = sorted(set(pages))
    result: dict[str, dict[str, Any]] = {}
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        for page in requested:
            row = connection.execute(
                """
                SELECT hp.page_file, e.source_path, e.commit_id, MIN(sr.start_line), MAX(sr.end_line)
                FROM human_projection hp
                JOIN entities e ON e.entity_id = hp.entity_id
                JOIN source_ranges sr ON sr.entity_id = e.entity_id
                WHERE hp.page_file = ?
                GROUP BY hp.page_file, e.source_path, e.commit_id
                ORDER BY e.source_path, MIN(sr.start_line)
                LIMIT 1
                """,
                (page,),
            ).fetchone()
            if row is None:
                raise TagNavigationError("PAGE_NOT_IN_MACHINE_LAYER", page)
            source_path = row[1]
            snapshot_path = snapshot / Path(source_path)
            human_path = source_output / "human" / Path(page)
            if not snapshot_path.is_file() or not human_path.is_file():
                raise TagNavigationError("SOURCE_EVIDENCE_MISSING", page)
            result[page] = {
                "source_path": source_path,
                "source_sha256": sha256_file(snapshot_path),
                "source_start_line": int(row[3]),
                "source_end_line": int(row[4]),
                "human_sha256": sha256_file(human_path),
                "commit": row[2],
            }
    finally:
        connection.close()
    return result


def _identifier(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _evidence(record: dict[str, Any], kind: str, observed_at: str) -> dict[str, Any]:
    if kind == "source":
        return {
            "source_id": _identifier("src", record["source_path"]),
            "source_kind": "source-range",
            "path": record["source_path"],
            "locator": {
                "kind": "line-range",
                "start_line": record["source_start_line"],
                "end_line": record["source_end_line"],
                "section_id": None,
            },
            "sha256": record["source_sha256"],
            "commit": record["commit"],
            "observed_at": observed_at,
        }
    page = record["page"]
    return {
        "source_id": _identifier("page", page),
        "source_kind": "reviewed-record",
        "path": f"human/{page}",
        "locator": {"kind": "whole-file", "start_line": None, "end_line": None, "section_id": None},
        "sha256": record["human_sha256"],
        "commit": record["commit"],
        "observed_at": observed_at,
    }


def _assertion(
    action: str,
    task_id: str,
    page: str,
    tag: str,
    actor_category: str,
    actor_key: str,
    evidence: dict[str, Any],
    stance: str | None,
    recorded_at: str,
) -> dict[str, Any]:
    assertion_id = _identifier("assert", task_id, page, tag, action, actor_key, stance or "none")
    return {
        "schema_version": 1,
        "assertion_id": assertion_id,
        "idempotency_key": _identifier("idem", assertion_id),
        "action": action,
        "tag": tag,
        "target": {"kind": "page", "path": page},
        "stance": stance,
        "actor": {"category": actor_category, "key": actor_key},
        "evidence": evidence,
        "recorded_at": recorded_at,
        "retracts": None,
    }


def build_study_assertions(protocol: dict[str, Any], source_output: Path) -> list[dict[str, Any]]:
    validate_study_protocol(protocol)
    pages = [candidate["page"] for task in protocol["tasks"] for candidate in task["machine_candidates"]]
    page_records = _page_evidence(source_output, pages)
    recorded_at = protocol["execution"]["as_of"]
    assertions: list[dict[str, Any]] = []
    for task in protocol["tasks"]:
        for candidate in task["machine_candidates"]:
            page = candidate["page"]
            record = {**page_records[page], "page": page}
            assertions.append(
                _assertion(
                    "propose",
                    task["task_id"],
                    page,
                    task["tag"],
                    "deterministic-tool",
                    "machine-proposer",
                    _evidence(record, "source", recorded_at),
                    None,
                    recorded_at,
                )
            )
            votes: list[tuple[str, str, str]]
            decision = candidate["decision"]
            if decision == "confirmed":
                votes = [("agent-support-a", "support", "source"), ("agent-support-b", "support", "page")]
            elif decision == "candidate":
                votes = [("agent-support-a", "support", "source")]
            elif decision == "opposed":
                votes = [("agent-oppose-a", "oppose", "source"), ("agent-oppose-b", "oppose", "page")]
            else:
                votes = [("agent-support-a", "support", "source"), ("agent-oppose-a", "oppose", "page")]
            last_vote: dict[str, Any] | None = None
            for actor, stance, evidence_kind in votes:
                last_vote = _assertion(
                    "vote",
                    task["task_id"],
                    page,
                    task["tag"],
                    "source-review-agent",
                    actor,
                    _evidence(record, evidence_kind, recorded_at),
                    stance,
                    recorded_at,
                )
                assertions.append(last_vote)
            if candidate["duplicate_last_vote"]:
                if last_vote is None:
                    raise AssertionError("duplicate_last_vote requires a vote")
                assertions.append(json.loads(json.dumps(last_vote)))
    return assertions


def _write_assertions(path: Path, assertions: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = b"".join(canonical_json_bytes(item) for item in assertions)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    read_assertion_jsonl(temporary)
    temporary.replace(path)
    read_assertion_jsonl(path)


def _copy_isolated_vault(source: Path, destination: Path) -> None:
    if destination.exists():
        raise TagNavigationError("TARGET_EXISTS", str(destination))
    shutil.copytree(source, destination)
    for relative in ISOLATION_EXCLUSIONS:
        target = destination / Path(relative)
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    community_plugins = destination / ".obsidian" / "community-plugins.json"
    if community_plugins.exists():
        atomic_write_json(community_plugins, [])


def _append_tags(vault: Path, assignments: dict[str, set[str]], condition: str) -> None:
    for page in sorted(assignments):
        path = vault / Path(page)
        if not path.is_file():
            raise TagNavigationError("STUDY_PAGE_MISSING", f"{condition}:{page}")
        data = path.read_bytes()
        if EXPERIMENT_MARKER.encode("utf-8") in data:
            raise TagNavigationError("EXPERIMENT_MARKER_EXISTS", f"{condition}:{page}")
        tags = " ".join(f"#{tag}" for tag in sorted(assignments[page]))
        suffix = f"\n\n{EXPERIMENT_MARKER}\n{tags}\n".encode("utf-8")
        path.write_bytes(data + suffix)


def _machine_assignments(assertions: list[dict[str, Any]]) -> dict[str, set[str]]:
    assignments: dict[str, set[str]] = defaultdict(set)
    for item in assertions:
        if item["action"] == "propose":
            assignments[item["target"]["path"]].add(item["tag"])
    return assignments


def _confirmed_assignments(audit: dict[str, Any]) -> dict[str, set[str]]:
    assignments: dict[str, set[str]] = defaultdict(set)
    for item in audit["results"]:
        if item["state"] == "confirmed":
            assignments[item["target"]["path"]].add(item["tag"])
    return assignments


def _vault_graph(vault: Path) -> tuple[dict[str, list[str]], dict[str, int]]:
    files = sorted(vault.rglob("*.md"), key=lambda path: path.relative_to(vault).as_posix())
    relatives = {path: path.relative_to(vault).as_posix() for path in files}
    by_stem: dict[str, list[str]] = defaultdict(list)
    for path, relative in relatives.items():
        by_stem[path.stem].append(relative)
    graph: dict[str, list[str]] = {relative: [] for relative in relatives.values()}
    unresolved = 0
    ambiguous = 0
    for path, relative in relatives.items():
        for raw in WIKILINK.findall(path.read_text(encoding="utf-8", errors="strict")):
            title = raw.split("|", 1)[0].split("#", 1)[0].replace("\\", "/")
            if title.endswith(".md"):
                title = title[:-3]
            candidates: list[str]
            if "/" in title:
                candidate = title.lstrip("/") + ".md"
                candidates = [candidate] if candidate in graph else []
            else:
                candidates = by_stem.get(title, [])
            if len(candidates) == 1:
                graph[relative].append(candidates[0])
            elif candidates:
                ambiguous += 1
            else:
                unresolved += 1
        graph[relative] = sorted(set(graph[relative]))
    return graph, {"resolved_links": sum(len(items) for items in graph.values()), "unresolved_links": unresolved, "ambiguous_links": ambiguous}


def _shortest_path(graph: dict[str, list[str]], start: str, target: str) -> list[str] | None:
    if start not in graph or target not in graph:
        return None
    queue = deque([start])
    previous: dict[str, str | None] = {start: None}
    while queue:
        current = queue.popleft()
        if current == target:
            break
        for neighbor in graph[current]:
            if neighbor not in previous:
                previous[neighbor] = current
                queue.append(neighbor)
    if target not in previous:
        return None
    path: list[str] = []
    current: str | None = target
    while current is not None:
        path.append(current)
        current = previous[current]
    return list(reversed(path))


def _orphan_count(graph: dict[str, list[str]], prefixes: list[str], assignments: dict[str, set[str]]) -> int:
    incoming = Counter(target for neighbors in graph.values() for target in neighbors)
    return sum(
        1
        for page in graph
        if any(page.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)
        and incoming[page] == 0
        and not assignments.get(page)
    )


def _measure_condition(
    condition: str,
    vault: Path,
    protocol: dict[str, Any],
    assignments: dict[str, set[str]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    graph, link_metrics = _vault_graph(vault)
    reverse_tags: dict[str, list[str]] = defaultdict(list)
    for page, tags in assignments.items():
        for tag in tags:
            reverse_tags[tag].append(page)
    for pages in reverse_tags.values():
        pages.sort(key=lambda value: (value.casefold(), value))
    budget = protocol["execution"]["step_budget"]
    entry = protocol["execution"]["entry_page"]
    rows: list[dict[str, Any]] = []
    for task in protocol["tasks"]:
        if condition == "no_tag":
            path = _shortest_path(graph, entry, task["target"])
            candidates: list[str] = []
            errors = 0
        else:
            candidates = reverse_tags.get(task["tag"], [])
            if task["target"] in candidates:
                visited = candidates[: candidates.index(task["target"]) + 1]
                path = [entry, f"#{task['tag']}", *visited]
                errors = len(visited) - 1
            else:
                path = None
                errors = len(candidates)
        steps = len(path) - 1 if path is not None else None
        discoverable = steps is not None and steps <= budget
        rows.append(
            {
                "task_id": task["task_id"],
                "condition": condition,
                "target": task["target"],
                "tag": task["tag"],
                "discoverable_within_budget": discoverable,
                "jump_steps": steps,
                "error_navigation_count": errors,
                "visited_path": path or [],
                "candidate_count": len(candidates),
            }
        )
    successful_steps = [row["jump_steps"] for row in rows if row["jump_steps"] is not None]
    aggregate = {
        "task_count": len(rows),
        "discoverable_count": sum(row["discoverable_within_budget"] for row in rows),
        "discoverability_rate": round(sum(row["discoverable_within_budget"] for row in rows) / len(rows), 6),
        "total_jump_steps": sum(successful_steps),
        "median_jump_steps": median(successful_steps) if successful_steps else None,
        "error_navigation_count": sum(row["error_navigation_count"] for row in rows),
        "orphan_page_count": _orphan_count(graph, protocol["execution"]["orphan_scope_prefixes"], assignments),
        "experimental_unique_tag_count": len(reverse_tags),
        "experimental_tag_assignment_count": sum(len(tags) for tags in assignments.values()),
        "markdown_page_count": len(graph),
        **link_metrics,
    }
    return aggregate, rows


def _audit_cost(assertions: list[dict[str, Any]], replay: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    unique = {(item["assertion_id"], item["idempotency_key"]) for item in assertions}
    return {
        "assertion_lines_evaluated": len(assertions),
        "unique_assertions_stored": len(unique),
        "duplicate_lines_ignored": replay["duplicates"],
        "proposal_events": sum(item["action"] == "propose" for item in assertions),
        "vote_events": sum(item["action"] == "vote" for item in assertions),
        "target_tag_pairs": len(audit["results"]),
        "reason_codes_emitted": sum(len(item["reason_codes"]) for item in audit["results"]),
        "confirmed_pairs": audit["summary"]["confirmed"],
        "excluded_pairs": len(audit["results"]) - audit["summary"]["confirmed"],
    }


def _directory_digest(root: Path, excluded: set[str]) -> str:
    entries = [item for item in _tree_entries(root) if item["path"] not in excluded]
    return sha256_bytes(canonical_json_bytes(entries))


def run_real_vault_study(
    source_output: Path,
    protocol: dict[str, Any],
    policy: dict[str, Any],
    output: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    protocol = validate_study_protocol(protocol)
    policy = validate_policy(policy)
    workspace = workspace_root.resolve()
    target = ensure_within(output, workspace, "out")
    if target.exists():
        raise TagNavigationError("TARGET_EXISTS", str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    before = source_identity(source_output.resolve())
    _validate_source_identity(before, protocol["source"])
    try:
        target.mkdir()
        atomic_write_json(target / "protocol.json", protocol)
        atomic_write_json(target / "policy.json", policy)
        atomic_write_json(target / "source-before.json", before)
        assertions = build_study_assertions(protocol, source_output.resolve())
        assertion_path = target / "assertions.jsonl"
        _write_assertions(assertion_path, assertions)
        replay = replay_with_rollback(assertion_path, target / "tags.sqlite", target / "tags.rollback.json")
        audit = audit_database(target / "tags.sqlite", policy, before["commit"], protocol["execution"]["as_of"])
        projection = build_projection(audit, policy)
        atomic_write_json(target / "audit.json", audit)
        atomic_write_json(target / "projection.json", projection)

        machine_assignments = _machine_assignments(assertions)
        confirmed_assignments = _confirmed_assignments(audit)
        assignment_map = {
            "no_tag": {},
            "machine_tag": machine_assignments,
            "confirmed_tag": confirmed_assignments,
        }
        aggregates: dict[str, dict[str, Any]] = {}
        rows: list[dict[str, Any]] = []
        vault_manifests: dict[str, dict[str, Any]] = {}
        for condition in CONDITIONS:
            vault = target / "vaults" / condition
            _copy_isolated_vault(source_output / "human", vault)
            _append_tags(vault, assignment_map[condition], condition)
            aggregate, current_rows = _measure_condition(condition, vault, protocol, assignment_map[condition])
            aggregates[condition] = aggregate
            rows.extend(current_rows)
            vault_manifests[condition] = tree_manifest(vault)

        after = source_identity(source_output.resolve())
        atomic_write_json(target / "source-after.json", after)
        if before["vault"]["tree_sha256"] != after["vault"]["tree_sha256"] or before["machine_sha256"] != after["machine_sha256"] or before["complete_sha256"] != after["complete_sha256"]:
            raise TagNavigationError("SOURCE_MUTATED_DURING_STUDY", str(source_output))
        audit_cost = _audit_cost(assertions, replay, audit)
        raw = {
            "schema_version": 1,
            "status": "passed",
            "study_id": protocol["study_id"],
            "task_order": protocol["execution"]["task_order"],
            "step_budget": protocol["execution"]["step_budget"],
            "records": rows,
            "vault_manifests": vault_manifests,
        }
        atomic_write_json(target / "raw-results.json", raw)
        report = {
            "schema_version": 1,
            "status": "passed",
            "study_id": protocol["study_id"],
            "scope": "isolated-real-vault-system-proxy",
            "production_default_changed": False,
            "effect_claim": "system-navigation-proxy-only",
            "human_result": "pending-human-validation",
            "source": {
                "commit": before["commit"],
                "vault_tree_sha256": before["vault"]["tree_sha256"],
                "machine_sha256": before["machine_sha256"],
                "counts": before["counts"],
                "unchanged_after_run": True,
            },
            "isolation": {
                "vaults": {condition: str((target / "vaults" / condition).resolve()) for condition in CONDITIONS},
                "excluded_control_paths": list(ISOLATION_EXCLUSIONS),
                "companion_plugin_enabled": False,
            },
            "conditions": aggregates,
            "audit_state_counts": audit["summary"],
            "audit_cost": audit_cost,
            "determinism": {
                "task_order": protocol["execution"]["task_order"],
                "step_budget": protocol["execution"]["step_budget"],
                "candidate_order": protocol["execution"]["candidate_order"],
                "as_of": protocol["execution"]["as_of"],
            },
            "artifacts": {
                "protocol": str((target / "protocol.json").resolve()),
                "assertions": str(assertion_path.resolve()),
                "database": str((target / "tags.sqlite").resolve()),
                "audit": str((target / "audit.json").resolve()),
                "projection": str((target / "projection.json").resolve()),
                "raw_results": str((target / "raw-results.json").resolve()),
            },
        }
        atomic_write_json(target / "report.json", report)
        excluded = {"study.rollback.json"}
        manifest = {
            "schema_version": 1,
            "target_path": str(target),
            "baseline_state": "absent",
            "excluded_from_digest": sorted(excluded),
            "generated_tree_sha256": _directory_digest(target, excluded),
        }
        atomic_write_json(target / "study.rollback.json", manifest)
        reopened_report = json.loads((target / "report.json").read_text(encoding="utf-8"))
        if reopened_report != report:
            raise TagNavigationError("ARTIFACT_REOPEN_FAILED", "report.json")
        return {
            **report,
            "output": str(target),
            "report_sha256": sha256_file(target / "report.json"),
            "rollback_manifest": str((target / "study.rollback.json").resolve()),
        }
    except Exception:
        if target.exists():
            shutil.rmtree(target)
        raise


def rollback_real_vault_study(manifest_path: Path, workspace_root: Path) -> dict[str, Any]:
    workspace = workspace_root.resolve()
    manifest = ensure_within(manifest_path, workspace, "manifest")
    try:
        value = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TagNavigationError("INVALID_STUDY_ROLLBACK", str(exc)) from exc
    expected = {"schema_version", "target_path", "baseline_state", "excluded_from_digest", "generated_tree_sha256"}
    if not isinstance(value, dict) or set(value) != expected or value.get("schema_version") != 1 or value.get("baseline_state") != "absent":
        raise TagNavigationError("INVALID_STUDY_ROLLBACK", "manifest 字段非法")
    target = ensure_within(Path(value["target_path"]), workspace, "target")
    if manifest.parent != target:
        raise TagNavigationError("INVALID_STUDY_ROLLBACK", "manifest 必须位于 target 根目录")
    excluded = set(value["excluded_from_digest"])
    if excluded != {"study.rollback.json"}:
        raise TagNavigationError("INVALID_STUDY_ROLLBACK", "excluded_from_digest 非法")
    actual = _directory_digest(target, excluded)
    if actual != value["generated_tree_sha256"]:
        raise TagNavigationError("ROLLBACK_DRIFT", f"expected={value['generated_tree_sha256']} actual={actual}")
    shutil.rmtree(target)
    if target.exists():
        raise TagNavigationError("ROLLBACK_VERIFY_FAILED", str(target))
    return {"schema_version": 1, "status": "rolled-back", "target": str(target), "baseline_state": "absent"}
