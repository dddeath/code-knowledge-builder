from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ckb_core.common import CkbError
from ckb_core.keyword_fallback import (
    KeywordProviderConfig,
    canonical_keyword_request,
    parse_provider_json,
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


if __name__ == "__main__":
    unittest.main()
