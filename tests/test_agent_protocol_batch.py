from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.agent_protocol import AGENT_PROTOCOL_VERSION
from ckb_core.agent_protocol_batch import PROTOCOL_RELEASES, supported_upgrade_path, version_matrix
from ckb_core.common import CkbError


class AgentProtocolBatchMatrixTests(unittest.TestCase):
    def test_frozen_historical_fixtures_match_matrix(self) -> None:
        fixture_path = ROOT / "tests/fixtures/agent-protocol-batch/versions.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(fixture["current_version"], AGENT_PROTOCOL_VERSION)
        self.assertEqual(len(fixture["fixtures"]), 4)
        self.assertEqual(len([item for item in fixture["fixtures"] if item["version"] != AGENT_PROTOCOL_VERSION]), 3)
        for item in fixture["fixtures"]:
            release = PROTOCOL_RELEASES[item["version"]]
            self.assertEqual(item["source_commit"], release.source_commit)
            self.assertEqual(item["output_contract"], release.output_contract)
            self.assertEqual(item["upgrade_path"], supported_upgrade_path(item["version"], AGENT_PROTOCOL_VERSION))
        self.assertEqual(version_matrix()["current_version"], AGENT_PROTOCOL_VERSION)

    def test_unknown_and_backward_paths_are_rejected(self) -> None:
        for version in ("0.9.0", "1.1.0", "1.2.0", "2.0.0"):
            with self.assertRaises(CkbError):
                supported_upgrade_path(version, AGENT_PROTOCOL_VERSION)
        with self.assertRaises(CkbError):
            supported_upgrade_path("1.5.0", "1.4.0")


if __name__ == "__main__":
    unittest.main()
