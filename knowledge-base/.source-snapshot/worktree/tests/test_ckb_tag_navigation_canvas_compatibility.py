from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
TAG_PROTOTYPE = REPO / "prototypes" / "ckb-tag-navigation"
CANVAS_PROTOTYPE = REPO / "prototypes" / "ckb-canvas-skill"
TAG_FIXTURE = REPO / "tests" / "fixtures" / "tag-navigation"
CANVAS_FIXTURE = REPO / "tests" / "fixtures" / "obsidian-canvas-agent-visualization" / "expected"
sys.path[:0] = [str(TAG_PROTOTYPE), str(CANVAS_PROTOTYPE)]

from ckb_canvas.contracts import validate_instance
from ckb_tag_navigation.projection import build_projection
from ckb_tag_navigation.state_machine import audit_database
from ckb_tag_navigation.store import replay_with_rollback


def digest_tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


class TagNavigationCanvasCompatibilityTests(unittest.TestCase):
    def test_canvas_contract_remains_valid_and_byte_unchanged(self) -> None:
        before = digest_tree(CANVAS_PROTOTYPE)
        canvas = json.loads((CANVAS_FIXTURE / "ckb-navigation.canvas").read_text(encoding="utf-8"))
        validate_instance("json-canvas-1.0-ckb-subset.schema.json", canvas)
        with tempfile.TemporaryDirectory(prefix="ckb-tag-canvas-") as temporary:
            root = Path(temporary)
            database = root / "tags.sqlite"
            replay_with_rollback(TAG_FIXTURE / "assertions.jsonl", database, root / "rollback.json")
            policy = json.loads((TAG_FIXTURE / "policy.json").read_text(encoding="utf-8"))
            audit = audit_database(database, policy, "19152b227ccf687e7e4d89337d421c22a4e1a75f", "2026-09-03T00:00:00Z")
            projection = build_projection(audit, policy)
            self.assertEqual("disabled", projection["production_integration"])
        self.assertEqual(before, digest_tree(CANVAS_PROTOTYPE))


if __name__ == "__main__":
    unittest.main()
