from __future__ import annotations

import json
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ckb_core.common import CkbError
from ckb_core.keyword_fallback import (
    KeywordFallbackOptions,
    KeywordProviderConfig,
    canonical_keyword_request,
    audit_keyword_cache,
    audit_keyword_fallback,
    keyword_cache_key,
    keyword_cache_path,
    parse_provider_json,
    run_keyword_provider,
    validate_provider_response,
)
from ckb_core.keyword_benchmark import run_keyword_benchmark
from ckb_core.machine_knowledge import retrieve_machine
from ckb_core.stdio_server import serve_stdio


FIXTURE = Path(__file__).parent / "fixtures" / "keyword_provider.py"
QUESTION = "定位机器检索的关键词慢路径"
CONFIG = KeywordProviderConfig(
    command=(sys.executable, str(FIXTURE)),
    provider="fixture",
    model="fixture-model",
    version="1",
)


def fixture_output(mode: str = "passed") -> str:
    environment = os.environ.copy()
    environment["CKB_FAKE_KEYWORD_PROVIDER_MODE"] = mode
    return subprocess.run(
        CONFIG.command,
        input=json.dumps(canonical_keyword_request(QUESTION), ensure_ascii=False),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    ).stdout


class KeywordFallbackSchemaTests(unittest.TestCase):
    def test_canonical_fixture_output_is_bounded_and_normalized(self) -> None:
        validated = validate_provider_response(
            parse_provider_json(fixture_output()),
            question=QUESTION,
            config=CONFIG,
        )
        self.assertEqual(validated["status"], "passed")
        self.assertEqual(validated["keywords"], ["machine retrieval", "关键词扩展"])
        self.assertEqual(validated["anchors"], ["retrieve_machine"])
        self.assertEqual(validated["usage"]["total_tokens"], 30)

    def test_invalid_json_is_rejected(self) -> None:
        with self.assertRaisesRegex(CkbError, "invalid JSON"):
            parse_provider_json(fixture_output("invalid-json"))

    def test_oversized_duplicate_injected_and_invalid_candidates_are_rejected(self) -> None:
        modes = {
            "too-many-keywords": "at most 16",
            "duplicate-keywords": "duplicate",
            "prompt-injection": "prompt-injection",
            "unsupported-characters": "unsupported characters",
            "wrong-request": "does not match",
        }
        for mode, message in modes.items():
            with self.subTest(mode=mode), self.assertRaisesRegex(CkbError, message):
                validate_provider_response(
                    parse_provider_json(fixture_output(mode)),
                    question=QUESTION,
                    config=CONFIG,
                )

    def test_canonical_failure_types_are_preserved_without_candidates(self) -> None:
        for mode in ("rate-limit", "missing-credentials"):
            with self.subTest(mode=mode):
                validated = validate_provider_response(
                    parse_provider_json(fixture_output(mode)),
                    question=QUESTION,
                    config=CONFIG,
                )
                self.assertEqual(validated["status"], "failed")
                self.assertEqual(validated["failure_type"], mode)
                self.assertEqual(validated["keywords"], [])


class KeywordFallbackAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.output = Path(self.temporary.name) / "output"
        self.output.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def config(self, *, timeout: float = 2.0, retries: int = 1, required_environment=()) -> KeywordProviderConfig:
        return KeywordProviderConfig(
            command=CONFIG.command,
            provider=CONFIG.provider,
            model=CONFIG.model,
            version=CONFIG.version,
            timeout_seconds=timeout,
            retries=retries,
            required_environment=tuple(required_environment),
        )

    def run_mode(self, mode: str, **config_values):
        with patch.dict(os.environ, {"CKB_FAKE_KEYWORD_PROVIDER_MODE": mode}, clear=False):
            return run_keyword_provider(self.output, QUESTION, self.config(**config_values), use_cache=False)

    def test_command_adapter_caches_only_validated_output_under_identity_key(self) -> None:
        with patch.dict(os.environ, {"CKB_FAKE_KEYWORD_PROVIDER_MODE": "passed"}, clear=False):
            cold = run_keyword_provider(self.output, QUESTION, self.config())
            hot = run_keyword_provider(self.output, QUESTION, self.config())
        self.assertEqual(cold["status"], "passed")
        self.assertFalse(cold["cache_hit"])
        self.assertEqual(cold["attempts"], 1)
        self.assertTrue(Path(cold["cache"]).is_file())
        self.assertEqual(hot["status"], "passed")
        self.assertTrue(hot["cache_hit"])
        self.assertEqual(hot["attempts"], 0)
        self.assertEqual(hot["usage"]["total_tokens"], 0)
        self.assertEqual(hot["cached_usage"]["total_tokens"], 30)
        self.assertEqual(cold["cache_key"], keyword_cache_key(QUESTION, self.config()))
        cache_text = Path(cold["cache"]).read_text(encoding="utf-8")
        self.assertNotIn(QUESTION, cache_text)
        self.assertNotIn("question", cache_text)
        self.assertEqual(audit_keyword_cache(self.output)["status"], "passed")

    def test_invalid_json_output_and_process_failures_fall_back(self) -> None:
        expected = {
            "invalid-json": "invalid-json",
            "too-many-keywords": "invalid-output",
            "prompt-injection": "invalid-output",
            "exit-nonzero": "process-failed",
            "rate-limit": "rate-limit",
        }
        for mode, failure_type in expected.items():
            with self.subTest(mode=mode):
                result = self.run_mode(mode)
                self.assertEqual(result["status"], "failed")
                self.assertEqual(result["failure_type"], failure_type)
                self.assertEqual(result["attempts"], 2 if failure_type in {"process-failed", "rate-limit"} else 1)
                self.assertEqual(result["keywords"], [])

    def test_timeout_is_bounded_and_retried_at_most_once(self) -> None:
        result = self.run_mode("timeout", timeout=0.1)
        self.assertEqual(result["failure_type"], "timeout")
        self.assertEqual(result["attempts"], 2)
        self.assertLess(result["latency_ms"], 1500)

    def test_missing_credentials_prevents_process_start(self) -> None:
        environment_name = "CKB_TEST_KEYWORD_PROVIDER_CREDENTIAL"
        with patch.dict(os.environ, {environment_name: ""}, clear=False), patch(
            "ckb_core.keyword_fallback.subprocess.run"
        ) as launched:
            result = run_keyword_provider(
                self.output,
                QUESTION,
                self.config(required_environment=(environment_name,)),
            )
        self.assertEqual(result["failure_type"], "missing-credentials")
        self.assertEqual(result["attempts"], 0)
        self.assertEqual(result["missing_environment"], [environment_name])
        launched.assert_not_called()

    def test_cache_audit_rejects_secret_shaped_content(self) -> None:
        with patch.dict(os.environ, {"CKB_FAKE_KEYWORD_PROVIDER_MODE": "passed"}, clear=False):
            result = run_keyword_provider(self.output, QUESTION, self.config())
        path = Path(result["cache"])
        value = json.loads(path.read_text(encoding="utf-8"))
        value["response"]["keywords"] = ["sk-abcdefghijklmnopqrstuvwxyz123456"]
        path.write_text(json.dumps(value), encoding="utf-8")
        audit = audit_keyword_cache(self.output)
        self.assertEqual(audit["status"], "failed")
        self.assertTrue(any("credential-shaped" in error for error in audit["errors"]))


class KeywordFallbackRetrievalWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.output = Path(self.temporary.name) / "output"
        (self.output / "machine").mkdir(parents=True)
        (self.output / "machine" / "knowledge.sqlite").write_bytes(b"fixture")
        self.options = KeywordFallbackOptions(config=CONFIG, force=False, use_cache=False)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_default_result_is_returned_unchanged_and_provider_is_not_called(self) -> None:
        baseline = {"status": "passed", "terms": ["base"], "anchors": [], "selected_entities": ["entity"]}
        with patch(
            "ckb_core.machine_knowledge._retrieve_machine_deterministic", return_value=baseline
        ) as deterministic, patch("ckb_core.machine_knowledge.run_keyword_provider") as provider:
            result = retrieve_machine(self.output, QUESTION, 1200, 8, "fast")
        self.assertIs(result, baseline)
        deterministic.assert_called_once_with(self.output, QUESTION, 1200, 8, "fast")
        provider.assert_not_called()

    def test_allow_mode_does_not_start_provider_after_passed_result(self) -> None:
        baseline = {"status": "passed", "terms": ["base"], "anchors": [], "selected_entities": ["entity"]}
        with patch(
            "ckb_core.machine_knowledge._retrieve_machine_deterministic", return_value=baseline
        ), patch("ckb_core.machine_knowledge.run_keyword_provider") as provider:
            result = retrieve_machine(
                self.output,
                QUESTION,
                1200,
                8,
                "fast",
                keyword_fallback=self.options,
            )
        provider.assert_not_called()
        self.assertEqual(result["keyword_fallback"]["status"], "skipped")
        self.assertEqual(result["keyword_fallback"]["provider"]["status"], "not-started")
        self.assertTrue(Path(result["keyword_fallback_record"]).is_file())

    def test_needs_source_read_uses_validated_terms_then_deterministic_selection(self) -> None:
        baseline = {"status": "needs-source-read", "terms": ["base"], "anchors": []}
        selected = {
            "status": "passed",
            "terms": ["base", "orderservice"],
            "anchors": ["orderservice"],
            "selected_entities": [{"entity_id": "entity-1"}],
            "estimated_tokens": 100,
        }
        provider_result = {
            "status": "passed",
            "provider": "fixture",
            "model": "fixture-model",
            "version": "1",
            "request_id": "keyword-test",
            "keywords": ["OrderService"],
            "anchors": ["OrderService"],
            "rewrites": ["订单服务保存入口"],
            "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2, "cost_usd": 0.0},
            "attempts": 1,
            "latency_ms": 1.0,
            "cache_hit": False,
            "cache_key": "a" * 64,
        }
        with patch(
            "ckb_core.machine_knowledge._retrieve_machine_deterministic",
            side_effect=[baseline, selected],
        ) as deterministic, patch(
            "ckb_core.machine_knowledge.run_keyword_provider", return_value=provider_result
        ) as provider:
            result = retrieve_machine(
                self.output,
                QUESTION,
                1200,
                8,
                "fast",
                keyword_fallback=self.options,
            )
        provider.assert_called_once()
        second = deterministic.call_args_list[1]
        self.assertIn("orderservice", second.kwargs["extra_terms"])
        self.assertEqual(second.kwargs["extra_anchors"], ["orderservice"])
        self.assertEqual(result["keyword_fallback"]["status"], "passed")
        self.assertTrue(result["keyword_fallback"]["final"]["deterministic_selection"])
        self.assertEqual(audit_keyword_fallback(self.output)["status"], "passed")

    def test_provider_failure_returns_original_result_with_structured_reason(self) -> None:
        baseline = {"status": "needs-source-read", "terms": ["base"], "anchors": []}
        provider_result = {
            "status": "failed",
            "failure_type": "timeout",
            "provider": "fixture",
            "model": "fixture-model",
            "version": "1",
            "keywords": [],
            "anchors": [],
            "rewrites": [],
            "usage": {},
            "attempts": 2,
            "latency_ms": 200.0,
            "cache_hit": False,
        }
        with patch(
            "ckb_core.machine_knowledge._retrieve_machine_deterministic", return_value=baseline
        ), patch("ckb_core.machine_knowledge.run_keyword_provider", return_value=provider_result):
            result = retrieve_machine(
                self.output,
                QUESTION,
                keyword_fallback=self.options,
            )
        self.assertEqual(result["status"], "needs-source-read")
        self.assertEqual(result["keyword_fallback"]["status"], "fallback")
        self.assertEqual(result["keyword_fallback"]["provider"]["failure_type"], "timeout")

    def test_stdio_exposes_the_same_nested_canonical_options(self) -> None:
        captured = []

        def fake_retrieve(path, question, budget, max_pages, profile, **kwargs):
            captured.append(kwargs["keyword_fallback"])
            return {
                "status": "passed",
                "pack": "fixture-pack",
                "record": "fixture-record",
            }

        request = {
            "id": "fallback-1",
            "method": "retrieve",
            "question": QUESTION,
            "keyword_fallback": {
                "mode": "force",
                "command": list(CONFIG.command),
                "provider": CONFIG.provider,
                "model": CONFIG.model,
                "version": CONFIG.version,
                "timeout_seconds": 2.0,
                "retries": 0,
                "required_environment": [],
                "use_cache": False,
            },
        }
        destination = io.StringIO()
        summary = serve_stdio(
            self.output,
            input_stream=io.StringIO(json.dumps(request) + "\n"),
            output_stream=destination,
            retrieve=fake_retrieve,
        )
        response = json.loads(destination.getvalue())
        self.assertTrue(response["ok"])
        self.assertTrue(captured[0].force)
        self.assertFalse(captured[0].use_cache)
        self.assertEqual(summary["succeeded"], 1)


class KeywordFallbackBenchmarkTests(unittest.TestCase):
    def test_fixed_benchmark_compares_quality_latency_context_usage_and_restores_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "output"
            output.mkdir()
            cases = root / "cases.json"
            cases.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "cases": [
                            {
                                "id": "case-1",
                                "question": QUESTION,
                                "expected_names": ["OrderService"],
                                "expected_source_paths": ["py/service.py"],
                                "budget": 1200,
                                "max_pages": 8,
                                "profile": "fast",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report_path = root / "benchmark.json"
            baseline = {"status": "needs-source-read", "selected_entities": []}
            selected = [{"name": "OrderService", "qualified_name": "OrderService", "source_path": "py/service.py"}]
            cold = {
                "status": "passed",
                "selected_entities": selected,
                "estimated_tokens": 500,
                "keyword_fallback": {
                    "status": "passed",
                    "provider": {
                        "status": "passed",
                        "provider": "fixture",
                        "model": "fixture-model",
                        "version": "1",
                        "request_id": "keyword-cold",
                        "latency_ms": 20.0,
                        "cache_hit": False,
                        "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15, "cost_usd": 0.001},
                    },
                },
            }
            hot = {
                "status": "passed",
                "selected_entities": selected,
                "estimated_tokens": 500,
                "keyword_fallback": {
                    "status": "passed",
                    "provider": {
                        "status": "passed",
                        "provider": "fixture",
                        "model": "fixture-model",
                        "version": "1",
                        "request_id": "keyword-hot",
                        "latency_ms": 0.0,
                        "cache_hit": True,
                        "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost_usd": 0.0},
                        "cached_usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15, "cost_usd": 0.001},
                    },
                },
            }
            cache_path = keyword_cache_path(output, QUESTION, CONFIG)
            cache_path.parent.mkdir(parents=True)
            cache_path.write_bytes(b"prior-cache-bytes")
            with patch(
                "ckb_core.keyword_benchmark.retrieve_machine",
                side_effect=[baseline, cold, hot],
            ):
                report = run_keyword_benchmark(output, cases, report_path, CONFIG)
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["summary"]["quality_claim"], "measured-gain")
            self.assertEqual(report["cases"][0]["quality_delta"], 1.0)
            self.assertTrue(report["cases"][0]["hot"]["cache_hit"])
            self.assertEqual(report["cases"][0]["hot"]["usage"]["total_tokens"], 0)
            self.assertTrue(report_path.is_file())
            self.assertEqual(cache_path.read_bytes(), b"prior-cache-bytes")


if __name__ == "__main__":
    unittest.main()
