from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "prototypes/ckb-semantic-vector-benchmark"
FIXTURE = ROOT / "tests/fixtures/qmd-fixed-three-arm"


def load_module(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


benchmark = load_module("ckb_qmd_three_arm_benchmark", PROTOTYPE / "qmd_benchmark.py")
recompute = load_module("ckb_qmd_three_arm_recompute", PROTOTYPE / "qmd_recompute.py")


class FrozenQmdContractTests(unittest.TestCase):
    def test_protocol_reuses_exact_corpus_questions_budget_and_judge(self) -> None:
        protocol = json.loads((FIXTURE / "protocol.json").read_text(encoding="utf-8"))
        source = ROOT / protocol["questions_source"]["path"]
        source_value = json.loads(source.read_text(encoding="utf-8"))
        self.assertEqual(protocol["status"], "frozen")
        self.assertTrue(protocol["frozen_before_effect_run"])
        self.assertEqual(
            [item["id"] for item in protocol["arms"]],
            ["sqlite-current", "semantic-vector", "qmd-vsearch"],
        )
        self.assertEqual(protocol["questions"], source_value["questions"])
        self.assertEqual(
            hashlib.sha256(source.read_bytes()).hexdigest(),
            protocol["questions_source"]["sha256"],
        )
        self.assertEqual(protocol["execution"]["budget_tokens"], 2400)
        self.assertEqual(protocol["execution"]["max_results"], 8)
        self.assertEqual(protocol["protocol_revision"], 2)
        self.assertEqual(protocol["resource_limits"]["extra_child_processes_max"], 3)
        self.assertEqual(
            protocol["execution"]["ranking_truncation"],
            "source-path-deduplicate-then-budget-then-top-k",
        )
        self.assertEqual(protocol["random_seed"], 0)
        self.assertEqual(
            protocol["qmd"]["candidate_depth"],
            protocol["corpus"]["entity_rows_with_source_path"],
        )
        self.assertEqual(protocol["qmd"]["environment"]["QMD_LLAMA_GPU"], "vulkan")

    def test_qmd_runtime_lock_and_model_are_pinned(self) -> None:
        manifest_path = FIXTURE / "qmd-runtime-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        lock = ROOT / manifest["package_lock"]["path"]
        self.assertEqual(manifest["package"]["version"], "2.8.3")
        self.assertEqual(manifest["package"]["git_head"], "facd35e01359e59d938bc9418e93fb9318addee3")
        self.assertEqual(hashlib.sha256(lock.read_bytes()).hexdigest(), manifest["package_lock"]["sha256"])
        self.assertEqual(manifest["model"]["bytes"], 333590944)
        self.assertEqual(len(manifest["model"]["sha256"]), 64)
        self.assertEqual(
            hashlib.sha256((PROTOTYPE / "qmd_adapter.mjs").read_bytes()).hexdigest(),
            manifest["adapter"]["sha256"],
        )


class QmdAvailabilityAndFailureTests(unittest.TestCase):
    def test_missing_qmd_package_is_structured_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(benchmark.QmdUnavailable, "Node executable is missing"):
                benchmark.qmd_runtime_identity(
                    root / "missing-package",
                    root / "missing-model",
                    FIXTURE / "qmd-runtime-manifest.json",
                    root / "missing-node",
                )
            output = root / "result"
            report = benchmark._write_unavailable(
                output,
                "qmd-unavailable",
                benchmark.QmdUnavailable("fixture missing runtime"),
            )
            self.assertEqual(report["status"], "qmd-unavailable")
            self.assertEqual(report["effect_claim"], "not-measured")

    def test_qmd_process_failure_is_not_treated_as_a_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"FAKE_QMD_MODE": "process-failure"}
        ):
            root = Path(temporary)
            with self.assertRaisesRegex(benchmark.QmdExecutionFailed, "exit 7"):
                benchmark._run_qmd_build_process(
                    {"corpus": {"entity_rows_with_source_path": 1}, "qmd": {"collection": "fixture"}},
                    [{"entity_id": "e1", "source_path": "a.py", "qualified_name": "a", "text": "fixed"}],
                    root / "package",
                    root / "model.gguf",
                    Path(sys.executable),
                    root / "qmd",
                    self._identity(),
                    FIXTURE / "fake_qmd_adapter.py",
                )

    def test_qmd_build_output_format_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"FAKE_QMD_MODE": "build-output-drift"}
        ):
            root = Path(temporary)
            with self.assertRaisesRegex(benchmark.QmdOutputDrift, "envelope drift"):
                benchmark._run_qmd_build_process(
                    {"corpus": {"entity_rows_with_source_path": 1}, "qmd": {"collection": "fixture"}},
                    [{"entity_id": "e1", "source_path": "a.py", "qualified_name": "a", "text": "fixed"}],
                    root / "package",
                    root / "model.gguf",
                    Path(sys.executable),
                    root / "qmd",
                    self._identity(),
                    FIXTURE / "fake_qmd_adapter.py",
                )

    def test_qmd_query_result_format_drift_is_rejected(self) -> None:
        payload = {
            "schema_version": 1,
            "kind": "qmd-query",
            "identity": {
                "package_name": "@tobilu/qmd",
                "package_version": "2.8.3",
                "build_commit": "facd35e",
                "node_version": "v24.19.0",
            },
            "question_id": "q01",
            "cache_state": "cold",
            "run_index": 1,
            "latency_ms": 1.0,
            "results": [{"file": "000000.md", "score": 0.5}],
        }
        with self.assertRaisesRegex(benchmark.QmdOutputDrift, "field drift"):
            benchmark.validate_qmd_query_payload(
                payload, self._identity(), "q01", "cold", 1
            )

    @staticmethod
    def _identity() -> dict[str, str]:
        return {
            "package_name": "@tobilu/qmd",
            "package_version": "2.8.3",
            "package_build_commit": "facd35e",
            "node_version": "v24.19.0",
        }


class CommonJudgeAndRecomputeTests(unittest.TestCase):
    def test_common_truncation_deduplicates_then_applies_budget_and_top_k(self) -> None:
        documents = [
            {"entity_id": "e1", "source_path": "a.py", "qualified_name": "a", "text": "a" * 8},
            {"entity_id": "e2", "source_path": "a.py", "qualified_name": "a2", "text": "b" * 8},
            {"entity_id": "e3", "source_path": "b.py", "qualified_name": "b", "text": "c" * 12},
            {"entity_id": "e4", "source_path": "c.py", "qualified_name": "c", "text": "d" * 8},
        ]
        hits = [
            {"entity_id": "e1", "source_path": "a.py", "score": 4},
            {"entity_id": "e2", "source_path": "a.py", "score": 3},
            {"entity_id": "e3", "source_path": "b.py", "score": 2},
            {"entity_id": "e4", "source_path": "c.py", "score": 1},
        ]
        selected = benchmark.apply_common_truncation(hits, documents, budget_tokens=5, top_k=8)
        self.assertEqual([item["source_path"] for item in selected], ["a.py", "b.py"])
        self.assertEqual(benchmark._visible_tokens(selected), 5)

    def test_quality_claims_distinguish_non_inferiority_improvement_and_regression(self) -> None:
        baseline = {"recall_at_8": 0.5, "mrr_at_8": 0.5, "ndcg_at_8": 0.5}
        self.assertEqual(benchmark.comparison(baseline, baseline)["quality_claim"], "point-metric-non-inferior")
        improved = {"recall_at_8": 0.6, "mrr_at_8": 0.5, "ndcg_at_8": 0.5}
        self.assertEqual(benchmark.comparison(baseline, improved)["quality_claim"], "improvement-demonstrated")
        regressed = {"recall_at_8": 0.6, "mrr_at_8": 0.4, "ndcg_at_8": 0.5}
        self.assertEqual(benchmark.comparison(baseline, regressed)["quality_claim"], "regression-observed")

    def test_recompute_accepts_qmd_as_the_third_arm(self) -> None:
        protocol = {"questions": [{"id": "q1", "relevance": [{"source_path": "a.py", "grade": 3}]}]}
        rows = []
        for index, state in enumerate(["cold", "hot", "hot", "hot", "hot", "hot"]):
            rows.append(
                {
                    "arm": "qmd-vsearch",
                    "question_id": "q1",
                    "cache_state": state,
                    "latency_ms": float(index + 1),
                    "selected_documents": [{"rank": 1, "source_path": "a.py"}],
                    "first_pack_estimated_tokens": 10,
                    "result_signature": "same",
                }
            )
        raw = {
            "rows": rows,
            "worker_resources": [
                {"arm": "qmd-vsearch", "peak_rss_bytes": 123, "peak_extra_child_processes": 0}
            ],
        }
        result = recompute.aggregate(protocol, raw, "qmd-vsearch")
        self.assertEqual(result["recall_at_8"], 1.0)
        self.assertEqual(result["deterministic_question_rate"], 1.0)


class CommittedResultTests(unittest.TestCase):
    def test_committed_result_is_recomputable_and_keeps_production_default(self) -> None:
        result = ROOT / "references/benchmarks/qmd-fixed-three-arm"
        report = json.loads((result / "report.json").read_text(encoding="utf-8"))
        raw = json.loads((result / "raw-results.json").read_text(encoding="utf-8"))
        recomputed = json.loads((result / "recomputed.json").read_text(encoding="utf-8"))
        protocol = FIXTURE / "protocol.json"
        self.assertEqual(report["status"], "passed")
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(len(raw["rows"]), 216)
        self.assertEqual(recomputed["status"], "passed")
        self.assertTrue(all(recomputed["checks"].values()))
        self.assertEqual(
            hashlib.sha256(protocol.read_bytes()).hexdigest(), report["protocol_sha256"]
        )
        self.assertFalse(report["decision"]["production_default_changed"])
        self.assertEqual(
            report["comparisons"]["qmd-vsearch_vs_sqlite-current"]["quality_claim"],
            "improvement-demonstrated",
        )
        self.assertEqual(
            report["comparisons"]["semantic-vector_vs_sqlite-current"]["quality_claim"],
            "regression-observed",
        )
        expected_failures = {
            "missing-qmd.json": "qmd-unavailable",
            "qmd-process-failure.json": "qmd-execution-failed",
            "qmd-output-drift.json": "qmd-output-drift",
        }
        for name, status in expected_failures.items():
            payload = json.loads((result / "failure-samples" / name).read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], status)
            self.assertEqual(payload["effect_claim"], "not-measured")


if __name__ == "__main__":
    unittest.main()
