"""generate、validate、rollback 的确定性编排。"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

from .contracts import CanvasFailure, CanvasSuccess, validate_instance
from .freeze import FrozenInputs, load_and_freeze_request
from .graph import (
    SelectedGraph,
    ValidationFacts,
    canonical_canvas_bytes,
    canonical_json_bytes,
    layout_graph,
    select_graph,
    validate_canvas,
)
from .transaction import (
    ArtifactBaseline,
    FaultHook,
    capture_baseline,
    cleanup_staged,
    promote_bundle,
    rollback_from_manifest,
    stage_bundle,
    verify_promoted,
)


@dataclass(frozen=True)
class RenderedBundle:
    selected: SelectedGraph
    facts: ValidationFacts
    canvas: dict[str, Any]
    canvas_bytes: bytes
    validation: dict[str, Any]
    validation_bytes: bytes
    rollback: dict[str, Any]
    rollback_bytes: bytes


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validation_manifest(
    frozen: FrozenInputs, facts: ValidationFacts, canvas_bytes: bytes
) -> dict[str, Any]:
    ckb = frozen.value["ckb"]
    value = {
        "schema_version": 1,
        "status": "passed",
        "request_sha256": frozen.request_sha256,
        "snapshot": {
            "commit": ckb["snapshot_commit"],
            "tree": ckb["snapshot_tree"],
            "state_sha256": ckb["state_sha256"],
            "machine_index_sha256": ckb["machine_index_sha256"],
            "human_projection_sha256": ckb["human_projection_sha256"],
            "human_manifest_sha256": ckb["human_manifest_sha256"],
            "local_openers_sha256": ckb["local_openers_sha256"],
        },
        "inputs": {
            "agent_pack_path": str(Path(ckb["agent_pack_path"]).resolve()),
            "agent_pack_sha256": ckb["agent_pack_sha256"],
            "record_path": str(Path(ckb["record_path"]).resolve()),
            "record_sha256": ckb["record_sha256"],
            "record_schema_version": 3,
        },
        "canvas": {"path": str(frozen.target_canvas), "sha256": _sha(canvas_bytes), "byte_length": len(canvas_bytes)},
        "node_count": facts.node_count,
        "edge_count": facts.edge_count,
        "role_counts": facts.role_counts,
        "checks": {
            "request_schema": "passed",
            "record_compatibility": "passed",
            "snapshot_consistency": "passed",
            "input_hashes": "passed",
            "path_scope": "passed",
            "canvas_schema": "passed",
            "budget": "passed",
            "stable_ids": "passed",
            "backlinks": "passed",
            "source_ranges": "passed",
            "dangling_edges": 0,
            "machine_fields_exposed": 0,
            "canonical_serialization": "passed",
        },
        "backlinks": list(facts.backlinks),
    }
    validate_instance("canvas-validation-manifest.schema.json", value)
    return value


def _rollback_manifest(
    frozen: FrozenInputs,
    baseline: ArtifactBaseline,
    canvas_bytes: bytes,
    validation_bytes: bytes,
) -> dict[str, Any]:
    actions = []
    for role in ("canvas", "validation_manifest", "rollback_manifest"):
        state = baseline.roles[role].state["state"]
        actions.append(
            {"role": role, "action": "delete" if state == "absent" else "restore", "verify": "absent" if state == "absent" else "sha256"}
        )
    value = {
        "schema_version": 1,
        "status": "ready",
        "request_sha256": frozen.request_sha256,
        "authorized_staging_root": str(frozen.staging_root),
        "backup_root": str(frozen.backup_root),
        "baseline": baseline.manifest_states(),
        "generated": {
            "canvas": {"path": str(frozen.target_canvas), "sha256": _sha(canvas_bytes)},
            "validation_manifest": {"path": str(frozen.validation_manifest), "sha256": _sha(validation_bytes)},
        },
        "rollback_manifest_path": str(frozen.rollback_manifest),
        "guard": {
            "expected_canvas_sha256": _sha(canvas_bytes),
            "expected_validation_sha256": _sha(validation_bytes),
            "expected_manifest_content_sha256": "0" * 64,
        },
        "actions": actions,
    }
    value["guard"]["expected_manifest_content_sha256"] = _sha(canonical_json_bytes(value))
    validate_instance("canvas-rollback-manifest.schema.json", value)
    return value


def _render(frozen: FrozenInputs, baseline: ArtifactBaseline) -> RenderedBundle:
    selected = select_graph(frozen)
    canvas = layout_graph(selected, frozen)
    facts = validate_canvas(canvas, frozen, selected)
    canvas_bytes = canonical_canvas_bytes(canvas)
    validation = _validation_manifest(frozen, facts, canvas_bytes)
    validation_bytes = canonical_json_bytes(validation)
    rollback = _rollback_manifest(frozen, baseline, canvas_bytes, validation_bytes)
    rollback_bytes = canonical_json_bytes(rollback)
    return RenderedBundle(
        selected,
        facts,
        canvas,
        canvas_bytes,
        validation,
        validation_bytes,
        rollback,
        rollback_bytes,
    )


def _bundle_bytes(rendered: RenderedBundle) -> dict[str, bytes]:
    return {
        "canvas": rendered.canvas_bytes,
        "validation_manifest": rendered.validation_bytes,
        "rollback_manifest": rendered.rollback_bytes,
    }


def generate(request_path: Path | str, *, fault_hook: FaultHook | None = None) -> CanvasSuccess:
    """执行 freeze → graph → baseline → stage → promote → verify。"""

    try:
        frozen = load_and_freeze_request(request_path, operation="generate")
        baseline = capture_baseline(frozen)
        rendered = _render(frozen, baseline)
        staged = stage_bundle(frozen, _bundle_bytes(rendered), fault_hook=fault_hook)
        promoted = promote_bundle(frozen, staged, baseline, fault_hook=fault_hook)
        verify_promoted(promoted, frozen=frozen, baseline=baseline)
        after = {"state": "present", "sha256": _sha(rendered.canvas_bytes)}
        result = {
            "schema_version": 1,
            "status": "passed",
            "operation": "generate",
            "exit_code": 0,
            "request_sha256": frozen.request_sha256,
            "canvas": {"path": str(frozen.target_canvas), "sha256": _sha(rendered.canvas_bytes), "byte_length": len(rendered.canvas_bytes)},
            "validation_manifest": {
                "path": str(frozen.validation_manifest),
                "sha256": _sha(rendered.validation_bytes),
                "byte_length": len(rendered.validation_bytes),
            },
            "rollback_manifest": {
                "path": str(frozen.rollback_manifest),
                "sha256": _sha(rendered.rollback_bytes),
                "byte_length": len(rendered.rollback_bytes),
            },
            "node_count": rendered.facts.node_count,
            "edge_count": rendered.facts.edge_count,
            "role_counts": rendered.facts.role_counts,
            "backlinks_checked": len(rendered.facts.backlinks),
            "dangling_edges": 0,
            "machine_fields_exposed": 0,
            "target_state": {
                "path": str(frozen.target_canvas),
                "before": baseline.roles["canvas"].state,
                "after": after,
                "changed": not (
                    baseline.roles["canvas"].state.get("state") == "present"
                    and baseline.roles["canvas"].state.get("sha256") == after["sha256"]
                ),
            },
        }
        return CanvasSuccess(result)
    except CanvasFailure as exc:
        exc.operation = "generate"
        raise


def validate_only(request_path: Path | str, *, fault_hook: FaultHook | None = None) -> dict[str, Any]:
    """执行到 staging 重开，清理临时文件且不 promotion。"""

    try:
        frozen = load_and_freeze_request(request_path, operation="validate")
        baseline = capture_baseline(frozen)
        rendered = _render(frozen, baseline)
        staged = stage_bundle(frozen, _bundle_bytes(rendered), fault_hook=fault_hook)
        cleanup_staged(staged)
        return rendered.validation
    except CanvasFailure as exc:
        exc.operation = "validate"
        raise


def rollback(manifest_path: Path | str, expected_sha256: str, *, fault_hook: FaultHook | None = None) -> dict[str, Any]:
    try:
        return rollback_from_manifest(manifest_path, expected_sha256, fault_hook=fault_hook)
    except CanvasFailure as exc:
        exc.operation = "rollback"
        raise
