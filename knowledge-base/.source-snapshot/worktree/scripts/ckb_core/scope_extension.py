"""Audited, reversible extension of a completed CKB knowledge scope."""

from __future__ import annotations

import hashlib
import json
import gc
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
from typing import Any
import warnings

from .common import CkbError, json_load, json_write, path_inside, sha256_file, stable_id
from .gitrepo import LANGUAGE_BY_SUFFIX, preflight
from .migration import (
    _entity_key,
    _preserve_mutable_layers,
    _replace_review_packs,
    _review_for_new_entity,
    _review_shape,
    _selected_entities,
)
from .pipeline import build_chunk, finalize, initialize, status as pipeline_status


SCOPE_EXTENSION_SCHEMA_VERSION = 1
STATE_RELATIVE = Path("scope-extension/state.json")
PLAN_RELATIVE = Path("scope-extension/plan.json")
AUDIT_RELATIVE = Path("scope-extension/audit.json")
SUPPORTED_LANGUAGES = tuple(sorted(set(LANGUAGE_BY_SUFFIX.values())))


def _error(category: str, message: str) -> CkbError:
    return CkbError(f"scope-extension:{category}: {message}")


def _canonical_entry(value: str) -> str:
    value = value.strip()
    if "#" not in value:
        raise _error("entry-shape", f"new entry must use LANGUAGE:PATH#QUALIFIED_NAME: {value}")
    left, qualified = value.split("#", 1)
    if ":" not in left:
        raise _error("entry-shape", f"new entry must use LANGUAGE:PATH#QUALIFIED_NAME: {value}")
    language, path = left.split(":", 1)
    language = language.strip().casefold()
    normalized_path = PurePosixPath(path.replace("\\", "/").strip("/"))
    if language not in SUPPORTED_LANGUAGES:
        raise _error("unsupported-language", f"entry language is not supported: {language}")
    if not path or normalized_path.is_absolute() or ".." in normalized_path.parts:
        raise _error("entry-path", f"entry path must be a repository-relative source path: {path}")
    if not qualified.strip():
        raise _error("entry-qualified-name", "entry qualified name must not be empty")
    return f"{language}:{normalized_path.as_posix()}#{qualified.strip()}"


def _tree_manifest(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise _error("output-missing", f"directory does not exist: {root}")
    files: list[dict[str, Any]] = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        files.append({"path": relative, "size": path.stat().st_size, "sha256": sha256_file(path)})
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "algorithm": "sha256-tree-v1",
        "file_count": len(files),
        "byte_count": sum(int(item["size"]) for item in files),
        "sha256": hashlib.sha256(canonical).hexdigest(),
        "files": files,
    }


def _same_manifest(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return all(left.get(key) == right.get(key) for key in ("algorithm", "file_count", "byte_count", "sha256", "files"))


def _sqlite_checks(output: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for relative in ("machine/knowledge.sqlite", "agent-index.sqlite", "machine/automation.sqlite"):
        path = output / relative
        if not path.is_file():
            if relative == "machine/automation.sqlite":
                continue
            checks.append({"path": relative, "integrity_check": "missing", "foreign_key_errors": None, "passed": False})
            continue
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        finally:
            connection.close()
        checks.append({
            "path": relative,
            "integrity_check": integrity,
            "foreign_key_errors": [list(row) for row in foreign_keys],
            "passed": integrity == "ok" and not foreign_keys,
        })
    return checks


def _release_audit_handles() -> None:
    """Release transient sqlite objects left by read-only audit helpers."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ResourceWarning)
        gc.collect()


def _candidate_graph(output: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    state = json_load(output / "state.json")
    entities: dict[str, dict[str, Any]] = {}
    links: dict[str, dict[str, Any]] = {}
    for batch in state["parse_batches"]:
        candidate = json_load(output / "chunks" / batch["id"] / "candidate.json")
        entities.update((item["id"], item) for item in candidate.get("entities", []))
        links.update((item["id"], item) for item in candidate.get("links", []))
    return [entities[key] for key in sorted(entities)], [links[key] for key in sorted(links)]


def _dimension(old_values: set[str], new_values: set[str]) -> dict[str, Any]:
    return {
        "retained": sorted(old_values & new_values),
        "added": sorted(new_values - old_values),
        "removed": sorted(old_values - new_values),
        "counts": {
            "retained": len(old_values & new_values),
            "added": len(new_values - old_values),
            "removed": len(old_values - new_values),
        },
    }


def _page_ids(document: dict[str, Any]) -> set[str]:
    return set(document.get("page_entity_ids") or [])


def _replace_prefix(value: Any, old: str, new: str) -> Any:
    if isinstance(value, dict):
        return {key: _replace_prefix(item, old, new) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_prefix(item, old, new) for item in value]
    if isinstance(value, str):
        return value.replace(old, new).replace(old.replace("\\", "/"), new.replace("\\", "/"))
    return value


def _rebind_preserved_json(staging: Path, previous_output: Path, mutable_files: list[dict[str, Any]]) -> list[str]:
    changed: list[str] = []
    old = str(previous_output.resolve())
    new = str(staging.resolve())
    for item in mutable_files:
        relative = str(item.get("relative_target") or "")
        path = staging / relative
        if path.suffix.casefold() != ".json" or not path.is_file():
            continue
        try:
            value = json_load(path)
        except (CkbError, OSError, UnicodeError, json.JSONDecodeError):
            continue
        updated = _replace_prefix(value, old, new)
        if updated != value:
            json_write(path, updated)
            changed.append(relative)
        item["post_extension_sha256"] = sha256_file(path)
        item["post_extension_size"] = path.stat().st_size
    return sorted(changed)


def _layer_inventory(output: Path, mutable_files: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    gaps = list((output / "workspace-meta/gaps/records").glob("gap-*.json"))
    gap_statuses: dict[str, int] = {}
    for path in gaps:
        status = str(json_load(path).get("status"))
        gap_statuses[status] = gap_statuses.get(status, 0) + 1
    manifests = list((output / "references/manifests").glob("*.json"))
    reference_statuses: dict[str, int] = {}
    for path in manifests:
        status = str(json_load(path).get("status"))
        reference_statuses[status] = reference_statuses.get(status, 0) + 1
    records = mutable_files or []
    return {
        "work_record_count": len(list((output / "workspace-meta/notes").glob("*.json"))),
        "reference_count": len(manifests),
        "reference_statuses": dict(sorted(reference_statuses.items())),
        "gap_count": len(gaps),
        "gap_statuses": dict(sorted(gap_statuses.items())),
        "feedback_count": len(list((output / "workspace-meta/feedback").glob("*/*.json"))),
        "operation_shard_count": len(list((output / "workspace-meta/operations").glob("*.jsonl"))),
        "vault_user_files": sorted(
            item["relative_target"]
            for item in records
            if item.get("kind") == "vault-user-file"
        ),
    }


def _preservation_errors(staging: Path, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for item in records:
        relative = str(item.get("relative_target") or "")
        baseline_relative = str(item.get("baseline_relative_target") or "")
        target = staging / relative
        baseline = staging / baseline_relative
        if not baseline.is_file() or sha256_file(baseline) != item.get("baseline_sha256"):
            errors.append({"path": relative, "reason": "baseline-missing-or-changed"})
            continue
        if not target.is_file():
            errors.append({"path": relative, "reason": "live-file-missing"})
            continue
        # A same-snapshot scope extension does not rekey page titles.  Vault
        # user bytes, including learning notes and work-record prose, therefore
        # remain exact; JSON control records may receive bounded path rebinding.
        if item.get("kind") == "vault-user-file" and sha256_file(target) != item.get("initial_target_sha256"):
            errors.append({"path": relative, "reason": "vault-user-file-changed"})
    return errors


def _recomputed_review_sets(staging: Path, old_graph: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    new_entities, _sources = _selected_entities(staging)
    _candidate_entities, candidate_links = _candidate_graph(staging)
    old_links = {item["id"]: item for item in old_graph.get("links", [])}
    new_links = {item["id"]: item for item in candidate_links}
    added_relation_ids = set(new_links) - set(old_links)
    affected_ids = {
        endpoint
        for relation_id in added_relation_ids
        for endpoint in (new_links[relation_id].get("source"), new_links[relation_id].get("target"))
        if endpoint
    }
    catalog = json_load(staging / "catalog.json")
    reuse_paths = set((catalog.get("migration_reuse") or {}).get("reused_file_paths", []))
    old_by_key = {_entity_key(entity): entity for entity in old_graph.get("entities", [])}
    reusable: set[str] = set()
    for entity in new_entities:
        previous = old_by_key.get(_entity_key(entity))
        if (
            entity["path"] in reuse_paths
            and entity["id"] not in affected_ids
            and previous
            and previous.get("review_status") == "agent-reviewed"
            and _review_shape(previous.get("classification")) == _review_shape(entity.get("classification"))
        ):
            reusable.add(entity["id"])
    selected = {item["id"] for item in new_entities}
    return reusable, selected - reusable, added_relation_ids


def _load_extension_state(output: Path) -> dict[str, Any]:
    path = output.resolve() / STATE_RELATIVE
    if not path.is_file():
        raise _error("state-missing", f"scope extension state does not exist: {path}")
    value = json_load(path)
    if value.get("schema_version") != SCOPE_EXTENSION_SCHEMA_VERSION:
        raise _error("state-schema", "scope extension state schema is unsupported")
    if Path(str(value.get("staging_output"))).resolve() != output.resolve():
        raise _error("absolute-binding", "state staging_output does not match the requested output")
    return value


def start_scope_extension(
    previous_output: Path,
    repository: Path,
    staging: Path,
    entries: list[str],
    expand_depth: int,
    expand_direction: str,
) -> dict[str, Any]:
    previous_output = previous_output.resolve()
    repository = repository.resolve()
    staging = staging.resolve()
    if path_inside(staging, previous_output) or path_inside(previous_output, staging):
        raise _error("overlapping-output", "staging and previous OUTPUT must be separate, non-overlapping directories")
    if expand_depth < 0:
        raise _error("expand-depth", "extension depth must be zero or greater")
    if expand_direction not in {"both", "callers", "callees"}:
        raise _error("expand-direction", f"unsupported expansion direction: {expand_direction}")
    canonical_added = [_canonical_entry(value) for value in entries]
    if not canonical_added:
        raise _error("entry-required", "at least one new entry is required")
    if len(set(canonical_added)) != len(canonical_added):
        raise _error("duplicate-entry", "the same new center was supplied more than once")

    old_state = json_load(previous_output / "state.json")
    old_audit = json_load(previous_output / "audit/global.json")
    old_scope = json_load(previous_output / "scope.json")
    old_graph = json_load(previous_output / "graph.json")
    if old_state.get("status") != "complete" or old_audit.get("status") != "passed" or not (previous_output / ".complete").is_file():
        raise _error("origin-not-audited", f"previous OUTPUT is not complete and globally audited: {previous_output}")
    selectors = old_scope.get("selectors") or {}
    old_entries = list(selectors.get("entries") or [])
    old_canonical = {_canonical_entry(value) for value in old_entries if "#" in str(value)}
    duplicates = sorted(set(canonical_added) & old_canonical)
    if duplicates:
        raise _error("entry-already-present", f"new center already exists in the old scope: {duplicates}")
    target_entries = [*old_entries, *sorted(canonical_added)]
    repository_state = preflight(repository)
    operation_id = stable_id(
        "scope-extension",
        previous_output,
        repository_state["commit"],
        *target_entries,
        expand_depth,
        expand_direction,
    )
    request = {
        "previous_output": str(previous_output),
        "repository": str(repository),
        "repository_commit": repository_state["commit"],
        "staging_output": str(staging),
        "added_entries": sorted(canonical_added),
        "target_entries": target_entries,
        "expand_depth": expand_depth,
        "expand_direction": expand_direction,
    }
    if staging.exists():
        state_path = staging / STATE_RELATIVE
        if not state_path.is_file():
            raise _error("staging-not-empty", f"staging already exists without matching extension state: {staging}")
        existing = _load_extension_state(staging)
        if existing.get("operation_id") != operation_id or existing.get("request") != request:
            raise _error("staging-conflict", "staging is bound to a different scope extension request")
        return extension_status(staging)

    origin_manifest = _tree_manifest(previous_output)
    try:
        initialize(
            repository,
            staging,
            old_state["format"],
            list(selectors.get("scope_paths") or []),
            target_entries,
            expand_depth,
            expand_direction,
            list(selectors.get("include") or []),
            csharp_solution=selectors.get("csharp_solution"),
            csharp_project=selectors.get("csharp_project"),
            allow_dotnet_restore=bool(selectors.get("allow_dotnet_restore", False)),
            page_config_path=previous_output / "page-config.json",
            reuse_from_output=previous_output,
        )
        mutable_files = _preserve_mutable_layers(previous_output, staging)
        rebound_json = _rebind_preserved_json(staging, previous_output, mutable_files)
        state = json_load(staging / "state.json")
        for batch in state["parse_batches"]:
            build_chunk(staging, batch["id"], "all")
        new_entities, _sources = _selected_entities(staging)
        _candidate_entities, candidate_links = _candidate_graph(staging)
        old_links = {item["id"]: item for item in old_graph.get("links", [])}
        new_links = {item["id"]: item for item in candidate_links}
        added_relation_ids = set(new_links) - set(old_links)
        affected_ids = {
            endpoint
            for relation_id in added_relation_ids
            for endpoint in (new_links[relation_id].get("source"), new_links[relation_id].get("target"))
            if endpoint
        }
        catalog = json_load(staging / "catalog.json")
        reuse_paths = set((catalog.get("migration_reuse") or {}).get("reused_file_paths", []))
        old_by_key = {_entity_key(entity): entity for entity in old_graph.get("entities", [])}
        reusable_reviews: dict[str, dict[str, Any]] = {}
        id_map: dict[str, str] = {}
        for entity in new_entities:
            previous = old_by_key.get(_entity_key(entity))
            if (
                entity["path"] in reuse_paths
                and entity["id"] not in affected_ids
                and previous
                and previous.get("review_status") == "agent-reviewed"
                and _review_shape(previous.get("classification")) == _review_shape(entity.get("classification"))
            ):
                reusable_reviews[entity["id"]] = _review_for_new_entity(entity, previous)
                id_map[str(previous["id"])] = entity["id"]
        reused_ids, delta_ids = _replace_review_packs(staging, reusable_reviews)

        new_scope = json_load(staging / "scope.json")
        new_navigation = json_load(staging / "navigation-plan.json")
        old_navigation = old_graph.get("navigation_plan") or {}
        dimensions = {
            "entries": _dimension(set(old_entries), set(target_entries)),
            "paths": _dimension(set(old_scope.get("selected_file_paths") or []), set(new_scope.get("selected_file_paths") or [])),
            "entities": _dimension({item["id"] for item in old_graph.get("entities", [])}, set(new_scope.get("selected_entity_ids") or [])),
            "relations": _dimension(set(old_links), set(new_links)),
            "pages": _dimension(_page_ids(old_navigation), _page_ids(new_navigation)),
        }
        removed = {name: value["removed"] for name, value in dimensions.items() if value["removed"]}
        if removed:
            raise _error("scope-contraction", f"append-only extension removed prior scope items: {removed}")
        final_state = json_load(staging / "state.json")
        extension = {
            "schema_version": SCOPE_EXTENSION_SCHEMA_VERSION,
            "operation_id": operation_id,
            "status": "pending-agent-review" if delta_ids else "ready-for-audit",
            "previous_output": str(previous_output),
            "staging_output": str(staging),
            "repository": str(repository),
            "repository_commit": repository_state["commit"],
            "request": request,
        }
        final_state["scope_extension"] = extension
        json_write(staging / "state.json", final_state)
        plan = {
            "schema_version": SCOPE_EXTENSION_SCHEMA_VERSION,
            "operation_id": operation_id,
            "status": extension["status"],
            "bindings": {
                "previous_output": str(previous_output),
                "staging_output": str(staging),
                "repository": str(repository),
                "repository_commit": repository_state["commit"],
                "origin_commit": old_state.get("repository", {}).get("commit"),
            },
            "selectors": {
                "old_entries": old_entries,
                "added_entries": sorted(canonical_added),
                "target_entries": target_entries,
                "expand_depth": expand_depth,
                "expand_direction": expand_direction,
            },
            "delta": dimensions,
            "review": {
                "reused_entity_ids": sorted(reused_ids),
                "delta_entity_ids": sorted(delta_ids),
                "affected_relation_ids": sorted(added_relation_ids),
                "affected_existing_entity_ids": sorted(affected_ids & {item["id"] for item in old_graph.get("entities", [])}),
                "old_to_new_id_map": id_map,
            },
            "reuse": {
                "file_paths": sorted(reuse_paths),
                "file_count": len(reuse_paths),
                "review_entity_count": len(reused_ids),
                "delta_review_entity_count": len(delta_ids),
            },
            "preservation": {
                "origin_manifest": origin_manifest,
                "mutable_files": mutable_files,
                "rebound_json_files": rebound_json,
                "origin_layers": _layer_inventory(previous_output, mutable_files),
            },
        }
        json_write(staging / PLAN_RELATIVE, plan)
        json_write(staging / STATE_RELATIVE, {**extension, "request": request})
    except Exception as exc:
        if staging.exists():
            shutil.rmtree(staging)
        if isinstance(exc, CkbError) and str(exc).startswith("scope-extension:"):
            raise
        message = str(exc)
        category = "entry-resolution" if "entry resolves to" in message else "start-failed"
        raise _error(category, message) from exc
    return extension_status(staging)


def _control_records(output: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Load and validate the immutable control history for one OUTPUT name.

    Legacy schema-1 records did not persist parent_operation_id.  Their parent
    is inferred only when exactly one older modified manifest equals the
    child's origin manifest.  New records persist that same relation and depth.
    """
    output = output.resolve()
    records: list[tuple[Path, dict[str, Any]]] = []
    by_id: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(output.parent.glob(f".{output.name}.scope-extension-*.json")):
        value = json_load(path)
        operation_id = str(value.get("operation_id") or "")
        if value.get("schema_version") != SCOPE_EXTENSION_SCHEMA_VERSION or not operation_id:
            raise _error("control-record-drift", f"control record schema or operation id is invalid: {path}")
        if path != _control_path(output, operation_id):
            raise _error("control-record-drift", f"control record path does not match operation id: {path}")
        if Path(str(value.get("output") or "")).resolve() != output:
            raise _error("control-record-drift", f"control record OUTPUT binding drifted: {path}")
        if operation_id in by_id:
            raise _error("control-record-drift", f"duplicate control operation id: {operation_id}")
        item = json.loads(json.dumps(value))
        records.append((path, item))
        by_id[operation_id] = (path, item)

    for path, value in records:
        origin = value.get("origin_manifest")
        if not isinstance(origin, dict):
            raise _error("control-record-drift", f"control origin manifest is missing: {path}")
        inferred = [
            candidate
            for _candidate_path, candidate in records
            if candidate.get("operation_id") != value.get("operation_id")
            and isinstance(candidate.get("modified_manifest"), dict)
            and _same_manifest(candidate["modified_manifest"], origin)
        ]
        if "parent_operation_id" in value:
            parent_id = value.get("parent_operation_id")
            if parent_id is not None:
                parent = by_id.get(str(parent_id))
                if parent is None or not isinstance(parent[1].get("modified_manifest"), dict) or not _same_manifest(parent[1]["modified_manifest"], origin):
                    raise _error("control-record-drift", f"parent operation does not produce the child origin: {path}")
        else:
            if len(inferred) > 1:
                raise _error("control-record-drift", f"legacy parent operation is ambiguous: {path}")
            parent_id = inferred[0]["operation_id"] if inferred else None
        value["parent_operation_id"] = parent_id

    depths: dict[str, int] = {}

    def depth(operation_id: str, trail: set[str]) -> int:
        if operation_id in depths:
            return depths[operation_id]
        if operation_id in trail:
            raise _error("control-record-drift", f"control parent cycle includes: {operation_id}")
        value = by_id[operation_id][1]
        parent_id = value.get("parent_operation_id")
        result = 1 if parent_id is None else depth(str(parent_id), {*trail, operation_id}) + 1
        recorded = value.get("chain_depth")
        if recorded is not None and int(recorded) != result:
            raise _error("control-record-drift", f"control chain depth drifted: {operation_id}")
        value["chain_depth"] = result
        depths[operation_id] = result
        return result

    for _path, value in records:
        depth(str(value["operation_id"]), set())
    return records


def _control_selection(output: Path, actual_manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    output = output.resolve()
    records = _control_records(output)
    actual = actual_manifest or _tree_manifest(output)
    active = [
        (path, value)
        for path, value in records
        if value.get("status") == "cutover-complete"
        and isinstance(value.get("modified_manifest"), dict)
        and _same_manifest(value["modified_manifest"], actual)
    ]
    if len(active) > 1:
        raise _error("control-record-active-ambiguous", f"multiple active cutovers match current OUTPUT: {[item[1]['operation_id'] for item in active]}")
    rolled_back = [
        (path, value)
        for path, value in records
        if value.get("status") == "rolled-back"
        and _same_manifest(value["origin_manifest"], actual)
    ]
    return {
        "records": records,
        "actual_manifest": actual,
        "active": active[0] if active else None,
        "rolled_back_matches": rolled_back,
    }


def _public_control(value: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(value))


def extension_status(output: Path) -> dict[str, Any]:
    output = output.resolve()
    controls = sorted(output.parent.glob(f".{output.name}.scope-extension-*.json"))
    if controls:
        selection = _control_selection(output)
        if selection["active"]:
            _path, active = selection["active"]
            return {
                "schema_version": SCOPE_EXTENSION_SCHEMA_VERSION,
                "status": "cutover-complete",
                "active_operation_id": active["operation_id"],
                "parent_operation_id": active.get("parent_operation_id"),
                "chain_depth": active["chain_depth"],
                "cutover": _public_control(active),
                "control_record_count": len(selection["records"]),
            }
        rolled_back = selection["rolled_back_matches"]
        return {
            "schema_version": SCOPE_EXTENSION_SCHEMA_VERSION,
            "status": "rolled-back" if len(rolled_back) == 1 else "no-active-cutover",
            "active_operation_id": None,
            "rolled_back_operation_id": rolled_back[0][1]["operation_id"] if len(rolled_back) == 1 else None,
            "matching_rolled_back_operation_ids": [value["operation_id"] for _path, value in rolled_back],
            "control_record_count": len(selection["records"]),
        }
    state = _load_extension_state(output)
    plan = json_load(output / PLAN_RELATIVE)
    build_state = json_load(output / "state.json")
    pending = [item["id"] for item in build_state.get("review_packs", []) if item.get("status") != "passed"]
    return {
        "schema_version": SCOPE_EXTENSION_SCHEMA_VERSION,
        "status": state["status"],
        "operation_id": state["operation_id"],
        "previous_output": state["previous_output"],
        "staging_output": state["staging_output"],
        "repository_commit": state["repository_commit"],
        "pending_review_packs": pending,
        "next_review_template": next((item.get("review_template_path") for item in build_state.get("review_packs", []) if item.get("status") != "passed"), None),
        "delta": plan["delta"],
        "reuse": plan["reuse"],
    }


def audit_scope_extension(staging: Path) -> dict[str, Any]:
    staging = staging.resolve()
    state = _load_extension_state(staging)
    plan = json_load(staging / PLAN_RELATIVE)
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any, category: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "category": category, "detail": detail})

    origin = Path(state["previous_output"])
    actual_origin = _tree_manifest(origin)
    expected_origin = plan["preservation"]["origin_manifest"]
    check("origin-output-unchanged", _same_manifest(actual_origin, expected_origin), {"expected": expected_origin["sha256"], "actual": actual_origin["sha256"]}, "origin-drift")
    repository_state = preflight(Path(state["repository"]))
    check("target-repository-pinned", repository_state["commit"] == state["repository_commit"], repository_state, "target-drift")
    removed = {name: value["removed"] for name, value in plan["delta"].items() if value["removed"]}
    check("append-only-delta", not removed, removed, "scope-contraction")
    build_state = json_load(staging / "state.json")
    old_graph = json_load(origin / "graph.json")
    expected_reused, expected_delta, expected_added_relations = _recomputed_review_sets(staging, old_graph)
    actual_reused = {
        entity_id
        for pack in build_state.get("review_packs", [])
        if str(pack.get("id", "")).startswith("migrated-")
        for entity_id in pack.get("entity_ids", [])
    }
    actual_delta = {
        entity_id
        for pack in build_state.get("review_packs", [])
        if str(pack.get("id", "")).startswith("delta-")
        for entity_id in pack.get("entity_ids", [])
    }
    review_detail = {
        "reused_missing": sorted(expected_reused - actual_reused),
        "reused_extra": sorted(actual_reused - expected_reused),
        "delta_missing": sorted(expected_delta - actual_delta),
        "delta_extra": sorted(actual_delta - expected_delta),
        "relation_delta_missing": sorted(expected_added_relations - set(plan["review"]["affected_relation_ids"])),
        "relation_delta_extra": sorted(set(plan["review"]["affected_relation_ids"]) - expected_added_relations),
        "plan_reused_missing": sorted(expected_reused - set(plan["review"]["reused_entity_ids"])),
        "plan_reused_extra": sorted(set(plan["review"]["reused_entity_ids"]) - expected_reused),
        "plan_delta_missing": sorted(expected_delta - set(plan["review"]["delta_entity_ids"])),
        "plan_delta_extra": sorted(set(plan["review"]["delta_entity_ids"]) - expected_delta),
    }
    check("exact-delta-review-set", not any(review_detail.values()), review_detail, "delta-review-drift")
    preservation_errors = _preservation_errors(staging, plan["preservation"]["mutable_files"])
    actual_layers = _layer_inventory(staging, plan["preservation"]["mutable_files"])
    expected_layers = plan["preservation"]["origin_layers"]
    check(
        "mutable-layers-preserved",
        not preservation_errors and actual_layers == expected_layers,
        {"errors": preservation_errors, "expected": expected_layers, "actual": actual_layers},
        "mutable-layer-loss",
    )
    pending = [item["id"] for item in build_state.get("review_packs", []) if item.get("status") != "passed"]
    check("delta-reviews-complete", not pending, pending, "review-pending")
    final_result: dict[str, Any] | None = None
    if not pending and all(item["passed"] for item in checks):
        try:
            final_result = finalize(staging)
        except CkbError as exc:
            check("global-finalize", False, str(exc), "global-audit")
        else:
            check("global-finalize", final_result.get("status") == "complete", final_result.get("global_audit"), "global-audit")
    else:
        check("global-finalize", False, "blocked by earlier extension checks", "blocked")
    global_audit = json_load(staging / "audit/global.json") if (staging / "audit/global.json").is_file() else {}
    check("global-audit-passed", global_audit.get("status") == "passed", global_audit.get("status"), "global-audit")
    sqlite_checks = _sqlite_checks(staging)
    check("sqlite-integrity-and-foreign-keys", bool(sqlite_checks) and all(item["passed"] for item in sqlite_checks), sqlite_checks, "sqlite-integrity")
    from .llm_wiki_capabilities import maintenance_check

    maintenance = maintenance_check(staging) if global_audit.get("status") == "passed" else {"status": "blocked"}
    _release_audit_handles()
    check("maintain", maintenance.get("status") == "passed", maintenance, "maintain")
    passed = all(item["passed"] for item in checks)
    result = {
        "schema_version": SCOPE_EXTENSION_SCHEMA_VERSION,
        "operation_id": state["operation_id"],
        "status": "ready" if passed else "failed",
        "checks": checks,
        "counts": {"passed": sum(item["passed"] for item in checks), "total": len(checks)},
        "sqlite": sqlite_checks,
        "maintenance_status": maintenance.get("status"),
    }
    json_write(staging / AUDIT_RELATIVE, result)
    if passed:
        state["status"] = "ready"
        plan["status"] = "ready"
        json_write(staging / STATE_RELATIVE, state)
        json_write(staging / PLAN_RELATIVE, plan)
        build_state = json_load(staging / "state.json")
        build_state["scope_extension"] = {**build_state.get("scope_extension", {}), "status": "ready"}
        json_write(staging / "state.json", build_state)
    return result


def _control_path(output: Path, operation_id: str) -> Path:
    return output.parent / f".{output.name}.scope-extension-{operation_id}.json"


def cutover_scope_extension(staging: Path, *, fault: str | None = None) -> dict[str, Any]:
    staging = staging.resolve()
    state = _load_extension_state(staging)
    audit = json_load(staging / AUDIT_RELATIVE) if (staging / AUDIT_RELATIVE).is_file() else {}
    if state.get("status") != "ready" or audit.get("status") != "ready":
        raise _error("not-ready", "scope extension audit has not marked staging ready")
    output = Path(state["previous_output"]).resolve()
    if path_inside(staging, output) or path_inside(output, staging):
        raise _error("overlapping-output", "staging and production OUTPUT overlap")
    plan = json_load(staging / PLAN_RELATIVE)
    expected_origin = plan["preservation"]["origin_manifest"]
    actual_origin = _tree_manifest(output)
    if not _same_manifest(expected_origin, actual_origin):
        raise _error("origin-drift", "production OUTPUT changed after scope extension start")
    repository_state = preflight(Path(state["repository"]))
    if repository_state["commit"] != state["repository_commit"]:
        raise _error("target-drift", "target repository commit changed before cutover")
    operation_id = state["operation_id"]
    backup = output.parent / f".{output.name}.scope-extension-backup-{operation_id}"
    control_path = _control_path(output, operation_id)
    selection = _control_selection(output, actual_origin) if list(output.parent.glob(f".{output.name}.scope-extension-*.json")) else {"active": None}
    parent = selection.get("active")
    parent_record = parent[1] if parent else None
    previous_attempts: list[dict[str, Any]] = []
    if control_path.is_file() and not backup.exists():
        existing = json_load(control_path)
        if existing.get("status") == "cutover-failed-restored":
            previous_attempts = list(existing.get("attempts") or [])
            previous_attempts.append(
                {
                    "status": existing["status"],
                    "failure": existing.get("failure"),
                    "origin_restored": existing.get("origin_restored"),
                }
            )
        else:
            raise _error("cutover-conflict", "cutover control record already exists in a non-retryable state")
    if backup.exists():
        raise _error("cutover-conflict", "cutover backup or control record already exists")
    record = {
        "schema_version": SCOPE_EXTENSION_SCHEMA_VERSION,
        "operation_id": operation_id,
        "status": "cutover-started",
        "parent_operation_id": parent_record.get("operation_id") if parent_record else None,
        "chain_depth": int(parent_record.get("chain_depth", 0)) + 1 if parent_record else 1,
        "output": str(output),
        "staging_output": str(staging),
        "backup_output": str(backup),
        "repository": state["repository"],
        "repository_commit": state["repository_commit"],
        "origin_manifest": expected_origin,
        "attempts": previous_attempts,
    }
    json_write(control_path, record)
    moved_staging = False
    try:
        # Some audit helpers use sqlite3 connection context managers whose
        # objects close only when released.  Collect before Windows directory
        # renames so verified databases do not retain transient file handles.
        _release_audit_handles()
        output.rename(backup)
        if fault == "after-backup-rename":
            raise OSError("injected failure after backup rename")
        backup_manifest = _tree_manifest(backup)
        if not _same_manifest(expected_origin, backup_manifest):
            raise _error("backup-verification", "renamed backup does not match the verified origin manifest")
        staging.rename(output)
        moved_staging = True
        if fault == "after-staging-rename":
            raise OSError("injected failure after staging rename")
        pipeline_status(output)
        sqlite_checks = _sqlite_checks(output)
        if not sqlite_checks or not all(item["passed"] for item in sqlite_checks):
            raise _error("cutover-verification", f"promoted SQLite verification failed: {sqlite_checks}")
        modified_manifest = _tree_manifest(output)
        record.update({
            "status": "cutover-complete",
            "backup_manifest": backup_manifest,
            "modified_manifest": modified_manifest,
            "sqlite": sqlite_checks,
        })
        json_write(control_path, record)
        return {
            "schema_version": SCOPE_EXTENSION_SCHEMA_VERSION,
            "status": "cutover-complete",
            "operation_id": operation_id,
            "parent_operation_id": record["parent_operation_id"],
            "chain_depth": record["chain_depth"],
            "output": str(output),
            "backup_output": str(backup),
            "control": str(control_path),
            "sqlite": sqlite_checks,
        }
    except Exception as exc:
        try:
            if moved_staging and output.exists():
                output.rename(staging)
            if backup.exists() and not output.exists():
                backup.rename(output)
        finally:
            restored = output.is_dir() and _same_manifest(expected_origin, _tree_manifest(output))
            record.update({"status": "cutover-failed-restored" if restored else "cutover-failed", "failure": str(exc), "origin_restored": restored})
            json_write(control_path, record)
        if isinstance(exc, CkbError):
            raise
        raise _error("cutover-failed", str(exc)) from exc


def _active_control(output: Path) -> tuple[Path, dict[str, Any]]:
    selection = _control_selection(output)
    if selection["active"]:
        return selection["active"]
    rolled_back = selection["rolled_back_matches"]
    if len(rolled_back) == 1:
        value = rolled_back[0][1]
        value["idempotent_selection"] = True
        return rolled_back[0][0], value
    if len(rolled_back) > 1:
        raise _error("control-record", f"no active cutover; multiple rolled-back operations match current OUTPUT: {[item[1]['operation_id'] for item in rolled_back]}")
    raise _error("control-record", "no active cutover matches current OUTPUT")


def rollback_scope_extension(output: Path, *, fault: str | None = None) -> dict[str, Any]:
    output = output.resolve()
    control_path, record = _active_control(output)
    if record.get("status") == "rolled-back":
        actual = _tree_manifest(output)
        if not _same_manifest(record["origin_manifest"], actual):
            raise _error("rollback-drift", "rolled-back OUTPUT no longer matches its origin manifest")
        return {
            "schema_version": SCOPE_EXTENSION_SCHEMA_VERSION,
            "status": "rolled-back",
            "operation_id": record["operation_id"],
            "reactivated_operation_id": None,
            "output": str(output),
            "idempotent": True,
        }
    actual_modified = _tree_manifest(output)
    if not _same_manifest(record["modified_manifest"], actual_modified):
        raise _error("modified-drift", "promoted OUTPUT changed after cutover; rollback guard stopped replacement")
    backup = Path(record["backup_output"])
    if not backup.is_dir() or not _same_manifest(record["origin_manifest"], _tree_manifest(backup)):
        raise _error("backup-verification", "cutover backup is missing or changed")
    rolled_forward = output.parent / f".{output.name}.scope-extension-modified-{record['operation_id']}"
    if rolled_forward.exists():
        raise _error("rollback-conflict", f"rollback quarantine already exists: {rolled_forward}")
    restored_origin = False
    try:
        _release_audit_handles()
        output.rename(rolled_forward)
        if fault == "after-modified-rename":
            raise OSError("injected failure after modified rename")
        backup.rename(output)
        restored_origin = True
        if fault == "after-backup-restore":
            raise OSError("injected failure after backup restore")
        restored = _tree_manifest(output)
        if not _same_manifest(record["origin_manifest"], restored):
            raise _error("rollback-verification", "restored OUTPUT differs from the pre-cutover byte manifest")
        sqlite_checks = _sqlite_checks(output)
        if not sqlite_checks or not all(item["passed"] for item in sqlite_checks):
            raise _error("rollback-sqlite", f"restored SQLite verification failed: {sqlite_checks}")
        parent_operation_id = record.get("parent_operation_id")
        if parent_operation_id:
            parent_matches = [
                value
                for _path, value in _control_records(output)
                if value.get("operation_id") == parent_operation_id
            ]
            if len(parent_matches) != 1 or parent_matches[0].get("status") != "cutover-complete" or not _same_manifest(parent_matches[0].get("modified_manifest", {}), restored):
                raise _error("rollback-parent", "restored OUTPUT does not match the recorded parent cutover")
        record.update({
            "status": "rolled-back",
            "rolled_forward_output": str(rolled_forward),
            "restored_manifest": restored,
            "rollback_sqlite": sqlite_checks,
            "reactivated_operation_id": parent_operation_id,
        })
        json_write(control_path, record)
        selected_after = _control_selection(output, restored)["active"]
        actual_reactivated = selected_after[1]["operation_id"] if selected_after else None
        if actual_reactivated != parent_operation_id:
            raise _error("rollback-parent", f"active parent mismatch after rollback: expected {parent_operation_id}, got {actual_reactivated}")
        return {
            "schema_version": SCOPE_EXTENSION_SCHEMA_VERSION,
            "status": "rolled-back",
            "operation_id": record["operation_id"],
            "reactivated_operation_id": parent_operation_id,
            "output": str(output),
            "modified_output": str(rolled_forward),
            "control": str(control_path),
            "sqlite": sqlite_checks,
        }
    except Exception as exc:
        try:
            if restored_origin and output.exists():
                output.rename(backup)
            if rolled_forward.exists() and not output.exists():
                rolled_forward.rename(output)
        finally:
            restored_modified = output.is_dir() and _same_manifest(record["modified_manifest"], _tree_manifest(output))
            record.update({
                "status": "cutover-complete" if restored_modified else "rollback-failed",
                "last_rollback_failure": str(exc),
                "modified_restored": restored_modified,
            })
            json_write(control_path, record)
        if isinstance(exc, CkbError):
            raise
        raise _error("rollback-failed", str(exc)) from exc
