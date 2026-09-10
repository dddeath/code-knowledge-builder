from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
PROTOTYPE = REPO / "prototypes" / "ckb-tag-navigation"
sys.path.insert(0, str(PROTOTYPE))

from ckb_tag_navigation.contracts import TagNavigationError, atomic_write_json
from ckb_tag_navigation.real_vault import (
    EXPERIMENT_MARKER,
    rollback_real_vault_study,
    run_real_vault_study,
    source_identity,
    validate_study_protocol,
)


COMMIT = "a" * 40
RESULT = REPO / "references" / "research-gap-enhancement-effects" / "obsidian-tag-real-vault-study-v1"


class RealVaultStudyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-tag-real-vault-")
        self.root = Path(self.temporary.name)
        self.source = self.root / "stable"
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self._make_source()
        self.identity = source_identity(self.source)
        self.protocol = self._protocol()
        self.policy = {
            "schema_version": 1,
            "min_support_votes": 2,
            "min_independent_agents": 2,
            "min_independent_sources": 2,
            "max_opposition_ratio": 0.25,
            "max_evidence_age_days": 90,
            "max_tags_per_page": 3,
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _make_source(self) -> None:
        vault = self.source / "human"
        snapshot = self.source / ".source-snapshot" / "worktree" / "src"
        snapshot.mkdir(parents=True)
        (snapshot / "target.py").write_text("def target():\n    return 1\n", encoding="utf-8")
        (snapshot / "decoy.py").write_text("def decoy():\n    return 0\n", encoding="utf-8")
        (vault / "pages").mkdir(parents=True)
        (vault / ".ckb").mkdir()
        plugin = vault / ".obsidian" / "plugins" / "code-knowledge-builder-companion"
        plugin.mkdir(parents=True)
        (plugin / "main.js").write_text("fixture", encoding="utf-8")
        atomic_write_json(vault / ".obsidian" / "community-plugins.json", ["code-knowledge-builder-companion"])
        atomic_write_json(vault / ".ckb" / "output-contract.json", {"output": str(self.source)})
        (vault / "INDEX.md").write_text("# 入口\n\n[[hub]]\n", encoding="utf-8")
        (vault / "hub.md").write_text("# 导览\n\n[[decoy]]\n[[target]]\n", encoding="utf-8")
        (vault / "pages" / "target.md").write_text("# 目标\n", encoding="utf-8")
        (vault / "pages" / "decoy.md").write_text("# 干扰\n", encoding="utf-8")
        atomic_write_json(self.source / ".complete", {"schema_version": 1, "status": "complete", "commit": COMMIT})
        database = self.source / "machine" / "knowledge.sqlite"
        database.parent.mkdir()
        connection = sqlite3.connect(database)
        connection.executescript(
            """
            CREATE TABLE entities(entity_id TEXT PRIMARY KEY, source_path TEXT, commit_id TEXT);
            CREATE TABLE source_ranges(entity_id TEXT PRIMARY KEY, start_line INTEGER, end_line INTEGER);
            CREATE TABLE human_projection(entity_id TEXT PRIMARY KEY, page_file TEXT);
            CREATE TABLE relations(relation_id TEXT PRIMARY KEY);
            """
        )
        for entity, page, source in (("e1", "pages/target.md", "src/target.py"), ("e2", "pages/decoy.md", "src/decoy.py")):
            connection.execute("INSERT INTO entities VALUES(?,?,?)", (entity, source, COMMIT))
            connection.execute("INSERT INTO source_ranges VALUES(?,?,?)", (entity, 1, 2))
            connection.execute("INSERT INTO human_projection VALUES(?,?)", (entity, page))
        connection.commit()
        connection.close()

    def _protocol(self) -> dict:
        return {
            "schema_version": 1,
            "study_id": "fixture-real-vault",
            "status": "frozen",
            "frozen_before_run": True,
            "source": {
                "expected_commit": self.identity["commit"],
                "expected_complete_sha256": self.identity["complete_sha256"],
                "expected_vault_tree_sha256": self.identity["vault"]["tree_sha256"],
                "expected_machine_sha256": self.identity["machine_sha256"],
                "expected_counts": self.identity["counts"],
            },
            "conditions": ["no_tag", "machine_tag", "confirmed_tag"],
            "execution": {
                "entry_page": "INDEX.md",
                "step_budget": 2,
                "task_order": ["T01"],
                "candidate_order": "casefolded-page-path",
                "baseline_route": "directed-wikilink-shortest-path",
                "tag_route": "global-tag-pane-then-casefolded-candidates",
                "orphan_scope_prefixes": ["pages"],
                "as_of": "2026-09-05T00:00:00Z",
            },
            "claim_boundary": {"automation": "system-navigation-proxy-only", "human": "pending-human-validation"},
            "tasks": [
                {
                    "task_id": "T01",
                    "prompt_zh": "定位目标页面。",
                    "target": "pages/target.md",
                    "tag": "导航/主题/目标",
                    "machine_candidates": [
                        {"page": "pages/target.md", "decision": "confirmed", "duplicate_last_vote": True},
                        {"page": "pages/decoy.md", "decision": "tied", "duplicate_last_vote": False},
                    ],
                }
            ],
        }

    def test_three_arms_copy_source_and_separate_system_from_human_claims(self) -> None:
        output = self.workspace / "run"
        before = source_identity(self.source)
        report = run_real_vault_study(self.source, self.protocol, self.policy, output, self.workspace)
        after = source_identity(self.source)
        self.assertEqual(before["vault"]["tree_sha256"], after["vault"]["tree_sha256"])
        self.assertEqual("system-navigation-proxy-only", report["effect_claim"])
        self.assertEqual("pending-human-validation", report["human_result"])
        self.assertFalse(report["production_default_changed"])
        self.assertEqual(1, report["conditions"]["no_tag"]["discoverable_count"])
        self.assertEqual(0, report["conditions"]["machine_tag"]["discoverable_count"])
        self.assertEqual(1, report["conditions"]["confirmed_tag"]["discoverable_count"])
        self.assertEqual(1, report["conditions"]["machine_tag"]["error_navigation_count"])
        self.assertEqual(0, report["conditions"]["confirmed_tag"]["error_navigation_count"])
        self.assertEqual(1, report["audit_cost"]["duplicate_lines_ignored"])
        self.assertEqual({"candidate": 0, "confirmed": 1, "contested": 1, "deprecated": 0}, report["audit_state_counts"])
        audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
        contested = next(item for item in audit["results"] if item["target"]["path"] == "pages/decoy.md")
        self.assertEqual("contested", contested["state"])
        self.assertEqual(1, contested["metrics"]["support_votes"])
        self.assertEqual(1, contested["metrics"]["oppose_votes"])
        self.assertEqual(0.5, contested["metrics"]["opposition_ratio"])
        self.assertEqual(["OPPOSITION_RATIO_EXCEEDED"], contested["reason_codes"])
        baseline = (output / "vaults" / "no_tag" / "pages" / "target.md").read_text(encoding="utf-8")
        machine = (output / "vaults" / "machine_tag" / "pages" / "target.md").read_text(encoding="utf-8")
        confirmed = (output / "vaults" / "confirmed_tag" / "pages" / "target.md").read_text(encoding="utf-8")
        self.assertNotIn(EXPERIMENT_MARKER, baseline)
        self.assertIn(EXPERIMENT_MARKER, machine)
        self.assertIn(EXPERIMENT_MARKER, confirmed)
        for condition in ("no_tag", "machine_tag", "confirmed_tag"):
            vault = output / "vaults" / condition
            self.assertFalse((vault / ".ckb" / "output-contract.json").exists())
            self.assertFalse((vault / ".obsidian" / "plugins" / "code-knowledge-builder-companion").exists())
            self.assertEqual([], json.loads((vault / ".obsidian" / "community-plugins.json").read_text(encoding="utf-8")))

    def test_rollback_deletes_unchanged_isolated_run_and_rejects_drift(self) -> None:
        first = self.workspace / "first"
        result = run_real_vault_study(self.source, self.protocol, self.policy, first, self.workspace)
        rolled_back = rollback_real_vault_study(Path(result["rollback_manifest"]), self.workspace)
        self.assertEqual("rolled-back", rolled_back["status"])
        self.assertFalse(first.exists())

        second = self.workspace / "second"
        result = run_real_vault_study(self.source, self.protocol, self.policy, second, self.workspace)
        (second / "vaults" / "no_tag" / "INDEX.md").write_text("drift", encoding="utf-8")
        with self.assertRaises(TagNavigationError) as raised:
            rollback_real_vault_study(Path(result["rollback_manifest"]), self.workspace)
        self.assertEqual("ROLLBACK_DRIFT", raised.exception.reason)
        self.assertTrue(second.exists())

    def test_source_drift_and_malicious_tag_stop_before_output(self) -> None:
        drifted = copy.deepcopy(self.protocol)
        drifted["source"]["expected_vault_tree_sha256"] = "0" * 64
        output = self.workspace / "drifted"
        with self.assertRaises(TagNavigationError) as raised:
            run_real_vault_study(self.source, drifted, self.policy, output, self.workspace)
        self.assertEqual("SOURCE_DRIFT", raised.exception.reason)
        self.assertFalse(output.exists())

        malicious = copy.deepcopy(self.protocol)
        malicious["tasks"][0]["tag"] = "../恶意"
        with self.assertRaises(TagNavigationError) as raised:
            validate_study_protocol(malicious)
        self.assertEqual("INVALID_TAG", raised.exception.reason)


class CommittedRealVaultStudyTests(unittest.TestCase):
    def test_committed_result_recomputes_and_preserves_claim_boundary(self) -> None:
        specification = importlib.util.spec_from_file_location("verify_tag_real_vault_result", RESULT / "verify_results.py")
        assert specification and specification.loader
        verifier = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(verifier)
        verified = verifier.verify(RESULT)
        self.assertEqual("passed", verified["status"])
        self.assertTrue(all(verified["checks"].values()))
        report = json.loads((RESULT / "report.json").read_text(encoding="utf-8"))
        self.assertEqual("system-navigation-proxy-only", report["effect_claim"])
        self.assertEqual("pending-human-validation", report["human_result"])
        self.assertFalse(report["production_default_changed"])
        self.assertEqual(
            json.loads((REPO / "tests" / "fixtures" / "tag-navigation-real-vault" / "protocol.json").read_text(encoding="utf-8")),
            json.loads((RESULT / "protocol.json").read_text(encoding="utf-8")),
        )


if __name__ == "__main__":
    unittest.main()
