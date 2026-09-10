from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

import benchmark_keyword_real_provider as benchmark


PROTOCOL = TESTS / "fixtures" / "keyword_real_provider_12case.json"


class KeywordRealProviderBenchmarkTests(unittest.TestCase):
    def test_protocol_freezes_twelve_real_cases_and_six_fault_probes(self) -> None:
        protocol, source = benchmark.validate_protocol(PROTOCOL)
        self.assertEqual(protocol["status"], "frozen")
        self.assertTrue(protocol["frozen_before_run"])
        self.assertEqual(len(protocol["questions"]), 12)
        self.assertEqual(
            [{name: value for name, value in item.items() if name != "coverage"} for item in protocol["questions"]],
            source["questions"],
        )
        self.assertEqual(
            {item["mode"] for item in protocol["fault_probes"]},
            set(benchmark.REQUIRED_FAULT_MODES),
        )
        coverage = {tag for item in protocol["questions"] for tag in item["coverage"]}
        self.assertIn("chinese-natural-language", coverage)
        self.assertIn("source-identifier", coverage)

    def test_missing_real_provider_is_recorded_as_not_executed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result"
            report = benchmark.run_benchmark(
                PROTOCOL,
                Path(temporary) / "unused-corpus",
                output,
                None,
            )
            persisted = json.loads((output / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report, persisted)
        self.assertEqual(report["status"], "not-executed")
        self.assertEqual(report["summary"]["real_provider_actual_calls"], 0)
        self.assertEqual(report["summary"]["quality_claim"], "not-executed")
        self.assertEqual(report["real_provider"]["effect_claim"], "not-executed")

    def test_timeout_uses_adapter_attempt_when_start_marker_races_process_startup(self) -> None:
        row = {
            "mode": "timeout",
            "expected_failure_type": "timeout",
            "provider_process_starts": 0,
            "baseline": {"status": "passed", "signature": "same", "quality": {"recall_at_8": 1.0}},
            "observed": {
                "status": "passed",
                "signature": "same",
                "quality": {"recall_at_8": 1.0},
                "fallback": {
                    "status": "fallback",
                    "provider": {"status": "failed", "failure_type": "timeout", "attempts": 1},
                },
            },
        }
        self.assertTrue(all(benchmark.fault_probe_checks(row).values()))


if __name__ == "__main__":
    unittest.main()
