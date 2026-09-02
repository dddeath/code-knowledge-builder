from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "prototypes" / "ckb-canvas-skill"
FIXTURE = REPO / "tests" / "fixtures" / "obsidian-canvas-agent-visualization"
sys.path[:0] = [str(REPO), str(SKILL), str(FIXTURE)]

from ckb_canvas.commands import generate, validate_only
from ckb_canvas.contracts import CanvasFailure
from ckb_canvas.freeze import load_and_freeze_request
from ckb_canvas.graph import canonical_canvas_bytes, layout_graph, select_graph, validate_canvas
from ckb_canvas.transaction import capture_baseline, promote_bundle, stage_bundle
from ckb_canvas.commands import _render, _bundle_bytes
from runtime_builder import build_case, sha256


class CanvasTransactionTests(unittest.TestCase):
    def test_validate_stages_and_reopens_without_promotion(self) -> None:
        case = build_case("validate-only")
        try:
            result = validate_only(case.request)
            self.assertEqual("passed", result["status"])
            self.assertFalse(case.target.exists())
            self.assertFalse(case.validation.exists())
            self.assertFalse(case.rollback_manifest.exists())
            self.assertEqual([], list(case.staging.glob("*.tmp")))
        finally:
            case.cleanup()

    def test_absent_generate_promotes_three_canonical_complete_roles(self) -> None:
        case = build_case("generate-absent")
        try:
            result = generate(case.request).to_dict()
            self.assertEqual("passed", result["status"])
            paths = [case.target.resolve(), case.validation, case.rollback_manifest]
            for path in paths:
                data = path.read_bytes()
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
                self.assertEqual(1, len(data) - len(data.rstrip(b"\n")))
                self.assertEqual(data, (json.dumps(json.loads(data.decode("utf-8")), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
            self.assertEqual(result["canvas"]["sha256"], sha256(case.target.resolve()))
            self.assertEqual(result["validation_manifest"]["sha256"], sha256(case.validation))
            self.assertEqual(result["rollback_manifest"]["sha256"], sha256(case.rollback_manifest))
        finally:
            case.cleanup()

    def test_promotion_detects_concurrent_canvas_and_preserves_external_bytes(self) -> None:
        case = build_case("promotion-drift")
        external = b"external-current-complete\n"
        fired = False

        def hook(phase: str, role: str) -> None:
            nonlocal fired
            if not fired and phase == "promotion-ready" and role == "validation_manifest":
                case.target.write_bytes(external)
                fired = True

        try:
            with self.assertRaises(CanvasFailure) as raised:
                generate(case.request, fault_hook=hook)
            self.assertEqual("promotion_drift", raised.exception.reason)
            self.assertEqual(6, raised.exception.exit_code)
            self.assertEqual(external, case.target.read_bytes())
            self.assertFalse(case.validation.exists())
            self.assertFalse(case.rollback_manifest.exists())
        finally:
            case.cleanup()

    def test_write_fsync_and_promotion_faults_leave_complete_baseline(self) -> None:
        for phase, role in (("before-write", "canvas"), ("before-fsync", "canvas"), ("promotion-ready", "validation_manifest")):
            with self.subTest(phase=phase):
                case = build_case(f"io-{phase}")

                def hook(actual_phase: str, actual_role: str) -> None:
                    if actual_phase == phase and actual_role == role:
                        raise OSError("injected fault")

                try:
                    with self.assertRaises(CanvasFailure) as raised:
                        generate(case.request, fault_hook=hook)
                    self.assertEqual("io_failure", raised.exception.reason)
                    self.assertFalse(case.target.exists())
                    self.assertFalse(case.validation.exists())
                    self.assertFalse(case.rollback_manifest.exists())
                finally:
                    case.cleanup()

    def test_staged_canvas_corruption_is_rejected_before_target_changes(self) -> None:
        case = build_case("staged-corruption")
        try:
            frozen = load_and_freeze_request(case.request)
            baseline = capture_baseline(frozen)
            rendered = _render(frozen, baseline)
            staged = stage_bundle(frozen, _bundle_bytes(rendered))
            staged.roles["canvas"].temporary_path.write_bytes(b'{"nodes":[]')
            with self.assertRaises(CanvasFailure) as raised:
                promote_bundle(frozen, staged, baseline)
            self.assertEqual("invalid_canvas", raised.exception.reason)
            self.assertFalse(case.target.exists())
            self.assertFalse(case.validation.exists())
            self.assertFalse(case.rollback_manifest.exists())
        finally:
            case.cleanup()


if __name__ == "__main__":
    unittest.main()
