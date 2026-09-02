from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


REPO = Path(__file__).resolve().parents[1]
PROTOTYPE = REPO / "prototypes" / "ckb-tag-navigation"
FIXTURE = REPO / "tests" / "fixtures" / "tag-navigation"
sys.path.insert(0, str(PROTOTYPE))

from ckb_tag_navigation.benchmark import load_records, recompute
from ckb_tag_navigation.contracts import TagNavigationError, canonical_json_bytes


class TagNavigationBenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads((FIXTURE / "navigation-benchmark.json").read_text(encoding="utf-8"))
        self.records = load_records(FIXTURE / "navigation-records.jsonl")

    def test_fixed_records_recompute_all_required_metrics(self) -> None:
        report = recompute(self.fixture, self.records)
        self.assertEqual("fixture-navigation-signal-only", report["effect_claim"])
        self.assertEqual(
            {"tasks": 6, "total_steps": 19, "median_steps": 3.0, "misdirected_links": 5, "page_count": 11, "conflicts": 0, "page_increment": 0},
            report["aggregate"]["no_tag"],
        )
        self.assertEqual(
            {"tasks": 6, "total_steps": 7, "median_steps": 1.0, "misdirected_links": 1, "page_count": 11, "conflicts": 0, "page_increment": 0},
            report["aggregate"]["confirmed_tag"],
        )

    def test_record_order_does_not_change_report(self) -> None:
        forward = recompute(self.fixture, self.records)
        reverse = recompute(self.fixture, list(reversed(self.records)))
        self.assertEqual(canonical_json_bytes(forward), canonical_json_bytes(reverse))

    def test_missing_per_task_record_stops_aggregation(self) -> None:
        with self.assertRaises(TagNavigationError) as raised:
            recompute(self.fixture, self.records[:-1])
        self.assertEqual("INCOMPLETE_BENCHMARK", raised.exception.reason)

    def test_page_increment_is_derived_from_page_sets(self) -> None:
        fixture = copy.deepcopy(self.fixture)
        fixture["page_sets"]["confirmed_tag"].append("human/pages/new.md")
        report = recompute(fixture, self.records)
        self.assertEqual(1, report["aggregate"]["confirmed_tag"]["page_increment"])


if __name__ == "__main__":
    unittest.main()
