from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
PROTOTYPE = REPO / "prototypes" / "ckb-page-fanout-benchmark"
FIXTURE = REPO / "tests" / "fixtures" / "page-fanout"
sys.path.insert(0, str(PROTOTYPE))
sys.path.insert(0, str(REPO / "scripts"))

from ckb_page_fanout.benchmark import aggregate_benchmark, snapshot_read_only
from ckb_page_fanout.contracts import FanoutError, atomic_write_json, canonical_json_bytes
from ckb_page_fanout.generator import generate_fanout
from ckb_page_fanout.judge import judge_arm
from ckb_core.human_page_templates import (
    HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
    get_human_page_template,
)
from ckb_core.page_config import DEFAULT_PAGE_CONFIG
from ckb_core.reference_documents import project_references


class PageFanoutBenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.fixture = self.workspace / "fixture"
        shutil.copytree(FIXTURE, self.fixture)
        self.fanout = self.workspace / "arm-b"
        self.rollback = self.workspace / "rollback.json"
        self.read_only = self.workspace / "read-only-kb"
        self.read_only.mkdir()
        (self.read_only / "sentinel.txt").write_text("stable\n", encoding="utf-8")
        generate_fanout(
            contract_path=self.fixture / "benchmark-contract.json",
            corpus_path=self.fixture / "corpus.json",
            source_root=self.fixture,
            conservative_root=self.fixture / "conservative",
            output_root=self.fanout,
            rollback_manifest=self.rollback,
            workspace_root=self.workspace,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _judge(self, root: Path) -> dict[str, object]:
        return judge_arm(
            judge_contract_path=self.fixture / "judge-contract.json",
            projection_root=root,
            source_root=self.fixture,
        )

    def _aggregate(self) -> dict[str, object]:
        arm_a = self._judge(self.fixture / "conservative")
        arm_b = self._judge(self.fanout)
        before = snapshot_read_only(self.read_only)
        after = snapshot_read_only(self.read_only)
        for name, value in (("arm-a.json", arm_a), ("arm-b.json", arm_b), ("before.json", before), ("after.json", after)):
            atomic_write_json(self.workspace / name, value)
        return aggregate_benchmark(
            contract_path=self.fixture / "benchmark-contract.json",
            corpus_path=self.fixture / "corpus.json",
            arm_a_path=self.workspace / "arm-a.json",
            arm_b_path=self.workspace / "arm-b.json",
            read_only_before_path=self.workspace / "before.json",
            read_only_after_path=self.workspace / "after.json",
        )

    def test_blinded_judge_recomputes_fixed_task_and_integrity_metrics(self) -> None:
        conservative = self._judge(self.fixture / "conservative")
        fanout = self._judge(self.fanout)
        self.assertEqual("arm_a", conservative["arm_id"])
        self.assertEqual("arm_b", fanout["arm_id"])
        self.assertEqual(
            {
                "tasks": 9,
                "found_tasks": 9,
                "failed_navigation_tasks": 0,
                "total_navigation_steps": 18,
                "median_navigation_steps": 2.0,
                "answer_correct": 9,
                "answer_accuracy": 1.0,
                "source_entailed": 9,
                "source_entailment_rate": 1.0,
                "misleading_links": 0,
                "page_count": 5,
                "new_page_count": 0,
                "orphan_pages": [],
                "orphan_page_count": 0,
                "duplicate_topics": [],
                "duplicate_topic_count": 0,
                "broken_links": [],
                "broken_link_count": 0,
                "reported_generation_context_bytes": 0,
                "reported_generated_output_bytes": 0,
            },
            conservative["aggregate"],
        )
        self.assertEqual(27, fanout["aggregate"]["total_navigation_steps"])
        self.assertEqual(3.0, fanout["aggregate"]["median_navigation_steps"])
        self.assertEqual(1.0, fanout["aggregate"]["answer_accuracy"])
        self.assertEqual(1.0, fanout["aggregate"]["source_entailment_rate"])
        self.assertEqual(14, fanout["aggregate"]["page_count"])
        self.assertEqual(0, fanout["aggregate"]["broken_link_count"])
        self.assertEqual(0, fanout["aggregate"]["orphan_page_count"])
        self.assertNotIn("conservative", json.dumps(conservative, ensure_ascii=False))
        self.assertNotIn("fanout", json.dumps(fanout, ensure_ascii=False))
        self.assertNotIn(".generator", (PROTOTYPE / "ckb_page_fanout" / "judge.py").read_text(encoding="utf-8"))

    def test_aggregate_preserves_negative_result_and_uses_fixed_thresholds(self) -> None:
        result = self._aggregate()
        self.assertEqual("passed", result["status"])
        self.assertEqual("retain-conservative", result["recommendation"])
        self.assertEqual(-1.0, result["comparison"]["median_navigation_step_reduction"])
        self.assertEqual(0.0, result["comparison"]["answer_accuracy_delta"])
        self.assertEqual(9, result["comparison"]["page_increment"])
        self.assertEqual(1.8, result["comparison"]["page_increment_ratio_to_conservative"])
        self.assertEqual(1704, result["comparison"]["generation_context_bytes"])
        self.assertEqual(6414, result["comparison"]["generated_output_bytes"])
        self.assertEqual(["median-navigation-step-reduction"], [item["name"] for item in result["recommendation_reasons"]])
        self.assertEqual(9, len(result["tasks"]))
        self.assertEqual("passed", result["read_only_guard"]["status"])

    def test_task_order_does_not_change_blinded_judge_output(self) -> None:
        first = self._judge(self.fanout)
        contract_path = self.fixture / "judge-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["tasks"].reverse()
        contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        second = self._judge(self.fanout)
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))

    def test_orphan_and_broken_link_are_recomputed_from_markdown(self) -> None:
        page = self.fanout / "references" / "engineering-guide.md"
        text = page.read_text(encoding="utf-8")
        text = "\n".join(line for line in text.splitlines() if "eng-snapshot" not in line) + "\n"
        page.write_text(text, encoding="utf-8")
        index = self.fanout / "INDEX.md"
        index.write_text(index.read_text(encoding="utf-8") + "- [[missing-page|错误入口]]\n", encoding="utf-8")
        result = self._judge(self.fanout)
        self.assertEqual(["concepts/eng-snapshot.md"], result["aggregate"]["orphan_pages"])
        self.assertEqual(1, result["aggregate"]["broken_link_count"])
        record = next(item for item in result["records"] if item["task_id"] == "eng-snapshot")
        self.assertFalse(record["found"])
        self.assertFalse(record["answer_correct"])

    def test_read_only_guard_rejects_any_snapshot_drift(self) -> None:
        arm_a = self._judge(self.fixture / "conservative")
        arm_b = self._judge(self.fanout)
        before = snapshot_read_only(self.read_only)
        (self.read_only / "sentinel.txt").write_text("changed\n", encoding="utf-8")
        after = snapshot_read_only(self.read_only)
        for name, value in (("arm-a.json", arm_a), ("arm-b.json", arm_b), ("before.json", before), ("after.json", after)):
            atomic_write_json(self.workspace / name, value)
        with self.assertRaises(FanoutError) as raised:
            aggregate_benchmark(
                contract_path=self.fixture / "benchmark-contract.json",
                corpus_path=self.fixture / "corpus.json",
                arm_a_path=self.workspace / "arm-a.json",
                arm_b_path=self.workspace / "arm-b.json",
                read_only_before_path=self.workspace / "before.json",
                read_only_after_path=self.workspace / "after.json",
            )
        self.assertEqual("READ_ONLY_ROOT_DRIFT", raised.exception.reason)

    def test_current_page_quota_v3_and_reference_projection_remain_compatible(self) -> None:
        contract = json.loads((self.fixture / "benchmark-contract.json").read_text(encoding="utf-8"))
        expected = contract["current_compatibility"]
        self.assertEqual(HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION, expected["human_page_template_schema_version"])
        self.assertEqual(HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION, expected["human_page_template_contract_version"])
        self.assertEqual(DEFAULT_PAGE_CONFIG["page_limits"], expected["default_page_limits"])
        self.assertEqual(DEFAULT_PAGE_CONFIG["relation_limits"], expected["default_relation_limits"])
        self.assertEqual(1, expected["reference_page_limit_per_source"])
        self.assertIn('"page_limit_per_source": 1', inspect.getsource(project_references))
        reference_contract = get_human_page_template("reference")
        self.assertEqual("reference", reference_contract.page_type)
        self.assertLessEqual(contract["fanout_policy"]["max_links_per_page"], reference_contract.source_link_budget.maximum)
        conservative = json.loads((self.fixture / "conservative" / "projection.json").read_text(encoding="utf-8"))
        fanout = json.loads((self.fanout / "projection.json").read_text(encoding="utf-8"))
        self.assertEqual(1, conservative["page_limit_per_source"])
        self.assertEqual(1, fanout["page_limit_per_source"])
        self.assertEqual(3, sum(1 for item in fanout["pages"] if item["kind"] == "reference"))
        self.assertEqual(9, sum(1 for item in fanout["pages"] if item["kind"] == "concept"))


if __name__ == "__main__":
    unittest.main()
