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

from ckb_tag_navigation.projection import build_projection
from ckb_tag_navigation.state_machine import audit_database
from ckb_tag_navigation.store import replay_with_rollback


class TagNavigationProjectionTests(unittest.TestCase):
    def test_only_confirmed_tags_project_with_per_page_quota(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ckb-tag-project-") as temporary:
            root = Path(temporary)
            database = root / "tags.sqlite"
            replay_with_rollback(FIXTURE / "assertions.jsonl", database, root / "rollback.json")
            policy = json.loads((FIXTURE / "policy.json").read_text(encoding="utf-8"))
            audit = audit_database(database, policy, "19152b227ccf687e7e4d89337d421c22a4e1a75f", "2026-09-03T00:00:00Z")
            projection = build_projection(audit, policy)
        self.assertEqual("disabled", projection["production_integration"])
        self.assertEqual(3, projection["page_tag_limit"])
        pages = {entry["page"]: entry["tags"] for entry in projection["entries"]}
        self.assertEqual({"human/pages/navigation.md", "human/pages/quota.md"}, set(pages))
        self.assertEqual(
            ["topic/alpha", "topic/beta", "topic/delta"],
            [item["tag"] for item in pages["human/pages/quota.md"]],
        )
        self.assertEqual(
            [{"page": "human/pages/quota.md", "tag": "topic/gamma", "reason_code": "PAGE_TAG_QUOTA_EXCEEDED"}],
            projection["suppressed"],
        )
        serialized = json.dumps(projection, ensure_ascii=False)
        for forbidden in ("agent-alpha", "assertion_id", "sha256", COMMIT := "19152b227ccf687e7e4d89337d421c22a4e1a75f"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
