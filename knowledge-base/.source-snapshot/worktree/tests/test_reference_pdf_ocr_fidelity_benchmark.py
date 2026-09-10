from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import unittest

from benchmark_reference_pdf_ocr_fidelity import run_benchmark


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "tests/fixtures/research-gap-enhancement-effects/pdf-ocr-code-table-fidelity-v1.json"
FIXTURES = ROOT / "tests/fixtures/reference-pdf-ocr"
COMMITTED = ROOT / "references/research-gap-enhancement-effects/pdf-ocr-code-table-fidelity-v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReferencePdfOcrFidelityBenchmarkTests(unittest.TestCase):
    def test_frozen_protocol_binds_distinct_native_scanned_and_hybrid_fixtures(self) -> None:
        protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        ground_truth_path = ROOT / protocol["fixture_manifest"]
        ground_truth = json.loads(ground_truth_path.read_text(encoding="utf-8"))
        self.assertEqual(protocol["status"], "frozen")
        self.assertEqual(_sha256(ground_truth_path), protocol["fixture_manifest_sha256"])
        self.assertEqual(ground_truth["kind_evidence"]["native_text_pages"], [True, True])
        self.assertEqual(ground_truth["kind_evidence"]["scanned_text_pages"], [False, False])
        self.assertEqual(ground_truth["kind_evidence"]["hybrid_text_pages"], [True, False])
        for name, document in ground_truth["documents"].items():
            self.assertEqual(_sha256(FIXTURES / document["path"]), protocol["fixture_sha256"][name])
        self.assertTrue(ground_truth["noise"]["repeated_header"])
        self.assertTrue(ground_truth["noise"]["footer_page_number"])
        self.assertEqual(
            ground_truth["quality_dimensions"],
            ["text_coverage", "code_fidelity", "table_structure", "source_page_locator"],
        )

    def test_committed_measurement_reports_each_quality_dimension_separately(self) -> None:
        report = json.loads((COMMITTED / "report.json").read_text(encoding="utf-8"))
        metrics = report["metrics"]
        self.assertEqual(report["status"], "measured")
        self.assertNotIn("pass_rate", report)
        self.assertNotIn("overall_accuracy", report)
        self.assertEqual(metrics["text_coverage"]["recall"], 1.0)
        self.assertEqual(metrics["text_coverage"]["matched_items"], 23)
        self.assertEqual(metrics["code_fidelity"]["exact_line_recall"], 0.666667)
        self.assertEqual(metrics["code_fidelity"]["symbol_sequence_accuracy"], 1.0)
        self.assertEqual(metrics["code_fidelity"]["indentation_accuracy"], 1.0)
        self.assertEqual(metrics["table_structure"]["cell_recall"], 1.0)
        self.assertEqual(metrics["table_structure"]["row_alignment_accuracy"], 1.0)
        self.assertEqual(metrics["table_structure"]["column_order_accuracy"], 1.0)
        self.assertTrue(metrics["table_structure"]["wrapped_cell_continuation"])
        self.assertTrue(metrics["table_structure"]["table_fragment_detected"])
        self.assertEqual(metrics["source_page_locator"]["accuracy"], 1.0)
        self.assertTrue(metrics["source_page_locator"]["hybrid_methods_match"])
        self.assertEqual(report["quality_gate_failures"], [])
        self.assertTrue(all(report["quality_gate_evaluations"].values()))

    def test_committed_measurement_proves_real_ocr_content_and_reopened_provenance(self) -> None:
        raw = json.loads((COMMITTED / "raw-results.json").read_text(encoding="utf-8"))
        self.assertEqual(raw["runtime"]["rapidocr_onnxruntime"], "1.4.4")
        self.assertEqual(raw["runtime"]["onnxruntime"], "1.29.0")
        self.assertEqual([page["method"] for page in raw["ingests"]["native"]["pages"]], ["native", "native"])
        self.assertEqual([page["method"] for page in raw["ingests"]["scanned"]["pages"]], ["ocr", "ocr"])
        self.assertEqual([page["method"] for page in raw["ingests"]["hybrid"]["pages"]], ["native", "ocr"])
        for name in ("native", "scanned", "hybrid"):
            checks = raw["ingest_checks"][name]
            self.assertTrue(checks["source_copy_exact"])
            self.assertTrue(checks["audit_passed"])
            self.assertTrue(checks["methods_match"])
        for page in raw["ingests"]["scanned"]["pages"]:
            self.assertEqual(page["ocr"]["metadata"]["engine"]["name"], "rapidocr_onnxruntime")
            self.assertEqual(page["ocr"]["metadata"]["engine"]["version"], "1.4.4")
            self.assertEqual(len(page["ocr"]["output_sha256"]), 64)
            self.assertIn("扫描" if page["page_number"] == 1 else "跨行表格", page["text"])

    def test_failure_matrix_covers_tool_timeout_empty_limit_and_corruption(self) -> None:
        report = json.loads((COMMITTED / "report.json").read_text(encoding="utf-8"))
        diagnostics = {item["case"]: item for item in report["diagnostics"]}
        self.assertEqual(
            set(diagnostics),
            {"ocr-tool-missing", "ocr-timeout", "ocr-empty-output", "ocr-page-limit", "corrupt-pdf"},
        )
        self.assertTrue(all(item["matched"] for item in diagnostics.values()))
        self.assertIn("ocr-tool-missing: rapidocr_onnxruntime", diagnostics["ocr-tool-missing"]["stderr"])
        self.assertEqual(diagnostics["ocr-timeout"]["observed_reason"], "ocr-timeout")
        self.assertEqual(
            diagnostics["ocr-empty-output"]["observed_reason"],
            "ocr-text-below-usable-threshold",
        )
        self.assertEqual(diagnostics["ocr-page-limit"]["attempted_pages"], 1)
        self.assertIn("corrupt or unsupported PDF source", diagnostics["corrupt-pdf"]["observed_reason"])

    @unittest.skipUnless(os.environ.get("CKB_RUN_REAL_OCR_BENCHMARK") == "1", "real OCR replay is opt-in")
    def test_live_real_ocr_replay_meets_frozen_gates(self) -> None:
        raw, report = run_benchmark(PROTOCOL)
        self.assertEqual(report["contract_failures"], [])
        self.assertEqual(report["quality_gate_failures"], [])
        self.assertEqual(raw["diagnostic_checks"], {name: True for name in [
            "ocr-tool-missing", "ocr-timeout", "ocr-empty-output", "ocr-page-limit", "corrupt-pdf"
        ]})


if __name__ == "__main__":
    unittest.main()
