from __future__ import annotations

import json
from pathlib import Path
import unittest


FIXTURES = Path(__file__).with_name("fixtures")


class ChineseRetrievalFixtureTests(unittest.TestCase):
    def test_frozen_protocol_shape(self) -> None:
        protocol = json.loads((FIXTURES / "chinese-retrieval-protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["status"], "frozen")
        self.assertTrue(protocol["frozen_before_run"])
        self.assertEqual(protocol["budget_tokens"], 2400)
        self.assertEqual(protocol["max_results"], 8)
        self.assertEqual(protocol["warmups"], 1)
        self.assertEqual(protocol["repetitions"], 9)
        self.assertEqual(len(protocol["queries"]), 12)
        self.assertEqual(len(protocol["acceptance_gates"]), 7)

    def test_baseline_records_all_mechanical_fragments(self) -> None:
        baseline = json.loads((FIXTURES / "chinese-retrieval-baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(baseline["status"], "baseline-captured")
        self.assertEqual(len(baseline["queries"]), 12)
        rows = {
            row["baseline_mechanical_fragment"]: row
            for row in baseline["tokenizer_cases"]
            if row.get("baseline_mechanical_fragment")
        }
        for fragment in baseline["acceptance_targets"]["mechanical_fragments_not_high_priority"]:
            self.assertIn(fragment, rows)
            self.assertIn(fragment, rows[fragment]["terms"])
            self.assertIn(fragment, rows[fragment]["fts_query"])

    def test_baseline_corpus_and_recall_are_complete(self) -> None:
        baseline = json.loads((FIXTURES / "chinese-retrieval-baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(baseline["corpus"]["machine_integrity"], "ok")
        self.assertEqual(baseline["corpus"]["legacy_integrity"], "ok")
        self.assertEqual(baseline["summary"]["target_source_recall_at_8"], 1.0)
        self.assertTrue(baseline["summary"]["deterministic_within_process"])


if __name__ == "__main__":
    unittest.main()
