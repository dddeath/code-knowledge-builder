from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "prototypes" / "ckb-canvas-skill"
FIXTURE = REPO / "tests" / "fixtures" / "obsidian-canvas-agent-visualization"
sys.path[:0] = [str(REPO), str(SKILL), str(FIXTURE)]

from ckb_canvas.commands import generate, validate_only
from ckb_canvas.contracts import CanvasFailure
from runtime_builder import build_case, sha256, write_json


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "ckb_canvas.py"), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )


class CanvasPathTests(unittest.TestCase):
    def test_chinese_paths_generate_and_reopen(self) -> None:
        case = build_case("中文路径成功")
        try:
            result = generate(case.request).to_dict()
            self.assertEqual("passed", result["status"])
            self.assertIn("交付暂存", result["canvas"]["path"])
            self.assertEqual(result["canvas"]["sha256"], sha256(Path(result["canvas"]["path"])))
        finally:
            case.cleanup()

    def test_250_to_259_character_target_is_complete_or_stable_io_failure(self) -> None:
        case = build_case("long-path", long_target=True)
        try:
            target_length = len(str(case.target))
            self.assertGreaterEqual(target_length, 250)
            self.assertLessEqual(target_length, 259)
            try:
                result = generate(case.request).to_dict()
            except CanvasFailure as exc:
                self.assertEqual("io_failure", exc.reason)
                self.assertEqual(7, exc.exit_code)
                self.assertFalse(case.target.exists())
            else:
                self.assertEqual("passed", result["status"])
                self.assertEqual(result["canvas"]["sha256"], sha256(Path(result["canvas"]["path"])))
        finally:
            case.cleanup()

    def test_inside_link_is_allowed_and_outside_link_is_rejected(self) -> None:
        inside = build_case("link-inside", link_mode="inside")
        try:
            result = generate(inside.request).to_dict()
            self.assertEqual("passed", result["status"])
            self.assertTrue(Path(result["canvas"]["path"]).is_file())
            self.assertTrue(str(Path(result["canvas"]["path"]).resolve()).startswith(str(inside.staging.resolve())))
        finally:
            inside.cleanup()

        outside = build_case("link-outside", link_mode="outside")
        try:
            with self.assertRaises(CanvasFailure) as raised:
                validate_only(outside.request)
            self.assertEqual("source_outside_scope", raised.exception.reason)
            self.assertEqual(2, raised.exception.exit_code)
            self.assertFalse(outside.target.exists())
        finally:
            outside.cleanup()

    def test_corrupt_request_and_record_emit_one_failure_object_without_traceback(self) -> None:
        request_case = build_case("corrupt-request")
        try:
            request_case.request.write_bytes(b'{"schema_version":1')
            completed = run_cli("validate", "--request", str(request_case.request))
            self.assertEqual(2, completed.returncode)
            result = json.loads(completed.stdout)
            self.assertEqual("invalid_request", result["reason"])
            self.assertNotIn("Traceback", completed.stderr)
        finally:
            request_case.cleanup()

        record_case = build_case("corrupt-record")
        try:
            record_case.record.write_bytes(b'{"schema_version":3')
            request = record_case.request_value()
            request["ckb"]["record_sha256"] = sha256(record_case.record)
            record_case.write_request(request)
            completed = run_cli("validate", "--request", str(record_case.request))
            self.assertEqual(2, completed.returncode)
            result = json.loads(completed.stdout)
            self.assertEqual("unsupported_record_schema", result["reason"])
            self.assertNotIn("Traceback", completed.stderr)
        finally:
            record_case.cleanup()

    def test_snapshot_and_evidence_drift_have_distinct_reasons(self) -> None:
        snapshot_case = build_case("snapshot-mismatch")
        try:
            state_path = snapshot_case.output / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["repository"]["commit"] = "f" * 40
            write_json(state_path, state)
            request = snapshot_case.request_value()
            request["ckb"]["state_sha256"] = sha256(state_path)
            snapshot_case.write_request(request)
            with self.assertRaises(CanvasFailure) as raised:
                validate_only(snapshot_case.request)
            self.assertEqual("snapshot_mismatch", raised.exception.reason)
        finally:
            snapshot_case.cleanup()

        drift_case = build_case("evidence-drift")
        try:
            page = drift_case.human / "pages" / "page-00.md"
            page.write_bytes(page.read_bytes() + b"drift\n")
            with self.assertRaises(CanvasFailure) as raised:
                validate_only(drift_case.request)
            self.assertEqual("input_drift", raised.exception.reason)
        finally:
            drift_case.cleanup()

    def test_missing_target_and_existing_target_are_guarded(self) -> None:
        missing = build_case("missing-human")
        try:
            (missing.human / "pages" / "page-00.md").unlink()
            with self.assertRaises(CanvasFailure) as raised:
                validate_only(missing.request)
            self.assertEqual("missing_target", raised.exception.reason)
        finally:
            missing.cleanup()

        existing = build_case("target-exists")
        try:
            existing.target.write_bytes(b"existing-complete\n")
            with self.assertRaises(CanvasFailure) as raised:
                generate(existing.request)
            self.assertEqual("target_exists", raised.exception.reason)
            self.assertEqual(b"existing-complete\n", existing.target.read_bytes())
        finally:
            existing.cleanup()


if __name__ == "__main__":
    unittest.main()
