from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from benchmark_reference_pdf_effect import main, run_benchmark, summarize


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "tests/fixtures/research-gap-enhancement-effects/pdf-native-v1.json"
DRIFT_PROTOCOL = ROOT / "tests/fixtures/research-gap-enhancement-effects/pdf-native-v1-parser-drift.json"
COMMITTED = ROOT / "references/research-gap-enhancement-effects/pdf-native-v1"


class ReferencePdfEffectBenchmarkTests(unittest.TestCase):
    def test_protocol_is_frozen_and_limits_claim_scope(self) -> None:
        protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        self.assertEqual(protocol["status"], "frozen")
        self.assertEqual(protocol["parser"], {"name": "pypdf", "version": "6.16.2"})
        self.assertEqual(protocol["gates"]["real_ocr_calls"], 0)
        self.assertEqual(protocol["gates"]["web_implementation_status"], "not-implemented")
        drift = json.loads(DRIFT_PROTOCOL.read_text(encoding="utf-8"))
        self.assertEqual(drift["parser"], {"name": "pypdf", "version": "6.16.2-drift"})
        self.assertTrue(drift["gates"]["parser_identity_matches_protocol"])

    def test_committed_result_replays_exactly(self) -> None:
        git = os.environ.get("CKB_GIT", "git")
        raw, report = run_benchmark(PROTOCOL, git)
        self.assertEqual(report, summarize(raw))
        expected_raw = json.loads((COMMITTED / "raw-results.json").read_text(encoding="utf-8"))
        expected_report = json.loads((COMMITTED / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(raw, expected_raw)
        self.assertEqual(report, expected_report)
        self.assertEqual(
            report["parser_identity"]["actual"],
            {
                "module_name": "pypdf",
                "module_version": "6.16.2",
                "distribution_name": "pypdf",
                "distribution_version": "6.16.2",
            },
        )
        self.assertTrue(report["checks"]["parser_identity_matches_protocol"])
        self.assertEqual(report["effect"]["native_pdf"], "已证实增强")
        self.assertEqual(report["effect"]["pdf_web_ocr_combined_gap"], "证据不足")

    def test_parser_version_drift_fails_without_overwriting_existing_results(self) -> None:
        git = os.environ.get("CKB_GIT", "git")
        with tempfile.TemporaryDirectory(prefix="ckb-pdf-effect-drift-") as directory:
            root = Path(directory)
            raw = root / "raw-results.json"
            report = root / "report.json"
            raw.write_bytes(b"original-raw\n")
            report.write_bytes(b"original-report\n")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_status = main(
                    [
                        "--protocol",
                        str(DRIFT_PROTOCOL),
                        "--raw",
                        str(raw),
                        "--report",
                        str(report),
                        "--git",
                        git,
                    ]
                )
            result = json.loads(output.getvalue())
            self.assertEqual(exit_status, 1)
            self.assertEqual(result["status"], "failed")
            self.assertFalse(result["written"])
            self.assertEqual(result["failed_checks"], ["parser_identity_matches_protocol"])
            self.assertEqual(result["parser_identity"]["expected"]["version"], "6.16.2-drift")
            self.assertEqual(result["parser_identity"]["actual"]["distribution_version"], "6.16.2")
            self.assertEqual(raw.read_bytes(), b"original-raw\n")
            self.assertEqual(report.read_bytes(), b"original-report\n")


if __name__ == "__main__":
    unittest.main()
