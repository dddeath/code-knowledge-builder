from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "prototypes" / "ckb-canvas-skill"
FIXTURE = REPO / "tests" / "fixtures" / "obsidian-canvas-agent-visualization"
sys.path[:0] = [str(REPO), str(SKILL), str(FIXTURE)]

from ckb_canvas.commands import generate, rollback
from ckb_canvas.contracts import CanvasFailure
from runtime_builder import build_case


class CanvasRollbackTests(unittest.TestCase):
    def test_absent_rollback_removes_all_three_generated_roles(self) -> None:
        case = build_case("rollback-absent")
        try:
            result = generate(case.request).to_dict()
            rolled_back = rollback(result["rollback_manifest"]["path"], result["rollback_manifest"]["sha256"])
            self.assertEqual("passed", rolled_back["status"])
            self.assertEqual(3, rolled_back["roles_verified"])
            self.assertFalse(case.target.exists())
            self.assertFalse(case.validation.exists())
            self.assertFalse(case.rollback_manifest.exists())
        finally:
            case.cleanup()

    def test_present_rollback_restores_three_roles_byte_identical(self) -> None:
        case = build_case("rollback-present", replace=True)
        try:
            original = dict(case.original_roles)
            result = generate(case.request).to_dict()
            self.assertNotEqual(original["canvas"], case.target.resolve().read_bytes())
            rolled_back = rollback(result["rollback_manifest"]["path"], result["rollback_manifest"]["sha256"])
            self.assertEqual("passed", rolled_back["status"])
            self.assertEqual(original["canvas"], case.target.resolve().read_bytes())
            self.assertEqual(original["validation_manifest"], case.validation.read_bytes())
            self.assertEqual(original["rollback_manifest"], case.rollback_manifest.read_bytes())
            backup_root = Path(case.request_value()["request"]["backup_root"])
            self.assertFalse(backup_root.exists())
        finally:
            case.cleanup()

    def test_rollback_drift_preserves_current_bytes_and_backup(self) -> None:
        case = build_case("rollback-drift", replace=True)
        external = b"externally-edited-canvas\n"
        try:
            result = generate(case.request).to_dict()
            case.target.resolve().write_bytes(external)
            with self.assertRaises(CanvasFailure) as raised:
                rollback(result["rollback_manifest"]["path"], result["rollback_manifest"]["sha256"])
            self.assertEqual("rollback_drift", raised.exception.reason)
            self.assertEqual(6, raised.exception.exit_code)
            self.assertEqual(external, case.target.resolve().read_bytes())
            backup_root = Path(case.request_value()["request"]["backup_root"])
            self.assertTrue(backup_root.is_dir())
            self.assertGreaterEqual(len(list(backup_root.iterdir())), 3)
        finally:
            case.cleanup()

    def test_wrong_manifest_hash_changes_nothing(self) -> None:
        case = build_case("rollback-manifest-hash")
        try:
            result = generate(case.request).to_dict()
            before = case.target.resolve().read_bytes()
            with self.assertRaises(CanvasFailure) as raised:
                rollback(result["rollback_manifest"]["path"], "0" * 64)
            self.assertEqual("rollback_drift", raised.exception.reason)
            self.assertEqual(before, case.target.resolve().read_bytes())
        finally:
            case.cleanup()


if __name__ == "__main__":
    unittest.main()
