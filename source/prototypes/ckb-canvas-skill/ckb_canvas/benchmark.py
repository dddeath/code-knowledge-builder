"""冻结 Markdown/Canvas block runner、judge 与七门汇总。"""

from __future__ import annotations

import json
import os
from pathlib import Path
import statistics
import tempfile
from typing import Any, Iterable

from .contracts import CanvasFailure, SchemaValidationError, validate_instance
from .graph import canonical_json_bytes


TASK_IDS = tuple(f"P{pair}{variant}" for pair in range(1, 7) for variant in ("A", "B"))
ASSIGNMENT_KEYS = (
    "sequence-1/markdown",
    "sequence-1/canvas",
    "sequence-2/markdown",
    "sequence-2/canvas",
)
SOURCE_PAIRS = {"P1", "P2", "P5"}
STOP_REASONS = {
    "missing-backlink",
    "machine-field-exposure",
    "write-outside-scope",
    "evidence-set-drift",
    "overwrite-on-drift",
    "unfrozen-environment",
    "unfrozen-task-order",
    "custom-uri-failed",
    "subpath-failed",
}


def _load_object(path: Path, *, detail: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CanvasFailure(
            "invalid_request", "benchmark", f"{detail}: {path}: {exc}", operation="benchmark", target_path=str(path)
        ) from exc
    if not isinstance(value, dict):
        raise CanvasFailure(
            "invalid_request", "benchmark", f"{detail} root must be an object", operation="benchmark", target_path=str(path)
        )
    return value


def validate_run(value: dict[str, Any]) -> None:
    """校验 benchmark schema 与 12 task/4 assignment/evidence 语义。"""

    try:
        validate_instance("benchmark-run.schema.json", value)
    except SchemaValidationError as exc:
        raise CanvasFailure(
            "invalid_request", "benchmark", f"benchmark run schema failed: {exc}", operation="benchmark", target_path="BENCHMARK-RUN.json"
        ) from exc
    task_ids = [item["task_id"] for item in value["tasks"]]
    if len(task_ids) != 12 or set(task_ids) != set(TASK_IDS) or len(task_ids) != len(set(task_ids)):
        raise CanvasFailure(
            "invalid_request", "benchmark", "runner must contain exactly 12 unique frozen tasks", operation="benchmark", target_path="BENCHMARK-RUN.json"
        )
    assignments = {(item["sequence_id"], item["condition"]): item for item in value["assignments"]}
    expected_assignments = {
        ("sequence-1", "markdown"),
        ("sequence-1", "canvas"),
        ("sequence-2", "markdown"),
        ("sequence-2", "canvas"),
    }
    if set(assignments) != expected_assignments or len(value["assignments"]) != 4:
        raise CanvasFailure(
            "invalid_request", "benchmark", "runner must contain four unique assignments", operation="benchmark", target_path="BENCHMARK-RUN.json"
        )
    for key, item in assignments.items():
        order = item["task_order"]
        if len(order) != 6 or len(set(order)) != 6 or not set(order).issubset(TASK_IDS):
            raise CanvasFailure(
                "invalid_request", "benchmark", f"assignment {key} must contain six unique tasks", operation="benchmark", target_path="BENCHMARK-RUN.json"
            )
    for sequence in ("sequence-1", "sequence-2"):
        combined = assignments[(sequence, "markdown")]["task_order"] + assignments[(sequence, "canvas")]["task_order"]
        if len(combined) != 12 or set(combined) != set(TASK_IDS):
            raise CanvasFailure(
                "invalid_request", "benchmark", f"{sequence} does not cover all 12 tasks exactly once", operation="benchmark", target_path="BENCHMARK-RUN.json"
            )
    for condition in ("markdown", "canvas"):
        combined = assignments[("sequence-1", condition)]["task_order"] + assignments[("sequence-2", condition)]["task_order"]
        if len(combined) != 12 or set(combined) != set(TASK_IDS):
            raise CanvasFailure(
                "invalid_request", "benchmark", f"{condition} does not cover all 12 tasks exactly once", operation="benchmark", target_path="BENCHMARK-RUN.json"
            )
    evidence = value["freeze"]["human_evidence_sha256"]
    if not (
        evidence
        == value["freeze"]["source_evidence_sha256"]
        == value["conditions"]["markdown"]["evidence_set_sha256"]
        == value["conditions"]["canvas"]["evidence_set_sha256"]
    ):
        raise CanvasFailure(
            "input_drift", "benchmark", "Markdown and Canvas evidence hashes differ", operation="benchmark", target_path="BENCHMARK-RUN.json"
        )
    if (
        value["freeze"]["budget"] != {"max_nodes": 12, "max_edges": 16}
        or value["conditions"]["canvas"]["max_nodes"] != 12
        or value["conditions"]["canvas"]["max_edges"] != 16
    ):
        raise CanvasFailure(
            "invalid_request", "benchmark", "runner budget differs from frozen Canvas budget", operation="benchmark", target_path="BENCHMARK-RUN.json"
        )


def load_run(path: Path | str) -> dict[str, Any]:
    value = _load_object(Path(path), detail="benchmark run cannot be loaded")
    validate_run(value)
    return value


def _assignment(run: dict[str, Any], sequence_id: str, condition: str) -> dict[str, Any]:
    for item in run["assignments"]:
        if item["sequence_id"] == sequence_id and item["condition"] == condition:
            return item
    raise CanvasFailure(
        "invalid_request", "benchmark", f"assignment is missing: {sequence_id}/{condition}", operation="benchmark", target_path="BENCHMARK-RUN.json"
    )


def _stopped_result(run: dict[str, Any], capture: dict[str, Any], reason: str) -> dict[str, Any]:
    value = {
        "schema_version": 1,
        "status": "stopped",
        "run_id": run["run_id"],
        "session_id": str(capture.get("session_id") or "SESSION"),
        "sequence_id": capture.get("sequence_id") if capture.get("sequence_id") in {"sequence-1", "sequence-2"} else "sequence-1",
        "condition": capture.get("condition") if capture.get("condition") in {"markdown", "canvas"} else "markdown",
        "participant_slot": str(capture.get("participant_slot") or "PARTICIPANT"),
        "environment_verified": bool(capture.get("environment_verified", False)),
        "task_order": list(capture.get("task_order") or _assignment(run, "sequence-1", "markdown")["task_order"]),
        "observations": [],
        "stop_reason": reason,
    }
    validate_instance("benchmark-session-result.schema.json", value)
    return value


def judge_session(run: dict[str, Any], captured: dict[str, Any]) -> dict[str, Any]:
    """按冻结答案页、来源范围和任务顺序判定一个 condition block。"""

    required_capture = {
        "schema_version",
        "session_id",
        "sequence_id",
        "condition",
        "participant_slot",
        "environment_verified",
        "task_order",
        "observations",
        "stop_reason",
    }
    if set(captured) != required_capture or captured.get("schema_version") != 1:
        raise CanvasFailure(
            "invalid_request", "benchmark", "session capture has unknown or missing fields", operation="benchmark", target_path="SESSION.json"
        )
    sequence = captured["sequence_id"]
    condition = captured["condition"]
    assignment = _assignment(run, sequence, condition)
    if run["environment"]["obsidian_version"] == "OBSIDIAN_VERSION" or not captured["environment_verified"]:
        return _stopped_result(run, captured, "unfrozen-environment")
    if captured["task_order"] != assignment["task_order"]:
        return _stopped_result(run, captured, "unfrozen-task-order")
    if captured["stop_reason"] is not None:
        if captured["stop_reason"] not in STOP_REASONS:
            raise CanvasFailure(
                "invalid_request", "benchmark", "session capture has an unknown stop reason", operation="benchmark", target_path="SESSION.json"
            )
        return _stopped_result(run, captured, captured["stop_reason"])
    raw_by_id = {item.get("task_id"): item for item in captured["observations"] if isinstance(item, dict)}
    if len(raw_by_id) != 6 or set(raw_by_id) != set(assignment["task_order"]):
        raise CanvasFailure(
            "invalid_request", "benchmark", "session observations do not match the six-task assignment", operation="benchmark", target_path="SESSION.json"
        )
    tasks = {item["task_id"]: item for item in run["tasks"]}
    judged: list[dict[str, Any]] = []
    for task_id in assignment["task_order"]:
        raw = raw_by_id[task_id]
        allowed = {
            "task_id",
            "elapsed_seconds",
            "first_correct_entry_seconds",
            "navigation_count",
            "backtrack_count",
            "comprehension_score",
            "unsupported_assertions",
            "submitted_page",
            "submitted_source_path",
            "submitted_start_line",
            "submitted_end_line",
        }
        if set(raw) != allowed:
            raise CanvasFailure(
                "invalid_request", "benchmark", f"observation {task_id} has unknown or missing fields", operation="benchmark", target_path="SESSION.json"
            )
        expected = tasks[task_id]["expected"]
        elapsed = float(raw["elapsed_seconds"])
        page_match = raw["submitted_page"] == expected["page"]
        source_required = task_id[:2] in SOURCE_PAIRS
        source_match = (
            raw["submitted_source_path"] == expected["source_path"]
            and raw["submitted_start_line"] == expected["start_line"]
            and raw["submitted_end_line"] == expected["end_line"]
        )
        success = elapsed <= tasks[task_id]["timeout_seconds"] and page_match and (not source_required or source_match)
        comprehension = int(raw["comprehension_score"]) if success else 0
        comprehension = max(0, min(2, comprehension))
        judged.append(
            {
                "task_id": task_id,
                "success": success,
                "elapsed_seconds": elapsed,
                "first_correct_entry_seconds": raw["first_correct_entry_seconds"] if success else None,
                "navigation_count": int(raw["navigation_count"]),
                "backtrack_count": int(raw["backtrack_count"]),
                "comprehension_score": comprehension,
                "source_verified": source_match if source_required else None,
                "unsupported_assertions": int(raw["unsupported_assertions"]),
                "submitted_page": raw["submitted_page"],
                "submitted_source_path": raw["submitted_source_path"],
                "submitted_start_line": raw["submitted_start_line"],
                "submitted_end_line": raw["submitted_end_line"],
            }
        )
    value = {
        "schema_version": 1,
        "status": "passed",
        "run_id": run["run_id"],
        "session_id": captured["session_id"],
        "sequence_id": sequence,
        "condition": condition,
        "participant_slot": captured["participant_slot"],
        "environment_verified": True,
        "task_order": list(assignment["task_order"]),
        "observations": judged,
        "stop_reason": None,
    }
    validate_instance("benchmark-session-result.schema.json", value)
    return value


def run_session(run_path: Path | str, session_id: Path | str) -> dict[str, Any]:
    """读取一个明确 capture 文件；不扫描 session 目录或随机化任务。"""

    run_path = Path(run_path)
    run = load_run(run_path)
    supplied = Path(session_id)
    capture_path = supplied if supplied.is_file() else run_path.parent / "sessions" / f"{session_id}.capture.json"
    if not capture_path.is_file():
        raise CanvasFailure(
            "missing_target", "benchmark", f"session capture is missing: {capture_path}", operation="benchmark", target_path=str(capture_path)
        )
    capture = _load_object(capture_path, detail="session capture cannot be loaded")
    if str(session_id) != str(capture_path) and capture.get("session_id") != str(session_id):
        raise CanvasFailure(
            "invalid_request", "benchmark", "session id does not match capture", operation="benchmark", target_path=str(capture_path)
        )
    return judge_session(run, capture)


def _metric_triplet(markdown: float, canvas: float) -> dict[str, float]:
    return {"markdown": round(markdown, 10), "canvas": round(canvas, 10), "delta": round(canvas - markdown, 10)}


def _median(values: Iterable[float]) -> float:
    items = list(values)
    return float(statistics.median(items)) if items else 0.0


def _summary_index(path: Path) -> dict[str, Any]:
    value = _load_object(path, detail="session index cannot be loaded")
    required = {
        "schema_version",
        "files",
        "structure",
        "rollback_probes_passed",
        "deterministic_hashes",
        "validation_manifest_hashes",
        "rollback_manifest_hashes",
    }
    if set(value) != required or value.get("schema_version") != 1:
        raise CanvasFailure(
            "invalid_request", "benchmark", "session index has unknown or missing fields", operation="benchmark", target_path=str(path)
        )
    if not isinstance(value["files"], list) or len(value["files"]) != len(set(value["files"])):
        raise CanvasFailure(
            "invalid_request", "benchmark", "session index files must be a unique array", operation="benchmark", target_path=str(path)
        )
    structure_required = {"node_count", "edge_count", "dangling_edges", "missing_backlinks", "machine_fields_exposed", "overlap_count"}
    if not isinstance(value["structure"], dict) or set(value["structure"]) != structure_required:
        raise CanvasFailure(
            "invalid_request", "benchmark", "session index structure is invalid", operation="benchmark", target_path=str(path)
        )
    return value


def summarize(run: dict[str, Any], sessions: list[dict[str, Any]], evidence: dict[str, Any]) -> dict[str, Any]:
    """只使用环境/顺序有效 block 计算指标和七门。"""

    validate_run(run)
    for session in sessions:
        try:
            validate_instance("benchmark-session-result.schema.json", session)
        except SchemaValidationError as exc:
            raise CanvasFailure(
                "invalid_request", "benchmark", f"session result schema failed: {exc}", operation="benchmark", target_path="SESSION.json"
            ) from exc
        if session["run_id"] != run["run_id"]:
            raise CanvasFailure(
                "input_drift", "benchmark", "session run_id differs from frozen run", operation="benchmark", target_path="SESSION.json"
            )
    stopped = [item for item in sessions if item["status"] == "stopped"]
    valid: list[dict[str, Any]] = []
    for item in sessions:
        assignment = _assignment(run, item["sequence_id"], item["condition"])
        if (
            item["status"] == "passed"
            and item["environment_verified"]
            and item["task_order"] == assignment["task_order"]
            and item["stop_reason"] is None
        ):
            valid.append(item)

    blocks = {key: 0 for key in ASSIGNMENT_KEYS}
    for item in valid:
        blocks[f"{item['sequence_id']}/{item['condition']}"] += 1
    session_groups: dict[tuple[str, str], set[str]] = {}
    for item in valid:
        session_groups.setdefault((item["sequence_id"], item["session_id"]), set()).add(item["condition"])
    independent = {(sequence, session) for (sequence, session), conditions in session_groups.items() if conditions == {"markdown", "canvas"}}
    sessions_by_sequence = {
        sequence: sum(1 for value in independent if value[0] == sequence) for sequence in ("sequence-1", "sequence-2")
    }

    observations = {"markdown": [], "canvas": []}
    for item in valid:
        observations[item["condition"]].extend(item["observations"])

    def condition_metrics(condition: str) -> dict[str, float]:
        rows = observations[condition]
        successful = [item for item in rows if item["success"]]
        source_rows = [item for item in rows if item["source_verified"] is not None]
        return {
            "success": sum(1 for item in rows if item["success"]) / len(rows) if rows else 0.0,
            "first": _median(float(item["first_correct_entry_seconds"]) for item in successful if item["first_correct_entry_seconds"] is not None),
            "navigation": _median(float(item["navigation_count"]) for item in rows),
            "comprehension": sum(item["comprehension_score"] for item in rows) / (2 * len(rows)) * 100 if rows else 0.0,
            "source": sum(1 for item in source_rows if item["source_verified"]) / len(source_rows) if source_rows else 0.0,
            "unsupported": float(sum(item["unsupported_assertions"] for item in rows)),
        }

    markdown = condition_metrics("markdown")
    canvas = condition_metrics("canvas")
    metrics = {
        "discoverability_success_rate": _metric_triplet(markdown["success"], canvas["success"]),
        "median_first_correct_entry_seconds": _metric_triplet(markdown["first"], canvas["first"]),
        "median_navigation_count": _metric_triplet(markdown["navigation"], canvas["navigation"]),
        "mean_comprehension_percent": _metric_triplet(markdown["comprehension"], canvas["comprehension"]),
        "source_verification_rate": _metric_triplet(markdown["source"], canvas["source"]),
        "unsupported_assertions": _metric_triplet(markdown["unsupported"], canvas["unsupported"]),
    }
    structure = evidence["structure"]
    structural_pass = (
        structure["node_count"] <= 12
        and structure["edge_count"] <= 16
        and structure["dangling_edges"] == 0
        and structure["missing_backlinks"] == 0
        and structure["machine_fields_exposed"] == 0
    )
    source_pass = (
        markdown["source"] == 1.0
        and canvas["source"] == 1.0
        and markdown["unsupported"] == 0
        and canvas["unsupported"] == 0
    )
    task_pass = (
        markdown["success"] >= run["gates"]["minimum_discoverability_success_rate"]
        and canvas["success"] >= run["gates"]["minimum_discoverability_success_rate"]
        and canvas["success"] >= markdown["success"]
    )
    comprehension_pass = canvas["comprehension"] >= markdown["comprehension"] - run["gates"]["maximum_comprehension_drop_percentage_points"]
    time_reduction = (markdown["first"] - canvas["first"]) / markdown["first"] if markdown["first"] > 0 else 0.0
    nav_reduction = (markdown["navigation"] - canvas["navigation"]) / markdown["navigation"] if markdown["navigation"] > 0 else 0.0
    efficiency_pass = (
        time_reduction >= run["gates"]["minimum_median_time_reduction"]
        or nav_reduction >= run["gates"]["minimum_median_navigation_reduction"]
    )
    rollback_pass = evidence["rollback_probes_passed"] == 3
    hashes = evidence["deterministic_hashes"]
    stability_pass = (
        len(hashes) == 10
        and len(set(hashes)) == 1
        and len(evidence["validation_manifest_hashes"]) == 10
        and len(set(evidence["validation_manifest_hashes"])) == 1
        and len(evidence["rollback_manifest_hashes"]) == 10
        and len(set(evidence["rollback_manifest_hashes"])) == 1
    )
    enough = (
        sessions_by_sequence["sequence-1"] >= run["session_policy"]["minimum_independent_sessions_per_sequence"]
        and sessions_by_sequence["sequence-2"] >= run["session_policy"]["minimum_independent_sessions_per_sequence"]
        and all(value >= run["session_policy"]["minimum_blocks_per_assignment"] for value in blocks.values())
    )
    gate_values = [
        ("structure", structural_pass, f"nodes={structure['node_count']}, edges={structure['edge_count']}, dangling={structure['dangling_edges']}"),
        ("source", source_pass, f"Markdown={markdown['source']:.10f}, Canvas={canvas['source']:.10f}, unsupported={markdown['unsupported'] + canvas['unsupported']:.0f}"),
        ("task", task_pass, f"Markdown={markdown['success']:.10f}, Canvas={canvas['success']:.10f}"),
        ("comprehension", comprehension_pass, f"Markdown={markdown['comprehension']:.4f}, Canvas={canvas['comprehension']:.4f}"),
        ("efficiency", efficiency_pass, f"time_reduction={time_reduction:.10f}, navigation_reduction={nav_reduction:.10f}"),
        ("rollback", rollback_pass, f"rollback probes={evidence['rollback_probes_passed']}/3"),
        ("stability", stability_pass, f"Canvas hashes={len(set(hashes)) if hashes else 0}, validation hashes={len(set(evidence['validation_manifest_hashes']))}, rollback hashes={len(set(evidence['rollback_manifest_hashes']))}"),
    ]
    if stopped:
        status = "stopped"
        decision = "return-to-design"
    elif not enough:
        status = "insufficient-data"
        decision = "collect-more-sessions"
    elif all(item[1] for item in gate_values):
        status = "passed"
        decision = "advance-to-product-decision"
    elif structural_pass and source_pass and comprehension_pass and not efficiency_pass:
        status = "failed"
        decision = "keep-markdown-default"
    else:
        status = "failed"
        decision = "return-to-design"
    gates = [
        {"gate": name, "status": "not-run" if not enough and not stopped else ("passed" if passed else "failed"), "evidence": evidence_text}
        for name, passed, evidence_text in gate_values
    ]
    value = {
        "schema_version": 1,
        "status": status,
        "run_id": run["run_id"],
        "sessions_by_sequence": sessions_by_sequence,
        "metrics": metrics,
        "structure": structure,
        "rollback_probes_passed": evidence["rollback_probes_passed"],
        "deterministic_hashes": list(hashes),
        "gates": gates,
        "decision": decision,
        "valid_independent_sessions": len(independent),
        "valid_condition_blocks": len(valid),
        "blocks_by_assignment": blocks,
    }
    validate_instance("benchmark-summary.schema.json", value)
    return value


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if path.read_bytes() != data:
            raise OSError("summary reopen bytes differ")
    finally:
        Path(temporary).unlink(missing_ok=True)


def summarize_to_path(run_path: Path | str, sessions_path: Path | str, write_path: Path | str) -> dict[str, Any]:
    run = load_run(run_path)
    sessions_root = Path(sessions_path).resolve(strict=True)
    index = _summary_index(sessions_root / "index.json")
    sessions: list[dict[str, Any]] = []
    for relative in index["files"]:
        pure = Path(relative)
        if pure.is_absolute() or ".." in pure.parts:
            raise CanvasFailure(
                "source_outside_scope", "benchmark", f"session file is outside root: {relative}", operation="benchmark", target_path=str(sessions_root)
            )
        path = (sessions_root / pure).resolve(strict=True)
        if os.path.commonpath([os.path.normcase(str(path)), os.path.normcase(str(sessions_root))]) != os.path.normcase(str(sessions_root)):
            raise CanvasFailure(
                "source_outside_scope", "benchmark", f"session file resolves outside root: {relative}", operation="benchmark", target_path=str(sessions_root)
            )
        sessions.append(_load_object(path, detail="session result cannot be loaded"))
    value = summarize(run, sessions, index)
    output = Path(write_path).resolve()
    _atomic_write(output, canonical_json_bytes(value))
    return value
