"""Batch migration of complete, versioned CKB knowledge outputs.

The public workflow is manifest driven.  Planning is read-only; later stages
reuse the incremental migration, Agent Protocol batch-lock, and atomic scope
cutover contracts instead of introducing an unrelated transaction model.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePath
import re
import sqlite3
from typing import Any

from . import SCHEMA_VERSION, VERSION
from .agent_protocol import AGENT_PROTOCOL_VERSION
from .agent_protocol_batch import BatchProjectError, SUPPORTED_HARNESSES, supported_upgrade_path
from .common import CkbError, json_load, json_write, path_inside, sha256_file, stable_id
from .gitrepo import preflight
from .scope_extension import _layer_inventory, _sqlite_checks, _tree_manifest


KNOWLEDGE_BATCH_MANIFEST_SCHEMA_VERSION = 1
KNOWLEDGE_BATCH_PLAN_SCHEMA_VERSION = 1
KNOWLEDGE_BATCH_STATE_SCHEMA_VERSION = 1
KNOWLEDGE_BATCH_PROJECT_SCHEMA_VERSION = 1
MAX_BATCH_PROJECTS = 128
MAX_PATH_LIMIT = 32760
DEFAULT_PATH_LIMIT = 240
HEX_SHA1 = re.compile(r"^[0-9a-f]{40}$")
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
PROJECT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

MANIFEST_KEYS = frozenset({"schema_version", "batch_id", "allowed_roots", "projects"})
PROJECT_KEYS = frozenset(
    {
        "project_id",
        "output",
        "repository",
        "staging",
        "source",
        "target",
        "origin_snapshot",
        "target_snapshot",
        "format",
        "scope_selectors",
        "runtime",
        "workspace_roots",
        "harnesses",
        "origin",
        "strategies",
        "cutover",
        "rollback",
        "max_path",
    }
)
VERSION_KEYS = frozenset({"ckb_version", "schema_version", "protocol_version", "release_commit"})
SNAPSHOT_KEYS = frozenset({"commit", "tree"})
RUNTIME_KEYS = frozenset({"python", "ckb"})
ORIGIN_KEYS = frozenset({"tree", "records"})
TREE_KEYS = frozenset({"algorithm", "file_count", "byte_count", "sha256"})
CUTOVER_KEYS = frozenset({"output", "backup_root"})
ROLLBACK_KEYS = frozenset({"quarantine_root"})
SCOPE_KEYS = frozenset(
    {
        "scope_paths",
        "entries",
        "expand_depth",
        "expand_direction",
        "include",
        "csharp_solution",
        "csharp_project",
        "allow_dotnet_restore",
    }
)
STRATEGIES = frozenset({"compatible-migration", "delta-review", "cold-build"})
REQUIRED_RECORDS = (
    "state.json",
    "scope.json",
    "catalog.json",
    "graph.json",
    "audit/global.json",
    ".complete",
    ".machine.complete",
    ".human.complete",
)


@dataclass(frozen=True)
class KnowledgeRelease:
    release_id: str
    ckb_version: str
    schema_version: int
    protocol_version: str | None
    source_commit: str
    next_release_id: str | None
    compatible: bool


# Every source commit below exists in repository history.  The two 5.3.0 rows
# deliberately distinguish the reference-only and protocol-aware checkpoints;
# a version label alone is not accepted as provenance.
KNOWLEDGE_RELEASES: dict[str, KnowledgeRelease] = {
    "5.1.1-s4-none": KnowledgeRelease(
        "5.1.1-s4-none",
        "5.1.1",
        4,
        None,
        "5034de2cc81e36385cbbe794d8105d2de687c725",
        "5.1.4-s4-p1.0.0",
        False,
    ),
    "5.1.4-s4-p1.0.0": KnowledgeRelease(
        "5.1.4-s4-p1.0.0",
        "5.1.4",
        4,
        "1.0.0",
        "c0e6cb650d707512d0edbcc481db373359a8f46f",
        "5.2.9-s4-p1.3.0",
        True,
    ),
    "5.2.9-s4-p1.3.0": KnowledgeRelease(
        "5.2.9-s4-p1.3.0",
        "5.2.9",
        4,
        "1.3.0",
        "3f117b8a3565b24633b88799a3ee180d6b3451ab",
        "5.3.0-s4-p1.3.0",
        True,
    ),
    "5.3.0-s4-p1.3.0": KnowledgeRelease(
        "5.3.0-s4-p1.3.0",
        "5.3.0",
        4,
        "1.3.0",
        "b666233cd4ec2cd1aecb3e6a7b194f61613be662",
        "5.3.0-s4-p1.4.0",
        True,
    ),
    "5.3.0-s4-p1.4.0": KnowledgeRelease(
        "5.3.0-s4-p1.4.0",
        "5.3.0",
        4,
        "1.4.0",
        "02b3f9bae10663f8d8d41626bb52454a226d4228",
        "5.4.0-s4-p1.5.0",
        True,
    ),
    "5.4.0-s4-p1.5.0": KnowledgeRelease(
        "5.4.0-s4-p1.5.0",
        "5.4.0",
        4,
        "1.5.0",
        "2d1ddc4de65c36c2ebe244e3d0556d4b613b2d3d",
        None,
        True,
    ),
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest_value(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _reject_unknown(value: dict[str, Any], allowed: frozenset[str], location: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise CkbError(f"unknown knowledge batch manifest field at {location}: {', '.join(unknown)}")


def _object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CkbError(f"knowledge batch manifest {location} must be an object")
    return value


def _absolute(value: Any, location: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CkbError(f"knowledge batch manifest {location} must be a non-empty absolute path")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise CkbError(f"knowledge batch manifest {location} must be absolute: {value}")
    return path.resolve()


def _within_any(path: Path, roots: list[Path]) -> bool:
    return any(path_inside(path, root) for root in roots)


def _normalized_protocol(value: Any) -> str | None:
    if value in {None, "", "none", "absent"}:
        return None
    return str(value)


def _release_for(value: dict[str, Any]) -> KnowledgeRelease | None:
    protocol = _normalized_protocol(value.get("protocol_version"))
    matches = [
        release
        for release in KNOWLEDGE_RELEASES.values()
        if release.ckb_version == value.get("ckb_version")
        and release.schema_version == value.get("schema_version")
        and release.protocol_version == protocol
        and release.source_commit == value.get("release_commit")
    ]
    return matches[0] if len(matches) == 1 else None


def _release_chain(source: KnowledgeRelease, target: KnowledgeRelease) -> list[KnowledgeRelease]:
    chain = [source]
    seen = {source.release_id}
    while chain[-1].release_id != target.release_id:
        next_id = chain[-1].next_release_id
        if not next_id or next_id in seen or next_id not in KNOWLEDGE_RELEASES:
            raise CkbError(f"knowledge release path is incomplete: {source.release_id} -> {target.release_id}")
        seen.add(next_id)
        chain.append(KNOWLEDGE_RELEASES[next_id])
    return chain


def knowledge_version_matrix() -> dict[str, Any]:
    current = _release_for(
        {
            "ckb_version": VERSION,
            "schema_version": SCHEMA_VERSION,
            "protocol_version": AGENT_PROTOCOL_VERSION,
            "release_commit": "2d1ddc4de65c36c2ebe244e3d0556d4b613b2d3d",
        }
    )
    if current is None:
        raise RuntimeError("current CKB release is absent from the knowledge migration matrix")
    return {
        "schema_version": 1,
        "current_release_id": current.release_id,
        "current": {
            "ckb_version": VERSION,
            "schema_version": SCHEMA_VERSION,
            "protocol_version": AGENT_PROTOCOL_VERSION,
        },
        "releases": [
            {
                "release_id": item.release_id,
                "ckb_version": item.ckb_version,
                "schema_version": item.schema_version,
                "protocol_version": item.protocol_version,
                "source_commit": item.source_commit,
                "next_release_id": item.next_release_id,
                "compatible": item.compatible,
            }
            for item in KNOWLEDGE_RELEASES.values()
        ],
    }


def _validate_version(value: Any, location: str) -> dict[str, Any]:
    result = _object(value, location)
    _reject_unknown(result, VERSION_KEYS, location)
    if not isinstance(result.get("ckb_version"), str) or not result["ckb_version"]:
        raise CkbError(f"knowledge batch manifest {location}.ckb_version is invalid")
    if not isinstance(result.get("schema_version"), int) or result["schema_version"] < 1:
        raise CkbError(f"knowledge batch manifest {location}.schema_version is invalid")
    protocol = result.get("protocol_version")
    if protocol is not None and (not isinstance(protocol, str) or not protocol):
        raise CkbError(f"knowledge batch manifest {location}.protocol_version is invalid")
    if not isinstance(result.get("release_commit"), str) or not HEX_SHA1.fullmatch(result["release_commit"]):
        raise CkbError(f"knowledge batch manifest {location}.release_commit must be a full commit SHA-1")
    return result


def _validate_snapshot(value: Any, location: str) -> dict[str, str]:
    result = _object(value, location)
    _reject_unknown(result, SNAPSHOT_KEYS, location)
    for field in SNAPSHOT_KEYS:
        if not isinstance(result.get(field), str) or not HEX_SHA1.fullmatch(result[field]):
            raise CkbError(f"knowledge batch manifest {location}.{field} must be a full Git SHA-1")
    return {"commit": result["commit"], "tree": result["tree"]}


def _validate_tree_summary(value: Any, location: str) -> dict[str, Any]:
    result = _object(value, location)
    _reject_unknown(result, TREE_KEYS, location)
    if result.get("algorithm") != "sha256-tree-v1":
        raise CkbError(f"knowledge batch manifest {location}.algorithm must be sha256-tree-v1")
    for field in ("file_count", "byte_count"):
        if not isinstance(result.get(field), int) or result[field] < 0:
            raise CkbError(f"knowledge batch manifest {location}.{field} is invalid")
    if not isinstance(result.get("sha256"), str) or not HEX_SHA256.fullmatch(result["sha256"]):
        raise CkbError(f"knowledge batch manifest {location}.sha256 must be a lowercase SHA-256")
    return dict(result)


def _validate_structural_manifest(manifest: dict[str, Any]) -> tuple[list[Path], list[dict[str, Any]]]:
    _reject_unknown(manifest, MANIFEST_KEYS, "manifest")
    if manifest.get("schema_version") != KNOWLEDGE_BATCH_MANIFEST_SCHEMA_VERSION:
        raise CkbError(f"unsupported knowledge batch manifest schema_version: {manifest.get('schema_version')}")
    batch_id = manifest.get("batch_id")
    if not isinstance(batch_id, str) or not PROJECT_ID.fullmatch(batch_id):
        raise CkbError("knowledge batch manifest batch_id is invalid")
    allowed = manifest.get("allowed_roots")
    if not isinstance(allowed, list) or not allowed:
        raise CkbError("knowledge batch manifest allowed_roots must be a non-empty list")
    roots = [_absolute(value, f"allowed_roots[{index}]") for index, value in enumerate(allowed)]
    if len({str(path) for path in roots}) != len(roots):
        raise CkbError("knowledge batch manifest allowed_roots contains duplicates")
    if any(not root.is_dir() for root in roots):
        raise CkbError("knowledge batch manifest allowed_roots must already exist")
    projects = manifest.get("projects")
    if not isinstance(projects, list) or not (1 <= len(projects) <= MAX_BATCH_PROJECTS):
        raise CkbError(f"knowledge batch manifest projects must contain 1..{MAX_BATCH_PROJECTS} entries")
    ids: set[str] = set()
    outputs: list[Path] = []
    stagings: list[Path] = []
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(projects):
        project = _object(raw, f"projects[{index}]")
        _reject_unknown(project, PROJECT_KEYS, f"projects[{index}]")
        project_id = project.get("project_id")
        if not isinstance(project_id, str) or not PROJECT_ID.fullmatch(project_id):
            raise CkbError(f"knowledge batch manifest projects[{index}].project_id is invalid")
        if project_id in ids:
            raise CkbError(f"knowledge batch manifest project_id is duplicated: {project_id}")
        ids.add(project_id)
        output = _absolute(project.get("output"), f"{project_id}.output")
        repository = _absolute(project.get("repository"), f"{project_id}.repository")
        staging = _absolute(project.get("staging"), f"{project_id}.staging")
        if not all(_within_any(path, roots) for path in (output, repository, staging)):
            raise CkbError(f"knowledge batch project path escapes allowed_roots: {project_id}")
        if output == staging or path_inside(output, staging) or path_inside(staging, output):
            raise CkbError(f"knowledge batch OUTPUT and staging overlap: {project_id}")
        outputs.append(output)
        stagings.append(staging)
        normalized.append(project)
    owned = [("output", path) for path in outputs] + [("staging", path) for path in stagings]
    for position, (role, path) in enumerate(owned):
        for other_role, other in owned[position + 1 :]:
            if path == other or path_inside(path, other) or path_inside(other, path):
                raise CkbError(f"knowledge batch {role}/{other_role} paths are duplicate or nested: {path} ; {other}")
    return roots, normalized


def load_knowledge_batch_manifest(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise CkbError(f"knowledge batch manifest is missing: {path}")
    value = json_load(path)
    if not isinstance(value, dict):
        raise CkbError("knowledge batch manifest root must be an object")
    _validate_structural_manifest(value)
    return value


def _file_record(output: Path, relative: str) -> dict[str, Any]:
    path = output / relative
    return {
        "path": relative,
        "exists": path.is_file(),
        "size": path.stat().st_size if path.is_file() else None,
        "sha256": sha256_file(path) if path.is_file() else None,
    }


def _origin_health(output: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any, category: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "category": category, "detail": detail})

    required = {relative: _file_record(output, relative) for relative in REQUIRED_RECORDS}
    check("required-records", all(item["exists"] for item in required.values()), required, "origin-record-missing")
    state = json_load(output / "state.json") if required["state.json"]["exists"] else {}
    scope = json_load(output / "scope.json") if required["scope.json"]["exists"] else {}
    graph = json_load(output / "graph.json") if required["graph.json"]["exists"] else {}
    audit = json_load(output / "audit/global.json") if required["audit/global.json"]["exists"] else {}
    markers = {
        name: json_load(output / name) if required[name]["exists"] else {}
        for name in (".complete", ".machine.complete", ".human.complete")
    }
    check("state-complete", state.get("status") == "complete", state.get("status"), "origin-state-incomplete")
    check("completion-markers", all(value.get("status") == "complete" for value in markers.values()), markers, "origin-marker-incomplete")
    check("global-audit", audit.get("status") == "passed", audit.get("status"), "origin-global-audit")
    facts = output / "facts"
    check("facts-layer", facts.is_dir() and any(facts.iterdir()), str(facts), "origin-facts-missing")
    reviews = {item.get("id"): item.get("status") for item in state.get("review_packs", [])}
    check("review-packs", bool(reviews) and all(value == "passed" for value in reviews.values()), reviews, "origin-review-incomplete")
    entity_review_errors = [
        item.get("id")
        for item in graph.get("entities", [])
        if item.get("classification") in {"page", "boundary", "appendix"} and item.get("review_status") != "agent-reviewed"
    ]
    check("entity-reviews", not entity_review_errors, entity_review_errors[:40], "origin-review-binding")
    sqlite_checks = _sqlite_checks(output)
    required_sqlite = {item["path"]: item for item in sqlite_checks}
    check(
        "double-sqlite",
        all(required_sqlite.get(name, {}).get("passed") for name in ("machine/knowledge.sqlite", "agent-index.sqlite")),
        sqlite_checks,
        "origin-sqlite",
    )
    human = output / "human"
    markdown = output / "markdown"
    check("human-markdown", human.is_dir() and markdown.is_dir(), {"human": human.is_dir(), "markdown": markdown.is_dir()}, "origin-projection-missing")
    return {
        "status": "passed" if all(item["passed"] for item in checks) else "failed",
        "checks": checks,
        "state": state,
        "scope": scope,
        "graph": graph,
        "audit": audit,
        "markers": markers,
        "sqlite": sqlite_checks,
    }


def _normalized_scope(value: Any, location: str) -> dict[str, Any]:
    scope = _object(value, location)
    _reject_unknown(scope, SCOPE_KEYS, location)
    result = {
        "scope_paths": list(scope.get("scope_paths") or []),
        "entries": list(scope.get("entries") or []),
        "expand_depth": int(scope.get("expand_depth", 1)),
        "expand_direction": str(scope.get("expand_direction", "both")),
        "include": list(scope.get("include") or []),
        "csharp_solution": scope.get("csharp_solution"),
        "csharp_project": scope.get("csharp_project"),
        "allow_dotnet_restore": bool(scope.get("allow_dotnet_restore", False)),
    }
    if result["expand_depth"] < 0 or result["expand_direction"] not in {"both", "callers", "callees"}:
        raise CkbError(f"knowledge batch manifest {location} expansion is invalid")
    return result


def _path_risks(paths: list[Path], maximum: int) -> list[dict[str, Any]]:
    return [
        {"path": str(path), "length": len(str(path)), "limit": maximum}
        for path in paths
        if len(str(path)) > maximum
    ]


def _inspect_knowledge_project(project: dict[str, Any], roots: list[Path]) -> dict[str, Any]:
    project_id = str(project["project_id"])
    output = _absolute(project["output"], f"{project_id}.output")
    repository = _absolute(project["repository"], f"{project_id}.repository")
    staging = _absolute(project["staging"], f"{project_id}.staging")
    source = _validate_version(project.get("source"), f"{project_id}.source")
    target = _validate_version(project.get("target"), f"{project_id}.target")
    origin_snapshot = _validate_snapshot(project.get("origin_snapshot"), f"{project_id}.origin_snapshot")
    target_snapshot = _validate_snapshot(project.get("target_snapshot"), f"{project_id}.target_snapshot")
    format_name = project.get("format")
    if format_name not in {"markdown", "logseq-db", "both"}:
        raise BatchProjectError("format-invalid", f"knowledge output format is invalid for {project_id}")
    scope_selectors = _normalized_scope(project.get("scope_selectors"), f"{project_id}.scope_selectors")
    runtime = _object(project.get("runtime"), f"{project_id}.runtime")
    _reject_unknown(runtime, RUNTIME_KEYS, f"{project_id}.runtime")
    python = _absolute(runtime.get("python"), f"{project_id}.runtime.python")
    ckb = _absolute(runtime.get("ckb"), f"{project_id}.runtime.ckb")
    if not python.is_file() or not ckb.is_file():
        raise BatchProjectError("runtime-missing", f"locked Python or CKB entrypoint is missing for {project_id}")
    workspace_values = project.get("workspace_roots")
    if not isinstance(workspace_values, list):
        raise BatchProjectError("workspace-roots-invalid", f"workspace_roots must be a list for {project_id}")
    workspace_roots = [_absolute(value, f"{project_id}.workspace_roots[{index}]") for index, value in enumerate(workspace_values)]
    if len({str(value) for value in workspace_roots}) != len(workspace_roots):
        raise BatchProjectError("workspace-root-duplicate", f"workspace_roots contains duplicates for {project_id}")
    if any(not value.is_dir() or not _within_any(value, roots) for value in workspace_roots):
        raise BatchProjectError("workspace-root-invalid", f"workspace root is missing or out of bounds for {project_id}")
    harnesses = project.get("harnesses")
    if not isinstance(harnesses, list) or not harnesses or len(set(harnesses)) != len(harnesses):
        raise BatchProjectError("harnesses-invalid", f"harnesses must be a unique non-empty list for {project_id}")
    unsupported = sorted(set(harnesses) - SUPPORTED_HARNESSES)
    if unsupported:
        raise BatchProjectError("harness-unsupported", f"unsupported Harness values for {project_id}: {unsupported}")
    strategies = project.get("strategies")
    if not isinstance(strategies, list) or not strategies or len(set(strategies)) != len(strategies):
        raise BatchProjectError("strategies-invalid", f"strategies must be a unique non-empty list for {project_id}")
    unknown_strategies = sorted(set(strategies) - STRATEGIES)
    if unknown_strategies:
        raise BatchProjectError("strategy-unsupported", f"unsupported migration strategies for {project_id}: {unknown_strategies}")
    cutover = _object(project.get("cutover"), f"{project_id}.cutover")
    _reject_unknown(cutover, CUTOVER_KEYS, f"{project_id}.cutover")
    cutover_output = _absolute(cutover.get("output"), f"{project_id}.cutover.output")
    backup_root = _absolute(cutover.get("backup_root"), f"{project_id}.cutover.backup_root")
    rollback = _object(project.get("rollback"), f"{project_id}.rollback")
    _reject_unknown(rollback, ROLLBACK_KEYS, f"{project_id}.rollback")
    quarantine_root = _absolute(rollback.get("quarantine_root"), f"{project_id}.rollback.quarantine_root")
    if cutover_output != output:
        raise BatchProjectError("cutover-output-mismatch", f"cutover.output must equal output for {project_id}")
    if not all(_within_any(value, roots) for value in (backup_root, quarantine_root)):
        raise BatchProjectError("recovery-path-out-of-bounds", f"backup or quarantine root escapes allowed_roots for {project_id}")
    maximum = project.get("max_path", DEFAULT_PATH_LIMIT)
    if not isinstance(maximum, int) or not (80 <= maximum <= MAX_PATH_LIMIT):
        raise BatchProjectError("path-limit-invalid", f"max_path must be 80..{MAX_PATH_LIMIT} for {project_id}")
    risks = _path_risks([output, repository, staging, backup_root, quarantine_root, *workspace_roots], maximum)
    if risks:
        raise BatchProjectError("path-too-long", f"knowledge batch path preflight failed for {project_id}: {risks}")
    if not output.is_dir():
        raise BatchProjectError("output-missing", f"origin knowledge OUTPUT is missing for {project_id}: {output}")
    if not repository.is_dir():
        raise BatchProjectError("repository-missing", f"target repository is missing for {project_id}: {repository}")
    if staging.exists():
        raise BatchProjectError("staging-conflict", f"staging already exists during read-only plan: {staging}")
    if not backup_root.parent.is_dir() or not quarantine_root.parent.is_dir():
        raise BatchProjectError("recovery-parent-missing", f"backup/quarantine parent must exist for {project_id}")
    origin_descriptor = _object(project.get("origin"), f"{project_id}.origin")
    _reject_unknown(origin_descriptor, ORIGIN_KEYS, f"{project_id}.origin")
    expected_tree = _validate_tree_summary(origin_descriptor.get("tree"), f"{project_id}.origin.tree")
    expected_records = origin_descriptor.get("records")
    if not isinstance(expected_records, dict) or set(REQUIRED_RECORDS) - set(expected_records):
        raise BatchProjectError("origin-record-summary-incomplete", f"origin.records must include every required record for {project_id}")
    if any(not isinstance(value, str) or not HEX_SHA256.fullmatch(value) for value in expected_records.values()):
        raise BatchProjectError("origin-record-digest-invalid", f"origin.records contains an invalid SHA-256 for {project_id}")
    actual_tree = _tree_manifest(output)
    tree_fields = {key: actual_tree[key] for key in TREE_KEYS}
    if tree_fields != expected_tree:
        raise BatchProjectError("origin-tree-drift", f"origin full-tree summary differs from manifest for {project_id}")
    record_drift = {
        relative: {"expected": digest, "actual": _file_record(output, relative)["sha256"]}
        for relative, digest in expected_records.items()
        if _file_record(output, relative)["sha256"] != digest
    }
    if record_drift:
        raise BatchProjectError("origin-record-drift", f"origin key record bytes differ from manifest for {project_id}: {record_drift}")
    health = _origin_health(output)
    if health["status"] != "passed":
        failed = [item for item in health["checks"] if not item["passed"]]
        category = failed[0]["category"] if failed else "origin-invalid"
        raise BatchProjectError(category, f"origin knowledge OUTPUT failed completeness preflight for {project_id}: {failed}")
    state = health["state"]
    protocol_path = output / "workspace-meta/agent-protocol.json"
    protocol = json_load(protocol_path) if protocol_path.is_file() else {}
    actual_source = {
        "ckb_version": state.get("version"),
        "schema_version": state.get("schema_version"),
        "protocol_version": protocol.get("protocol_version"),
    }
    expected_source = {
        "ckb_version": source["ckb_version"],
        "schema_version": source["schema_version"],
        "protocol_version": _normalized_protocol(source.get("protocol_version")),
    }
    if actual_source != expected_source:
        raise BatchProjectError("source-version-mismatch", f"origin versions differ from manifest for {project_id}: {actual_source} != {expected_source}")
    state_snapshot = {
        "commit": state.get("repository", {}).get("commit"),
        "tree": state.get("repository", {}).get("tree"),
    }
    if state_snapshot != origin_snapshot:
        raise BatchProjectError("origin-repository-mismatch", f"origin OUTPUT commit/tree differs from manifest for {project_id}")
    if state.get("format") != format_name:
        raise BatchProjectError("format-mismatch", f"origin format differs from manifest for {project_id}")
    actual_scope = _normalized_scope((health["scope"].get("selectors") or {}), f"{project_id}.actual-scope")
    if actual_scope != scope_selectors:
        raise BatchProjectError("scope-selector-mismatch", f"origin scope selectors differ from manifest for {project_id}")
    repository_state = preflight(repository)
    if {"commit": repository_state["commit"], "tree": repository_state["tree"]} != target_snapshot:
        raise BatchProjectError("target-repository-drift", f"target repository commit/tree differs from manifest for {project_id}")
    if target["ckb_version"] != VERSION or target["schema_version"] != SCHEMA_VERSION or _normalized_protocol(target.get("protocol_version")) != AGENT_PROTOCOL_VERSION:
        raise BatchProjectError("target-not-current", f"target must equal current CKB/Schema/Protocol for {project_id}")
    source_release = _release_for(source)
    target_release = _release_for(target)
    if target_release is None:
        raise BatchProjectError("target-release-unknown", f"target release provenance is absent from the frozen matrix for {project_id}")
    if source_release is None:
        decision = "awaiting-review"
        chain: list[KnowledgeRelease] = []
        reason = "source-release-unknown"
    else:
        try:
            chain = _release_chain(source_release, target_release)
        except CkbError:
            decision = "awaiting-review"
            chain = []
            reason = "version-chain-missing"
        else:
            if not source_release.compatible:
                decision = "cold-build-required"
                reason = "source-release-requires-cold-build"
            elif "compatible-migration" not in strategies:
                decision = "cold-build-required" if "cold-build" in strategies else "awaiting-review"
                reason = "compatible-strategy-not-allowed"
            elif target_snapshot != origin_snapshot and "delta-review" not in strategies:
                decision = "awaiting-review"
                reason = "delta-review-strategy-not-allowed"
            else:
                decision = "ready"
                reason = "compatible-migration"
    if decision == "cold-build-required" and "cold-build" not in strategies:
        decision = "failed"
        reason = "cold-build-strategy-not-allowed"
    try:
        protocol_chain = supported_upgrade_path(str(source["protocol_version"]), AGENT_PROTOCOL_VERSION) if source_release and source_release.protocol_version else []
    except CkbError:
        protocol_chain = []
        if decision == "ready":
            decision = "awaiting-review"
            reason = "protocol-chain-missing"
    layers = _layer_inventory(output)
    return {
        "project_id": project_id,
        "status": decision,
        "reason": reason,
        "strategy": "compatible-migration" if decision == "ready" else "cold-build" if decision == "cold-build-required" else None,
        "output": str(output),
        "repository": str(repository),
        "staging": str(staging),
        "source": source,
        "target": target,
        "origin_snapshot": origin_snapshot,
        "target_snapshot": target_snapshot,
        "format": format_name,
        "scope_selectors": scope_selectors,
        "runtime": {"python": str(python), "ckb": str(ckb)},
        "workspace_roots": [str(value) for value in workspace_roots],
        "harnesses": sorted(harnesses),
        "strategies": sorted(strategies),
        "version_chain": [item.release_id for item in chain],
        "protocol_chain": protocol_chain,
        "origin_manifest": actual_tree,
        "origin_records": {relative: _file_record(output, relative) for relative in sorted(expected_records)},
        "origin_layers": layers,
        "sqlite": health["sqlite"],
        "cutover": {"output": str(cutover_output), "backup_root": str(backup_root)},
        "rollback": {"quarantine_root": str(quarantine_root)},
        "max_path": maximum,
        "risks": [
            "delta-agent-review" if target_snapshot != origin_snapshot else "same-snapshot-rekey-audit",
            "mutable-layer-preservation",
            "atomic-per-output-cutover",
        ],
    }


def create_knowledge_batch_plan(manifest_path: Path, write: Path | None = None) -> dict[str, Any]:
    manifest_path = manifest_path.expanduser().resolve()
    manifest = load_knowledge_batch_manifest(manifest_path)
    roots, projects = _validate_structural_manifest(manifest)
    normalized_manifest = {
        "schema_version": KNOWLEDGE_BATCH_MANIFEST_SCHEMA_VERSION,
        "batch_id": manifest["batch_id"],
        "allowed_roots": sorted(str(path) for path in roots),
        "projects": sorted(projects, key=lambda item: str(item["project_id"])),
    }
    manifest_digest = _digest_value(normalized_manifest)
    results: list[dict[str, Any]] = []
    for project in normalized_manifest["projects"]:
        try:
            results.append(_inspect_knowledge_project(project, roots))
        except BatchProjectError as exc:
            results.append(
                {
                    "project_id": str(project["project_id"]),
                    "status": "failed",
                    "reason": exc.category,
                    "strategy": None,
                    "output": str(project["output"]),
                    "repository": str(project["repository"]),
                    "staging": str(project["staging"]),
                    "failure": {"category": exc.category, "detail": str(exc)},
                }
            )
        except (CkbError, OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
            results.append(
                {
                    "project_id": str(project["project_id"]),
                    "status": "failed",
                    "reason": "project-validation-failed",
                    "strategy": None,
                    "output": str(project["output"]),
                    "repository": str(project["repository"]),
                    "staging": str(project["staging"]),
                    "failure": {"category": "project-validation-failed", "detail": str(exc)},
                }
            )
    counts: dict[str, int] = {}
    for item in results:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    actionable = counts.get("ready", 0) + counts.get("cold-build-required", 0)
    failed = counts.get("failed", 0)
    status = "ready" if actionable == len(results) else "failed" if actionable == 0 else "partial"
    body = {
        "schema_version": KNOWLEDGE_BATCH_PLAN_SCHEMA_VERSION,
        "batch_id": manifest["batch_id"],
        "operation_id": stable_id("knowledge-batch", manifest["batch_id"], manifest_digest),
        "status": status,
        "dry_run": True,
        "manifest": str(manifest_path),
        "manifest_digest": manifest_digest,
        "version_matrix": knowledge_version_matrix(),
        "summary": {"projects": len(results), "actionable": actionable, "failed": failed, "counts": dict(sorted(counts.items()))},
        "projects": results,
    }
    plan = {**body, "plan_digest": _digest_value(body)}
    if write is not None:
        write = write.expanduser().resolve()
        if any(path_inside(write, Path(item["output"])) or path_inside(write, Path(item["staging"])) for item in results):
            raise CkbError("knowledge batch plan must be outside every OUTPUT and staging directory")
        json_write(write, plan)
        return {**plan, "plan_path": str(write)}
    return plan

