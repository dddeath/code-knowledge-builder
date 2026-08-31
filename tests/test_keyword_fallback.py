from __future__ import annotations

import json
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
    KeywordProviderConfig,
    canonical_keyword_request,
    audit_keyword_cache,
    keyword_cache_key,
    parse_provider_json,
    run_keyword_provider,
    validate_provider_response,
)


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


if __name__ == "__main__":
    unittest.main()
