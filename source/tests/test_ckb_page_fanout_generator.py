from __future__ import annotations

import copy
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

from ckb_page_fanout.contracts import FanoutError, tree_manifest
from ckb_page_fanout.generator import generate_fanout, rollback_fanout


class PageFanoutGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.fixture = self.workspace / "fixture"
        shutil.copytree(FIXTURE, self.fixture)
        self.output = self.workspace / "arm-b"
        self.rollback = self.workspace / "rollback.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_json(self, relative: str, value: dict[str, object]) -> None:
        (self.fixture / relative).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _contract(self) -> dict[str, object]:
        return json.loads((self.fixture / "benchmark-contract.json").read_text(encoding="utf-8"))

    def _corpus(self) -> dict[str, object]:
        return json.loads((self.fixture / "corpus.json").read_text(encoding="utf-8"))

    def _generate(self) -> dict[str, object]:
        return generate_fanout(
            contract_path=self.fixture / "benchmark-contract.json",
            corpus_path=self.fixture / "corpus.json",
            source_root=self.fixture,
            conservative_root=self.fixture / "conservative",
            output_root=self.output,
            rollback_manifest=self.rollback,
            workspace_root=self.workspace,
        )

    def test_generates_nine_grounded_pages_and_rejects_the_duplicate(self) -> None:
        baseline = tree_manifest(self.fixture / "conservative")
        result = self._generate()
        projection = json.loads((self.output / "projection.json").read_text(encoding="utf-8"))
        self.assertEqual("passed", result["status"])
        self.assertEqual(9, result["accepted_count"])
        self.assertEqual(1, result["rejected_count"])
        self.assertEqual(["DUPLICATE_TOPIC"], result["rejection_reasons"])
        self.assertEqual(14, projection["page_count"])
        self.assertEqual(9, projection["new_page_count"])
        self.assertEqual(3, max(len(value) for value in self._accepted_by_document(projection).values()))
        self.assertEqual(9, len(list((self.output / "concepts").glob("*.md"))))
        self.assertEqual(1704, projection["generation_context_bytes"])
        self.assertEqual(6414, projection["generated_output_bytes"])
        self.assertEqual(baseline, tree_manifest(self.fixture / "conservative"))
        rejected = projection["rejected_candidates"]
        self.assertEqual("ops-snapshot-duplicate", rejected[0]["candidate_id"])
        self.assertEqual(1.0, rejected[0]["detail"]["similarity"])

    @staticmethod
    def _accepted_by_document(projection: dict[str, object]) -> dict[str, list[dict[str, object]]]:
        result: dict[str, list[dict[str, object]]] = {}
        for item in projection["accepted_candidates"]:  # type: ignore[index]
            result.setdefault(item["document_id"], []).append(item)  # type: ignore[index]
        return result

    def test_guarded_rollback_removes_only_the_unchanged_output(self) -> None:
        result = self._generate()
        rolled_back = rollback_fanout(self.rollback, self.workspace)
        self.assertEqual("rolled-back", rolled_back["status"])
        self.assertEqual(result["output_tree_sha256"], rolled_back["verified_output_sha256"])
        self.assertFalse(self.output.exists())
        self.assertTrue((self.fixture / "conservative" / "projection.json").is_file())

    def test_rollback_detects_output_drift_and_preserves_the_scene(self) -> None:
        self._generate()
        (self.output / "INDEX.md").write_text("drift\n", encoding="utf-8")
        with self.assertRaises(FanoutError) as raised:
            rollback_fanout(self.rollback, self.workspace)
        self.assertEqual("ROLLBACK_DRIFT", raised.exception.reason)
        self.assertTrue(self.output.is_dir())

    def test_source_drift_stops_before_any_output(self) -> None:
        path = self.fixture / "documents" / "engineering-guide.md"
        path.write_text(path.read_text(encoding="utf-8") + "漂移\n", encoding="utf-8")
        with self.assertRaises(FanoutError) as raised:
            self._generate()
        self.assertEqual("SOURCE_DRIFT", raised.exception.reason)
        self.assertFalse(self.output.exists())
        self.assertFalse((self.workspace / ".arm-b.staging").exists())
        self.assertFalse(self.rollback.exists())

    def test_non_entailed_chinese_claim_stops_without_residue(self) -> None:
        corpus = self._corpus()
        corpus["documents"][0]["candidates"][0]["claim_zh"] = "这条中文主张没有出现在冻结原文。"  # type: ignore[index]
        self._write_json("corpus.json", corpus)
        with self.assertRaises(FanoutError) as raised:
            self._generate()
        self.assertEqual("CLAIM_NOT_ENTAILED", raised.exception.reason)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.rollback.exists())

    def test_source_range_drift_stops_without_residue(self) -> None:
        corpus = self._corpus()
        corpus["documents"][0]["candidates"][0]["source_range"] = {"start_line": 5, "end_line": 5}  # type: ignore[index]
        self._write_json("corpus.json", corpus)
        with self.assertRaises(FanoutError) as raised:
            self._generate()
        self.assertEqual("SOURCE_RANGE_DRIFT", raised.exception.reason)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.rollback.exists())

    def test_same_name_conflict_has_a_distinct_stable_reason(self) -> None:
        corpus = self._corpus()
        corpus["documents"][0]["candidates"].insert(  # type: ignore[index]
            0,
            {
                "candidate_id": "eng-title-conflict",
                "term": "工程交付指南",
                "claim_zh": "# 工程交付指南",
                "source_range": {"start_line": 1, "end_line": 1},
                "source_text": "# 工程交付指南",
            },
        )
        self._write_json("corpus.json", corpus)
        self._generate()
        projection = json.loads((self.output / "projection.json").read_text(encoding="utf-8"))
        rejected = {item["candidate_id"]: item for item in projection["rejected_candidates"]}
        self.assertEqual("TITLE_CONFLICT", rejected["eng-title-conflict"]["reason"])
        self.assertEqual("references/engineering-guide.md", rejected["eng-title-conflict"]["detail"]["existing_page"])

    def test_document_and_global_page_quotas_return_stable_reasons(self) -> None:
        contract = self._contract()
        contract["fanout_policy"]["max_pages_per_document"] = 2  # type: ignore[index]
        contract["fanout_policy"]["max_total_new_pages"] = 4  # type: ignore[index]
        self._write_json("benchmark-contract.json", contract)
        self._generate()
        projection = json.loads((self.output / "projection.json").read_text(encoding="utf-8"))
        reasons = {item["reason"] for item in projection["rejected_candidates"]}
        self.assertIn("DOCUMENT_PAGE_QUOTA", reasons)
        self.assertIn("GLOBAL_PAGE_QUOTA", reasons)
        self.assertLessEqual(projection["new_page_count"], 4)

    def test_link_quota_failure_cleans_staging_and_output(self) -> None:
        contract = self._contract()
        contract["fanout_policy"]["max_links_per_page"] = 2  # type: ignore[index]
        self._write_json("benchmark-contract.json", contract)
        with self.assertRaises(FanoutError) as raised:
            self._generate()
        self.assertEqual("PAGE_LINK_QUOTA", raised.exception.reason)
        self.assertFalse(self.output.exists())
        self.assertFalse((self.workspace / ".arm-b.staging").exists())

    def test_broken_link_failure_cleans_staging_and_output(self) -> None:
        references = self.fixture / "conservative" / "REFERENCES.md"
        references.write_text(references.read_text(encoding="utf-8") + "- [[references/missing|缺失]]\n", encoding="utf-8")
        contract = self._contract()
        contract["fanout_policy"]["max_links_per_page"] = 4  # type: ignore[index]
        self._write_json("benchmark-contract.json", contract)
        with self.assertRaises(FanoutError) as raised:
            self._generate()
        self.assertEqual("BROKEN_LINK", raised.exception.reason)
        self.assertFalse(self.output.exists())
        self.assertFalse((self.workspace / ".arm-b.staging").exists())


if __name__ == "__main__":
    unittest.main()
