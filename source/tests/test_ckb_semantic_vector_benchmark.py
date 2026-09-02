from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "prototypes/ckb-semantic-vector-benchmark"
FIXTURE = ROOT / "tests/fixtures/semantic-vector-retrieval"


def load_module(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


benchmark = load_module("ckb_semantic_vector_benchmark", PROTOTYPE / "benchmark.py")
recompute = load_module("ckb_semantic_vector_recompute", PROTOTYPE / "recompute.py")


class FrozenContractTests(unittest.TestCase):
    def test_protocol_freezes_three_arms_and_existing_twelve_labels(self) -> None:
        protocol = json.loads((FIXTURE / "protocol.json").read_text(encoding="utf-8"))
        source = ROOT / protocol["questions_source"]["path"]
        original = json.loads(source.read_text(encoding="utf-8"))
        self.assertEqual(protocol["status"], "frozen")
        self.assertTrue(protocol["frozen_before_effect_run"])
        self.assertEqual(
            [item["id"] for item in protocol["arms"]],
            ["sqlite-current", "semantic-vector", "hybrid-rrf"],
        )
        self.assertEqual(protocol["questions"], original["questions"])
        self.assertEqual(len(protocol["questions"]), 12)
        self.assertEqual(protocol["execution"]["max_results"], 8)
        self.assertEqual(protocol["execution"]["cold_runs"], 1)
        self.assertEqual(protocol["execution"]["hot_runs"], 5)
        self.assertEqual(
            hashlib.sha256(source.read_bytes()).hexdigest(),
            protocol["questions_source"]["sha256"],
        )

    def test_protocol_schema_drift_is_rejected_before_external_reads(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            protocol_path = Path(temporary) / "protocol.json"
            protocol_path.write_text(
                json.dumps({"schema_version": 2, "status": "frozen"}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "schema version mismatch"):
                benchmark.validate_protocol(
                    protocol_path,
                    Path(temporary) / "missing-corpus",
                    Path(temporary) / "missing-manifest",
                    Path(temporary) / "missing-model",
                )

    def test_model_manifest_is_revision_and_file_hash_pinned(self) -> None:
        protocol = json.loads((FIXTURE / "protocol.json").read_text(encoding="utf-8"))
        manifest = json.loads((FIXTURE / "model-artifact-manifest.json").read_text())
        self.assertEqual(manifest["status"], "verified-local-snapshot")
        self.assertEqual(manifest["revision"], protocol["model"]["artifact_revision"])
        self.assertEqual(len(manifest["files"]), 8)
        self.assertEqual(sum(item["bytes"] for item in manifest["files"]), manifest["total_bytes"])
        self.assertTrue(all(len(item["sha256"]) == 64 for item in manifest["files"]))


class DriftAndAvailabilityTests(unittest.TestCase):
    def test_model_identity_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = root / "model"
            model.mkdir()
            artifact = model / "model.onnx"
            artifact.write_bytes(b"fixed")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "status": "verified-local-snapshot",
                        "repository": "fixture/model",
                        "revision": "fixed-revision",
                        "files": [
                            {
                                "path": "model.onnx",
                                "bytes": 5,
                                "sha256": hashlib.sha256(b"fixed").hexdigest(),
                            }
                        ],
                        "total_bytes": 5,
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(benchmark.validate_model_artifacts(model, manifest)["files"], 1)
            artifact.write_bytes(b"drift")
            with self.assertRaisesRegex(benchmark.ModelUnavailable, "identity drift"):
                benchmark.validate_model_artifacts(model, manifest)

    def test_missing_engine_has_structured_unavailable_evidence(self) -> None:
        missing = importlib.metadata.PackageNotFoundError("fastembed")
        with patch.object(importlib.metadata, "version", side_effect=missing):
            with self.assertRaises(benchmark.EngineUnavailable):
                benchmark.engine_identity("0.8.0")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            report = benchmark._write_unavailable(
                output, "engine-unavailable", benchmark.EngineUnavailable("missing")
            )
            self.assertEqual(report["status"], "engine-unavailable")
            self.assertEqual(report["effect_claim"], "not-measured")
            self.assertEqual(
                json.loads((output / "report.json").read_text())["status"],
                "engine-unavailable",
            )

    def test_index_digest_drift_is_rejected(self) -> None:
        try:
            import numpy as np
        except ImportError:
            self.skipTest("NumPy is required for the isolated vector index test")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            documents = [
                {
                    "entity_id": "e1",
                    "source_path": "scripts/a.py",
                    "qualified_name": "a",
                    "text": "fixed",
                }
            ]
            documents_path = root / "documents.json"
            documents_path.write_text(json.dumps(documents), encoding="utf-8")
            vectors_path = root / "vectors.npy"
            with vectors_path.open("wb") as stream:
                np.save(stream, np.asarray([[1.0, 0.0]], dtype=np.float32), allow_pickle=False)
            manifest = {
                "documents_digest": benchmark.documents_digest(documents),
                "files": {
                    "documents.json": {
                        "sha256": hashlib.sha256(documents_path.read_bytes()).hexdigest()
                    },
                    "vectors.npy": {
                        "sha256": hashlib.sha256(vectors_path.read_bytes()).hexdigest()
                    },
                },
            }
            (root / "index-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            protocol = {"model": {"dimension": 2, "dtype": "float32"}}
            loaded, _, _ = benchmark._load_index(root, protocol)
            self.assertEqual(list(loaded.shape), [1, 2])
            vectors_path.write_bytes(vectors_path.read_bytes() + b"drift")
            with self.assertRaisesRegex(ValueError, "vectors digest drift"):
                benchmark._load_index(root, protocol)

    def test_index_size_is_reported_after_final_manifest_serialization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "vectors.npy").write_bytes(b"vector-payload")
            (root / "documents.json").write_bytes(b"document-payload\n")
            payload_bytes = (root / "vectors.npy").stat().st_size + (
                root / "documents.json"
            ).stat().st_size
            benchmark.json_write(root / "index-manifest.json", {"payload_bytes": payload_bytes})
            protocol = {
                "index": {
                    "files": ["vectors.npy", "documents.json", "index-manifest.json"]
                }
            }
            accounting = benchmark.index_size_accounting(root, protocol)
            self.assertEqual(accounting["index_payload_bytes"], payload_bytes)
            self.assertEqual(
                accounting["index_bytes"],
                payload_bytes + (root / "index-manifest.json").stat().st_size,
            )
            benchmark.json_write(
                root / "index-manifest.json",
                {"payload_bytes": payload_bytes, "index_bytes": accounting["index_bytes"]},
            )
            with self.assertRaisesRegex(ValueError, "self-referential"):
                benchmark.index_size_accounting(root, protocol)


class DeterministicMetricTests(unittest.TestCase):
    def test_rank_metrics_and_missing_reason_are_recomputed(self) -> None:
        documents = [
            {"rank": 1, "source_path": "scripts/other.py"},
            {"rank": 2, "source_path": "scripts/target.py"},
        ]
        labels = [
            {"source_path": "scripts/target.py", "grade": 3},
            {"source_path": "scripts/missing.py", "grade": 1},
        ]
        result = benchmark.quality_for_ranking(documents, labels)
        self.assertEqual(result["recall_at_8"], 0.5)
        self.assertEqual(result["mrr_at_8"], 0.5)
        self.assertEqual(result["relevant_hits"][0]["rank"], 2)
        self.assertEqual(result["missing"][0]["reason"], "not-selected")

    def test_hybrid_ties_have_stable_path_order(self) -> None:
        sqlite_hits = [
            {"rank": 1, "source_path": "scripts/b.py", "entity_id": "b"},
            {"rank": 2, "source_path": "scripts/a.py", "entity_id": "a"},
        ]
        vector_hits = [
            {"rank": 1, "source_path": "scripts/a.py", "entity_id": "a"},
            {"rank": 2, "source_path": "scripts/b.py", "entity_id": "b"},
        ]
        documents = [
            {"source_path": "scripts/a.py", "text": "a"},
            {"source_path": "scripts/b.py", "text": "b"},
        ]
        first = benchmark._hybrid_ranking(sqlite_hits, vector_hits, documents, 60, 8)
        second = benchmark._hybrid_ranking(sqlite_hits, vector_hits, documents, 60, 8)
        self.assertEqual(first, second)
        self.assertEqual([item["source_path"] for item in first], ["scripts/a.py", "scripts/b.py"])
        self.assertEqual(benchmark.result_signature(first), benchmark.result_signature(second))

    def test_independent_aggregate_recomputes_report_fields(self) -> None:
        protocol = {
            "questions": [
                {
                    "id": "q1",
                    "relevance": [{"source_path": "scripts/a.py", "grade": 3}],
                }
            ]
        }
        rows = []
        for index, state in enumerate(["cold", "hot", "hot", "hot", "hot", "hot"]):
            rows.append(
                {
                    "arm": "semantic-vector",
                    "question_id": "q1",
                    "cache_state": state,
                    "latency_ms": float(index + 1),
                    "selected_documents": [{"rank": 1, "source_path": "scripts/a.py"}],
                    "first_pack_estimated_tokens": 10,
                    "result_signature": "same",
                }
            )
        raw = {
            "rows": rows,
            "worker_resources": [
                {
                    "arm": "semantic-vector",
                    "peak_rss_bytes": 123,
                    "peak_extra_child_processes": 0,
                }
            ],
        }
        result = recompute.aggregate(protocol, raw, "semantic-vector")
        self.assertEqual(result["recall_at_8"], 1.0)
        self.assertEqual(result["mrr_at_8"], 1.0)
        self.assertEqual(result["ndcg_at_8"], 1.0)
        self.assertEqual(result["worker_process_starts"], 1)
        self.assertEqual(result["deterministic_question_rate"], 1.0)


class ResourceAndIsolationTests(unittest.TestCase):
    def test_json_writer_uses_utf8_lf_on_windows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result.json"
            benchmark.json_write(output, {"结论": "固定"})
            data = output.read_bytes()
            self.assertNotIn(b"\r\n", data)
            self.assertEqual(data.count(b"\n"), 3)
            self.assertEqual(json.loads(data.decode("utf-8")), {"结论": "固定"})

    def test_resource_limits_have_positive_and_negative_cases(self) -> None:
        limits = {
            "index_build_seconds_max": 10,
            "peak_rss_bytes_max": 100,
            "index_bytes_max": 50,
            "runtime_and_model_bytes_max": 200,
            "extra_child_processes_max": 1,
            "network_calls_during_measurement_max": 0,
        }
        resources = {
            "first_index_seconds": 9,
            "peak_rss_bytes": 99,
            "index_bytes": 49,
            "runtime_and_model_bytes": 199,
            "peak_extra_child_processes": 1,
            "network_attempts": 0,
        }
        self.assertTrue(all(benchmark.evaluate_resource_limits(resources, limits).values()))
        for name, value in (
            ("first_index_seconds", 11),
            ("peak_rss_bytes", 101),
            ("index_bytes", 51),
            ("runtime_and_model_bytes", 201),
            ("peak_extra_child_processes", 2),
            ("network_attempts", 1),
        ):
            drifted = dict(resources)
            drifted[name] = value
            self.assertFalse(all(benchmark.evaluate_resource_limits(drifted, limits).values()))

    def test_network_guard_blocks_and_records_connection_attempt(self) -> None:
        with benchmark.network_guard() as attempts:
            probe = socket.socket()
            try:
                with self.assertRaisesRegex(RuntimeError, "network is disabled"):
                    probe.connect(("127.0.0.1", 9))
            finally:
                probe.close()
        self.assertEqual(attempts, ["('127.0.0.1', 9)"])


if __name__ == "__main__":
    unittest.main()
