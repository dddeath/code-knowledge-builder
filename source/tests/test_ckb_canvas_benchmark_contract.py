from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "prototypes" / "ckb-canvas-skill"
FIXTURE = REPO / "tests" / "fixtures" / "obsidian-canvas-agent-visualization"
BENCHMARK = FIXTURE / "benchmark"
sys.path[:0] = [str(REPO), str(SKILL), str(FIXTURE)]

from ckb_canvas.benchmark import judge_session, load_run, run_session, summarize_to_path, validate_run
from ckb_canvas.contracts import CanvasFailure, validate_instance
from ckb_canvas.graph import canonical_json_bytes


def _capture(
    run: dict,
    sequence: str,
    condition: str,
    session_id: str,
    participant: str,
    *,
    first_seconds: float,
    navigation: int,
) -> dict:
    assignment = next(
        item for item in run["assignments"] if item["sequence_id"] == sequence and item["condition"] == condition
    )
    tasks = {item["task_id"]: item for item in run["tasks"]}
    observations = []
    for task_id in assignment["task_order"]:
        expected = tasks[task_id]["expected"]
        observations.append(
            {
                "task_id": task_id,
                "elapsed_seconds": first_seconds + 10,
                "first_correct_entry_seconds": first_seconds,
                "navigation_count": navigation,
                "backtrack_count": 0,
                "comprehension_score": 2,
                "unsupported_assertions": 0,
                "submitted_page": expected["page"],
                "submitted_source_path": expected["source_path"],
                "submitted_start_line": expected["start_line"],
                "submitted_end_line": expected["end_line"],
            }
        )
    return {
        "schema_version": 1,
        "session_id": session_id,
        "sequence_id": sequence,
        "condition": condition,
        "participant_slot": participant,
        "environment_verified": True,
        "task_order": list(assignment["task_order"]),
        "observations": observations,
        "stop_reason": None,
    }


class CanvasBenchmarkContractTests(unittest.TestCase):
    def test_frozen_run_has_12_tasks_four_assignments_and_equal_evidence(self) -> None:
        run = load_run(BENCHMARK / "benchmark-run.json")
        self.assertEqual(12, len(run["tasks"]))
        self.assertEqual(12, len({item["task_id"] for item in run["tasks"]}))
        self.assertEqual(4, len(run["assignments"]))
        self.assertTrue(all(len(item["task_order"]) == len(set(item["task_order"])) == 6 for item in run["assignments"]))
        task_ids = {item["task_id"] for item in run["tasks"]}
        for sequence in ("sequence-1", "sequence-2"):
            combined = [
                task
                for item in run["assignments"]
                if item["sequence_id"] == sequence
                for task in item["task_order"]
            ]
            self.assertEqual(task_ids, set(combined))
            self.assertEqual(12, len(combined))
        for condition in ("markdown", "canvas"):
            combined = [
                task for item in run["assignments"] if item["condition"] == condition for task in item["task_order"]
            ]
            self.assertEqual(task_ids, set(combined))
            self.assertEqual(12, len(combined))
        evidence = run["freeze"]["human_evidence_sha256"]
        self.assertEqual(evidence, run["freeze"]["source_evidence_sha256"])
        self.assertEqual(evidence, run["conditions"]["markdown"]["evidence_set_sha256"])
        self.assertEqual(evidence, run["conditions"]["canvas"]["evidence_set_sha256"])
        self.assertEqual({"max_nodes": 12, "max_edges": 16}, run["freeze"]["budget"])

    def test_design_session_and_summary_examples_are_schema_valid_only(self) -> None:
        validate_instance(
            "benchmark-session-result.schema.json",
            json.loads((BENCHMARK / "benchmark-session-result.json").read_text(encoding="utf-8")),
        )
        validate_instance(
            "benchmark-summary.schema.json",
            json.loads((BENCHMARK / "benchmark-summary.json").read_text(encoding="utf-8")),
        )

    def test_unfilled_obsidian_version_stops_session(self) -> None:
        result = run_session(BENCHMARK / "benchmark-run.json", BENCHMARK / "session-capture.json")
        self.assertEqual("stopped", result["status"])
        self.assertEqual("unfrozen-environment", result["stop_reason"])
        self.assertEqual([], result["observations"])

    def test_judge_owns_page_source_and_range_verdict(self) -> None:
        run = load_run(BENCHMARK / "benchmark-run.json")
        run = copy.deepcopy(run)
        run["environment"]["obsidian_version"] = "1.8.10"
        capture = _capture(run, "sequence-1", "markdown", "S1", "P1", first_seconds=40, navigation=5)
        capture["observations"][0]["submitted_page"] = "INDEX.md" if capture["observations"][0]["submitted_page"] != "INDEX.md" else "WIKI.md"
        result = judge_session(run, capture)
        self.assertFalse(result["observations"][0]["success"])
        self.assertEqual(0, result["observations"][0]["comprehension_score"])

    def test_summary_passes_only_with_four_independent_sessions_and_all_seven_gates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-canvas-benchmark-") as temporary:
            root = Path(temporary)
            run = load_run(BENCHMARK / "benchmark-run.json")
            run = copy.deepcopy(run)
            run["environment"]["obsidian_version"] = "1.8.10"
            run_path = root / "benchmark-run.json"
            run_path.write_bytes(canonical_json_bytes(run))
            sessions_root = root / "sessions"
            sessions_root.mkdir()
            files: list[str] = []
            for sequence, slots in (("sequence-1", ("S1", "S2")), ("sequence-2", ("S3", "S4"))):
                for slot in slots:
                    for condition in ("markdown", "canvas"):
                        capture = _capture(
                            run,
                            sequence,
                            condition,
                            slot,
                            f"participant-{slot}",
                            first_seconds=40 if condition == "markdown" else 30,
                            navigation=5 if condition == "markdown" else 4,
                        )
                        result = judge_session(run, capture)
                        name = f"{slot}-{condition}.json"
                        (sessions_root / name).write_bytes(canonical_json_bytes(result))
                        files.append(name)
            evidence = {
                "schema_version": 1,
                "files": files,
                "structure": {
                    "node_count": 4,
                    "edge_count": 3,
                    "dangling_edges": 0,
                    "missing_backlinks": 0,
                    "machine_fields_exposed": 0,
                    "overlap_count": 0,
                },
                "rollback_probes_passed": 3,
                "deterministic_hashes": ["3" * 64] * 10,
                "validation_manifest_hashes": ["4" * 64] * 10,
                "rollback_manifest_hashes": ["5" * 64] * 10,
            }
            (sessions_root / "index.json").write_bytes(canonical_json_bytes(evidence))
            summary_path = root / "summary.json"
            summary = summarize_to_path(run_path, sessions_root, summary_path)
            self.assertEqual("passed", summary["status"])
            self.assertEqual("advance-to-product-decision", summary["decision"])
            self.assertEqual(4, summary["valid_independent_sessions"])
            self.assertEqual(8, summary["valid_condition_blocks"])
            self.assertEqual({"passed"}, {item["status"] for item in summary["gates"]})
            self.assertEqual(summary, json.loads(summary_path.read_text(encoding="utf-8")))

    def test_runner_rejects_evidence_drift(self) -> None:
        run = load_run(BENCHMARK / "benchmark-run.json")
        run = copy.deepcopy(run)
        run["conditions"]["canvas"]["evidence_set_sha256"] = "0" * 64
        with self.assertRaises(CanvasFailure) as raised:
            validate_run(run)
        self.assertEqual("input_drift", raised.exception.reason)

    def test_benchmark_cli_stdout_is_one_schema_object(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SKILL / "scripts" / "ckb_canvas.py"),
                "benchmark",
                "--run",
                str(BENCHMARK / "benchmark-run.json"),
                "--session",
                str(BENCHMARK / "session-capture.json"),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        value = json.loads(completed.stdout)
        validate_instance("benchmark-session-result.schema.json", value)
        self.assertEqual("stopped", value["status"])


if __name__ == "__main__":
    unittest.main()
