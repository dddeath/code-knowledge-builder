"""Batch migration of complete, versioned CKB knowledge outputs.

The public workflow is manifest driven.  Planning is read-only; later stages
reuse the incremental migration, Agent Protocol batch-lock, and atomic scope
cutover contracts instead of introducing an unrelated transaction model.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
from typing import Any

from . import SCHEMA_VERSION, VERSION
from .agent_protocol import AGENT_PROTOCOL_VERSION, install_agent_protocol, project_agent_protocol
from .agent_protocol_batch import (
    BatchProjectError,
    SUPPORTED_HARNESSES,
    _create_backup as _create_protocol_backup,
    _output_lock,
    _restore_backup as _restore_protocol_backup,
    snapshot_digest as _protocol_snapshot_digest,
    snapshot_files as _protocol_snapshot_files,
    supported_upgrade_path,
)
from .common import CkbError, json_load, json_write, path_inside, sha256_file, stable_id, utc_now
from .gitrepo import preflight
from .migration import (
    _preserve_mutable_layers,
    _replace_review_packs,
    audit_migration,
    migrate_output,
)
from .pipeline import build_chunk, finalize, initialize, status as pipeline_status
from .scope_extension import _layer_inventory, _preservation_errors, _release_audit_handles, _sqlite_checks, _tree_manifest


KNOWLEDGE_BATCH_MANIFEST_SCHEMA_VERSION = 1
KNOWLEDGE_BATCH_PLAN_SCHEMA_VERSION = 1
KNOWLEDGE_BATCH_STATE_SCHEMA_VERSION = 1
KNOWLEDGE_BATCH_PROJECT_SCHEMA_VERSION = 1
MAX_BATCH_PROJECTS = 128
MAX_PATH_LIMIT = 32760
DEFAULT_PATH_LIMIT = 240
MAX_STATE_EVENTS = 512
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
        "entry_ids",
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
    try:
        sqlite_checks = _sqlite_checks(output)
    except sqlite3.Error as exc:
        sqlite_checks = [
            {
                "path": "machine/knowledge.sqlite",
                "integrity_check": "error",
                "foreign_key_errors": None,
                "passed": False,
                "detail": str(exc),
            }
        ]
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
    mirror_errors: list[dict[str, Any]] = []
    if human.is_dir() and markdown.is_dir():
        excluded = {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}
        human_files = {
            path.relative_to(human).as_posix(): path
            for path in human.rglob("*.md")
            if path.relative_to(human).as_posix() not in excluded
            and not path.relative_to(human).as_posix().startswith((".github/", ".cursor/", ".obsidian/"))
        }
        markdown_files = {
            path.relative_to(markdown).as_posix(): path
            for path in markdown.rglob("*.md")
            if path.relative_to(markdown).as_posix() not in excluded
            and not path.relative_to(markdown).as_posix().startswith((".github/", ".cursor/", ".obsidian/"))
        }
        if set(human_files) != set(markdown_files):
            mirror_errors.append(
                {
                    "reason": "mirror-file-set",
                    "human_only": sorted(set(human_files) - set(markdown_files)),
                    "markdown_only": sorted(set(markdown_files) - set(human_files)),
                }
            )
        for relative in sorted(set(human_files) & set(markdown_files)):
            if human_files[relative].read_bytes() != markdown_files[relative].read_bytes():
                mirror_errors.append({"reason": "mirror-byte-drift", "path": relative})
    check("human-markdown-parity", not mirror_errors, mirror_errors, "origin-mirror-drift")
    readability = json_load(markdown / "readability-audit.json") if (markdown / "readability-audit.json").is_file() else {}
    check(
        "readability-record",
        readability.get("status") == "passed" and not readability.get("errors"),
        readability,
        "origin-readability",
    )
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


def _complete_layer_inventory(output: Path, mutable_files: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    base = _layer_inventory(output, mutable_files)
    names: dict[str, dict[str, str]] = {}
    mirror_errors: list[dict[str, Any]] = []
    for root_name in ("human", "markdown"):
        root = output / root_name / "user"
        for path in sorted(root.glob("*.md")) if root.is_dir() else []:
            entry = names.setdefault(path.name, {})
            entry[root_name] = sha256_file(path)
    for name, hashes in sorted(names.items()):
        if set(hashes) != {"human", "markdown"} or hashes.get("human") != hashes.get("markdown"):
            mirror_errors.append({"name": name, "hashes": hashes})
    reference_files = sorted(path.relative_to(output).as_posix() for path in (output / "references").rglob("*") if path.is_file()) if (output / "references").is_dir() else []
    feedback_files = sorted(path.relative_to(output).as_posix() for path in (output / "workspace-meta/feedback").rglob("*.json")) if (output / "workspace-meta/feedback").is_dir() else []
    operation_files = sorted(path.relative_to(output).as_posix() for path in (output / "workspace-meta/operations").glob("*.jsonl")) if (output / "workspace-meta/operations").is_dir() else []
    automation = output / "machine/automation.sqlite"
    protocol = output / "workspace-meta/agent-protocol.json"
    return {
        **base,
        "learning_note_count": len(names),
        "learning_notes": [{"name": name, "sha256": hashes.get("human"), "mirrors": hashes} for name, hashes in sorted(names.items())],
        "learning_note_mirror_errors": mirror_errors,
        "reference_source_file_count": len(reference_files),
        "reference_source_files": reference_files,
        "feedback_record_count": len(feedback_files),
        "operation_file_count": len(operation_files),
        "automation_database_present": automation.is_file(),
        "agent_protocol_record_present": protocol.is_file(),
        "agent_protocol_record_sha256": sha256_file(protocol) if protocol.is_file() else None,
    }


def _normalized_scope(value: Any, location: str) -> dict[str, Any]:
    scope = _object(value, location)
    _reject_unknown(scope, SCOPE_KEYS, location)
    result = {
        "scope_paths": list(scope.get("scope_paths") or []),
        "entries": list(scope.get("entries") or []),
        "entry_ids": list(scope.get("entry_ids") or []),
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
    missing_records = [relative for relative in expected_records if not (output / relative).is_file()]
    if missing_records:
        raise BatchProjectError("origin-record-missing", f"origin key records are missing for {project_id}: {missing_records}")
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
    layers = _complete_layer_inventory(output)
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


def _load_knowledge_batch_plan(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise CkbError(f"knowledge batch plan is missing: {path}")
    plan = json_load(path)
    if not isinstance(plan, dict) or plan.get("schema_version") != KNOWLEDGE_BATCH_PLAN_SCHEMA_VERSION:
        raise CkbError(f"unsupported knowledge batch plan schema: {path}")
    digest = plan.get("plan_digest")
    if not isinstance(digest, str) or not HEX_SHA256.fullmatch(digest):
        raise CkbError(f"knowledge batch plan digest is invalid: {path}")
    body = {key: value for key, value in plan.items() if key not in {"plan_digest", "plan_path"}}
    if _digest_value(body) != digest:
        raise CkbError(f"knowledge batch plan digest mismatch: {path}")
    return plan


def _save_knowledge_state(path: Path, state: dict[str, Any]) -> None:
    state["updated_at_utc"] = utc_now()
    json_write(path, state)


def _load_knowledge_state(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise CkbError(f"knowledge batch state is missing: {path}")
    state = json_load(path)
    if not isinstance(state, dict) or state.get("schema_version") != KNOWLEDGE_BATCH_STATE_SCHEMA_VERSION:
        raise CkbError(f"unsupported knowledge batch state schema: {path}")
    if Path(str(state.get("state"))).resolve() != path:
        raise CkbError("knowledge batch state absolute binding is invalid")
    return state


def _state_event(
    state: dict[str, Any],
    project_id: str,
    action: str,
    status: str,
    category: str | None = None,
) -> None:
    events = state.setdefault("events", [])
    events.append(
        {
            "event_id": stable_id("knowledge-batch-event", state["batch_id"], len(events), project_id, action, status),
            "project_id": project_id,
            "action": action,
            "status": status,
            "category": category,
            "recorded_at_utc": utc_now(),
        }
    )
    if len(events) > MAX_STATE_EVENTS:
        del events[: len(events) - MAX_STATE_EVENTS]


def _new_knowledge_state(plan: dict[str, Any], plan_path: Path, state_path: Path) -> dict[str, Any]:
    projects: dict[str, dict[str, Any]] = {}
    for project in plan["projects"]:
        plan_status = project["status"]
        actionable = plan_status in {"ready", "cold-build-required"}
        projects[project["project_id"]] = {
            "project_id": project["project_id"],
            "status": "pending" if actionable else plan_status,
            "plan_status": plan_status,
            "strategy": project.get("strategy"),
            "operation_id": stable_id(
                "knowledge-migration",
                plan["operation_id"],
                project["project_id"],
                (project.get("origin_manifest") or {}).get("sha256"),
                (project.get("target_snapshot") or {}).get("commit"),
            ) if actionable else None,
            "output": project["output"],
            "staging": project["staging"],
            "origin_digest": (project.get("origin_manifest") or {}).get("sha256"),
            "staging_digest": None,
            "modified_digest": None,
            "audit": None,
            "pending_review_packs": [],
            "backup_output": None,
            "control": None,
            "protocol_backup": None,
            "failure": project.get("failure"),
        }
    stamp = utc_now()
    return {
        "schema_version": KNOWLEDGE_BATCH_STATE_SCHEMA_VERSION,
        "batch_id": plan["batch_id"],
        "operation_id": plan["operation_id"],
        "status": "running",
        "plan": str(plan_path.resolve()),
        "plan_digest": plan["plan_digest"],
        "state": str(state_path.resolve()),
        "created_at_utc": stamp,
        "updated_at_utc": stamp,
        "projects": projects,
        "events": [],
    }


def _summarize_knowledge_state(state: dict[str, Any]) -> str:
    values = [item["status"] for item in state["projects"].values()]
    eligible = [value for value in values if value not in {"failed", "awaiting-review"}]
    if eligible and all(value == "rolled-back" for value in eligible):
        return "rolled-back"
    if values and all(value == "cutover-complete" for value in values):
        return "cutover-complete"
    if any(value == "cutover-complete" for value in values):
        return "partial"
    if any(value in {"failed", "awaiting-review"} for value in values) and any(
        value in {"ready", "review-pending", "pending", "applying", "rolled-back"} for value in values
    ):
        return "partial"
    if any(value == "ready" for value in values):
        return "ready"
    if any(value == "review-pending" for value in values):
        return "review-pending"
    if any(value in {"pending", "applying"} for value in values):
        return "running"
    if values and all(value in {"failed", "awaiting-review", "cold-build-required"} for value in values):
        return "failed"
    return "partial" if any(value == "failed" for value in values) else "running"


def _manifest_matches(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    return all(expected.get(key) == actual.get(key) for key in ("algorithm", "file_count", "byte_count", "sha256", "files"))


def _verify_plan_bindings(project: dict[str, Any]) -> None:
    output = Path(project["output"]).resolve()
    actual = _tree_manifest(output)
    if not _manifest_matches(project["origin_manifest"], actual):
        raise BatchProjectError("origin-drift", f"origin knowledge OUTPUT changed after plan: {project['project_id']}")
    repository = preflight(Path(project["repository"]))
    if {"commit": repository["commit"], "tree": repository["tree"]} != project["target_snapshot"]:
        raise BatchProjectError("repository-drift", f"target repository changed after plan: {project['project_id']}")


def _knowledge_output_lock(output: Path):
    """Use the proven owner-token lock outside the directory being renamed.

    The Agent Protocol batch lock file lives inside OUTPUT because that batch
    edits individual files.  Complete migration atomically renames OUTPUT, so
    its equivalent lock anchor is a deterministic sibling; otherwise Windows
    would keep an open descriptor inside the directory being promoted.
    """
    anchor = output.resolve().parent / f".{output.name}.knowledge-batch-lock"
    anchor.mkdir(parents=True, exist_ok=True)
    return _output_lock(anchor)


def _detach_staging_workspace_roots(staging: Path, project: dict[str, Any]) -> dict[str, Any]:
    record_path = staging / "workspace-meta/agent-protocol.json"
    if record_path.is_file():
        record = json_load(record_path)
        record["workspace_roots"] = []
        record["output"] = str(staging.resolve())
        record["python"] = project["runtime"]["python"]
        record["ckb"] = project["runtime"]["ckb"]
        json_write(record_path, record)
    # This writes only internal staging adapters.  External Harness roots are
    # upgraded transactionally during cutover and are separately backed up.
    return project_agent_protocol(
        staging,
        python=Path(project["runtime"]["python"]),
        ckb=Path(project["runtime"]["ckb"]),
    )


def _cold_build(project: dict[str, Any]) -> dict[str, Any]:
    previous_output = Path(project["output"]).resolve()
    repository = Path(project["repository"]).resolve()
    staging = Path(project["staging"]).resolve()
    selectors = project["scope_selectors"]
    initialize(
        repository,
        staging,
        project["format"],
        list(selectors.get("scope_paths") or []),
        list(selectors.get("entries") or []),
        int(selectors.get("expand_depth", 1)),
        str(selectors.get("expand_direction", "both")),
        list(selectors.get("include") or []),
        csharp_solution=selectors.get("csharp_solution"),
        csharp_project=selectors.get("csharp_project"),
        allow_dotnet_restore=bool(selectors.get("allow_dotnet_restore", False)),
        page_config_path=previous_output / "page-config.json",
    )
    preserved = _preserve_mutable_layers(previous_output, staging)
    state = json_load(staging / "state.json")
    for batch in state["parse_batches"]:
        build_chunk(staging, batch["id"], "all")
    _reused, delta_ids = _replace_review_packs(staging, {})
    state = json_load(staging / "state.json")
    migration = {
        "schema_version": 1,
        "mode": "cold-build",
        "origin_output": str(previous_output),
        "origin_version": project["source"]["ckb_version"],
        "origin_commit": project["origin_snapshot"]["commit"],
        "target_version": VERSION,
        "target_commit": project["target_snapshot"]["commit"],
        "status": "pending-agent-review",
        "started_at_utc": utc_now(),
    }
    state["migration"] = migration
    json_write(staging / "state.json", state)
    migration_plan = {
        "schema_version": 1,
        "status": "pending-agent-review",
        "mode": "cold-build",
        "origin": {
            "output": str(previous_output),
            "version": project["source"]["ckb_version"],
            "commit": project["origin_snapshot"]["commit"],
        },
        "target": {
            "output": str(staging),
            "version": VERSION,
            "repository": str(repository),
            "commit": project["target_snapshot"]["commit"],
        },
        "files": {"reused": [], "reused_count": 0, "parsed_count": len(state.get("parse_batches", []))},
        "entities": {"reused_review_count": 0, "delta_review_count": len(delta_ids), "old_to_new_id_map": {}},
        "mutable_files": preserved,
        "cold_build": {
            "reused_fact_count": 0,
            "reused_review_count": 0,
            "required_review_entity_ids": sorted(delta_ids),
            "incompatible_layers": ["facts", "graph", "review", "human-projection", "machine-indexes"],
        },
        "created_at_utc": utc_now(),
    }
    json_write(staging / "migration/plan.json", migration_plan)
    return {
        "schema_version": 1,
        "status": "pending-agent-review",
        "output": str(staging),
        "strategy": "cold-build",
        "delta_review_entity_count": len(delta_ids),
        "preserved_mutable_file_count": len(preserved),
    }


def _project_record(staging: Path, batch_id: str, project: dict[str, Any], project_state: dict[str, Any]) -> dict[str, Any]:
    migration_plan = json_load(staging / "migration/plan.json")
    record = {
        "schema_version": KNOWLEDGE_BATCH_PROJECT_SCHEMA_VERSION,
        "batch_id": batch_id,
        "project_id": project["project_id"],
        "operation_id": project_state["operation_id"],
        "status": "review-pending",
        "strategy": project_state["strategy"],
        "bindings": {
            "origin_output": project["output"],
            "staging_output": project["staging"],
            "repository": project["repository"],
            "origin_snapshot": project["origin_snapshot"],
            "target_snapshot": project["target_snapshot"],
        },
        "version_chain": project["version_chain"],
        "protocol_chain": project["protocol_chain"],
        "origin_manifest": project["origin_manifest"],
        "origin_layers": project["origin_layers"],
        "mutable_files": migration_plan.get("mutable_files", []),
        "workspace_roots": project["workspace_roots"],
        "created_at_utc": utc_now(),
    }
    json_write(staging / "knowledge-batch/project.json", record)
    return record


def _pending_reviews(staging: Path) -> list[str]:
    state = json_load(staging / "state.json")
    return [item["id"] for item in state.get("review_packs", []) if item.get("status") != "passed"]


def _mutable_preservation_check(staging: Path, record: dict[str, Any]) -> dict[str, Any]:
    files = list(record.get("mutable_files") or [])
    errors = _preservation_errors(staging, files)
    missing_baselines = []
    for item in files:
        relative = item.get("baseline_relative_target")
        if not relative:
            missing_baselines.append(item.get("relative_target"))
            continue
        path = staging / str(relative)
        if not path.is_file() or sha256_file(path) != item.get("baseline_sha256"):
            missing_baselines.append(item.get("relative_target"))
    return {"passed": not errors and not missing_baselines, "errors": errors, "missing_baselines": missing_baselines}


def _old_entity_id_errors(staging: Path) -> list[str]:
    migration_plan = json_load(staging / "migration/plan.json")
    mapping = (migration_plan.get("entities") or {}).get("old_to_new_id_map", {})
    old_ids = {old for old, new in mapping.items() if old != new}
    graph = json_load(staging / "graph.json") if (staging / "graph.json").is_file() else {}
    new_ids = {item.get("id") for item in graph.get("entities", [])}
    return sorted(old_ids & new_ids)


def _knowledge_project_audit(project: dict[str, Any], project_state: dict[str, Any]) -> dict[str, Any]:
    staging = Path(project["staging"]).resolve()
    record_path = staging / "knowledge-batch/project.json"
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any, category: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "category": category, "detail": detail})

    if not record_path.is_file():
        result = {
            "schema_version": KNOWLEDGE_BATCH_PROJECT_SCHEMA_VERSION,
            "project_id": project["project_id"],
            "status": "failed",
            "checks": [{"name": "project-record", "passed": False, "category": "staging-record-missing", "detail": str(record_path)}],
        }
        return result
    record = json_load(record_path)
    check(
        "absolute-bindings",
        record.get("batch_id") is not None
        and record.get("project_id") == project["project_id"]
        and record.get("operation_id") == project_state["operation_id"]
        and Path(record.get("bindings", {}).get("staging_output", "")).resolve() == staging,
        record.get("bindings"),
        "staging-binding",
    )
    try:
        _verify_plan_bindings(project)
    except BatchProjectError as exc:
        check("origin-and-repository-pinned", False, str(exc), exc.category)
    else:
        check("origin-and-repository-pinned", True, project["target_snapshot"], "drift")
    pending = _pending_reviews(staging)
    migration_audit = audit_migration(staging, require_complete_reviews=False)
    check(
        "migration-reuse-and-review-binding",
        migration_audit.get("status") in {"passed", "pending-agent-review"},
        migration_audit,
        "migration-audit",
    )
    if project_state["strategy"] == "cold-build":
        migration_plan = json_load(staging / "migration/plan.json")
        cold = migration_plan.get("cold_build") or {}
        cold_ok = (
            migration_plan.get("files", {}).get("reused_count") == 0
            and migration_plan.get("entities", {}).get("reused_review_count") == 0
            and cold.get("reused_fact_count") == 0
            and cold.get("reused_review_count") == 0
        )
        check("cold-build-does-not-reuse-incompatible-facts", cold_ok, cold, "cold-build-reuse")
    check("delta-reviews-complete", not pending, pending, "review-pending")
    if not pending and all(item["passed"] for item in checks):
        try:
            if json_load(staging / "state.json").get("status") != "complete":
                finalize(staging)
        except (CkbError, OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
            check("current-finalize", False, str(exc), "global-finalize")
        else:
            check("current-finalize", True, "complete", "global-finalize")
    else:
        check("current-finalize", False, "blocked by pending review or earlier check", "blocked")
    global_audit = json_load(staging / "audit/global.json") if (staging / "audit/global.json").is_file() else {}
    check("global-audit", global_audit.get("status") == "passed", global_audit, "global-audit")
    markers = {
        name: json_load(staging / name) if (staging / name).is_file() else {}
        for name in (".complete", ".machine.complete", ".human.complete")
    }
    check("three-completion-markers", all(value.get("status") == "complete" for value in markers.values()), markers, "completion-markers")
    sqlite_checks = _sqlite_checks(staging)
    required_sqlite = {item["path"]: item for item in sqlite_checks}
    check(
        "double-sqlite-integrity-and-foreign-keys",
        all(required_sqlite.get(name, {}).get("passed") for name in ("machine/knowledge.sqlite", "agent-index.sqlite")),
        sqlite_checks,
        "sqlite-integrity",
    )
    preservation = _mutable_preservation_check(staging, record)
    check("all-mutable-layers-preserved", preservation["passed"], preservation, "mutable-layer-loss")
    old_ids = _old_entity_id_errors(staging)
    check("old-entity-id-residue-zero", not old_ids, old_ids[:40], "old-entity-id-residue")
    readability = json_load(staging / "markdown/readability-audit.json") if (staging / "markdown/readability-audit.json").is_file() else {}
    check("human-readability", readability.get("status") == "passed" and not readability.get("errors"), readability, "readability")
    from .agent_protocol import audit_agent_protocol
    from .llm_wiki_capabilities import maintenance_check
    from .operation_journal import audit_operation_journal
    from .reference_documents import audit_references
    from .research_gaps import audit_gap_register

    if global_audit.get("status") == "passed":
        reference = audit_references(staging)
        gaps = audit_gap_register(staging)
        operations = audit_operation_journal(staging)
        agent_policy = audit_agent_protocol(staging)
        maintenance = maintenance_check(staging)
    else:
        reference = gaps = operations = agent_policy = maintenance = {"status": "blocked"}
    _release_audit_handles()
    check("reference-layer", reference.get("status") == "passed", reference, "reference-audit")
    check("research-gap-layer", gaps.get("status") == "passed", gaps, "gap-audit")
    check("operation-journal", operations.get("status") == "passed", operations, "operation-audit")
    check("agent-policy", agent_policy.get("status") == "passed", agent_policy, "agent-policy-audit")
    check("maintain", maintenance.get("status") == "passed", maintenance, "maintain")
    passed = all(item["passed"] for item in checks)
    pending_only = bool(pending) and all(item["passed"] or item["category"] in {"review-pending", "blocked", "global-audit", "completion-markers", "sqlite-integrity", "readability", "reference-audit", "gap-audit", "operation-audit", "agent-policy-audit", "maintain"} for item in checks)
    status = "ready" if passed else "review-pending" if pending_only else "failed"
    result = {
        "schema_version": KNOWLEDGE_BATCH_PROJECT_SCHEMA_VERSION,
        "project_id": project["project_id"],
        "operation_id": project_state["operation_id"],
        "status": status,
        "strategy": project_state["strategy"],
        "checks": checks,
        "counts": {"passed": sum(item["passed"] for item in checks), "total": len(checks)},
        "pending_review_packs": pending,
        "origin_layers": record.get("origin_layers"),
        "current_layers": _complete_layer_inventory(staging, record.get("mutable_files")),
        "sqlite": sqlite_checks,
        "audited_at_utc": utc_now(),
    }
    json_write(staging / "knowledge-batch/audit.json", result)
    record["status"] = status
    record["audited_at_utc"] = result["audited_at_utc"]
    json_write(record_path, record)
    return result


def _apply_one_project(
    state: dict[str, Any],
    state_path: Path,
    project: dict[str, Any],
    *,
    retry_failed: bool,
    fault: str | None = None,
) -> None:
    project_id = project["project_id"]
    item = state["projects"][project_id]
    if project["status"] not in {"ready", "cold-build-required"}:
        return
    if item["status"] in {"ready", "review-pending", "cutover-complete", "rolled-back"}:
        if item["status"] in {"ready", "review-pending"}:
            staging = Path(project["staging"])
            if not staging.is_dir() or not (staging / "knowledge-batch/project.json").is_file():
                raise BatchProjectError("staging-missing", f"recorded staging is missing for {project_id}")
            if item["status"] == "review-pending" and retry_failed:
                with _knowledge_output_lock(Path(project["output"])):
                    audit = _knowledge_project_audit(project, item)
                item["audit"] = str((staging / "knowledge-batch/audit.json").resolve())
                item["pending_review_packs"] = audit.get("pending_review_packs", [])
                item["status"] = audit["status"]
                item["staging_digest"] = _tree_manifest(staging)["sha256"]
                item["failure"] = None if audit["status"] in {"ready", "review-pending"} else {
                    "category": "staging-audit-failed",
                    "detail": item["audit"],
                }
                _state_event(state, project_id, "resume", item["status"], (item.get("failure") or {}).get("category"))
                _save_knowledge_state(state_path, state)
        return
    if item["status"] == "failed" and not retry_failed:
        return
    if item["status"] == "failed":
        item["status"] = "pending"
        item["failure"] = None
    output = Path(project["output"]).resolve()
    staging = Path(project["staging"]).resolve()
    with _knowledge_output_lock(output):
        _verify_plan_bindings(project)
        if item["status"] == "applying" and staging.exists():
            marker = staging / "knowledge-batch/project.json"
            if marker.is_file():
                value = json_load(marker)
                if value.get("operation_id") != item["operation_id"]:
                    raise BatchProjectError("resume-staging-conflict", f"interrupted staging belongs to another operation: {project_id}")
            shutil.rmtree(staging)
            _state_event(state, project_id, "resume", "staging-reset")
            item["status"] = "pending"
            _save_knowledge_state(state_path, state)
        if staging.exists():
            raise BatchProjectError("staging-conflict", f"staging exists before apply: {staging}")
        item["status"] = "applying"
        item["failure"] = None
        _state_event(state, project_id, "apply", "applying")
        _save_knowledge_state(state_path, state)
        if fault == "before-build":
            raise OSError("injected failure before staging build")
        if item["strategy"] == "cold-build":
            _cold_build(project)
        else:
            migrate_output(output, Path(project["repository"]), staging, project["format"])
        _detach_staging_workspace_roots(staging, project)
        _project_record(staging, state["batch_id"], project, item)
        if fault == "after-build":
            raise OSError("injected failure after staging build")
        audit = _knowledge_project_audit(project, item)
        item["audit"] = str((staging / "knowledge-batch/audit.json").resolve())
        item["pending_review_packs"] = audit.get("pending_review_packs", [])
        item["status"] = audit["status"]
        item["staging_digest"] = _tree_manifest(staging)["sha256"]
        item["failure"] = None if audit["status"] in {"ready", "review-pending"} else {
            "category": "staging-audit-failed",
            "detail": str(item["audit"]),
        }
        _state_event(state, project_id, "apply", item["status"], (item.get("failure") or {}).get("category"))
        _save_knowledge_state(state_path, state)


def apply_knowledge_batch_plan(
    plan_path: Path,
    state_path: Path,
    *,
    retry_failed: bool = False,
    faults: dict[str, str] | None = None,
) -> dict[str, Any]:
    plan_path = plan_path.expanduser().resolve()
    state_path = state_path.expanduser().resolve()
    plan = _load_knowledge_batch_plan(plan_path)
    for project in plan["projects"]:
        if path_inside(state_path, Path(project["output"])) or path_inside(state_path, Path(project["staging"])):
            raise CkbError("knowledge batch state must be outside every OUTPUT and staging directory")
    if state_path.is_file():
        state = _load_knowledge_state(state_path)
        if state.get("operation_id") != plan["operation_id"] or state.get("plan_digest") != plan["plan_digest"]:
            raise CkbError("knowledge batch state is bound to another immutable plan")
    else:
        state = _new_knowledge_state(plan, plan_path, state_path)
        _save_knowledge_state(state_path, state)
    plan_by_id = {item["project_id"]: item for item in plan["projects"]}
    for project_id in sorted(plan_by_id):
        project = plan_by_id[project_id]
        try:
            _apply_one_project(
                state,
                state_path,
                project,
                retry_failed=retry_failed,
                fault=(faults or {}).get(project_id),
            )
        except BatchProjectError as exc:
            item = state["projects"][project_id]
            item["status"] = "failed"
            item["failure"] = {"category": exc.category, "detail": str(exc)}
            _state_event(state, project_id, "apply", "failed", exc.category)
            _save_knowledge_state(state_path, state)
        except (CkbError, OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
            item = state["projects"][project_id]
            item["status"] = "failed"
            item["failure"] = {"category": "apply-failed", "detail": str(exc)}
            _state_event(state, project_id, "apply", "failed", "apply-failed")
            _save_knowledge_state(state_path, state)
    state["status"] = _summarize_knowledge_state(state)
    _save_knowledge_state(state_path, state)
    return knowledge_batch_status(state_path)


def resume_knowledge_batch_state(
    state_path: Path,
    *,
    faults: dict[str, str] | None = None,
) -> dict[str, Any]:
    state = _load_knowledge_state(state_path)
    return apply_knowledge_batch_plan(Path(state["plan"]), state_path, retry_failed=True, faults=faults)


def knowledge_batch_status(state_path: Path) -> dict[str, Any]:
    state_path = state_path.expanduser().resolve()
    state = _load_knowledge_state(state_path)
    plan = _load_knowledge_batch_plan(Path(state["plan"]))
    plan_by_id = {item["project_id"]: item for item in plan["projects"]}
    projects = []
    drifted = 0
    for project_id in sorted(state["projects"]):
        value = dict(state["projects"][project_id])
        project = plan_by_id[project_id]
        drift = None
        try:
            if value["status"] in {"ready", "review-pending"}:
                staging = Path(project["staging"])
                if not staging.is_dir():
                    drift = {"category": "staging-missing"}
                else:
                    actual = _tree_manifest(staging)["sha256"]
                    if value.get("staging_digest") and actual != value["staging_digest"]:
                        drift = {"category": "staging-drift", "expected": value["staging_digest"], "actual": actual}
            elif value["status"] == "cutover-complete":
                output = Path(project["output"])
                actual = _tree_manifest(output)["sha256"] if output.is_dir() else None
                if actual != value.get("modified_digest"):
                    drift = {"category": "cutover-output-drift", "expected": value.get("modified_digest"), "actual": actual}
            elif value["status"] == "rolled-back":
                output = Path(project["output"])
                actual = _tree_manifest(output)["sha256"] if output.is_dir() else None
                if actual != value.get("origin_digest"):
                    drift = {"category": "rollback-output-drift", "expected": value.get("origin_digest"), "actual": actual}
        except (CkbError, OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
            drift = {"category": "status-probe-failed", "detail": str(exc)}
        value["drift"] = drift
        if drift:
            drifted += 1
        value["commands"] = {
            "resume": f"migrate batch resume --state '{state_path}'",
            "audit": f"migrate batch audit --state '{state_path}'",
            "cutover": f"migrate batch cutover --state '{state_path}' --project {project_id}",
            "rollback": f"migrate batch rollback --state '{state_path}' --project {project_id}",
        }
        projects.append(value)
    counts: dict[str, int] = {}
    for item in projects:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return {
        "schema_version": KNOWLEDGE_BATCH_STATE_SCHEMA_VERSION,
        "batch_id": state["batch_id"],
        "operation_id": state["operation_id"],
        "status": "drifted" if drifted else state["status"],
        "state": str(state_path),
        "plan": state["plan"],
        "summary": {"projects": len(projects), "drifted": drifted, "counts": dict(sorted(counts.items()))},
        "projects": projects,
        "event_count": len(state.get("events", [])),
    }


def audit_knowledge_batch_state(state_path: Path) -> dict[str, Any]:
    state_path = state_path.expanduser().resolve()
    state = _load_knowledge_state(state_path)
    plan = _load_knowledge_batch_plan(Path(state["plan"]))
    plan_by_id = {item["project_id"]: item for item in plan["projects"]}
    results = []
    for project_id in sorted(state["projects"]):
        item = state["projects"][project_id]
        project = plan_by_id[project_id]
        if project["status"] not in {"ready", "cold-build-required"}:
            result = {
                "project_id": project_id,
                "status": project["status"],
                "failure": project.get("failure") or {"category": project.get("reason")},
            }
        elif item["status"] in {"cutover-complete", "rolled-back"}:
            result = {
                "project_id": project_id,
                "status": "passed",
                "phase": item["status"],
                "control": item.get("control"),
            }
        elif not Path(project["staging"]).is_dir():
            result = {
                "project_id": project_id,
                "status": "failed",
                "failure": {"category": "staging-missing"},
            }
            item["status"] = "failed"
            item["failure"] = result["failure"]
        else:
            result = _knowledge_project_audit(project, item)
            item["audit"] = str((Path(project["staging"]) / "knowledge-batch/audit.json").resolve())
            item["pending_review_packs"] = result.get("pending_review_packs", [])
            item["status"] = result["status"]
            item["staging_digest"] = _tree_manifest(Path(project["staging"]))["sha256"]
            item["failure"] = None if result["status"] in {"ready", "review-pending"} else {
                "category": "staging-audit-failed",
                "detail": item["audit"],
            }
        results.append(result)
        _state_event(state, project_id, "audit", result["status"], (result.get("failure") or {}).get("category"))
        _save_knowledge_state(state_path, state)
    state["status"] = _summarize_knowledge_state(state)
    _save_knowledge_state(state_path, state)
    failed = sum(item["status"] in {"failed", "awaiting-review"} for item in results)
    pending = sum(item["status"] == "review-pending" for item in results)
    ready = sum(item["status"] in {"ready", "passed"} for item in results)
    return {
        "schema_version": KNOWLEDGE_BATCH_STATE_SCHEMA_VERSION,
        "batch_id": state["batch_id"],
        "status": "passed" if failed == 0 and pending == 0 else "review-pending" if failed == 0 else "failed" if ready == 0 else "partial",
        "state": str(state_path),
        "summary": {"projects": len(results), "ready": ready, "review_pending": pending, "failed": failed},
        "projects": results,
    }


def _control_path(output: Path, operation_id: str, project_id: str) -> Path:
    return output.parent / f".{output.name}.knowledge-migration-{operation_id}-{project_id}.json"


def _control_records(output: Path) -> list[tuple[Path, dict[str, Any]]]:
    records = []
    for path in sorted(output.parent.glob(f".{output.name}.knowledge-migration-*.json")):
        try:
            value = json_load(path)
        except (CkbError, OSError, ValueError, json.JSONDecodeError):
            continue
        if value.get("schema_version") == KNOWLEDGE_BATCH_PROJECT_SCHEMA_VERSION and value.get("output") == str(output.resolve()):
            records.append((path, value))
    return records


def _active_control(output: Path, actual: dict[str, Any] | None = None) -> tuple[Path, dict[str, Any]] | None:
    actual = actual or _tree_manifest(output)
    matches = [
        (path, value)
        for path, value in _control_records(output)
        if value.get("status") == "cutover-complete"
        and isinstance(value.get("modified_manifest"), dict)
        and _manifest_matches(value["modified_manifest"], actual)
    ]
    if len(matches) > 1:
        raise BatchProjectError("active-chain-ambiguous", f"multiple migration controls match the active OUTPUT: {output}")
    return matches[0] if matches else None


def _protocol_digest(project: dict[str, Any]) -> str:
    return _protocol_snapshot_digest(
        _protocol_snapshot_files(
            Path(project["output"]),
            [Path(value) for value in project.get("workspace_roots", [])],
        )
    )


def _cutover_one(
    state: dict[str, Any],
    state_path: Path,
    project: dict[str, Any],
    *,
    fault: str | None = None,
) -> dict[str, Any]:
    project_id = project["project_id"]
    item = state["projects"][project_id]
    output = Path(project["output"]).resolve()
    staging = Path(project["staging"]).resolve()
    if item["status"] == "cutover-complete":
        control = json_load(Path(item["control"]))
        if not _manifest_matches(control["modified_manifest"], _tree_manifest(output)):
            raise BatchProjectError("cutover-post-drift", f"completed cutover drifted for {project_id}")
        return {"project_id": project_id, "status": "skipped", "control": item["control"]}
    if item["status"] != "ready":
        raise BatchProjectError("not-ready", f"project audit has not marked staging ready: {project_id}")
    with _knowledge_output_lock(output):
        _verify_plan_bindings(project)
        audit = json_load(Path(item["audit"])) if item.get("audit") and Path(item["audit"]).is_file() else {}
        if audit.get("status") != "ready":
            raise BatchProjectError("audit-not-ready", f"staging audit is not ready for {project_id}")
        current_staging = _tree_manifest(staging)
        if current_staging["sha256"] != item.get("staging_digest"):
            raise BatchProjectError("staging-drift", f"staging changed after audit for {project_id}")
        operation_id = item["operation_id"]
        backup_root = Path(project["cutover"]["backup_root"]).resolve()
        backup_root.mkdir(parents=True, exist_ok=True)
        backup = backup_root / f"{output.name}.{operation_id}.{project_id}"
        if backup.exists():
            raise BatchProjectError("cutover-backup-conflict", f"cutover backup already exists: {backup}")
        control_path = _control_path(output, operation_id, project_id)
        previous_attempts: list[dict[str, Any]] = []
        if control_path.exists():
            previous = json_load(control_path)
            if previous.get("status") != "cutover-failed-restored":
                raise BatchProjectError("cutover-control-conflict", f"cutover control already exists: {control_path}")
            previous_attempts = list(previous.get("attempts") or [])
            previous_attempts.append(
                {
                    "status": previous.get("status"),
                    "failure": previous.get("failure"),
                    "origin_restored": previous.get("origin_restored"),
                }
            )
        active_parent = _active_control(output, project["origin_manifest"])
        protocol_backup_root = state_path.parent / ".ckb-knowledge-migration-protocol-backups" / state["batch_id"] / project_id
        protocol_backup_project = {
            "project_id": project_id,
            "output": str(output),
            "workspace_roots": project["workspace_roots"],
        }
        protocol_backup = _create_protocol_backup(protocol_backup_project, protocol_backup_root)
        record = {
            "schema_version": KNOWLEDGE_BATCH_PROJECT_SCHEMA_VERSION,
            "batch_id": state["batch_id"],
            "project_id": project_id,
            "operation_id": operation_id,
            "status": "cutover-started",
            "output": str(output),
            "staging_output": str(staging),
            "backup_output": str(backup),
            "parent_operation_id": active_parent[1]["operation_id"] if active_parent else None,
            "chain_depth": int(active_parent[1].get("chain_depth", 0)) + 1 if active_parent else 1,
            "origin_manifest": project["origin_manifest"],
            "staging_manifest": current_staging,
            "protocol_backup": protocol_backup["manifest_path"],
            "attempts": previous_attempts,
            "started_at_utc": utc_now(),
        }
        json_write(control_path, record)
        moved_staging = False
        try:
            _release_audit_handles()
            output.rename(backup)
            if fault == "after-backup-rename":
                raise OSError("injected failure after backup rename")
            if not _manifest_matches(project["origin_manifest"], _tree_manifest(backup)):
                raise BatchProjectError("backup-verification", f"cutover backup differs from origin for {project_id}")
            staging.rename(output)
            moved_staging = True
            if fault == "after-staging-rename":
                raise OSError("injected failure after staging rename")
            pipeline_status(output)
            install_agent_protocol(
                output,
                [Path(value) for value in project["workspace_roots"]],
                python=Path(project["runtime"]["python"]),
                ckb=Path(project["runtime"]["ckb"]),
            )
            if fault == "after-protocol-upgrade":
                raise OSError("injected failure after Agent Protocol upgrade")
            sqlite_checks = _sqlite_checks(output)
            if not sqlite_checks or not all(value["passed"] for value in sqlite_checks):
                raise BatchProjectError("cutover-sqlite", f"promoted SQLite verification failed for {project_id}: {sqlite_checks}")
            from .llm_wiki_capabilities import maintenance_check

            maintenance = maintenance_check(output)
            _release_audit_handles()
            if maintenance.get("status") != "passed":
                raise BatchProjectError("cutover-maintain", f"promoted maintain failed for {project_id}")
            modified = _tree_manifest(output)
            protocol_digest = _protocol_digest(project)
            record.update(
                {
                    "status": "cutover-complete",
                    "backup_manifest": _tree_manifest(backup),
                    "modified_manifest": modified,
                    "protocol_applied_digest": protocol_digest,
                    "sqlite": sqlite_checks,
                    "maintenance_status": maintenance.get("status"),
                    "completed_at_utc": utc_now(),
                }
            )
            json_write(control_path, record)
            item["status"] = "cutover-complete"
            item["modified_digest"] = modified["sha256"]
            item["backup_output"] = str(backup)
            item["control"] = str(control_path)
            item["protocol_backup"] = protocol_backup["manifest_path"]
            item["failure"] = None
            _state_event(state, project_id, "cutover", "cutover-complete")
            _save_knowledge_state(state_path, state)
            return {
                "project_id": project_id,
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
                _restore_protocol_backup(Path(protocol_backup["manifest_path"]))
            finally:
                restored = output.is_dir() and _manifest_matches(project["origin_manifest"], _tree_manifest(output))
                record.update(
                    {
                        "status": "cutover-failed-restored" if restored else "cutover-failed",
                        "failure": str(exc),
                        "origin_restored": restored,
                    }
                )
                json_write(control_path, record)
            if isinstance(exc, BatchProjectError):
                raise
            raise BatchProjectError("cutover-failed", str(exc)) from exc


def cutover_knowledge_batch_state(
    state_path: Path,
    project_ids: list[str] | None = None,
    *,
    faults: dict[str, str] | None = None,
) -> dict[str, Any]:
    state_path = state_path.expanduser().resolve()
    state = _load_knowledge_state(state_path)
    plan = _load_knowledge_batch_plan(Path(state["plan"]))
    plan_by_id = {item["project_id"]: item for item in plan["projects"]}
    requested = sorted(set(project_ids or []))
    unknown = sorted(set(requested) - set(plan_by_id))
    if unknown:
        raise CkbError(f"unknown knowledge batch cutover project: {', '.join(unknown)}")
    selected = requested or sorted(project_id for project_id, item in state["projects"].items() if item["status"] in {"ready", "cutover-complete"})
    if not selected:
        raise CkbError("knowledge batch cutover has no audit-ready project")
    results = []
    for project_id in selected:
        try:
            result = _cutover_one(state, state_path, plan_by_id[project_id], fault=(faults or {}).get(project_id))
        except BatchProjectError as exc:
            item = state["projects"][project_id]
            item["failure"] = {"category": exc.category, "detail": str(exc)}
            _state_event(state, project_id, "cutover", "failed", exc.category)
            _save_knowledge_state(state_path, state)
            result = {"project_id": project_id, "status": "failed", "failure": item["failure"]}
        results.append(result)
    state["status"] = _summarize_knowledge_state(state)
    _save_knowledge_state(state_path, state)
    failed = sum(item["status"] == "failed" for item in results)
    passed = sum(item["status"] == "cutover-complete" for item in results)
    return {
        "schema_version": KNOWLEDGE_BATCH_STATE_SCHEMA_VERSION,
        "batch_id": state["batch_id"],
        "status": "passed" if failed == 0 else "failed" if passed == 0 else "partial",
        "state": str(state_path),
        "summary": {"selected": len(results), "cutover_complete": passed, "skipped": len(results) - passed - failed, "failed": failed},
        "projects": results,
    }


def _rollback_one(
    state: dict[str, Any],
    state_path: Path,
    project: dict[str, Any],
    *,
    fault: str | None = None,
) -> dict[str, Any]:
    project_id = project["project_id"]
    item = state["projects"][project_id]
    output = Path(project["output"]).resolve()
    if item["status"] == "rolled-back":
        if not _manifest_matches(project["origin_manifest"], _tree_manifest(output)):
            raise BatchProjectError("rollback-post-drift", f"rolled-back OUTPUT drifted for {project_id}")
        return {"project_id": project_id, "status": "skipped", "idempotent": True}
    if item["status"] != "cutover-complete" or not item.get("control"):
        raise BatchProjectError("rollback-not-eligible", f"project has no completed cutover: {project_id}")
    control_path = Path(item["control"])
    if not control_path.is_file():
        raise BatchProjectError("rollback-control-missing", f"rollback control is missing for {project_id}")
    record = json_load(control_path)
    with _knowledge_output_lock(output):
        actual = _tree_manifest(output)
        if not _manifest_matches(record["modified_manifest"], actual):
            raise BatchProjectError("rollback-external-drift", f"promoted OUTPUT changed after cutover: {project_id}")
        if _protocol_digest(project) != record.get("protocol_applied_digest"):
            raise BatchProjectError("rollback-protocol-drift", f"Agent Protocol managed bytes changed after cutover: {project_id}")
        backup = Path(record["backup_output"])
        if not backup.is_dir() or not _manifest_matches(record["origin_manifest"], _tree_manifest(backup)):
            raise BatchProjectError("rollback-backup-drift", f"rollback backup is missing or changed: {project_id}")
        quarantine_root = Path(project["rollback"]["quarantine_root"]).resolve()
        quarantine_root.mkdir(parents=True, exist_ok=True)
        quarantine = quarantine_root / f"{output.name}.{record['operation_id']}.{project_id}"
        if quarantine.exists():
            raise BatchProjectError("rollback-quarantine-conflict", f"rollback quarantine already exists: {quarantine}")
        restored_origin = False
        try:
            _release_audit_handles()
            output.rename(quarantine)
            if fault == "after-modified-rename":
                raise OSError("injected failure after modified rename")
            backup.rename(output)
            restored_origin = True
            if fault == "after-backup-restore":
                raise OSError("injected failure after backup restore")
            _restore_protocol_backup(Path(record["protocol_backup"]))
            if fault == "after-protocol-restore":
                raise OSError("injected failure after Agent Protocol restore")
            restored = _tree_manifest(output)
            if not _manifest_matches(record["origin_manifest"], restored):
                raise BatchProjectError("rollback-verification", f"restored OUTPUT differs from the exact origin for {project_id}")
            sqlite_checks = _sqlite_checks(output)
            if not sqlite_checks or not all(value["passed"] for value in sqlite_checks):
                raise BatchProjectError("rollback-sqlite", f"restored SQLite verification failed for {project_id}")
            record.update(
                {
                    "status": "rolled-back",
                    "rolled_forward_output": str(quarantine),
                    "restored_manifest": restored,
                    "rollback_sqlite": sqlite_checks,
                    "rolled_back_at_utc": utc_now(),
                }
            )
            json_write(control_path, record)
            item["status"] = "rolled-back"
            item["failure"] = None
            _state_event(state, project_id, "rollback", "rolled-back")
            _save_knowledge_state(state_path, state)
            return {
                "project_id": project_id,
                "status": "rolled-back",
                "operation_id": record["operation_id"],
                "reactivated_operation_id": record.get("parent_operation_id"),
                "output": str(output),
                "modified_output": str(quarantine),
                "control": str(control_path),
                "sqlite": sqlite_checks,
            }
        except Exception as exc:
            try:
                if restored_origin and output.exists():
                    output.rename(backup)
                if quarantine.exists() and not output.exists():
                    quarantine.rename(output)
                # Restore the promoted managed bytes when the old backup was
                # partially applied.  The quarantined promoted OUTPUT carries
                # its exact internal bytes; external blocks are guarded by the
                # applied digest and remain untouched unless backup restore ran.
                if _protocol_digest(project) != record.get("protocol_applied_digest"):
                    install_agent_protocol(
                        output,
                        [Path(value) for value in project["workspace_roots"]],
                        python=Path(project["runtime"]["python"]),
                        ckb=Path(project["runtime"]["ckb"]),
                    )
            finally:
                restored_modified = output.is_dir() and _manifest_matches(record["modified_manifest"], _tree_manifest(output))
                record.update(
                    {
                        "status": "cutover-complete" if restored_modified else "rollback-failed",
                        "last_rollback_failure": str(exc),
                        "modified_restored": restored_modified,
                    }
                )
                json_write(control_path, record)
            if isinstance(exc, BatchProjectError):
                raise
            raise BatchProjectError("rollback-failed", str(exc)) from exc


def rollback_knowledge_batch_state(
    state_path: Path,
    project_ids: list[str] | None = None,
    *,
    faults: dict[str, str] | None = None,
) -> dict[str, Any]:
    state_path = state_path.expanduser().resolve()
    state = _load_knowledge_state(state_path)
    plan = _load_knowledge_batch_plan(Path(state["plan"]))
    plan_by_id = {item["project_id"]: item for item in plan["projects"]}
    requested = sorted(set(project_ids or []))
    unknown = sorted(set(requested) - set(plan_by_id))
    if unknown:
        raise CkbError(f"unknown knowledge batch rollback project: {', '.join(unknown)}")
    selected = requested or sorted(project_id for project_id, item in state["projects"].items() if item["status"] in {"cutover-complete", "rolled-back"})
    if not selected:
        raise CkbError("knowledge batch rollback has no completed project to restore")
    results = []
    for project_id in selected:
        try:
            result = _rollback_one(state, state_path, plan_by_id[project_id], fault=(faults or {}).get(project_id))
        except BatchProjectError as exc:
            item = state["projects"][project_id]
            item["failure"] = {"category": exc.category, "detail": str(exc)}
            _state_event(state, project_id, "rollback", "failed", exc.category)
            _save_knowledge_state(state_path, state)
            result = {"project_id": project_id, "status": "failed", "failure": item["failure"]}
        results.append(result)
    state["status"] = _summarize_knowledge_state(state)
    _save_knowledge_state(state_path, state)
    failed = sum(item["status"] == "failed" for item in results)
    passed = sum(item["status"] == "rolled-back" for item in results)
    return {
        "schema_version": KNOWLEDGE_BATCH_STATE_SCHEMA_VERSION,
        "batch_id": state["batch_id"],
        "status": "passed" if failed == 0 else "failed" if passed == 0 else "partial",
        "state": str(state_path),
        "summary": {"selected": len(results), "rolled_back": passed, "skipped": len(results) - passed - failed, "failed": failed},
        "projects": results,
    }
