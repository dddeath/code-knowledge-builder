from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class KnowledgeBatchVersionMatrixTests(unittest.TestCase):
    def test_matrix_uses_real_historical_releases(self) -> None:
        from scripts.ckb_core.knowledge_batch_migration import KNOWLEDGE_RELEASES, knowledge_version_matrix

        matrix = knowledge_version_matrix()
        self.assertEqual("5.4.0-s4-p1.5.0", matrix["current_release_id"])
        self.assertGreaterEqual(len(KNOWLEDGE_RELEASES), 6)
        for release in KNOWLEDGE_RELEASES.values():
            source = subprocess.run(
                ["git", "-C", str(ROOT), "show", f"{release.source_commit}:scripts/ckb_core/__init__.py"],
                check=True,
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
            ).stdout
            self.assertIn(f'VERSION = "{release.ckb_version}"', source)
            self.assertIn(f"SCHEMA_VERSION = {release.schema_version}", source)
            if release.protocol_version is not None:
                protocol = subprocess.run(
                    ["git", "-C", str(ROOT), "show", f"{release.source_commit}:scripts/ckb_core/agent_protocol.py"],
                    check=True,
                    text=True,
                    encoding="utf-8",
                    stdout=subprocess.PIPE,
                ).stdout
                self.assertIn(f'AGENT_PROTOCOL_VERSION = "{release.protocol_version}"', protocol)

    def test_reference_matrix_matches_runtime_matrix(self) -> None:
        from scripts.ckb_core.knowledge_batch_migration import knowledge_version_matrix

        reference = json.loads((ROOT / "references/knowledge-base-batch-migration-versions.json").read_text(encoding="utf-8"))
        runtime = knowledge_version_matrix()
        self.assertEqual(reference["current_release_id"], runtime["current_release_id"])
        self.assertEqual(reference["releases"], runtime["releases"])


if __name__ == "__main__":
    unittest.main()
