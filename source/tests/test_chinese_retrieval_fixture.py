from __future__ import annotations

import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import benchmark_chinese_retrieval as effect_benchmark


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


class ChineseRetrievalEffectRetestFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = FIXTURES / "chinese-retrieval-effects"
        self.protocol = json.loads((self.root / "protocol.json").read_text(encoding="utf-8"))
        self.replay = json.loads((self.root / "replay-responses.json").read_text(encoding="utf-8"))

    def test_three_arm_protocol_is_frozen_at_the_fixed_knowledge_base_commit(self) -> None:
        self.assertEqual(self.protocol["status"], "frozen")
        self.assertTrue(self.protocol["frozen_before_run"])
        self.assertEqual(
            self.protocol["corpus"]["repository_commit"],
            "19152b227ccf687e7e4d89337d421c22a4e1a75f",
        )
        self.assertEqual(
            [arm["id"] for arm in self.protocol["arms"]],
            ["legacy-deterministic", "current-deterministic", "llm-replay-fallback"],
        )
        self.assertEqual(self.protocol["cold_runs"], 1)
        self.assertEqual(self.protocol["hot_runs"], 5)
        self.assertEqual(self.protocol["max_results"], 8)
        self.assertEqual(self.protocol["profile"], "fast")
        self.assertEqual(
            self.protocol["metrics"],
            [
                "recall_at_8",
                "mrr_at_8",
                "ndcg_at_8",
                "first_pack_estimated_tokens",
                "latency_ms_p50",
                "latency_ms_p95",
                "provider_process_starts",
            ],
        )

    def test_questions_have_fixed_relevance_labels_and_replay_responses(self) -> None:
        questions = self.protocol["questions"]
        self.assertEqual(len(questions), 12)
        self.assertEqual(len({item["id"] for item in questions}), len(questions))
        replay_by_hash = {item["input_hash"]: item for item in self.replay["responses"]}
        self.assertEqual(len(replay_by_hash), len(questions))
        for item in questions:
            with self.subTest(item=item["id"]):
                self.assertEqual(len(item["relevance"]), 1)
                self.assertEqual(item["relevance"][0]["grade"], 3)
                self.assertTrue(item["relevance"][0]["source_path"].startswith("scripts/"))
                input_hash = hashlib.sha256(item["question"].encode("utf-8")).hexdigest()
                response = replay_by_hash[input_hash]
                self.assertEqual(response["case_id"], item["id"])
                self.assertIn(item["relevance"][0]["symbol"], response["anchors"])

    def test_replay_is_declared_separately_from_real_provider_evidence(self) -> None:
        self.assertEqual(self.replay["evidence_class"], "fixed-replay-not-real-model")
        self.assertEqual(self.protocol["real_provider_without_explicit_command"], "provider-unavailable")
        self.assertEqual(self.protocol["provider"]["retries"], 0)
        self.assertEqual(self.protocol["provider"]["timeout_seconds"], 5.0)

    def test_legacy_arm_preserves_the_exact_mechanical_fragments(self) -> None:
        question = "返回的检索包不满是否会回退"
        legacy = effect_benchmark.legacy_search_terms(question)
        current = effect_benchmark.machine.search_terms(question)
        self.assertIn("回的检", legacy)
        self.assertIn("包不满", legacy)
        self.assertNotIn("回的检", current)
        self.assertNotIn("包不满", current)

    def test_rank_metrics_are_computed_from_document_order_and_fixed_grades(self) -> None:
        documents = [
            {"rank": 1, "source_path": "scripts/other.py"},
            {"rank": 2, "source_path": "scripts/target.py"},
        ]
        labels = [
            {"source_path": "scripts/target.py", "grade": 3},
            {"source_path": "scripts/missing.py", "grade": 1},
        ]
        quality = effect_benchmark.quality_for_ranking(documents, labels)
        self.assertEqual(quality["recall_at_8"], 0.5)
        self.assertEqual(quality["mrr_at_8"], 0.5)
        self.assertEqual(quality["relevant_hits"][0]["rank"], 2)
        self.assertEqual(
            quality["missing"],
            [{"source_path": "scripts/missing.py", "grade": 1, "reason": "not-selected"}],
        )

    def test_source_corpus_drift_fails_without_damaging_copied_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source_machine = source / "machine" / "knowledge.sqlite"
            source_machine.parent.mkdir(parents=True)
            source_machine.write_bytes(b"source-machine-before")
            source_legacy = source / "agent-index.sqlite"
            source_legacy.write_bytes(b"source-legacy-before")
            output = root / "run"
            drifted = False

            def fake_copy(_source: Path, target: Path) -> dict[str, object]:
                target_machine = target / "machine" / "knowledge.sqlite"
                target_machine.parent.mkdir(parents=True)
                target_machine.write_bytes(b"copied-machine-fixed")
                target_legacy = target / "agent-index.sqlite"
                target_legacy.write_bytes(b"copied-legacy-fixed")
                return {
                    "source": str(source),
                    "repository_commit": self.protocol["corpus"]["repository_commit"],
                    "source_machine_sha256_before": effect_benchmark.sha256(source_machine),
                    "copied_machine_sha256": effect_benchmark.sha256(target_machine),
                    "source_legacy_sha256_before": effect_benchmark.sha256(source_legacy),
                    "copied_legacy_sha256": effect_benchmark.sha256(target_legacy),
                    "integrity": {"machine": "ok", "legacy": "ok"},
                }

            def fake_row(arm, cache_state, run_index, corpus, question, protocol, config, marker):
                nonlocal drifted
                if not drifted:
                    source_machine.write_bytes(b"source-machine-drifted-during-measurement")
                    drifted = True
                document = {
                    "rank": 1,
                    "source_path": question["relevance"][0]["source_path"],
                    "entity_id": f"entity-{question['id']}",
                    "qualified_name": question["relevance"][0]["symbol"],
                    "score": 1.0,
                }
                quality = effect_benchmark.quality_for_ranking([document], question["relevance"])
                replay = arm == "llm-replay-fallback"
                return {
                    "question_id": question["id"],
                    "question": question["question"],
                    "arm": arm,
                    "cache_state": cache_state,
                    "run_index": run_index,
                    "latency_ms": 1.0,
                    "status": "passed",
                    "terms": ["term"],
                    "anchors": [],
                    "selected_documents": [document],
                    "quality": quality,
                    "first_pack_estimated_tokens": 100,
                    "provider_process_starts": int(replay and cache_state == "cold"),
                    "provider": {"cache_hit": cache_state == "hot"} if replay else {},
                    "fallback": None,
                    "result_signature": f"{arm}-{question['id']}",
                }

            with patch.object(effect_benchmark, "validate_protocol"), patch.object(
                effect_benchmark, "copy_corpus", side_effect=fake_copy
            ), patch.object(effect_benchmark, "run_row", side_effect=fake_row), patch.object(
                effect_benchmark,
                "run_failure_probe",
                return_value={"status": "passed", "checks": {}, "provider_process_starts": 1},
            ):
                report = effect_benchmark.run_benchmark(self.root / "protocol.json", source, output)

            raw = json.loads((output / "raw-results.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "failed")
            self.assertFalse(report["checks"]["source_corpus_unchanged"])
            self.assertTrue(report["checks"]["benchmark_index_unchanged"])
            self.assertTrue(raw["corpus"]["source_drift_during_run"])
            self.assertEqual((output / "corpus/machine/knowledge.sqlite").read_bytes(), b"copied-machine-fixed")
            self.assertEqual((output / "corpus/agent-index.sqlite").read_bytes(), b"copied-legacy-fixed")


if __name__ == "__main__":
    unittest.main()
