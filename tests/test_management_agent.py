from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.common import CkbError
from ckb_core.management_agent import (
    MANAGEMENT_CAPABILITIES,
    _audit_event,
    _locked_registry,
    audit_manager_registry,
    binding_schema,
    canonical_binding_input,
    harness_capabilities,
)


class ManagementSchemaPersistenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-manager-")
        self.root = Path(self.temporary.name)
        self.registry = self.root / "manager.json"
        for name in ("workspace", "workspace/repo", "workspace/knowledge"):
            (self.root / name).mkdir(exist_ok=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def payload(self, **values: object) -> dict[str, object]:
        return {
            "schema_version": 1,
            "conversation_id": "conversation-fixture",
            "harness_id": "generic",
            "workspace_root": str(self.root / "workspace"),
            "repo_root": str(self.root / "workspace/repo"),
            "knowledge_base": str(self.root / "workspace/knowledge"),
            "integration_branch": "main",
            **values,
        }

    def test_public_schema_has_four_separate_capabilities_and_privacy_contract(self) -> None:
        schema = binding_schema()
        capability_fields = schema["properties"]["capabilities"]["properties"]
        self.assertEqual(set(capability_fields), set(MANAGEMENT_CAPABILITIES))
        self.assertFalse(schema["privacy"]["raw_conversation_content"])
        self.assertFalse(schema["privacy"]["credentials"])
        self.assertIn("transcript_path", schema["privacy"]["forbidden_fields"])

    def test_canonical_input_drops_unrecognized_sensitive_content(self) -> None:
        canonical, ignored = canonical_binding_input(
            self.payload(
                prompt="do not persist this prompt",
                secret="fixture-secret-value",
                transcript_path="/private/transcript.jsonl",
                arbitrary={"token": "nested-secret"},
            )
        )
        serialized = json.dumps(canonical, ensure_ascii=False)
        self.assertEqual(ignored, ["arbitrary", "prompt", "secret", "transcript_path"])
        self.assertNotIn("do not persist", serialized)
        self.assertNotIn("fixture-secret", serialized)
        self.assertNotIn("transcript", serialized)
        self.assertNotIn("nested-secret", serialized)

    def test_unknown_harness_declares_only_generic_binding(self) -> None:
        capabilities = harness_capabilities("unknown-harness")
        self.assertTrue(capabilities["binding"]["available"])
        self.assertFalse(capabilities["prompt_injection"]["available"])
        self.assertFalse(capabilities["event_sync"]["available"])
        self.assertFalse(capabilities["task_dispatch"]["available"])

    def test_malformed_registry_is_reported_without_replacement(self) -> None:
        original = b'{"schema_version": 99, "prompt": "private"}\n'
        self.registry.write_bytes(original)
        result = audit_manager_registry(self.registry)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.registry.read_bytes(), original)

    def test_locked_registry_serializes_concurrent_audit_events(self) -> None:
        def append(index: int) -> None:
            with _locked_registry(self.registry) as (_path, value):
                value["audit_log"].append(_audit_event(None, "fixture", "passed", f"event-{index}"))

        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(append, range(24)))
        stored = json.loads(self.registry.read_text(encoding="utf-8"))
        self.assertEqual(len(stored["audit_log"]), 24)
        self.assertEqual(audit_manager_registry(self.registry)["status"], "passed")

    def test_canonical_input_rejects_missing_identity(self) -> None:
        payload = self.payload()
        del payload["conversation_id"]
        with self.assertRaises(CkbError):
            canonical_binding_input(payload)


if __name__ == "__main__":
    unittest.main()
