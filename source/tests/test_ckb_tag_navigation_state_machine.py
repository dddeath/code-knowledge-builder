from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
PROTOTYPE = REPO / "prototypes" / "ckb-tag-navigation"
FIXTURE = REPO / "tests" / "fixtures" / "tag-navigation"
sys.path.insert(0, str(PROTOTYPE))

from ckb_tag_navigation.contracts import canonical_json_bytes
from ckb_tag_navigation.state_machine import audit_database
from ckb_tag_navigation.store import replay_with_rollback


COMMIT = "19152b227ccf687e7e4d89337d421c22a4e1a75f"
AS_OF = "2026-09-03T00:00:00Z"


class TagNavigationStateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-tag-state-")
        self.root = Path(self.temporary.name)
        self.database = self.root / "tags.sqlite"
        replay_with_rollback(FIXTURE / "assertions.jsonl", self.database, self.root / "rollback.json")
        self.policy = json.loads((FIXTURE / "policy.json").read_text(encoding="utf-8"))
        self.audit = audit_database(self.database, self.policy, COMMIT, AS_OF)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def by_tag(self, tag: str) -> dict:
        return next(result for result in self.audit["results"] if result["tag"] == tag)

    def test_all_four_states_and_counts_are_frozen(self) -> None:
        self.assertEqual({"candidate": 1, "confirmed": 5, "contested": 1, "deprecated": 3}, self.audit["summary"])
        self.assertEqual("confirmed", self.by_tag("topic/navigation")["state"])
        self.assertEqual("candidate", self.by_tag("interface/obsidian")["state"])
        self.assertEqual("contested", self.by_tag("topic/retrieval")["state"])
        self.assertEqual("deprecated", self.by_tag("lifecycle/stale")["state"])

    def test_single_agent_revote_counts_once(self) -> None:
        result = self.by_tag("interface/obsidian")
        self.assertEqual(1, result["metrics"]["support_votes"])
        self.assertEqual(1, result["metrics"]["independent_support_agents"])
        self.assertEqual(1, result["metrics"]["superseded_vote_count"])
        self.assertIn("INDEPENDENT_AGENTS_BELOW_MINIMUM", result["reason_codes"])

    def test_opposition_ratio_commit_drift_staleness_and_retraction_have_reason_codes(self) -> None:
        self.assertEqual(0.333333, self.by_tag("topic/retrieval")["metrics"]["opposition_ratio"])
        self.assertEqual(["OPPOSITION_RATIO_EXCEEDED"], self.by_tag("topic/retrieval")["reason_codes"])
        self.assertIn("COMMIT_DRIFT", self.by_tag("lifecycle/drift")["reason_codes"])
        self.assertIn("STALE_EVIDENCE", self.by_tag("lifecycle/stale")["reason_codes"])
        self.assertIn("ALL_SUPPORT_RETRACTED", self.by_tag("topic/withdrawn")["reason_codes"])

    def test_repeated_audit_bytes_are_identical(self) -> None:
        second = audit_database(self.database, self.policy, COMMIT, AS_OF)
        self.assertEqual(canonical_json_bytes(self.audit), canonical_json_bytes(second))
        keys = [(item["target"]["path"], item["tag"]) for item in self.audit["results"]]
        self.assertEqual(sorted(keys), keys)


if __name__ == "__main__":
    unittest.main()
