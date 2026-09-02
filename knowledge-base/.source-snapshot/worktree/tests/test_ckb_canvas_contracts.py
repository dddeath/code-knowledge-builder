from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "prototypes" / "ckb-canvas-skill"
FIXTURE = REPO / "tests" / "fixtures" / "obsidian-canvas-agent-visualization"
DESIGN = REPO / "references" / "design" / "obsidian-canvas-agent-visualization"
sys.path[:0] = [str(REPO), str(SKILL), str(FIXTURE)]

from ckb_canvas.commands import validate_only
from ckb_canvas.contracts import CanvasFailure, SCHEMA_NAMES, validate_instance
from runtime_builder import build_acceptance_runtime, build_case, sha256, write_json


def setUpModule() -> None:
    build_acceptance_runtime()


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "ckb_canvas.py"), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )


class CanvasContractTests(unittest.TestCase):
    def test_all_nine_schemas_parse_and_match_design(self) -> None:
        self.assertEqual(9, len(SCHEMA_NAMES))
        for name in sorted(SCHEMA_NAMES):
            design = DESIGN / "schemas" / name
            prototype = SKILL / "schemas" / name
            json.loads(design.read_text(encoding="utf-8"))
            json.loads(prototype.read_text(encoding="utf-8"))
            self.assertEqual(design.read_bytes(), prototype.read_bytes(), name)
            self.assertEqual(hashlib.sha256(design.read_bytes()).hexdigest(), hashlib.sha256(prototype.read_bytes()).hexdigest())

    def test_design_success_and_failure_fixtures_validate(self) -> None:
        success = FIXTURE / "expected"
        validate_instance("canvas-request.schema.json", json.loads((success / "canvas-request.json").read_text(encoding="utf-8")))
        validate_instance("canvas-success.schema.json", json.loads((success / "canvas-success.json").read_text(encoding="utf-8")))
        validate_instance(
            "canvas-validation-manifest.schema.json",
            json.loads((success / "ckb-navigation.canvas.validation.json").read_text(encoding="utf-8")),
        )
        validate_instance(
            "canvas-rollback-manifest.schema.json",
            json.loads((success / "ckb-navigation.canvas.rollback.json").read_text(encoding="utf-8")),
        )
        validate_instance(
            "json-canvas-1.0-ckb-subset.schema.json",
            json.loads((success / "ckb-navigation.canvas").read_text(encoding="utf-8")),
        )
        catalog = json.loads((DESIGN / "fixtures" / "failure-catalog.json").read_text(encoding="utf-8"))
        expected_reasons = {item["reason"] for item in catalog["failures"]}
        actual_reasons: set[str] = set()
        for path in sorted((FIXTURE / "failure-results").glob("*.json")):
            design_path = DESIGN / "fixtures" / "failure-results" / path.name
            self.assertEqual(design_path.read_bytes(), path.read_bytes(), path.name)
            value = json.loads(path.read_text(encoding="utf-8"))
            validate_instance("canvas-failure.schema.json", value)
            actual_reasons.add(value["reason"])
        self.assertEqual(expected_reasons, actual_reasons)
        self.assertEqual(17, len(actual_reasons))

    def test_each_request_object_layer_rejects_unknown_field_with_exit_2(self) -> None:
        case = build_case("unknown-fields")
        try:
            base = case.request_value()

            def variants():
                value = copy.deepcopy(base); value["unknown"] = 1; yield value
                value = copy.deepcopy(base); value["ckb"]["unknown"] = 1; yield value
                value = copy.deepcopy(base); value["ckb"]["frozen_evidence"]["unknown"] = 1; yield value
                value = copy.deepcopy(base); value["ckb"]["frozen_evidence"]["human_files"][0]["unknown"] = 1; yield value
                value = copy.deepcopy(base); value["ckb"]["frozen_evidence"]["source_files"][0]["unknown"] = 1; yield value
                value = copy.deepcopy(base); value["request"]["unknown"] = 1; yield value
                value = copy.deepcopy(base); value["request"]["baseline"]["unknown"] = 1; yield value
                value = copy.deepcopy(base); value["request"]["baseline"]["canvas"]["unknown"] = 1; yield value
                value = copy.deepcopy(base); value["request"]["required_entries"][0]["unknown"] = 1; yield value
                value = copy.deepcopy(base); value["budget"]["unknown"] = 1; yield value

            for index, value in enumerate(variants()):
                with self.subTest(layer=index):
                    case.write_request(value)
                    completed = run_cli("validate", "--request", str(case.request))
                    self.assertEqual(2, completed.returncode, completed.stderr)
                    result = json.loads(completed.stdout)
                    self.assertEqual("invalid_request", result["reason"])
                    self.assertFalse(case.staging.joinpath("ckb-navigation.canvas").exists())
        finally:
            case.cleanup()

    def _assert_record_rejected(self, mutate) -> None:
        case = build_case("record-rejected")
        try:
            record = json.loads(case.record.read_text(encoding="utf-8"))
            mutate(record)
            write_json(case.record, record)
            request = case.request_value()
            request["ckb"]["record_sha256"] = sha256(case.record)
            case.write_request(request)
            with self.assertRaises(CanvasFailure) as raised:
                validate_only(case.request)
            self.assertEqual("unsupported_record_schema", raised.exception.reason)
            self.assertEqual(2, raised.exception.exit_code)
        finally:
            case.cleanup()

    def test_record_1_keyword_variant_and_unknown_candidate_rejected(self) -> None:
        self._assert_record_rejected(lambda value: value.__setitem__("schema_version", 1))
        self._assert_record_rejected(lambda value: value.__setitem__("keyword_fallback", {"status": "passed"}))
        self._assert_record_rejected(lambda value: value["selected_entities"][0].__setitem__("unknown", 1))

    def test_pack_record_crosslink_is_exact(self) -> None:
        case = build_case("pack-record-mismatch")
        try:
            record = json.loads(case.record.read_text(encoding="utf-8"))
            record["pack"] = str(case.pack.with_name("other.md"))
            write_json(case.record, record)
            request = case.request_value()
            request["ckb"]["record_sha256"] = sha256(case.record)
            case.write_request(request)
            with self.assertRaises(CanvasFailure) as raised:
                validate_only(case.request)
            self.assertEqual("pack_record_mismatch", raised.exception.reason)
        finally:
            case.cleanup()

    def test_acceptance_runtime_request_is_valid(self) -> None:
        case = build_acceptance_runtime()
        result = validate_only(case.request)
        self.assertEqual("passed", result["status"])
        self.assertEqual(4, result["node_count"])
        self.assertEqual(3, result["edge_count"])


if __name__ == "__main__":
    unittest.main()
