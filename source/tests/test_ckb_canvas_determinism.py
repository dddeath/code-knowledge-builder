from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "prototypes" / "ckb-canvas-skill"
FIXTURE = REPO / "tests" / "fixtures" / "obsidian-canvas-agent-visualization"
sys.path[:0] = [str(REPO), str(SKILL), str(FIXTURE)]

from ckb_canvas.commands import generate, rollback
from ckb_canvas.graph import canonical_json_bytes
from runtime_builder import build_case


class CanvasDeterminismTests(unittest.TestCase):
    def test_ten_generations_have_one_canvas_and_two_single_manifest_hashes(self) -> None:
        case = build_case("determinism-10x")
        canvas_hashes: set[str] = set()
        validation_hashes: set[str] = set()
        rollback_content_hashes: set[str] = set()
        full_rollback_hashes: set[str] = set()
        try:
            request_before = case.request.read_bytes()
            for _iteration in range(10):
                result = generate(case.request).to_dict()
                canvas_hashes.add(result["canvas"]["sha256"])
                validation_hashes.add(result["validation_manifest"]["sha256"])
                full_rollback_hashes.add(result["rollback_manifest"]["sha256"])
                manifest = json.loads(Path(result["rollback_manifest"]["path"]).read_text(encoding="utf-8"))
                rollback_content_hashes.add(manifest["guard"]["expected_manifest_content_sha256"])
                normalized = json.loads(json.dumps(manifest))
                normalized["guard"]["expected_manifest_content_sha256"] = "0" * 64
                self.assertEqual(
                    manifest["guard"]["expected_manifest_content_sha256"],
                    hashlib.sha256(canonical_json_bytes(normalized)).hexdigest(),
                )
                rollback(result["rollback_manifest"]["path"], result["rollback_manifest"]["sha256"])
                self.assertFalse(case.target.exists())
                self.assertFalse(case.validation.exists())
                self.assertFalse(case.rollback_manifest.exists())
            self.assertEqual(1, len(canvas_hashes))
            self.assertEqual(1, len(validation_hashes))
            self.assertEqual(1, len(rollback_content_hashes))
            self.assertEqual(1, len(full_rollback_hashes))
            self.assertEqual(request_before, case.request.read_bytes())
        finally:
            case.cleanup()


if __name__ == "__main__":
    unittest.main()
