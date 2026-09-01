from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
GIT_COMMON_DIR = ROOT.parents[1] / "source" / ".git"


class KnowledgeBatchVersionMatrixTests(unittest.TestCase):
    def test_matrix_uses_real_historical_releases(self) -> None:
        from ckb_core.knowledge_batch_migration import KNOWLEDGE_RELEASES, knowledge_version_matrix

        matrix = knowledge_version_matrix()
        self.assertEqual("5.4.0-s4-p1.5.0", matrix["current_release_id"])
        self.assertGreaterEqual(len(KNOWLEDGE_RELEASES), 6)
        for release in KNOWLEDGE_RELEASES.values():
            source = subprocess.run(
                ["git", f"--git-dir={GIT_COMMON_DIR}", f"--work-tree={ROOT}", "show", f"{release.source_commit}:scripts/ckb_core/__init__.py"],
                check=True,
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
            ).stdout
            self.assertIn(f'VERSION = "{release.ckb_version}"', source)
            self.assertIn(f"SCHEMA_VERSION = {release.schema_version}", source)
            if release.protocol_version is not None:
                protocol = subprocess.run(
                    ["git", f"--git-dir={GIT_COMMON_DIR}", f"--work-tree={ROOT}", "show", f"{release.source_commit}:scripts/ckb_core/agent_protocol.py"],
                    check=True,
                    text=True,
                    encoding="utf-8",
                    stdout=subprocess.PIPE,
                ).stdout
                self.assertIn(f'AGENT_PROTOCOL_VERSION = "{release.protocol_version}"', protocol)

    def test_reference_matrix_matches_runtime_matrix(self) -> None:
        from ckb_core.knowledge_batch_migration import knowledge_version_matrix

        reference = json.loads((ROOT / "references/knowledge-base-batch-migration-versions.json").read_text(encoding="utf-8"))
        runtime = knowledge_version_matrix()
        self.assertEqual(reference["current_release_id"], runtime["current_release_id"])
        self.assertEqual(reference["releases"], runtime["releases"])


class KnowledgeBatchWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        from ckb_core.pipeline import finalize, initialize
        from test_scope_extension import review_all

        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-knowledge-batch-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.output = self.root / "knowledge"
        self.staging = self.root / "staging"
        self.repo.mkdir()
        (self.repo / "app.py").write_text("def value(number):\n    return number + 1\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-m", "fixture"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.old_provider = os.environ.get("CKB_TEST_PROVIDER")
        os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"
        initialize(self.repo, self.output, "markdown", ["app.py"], ["python:app.py#value"], 0, "both", [])
        review_all(self.output)
        finalize(self.output)

    def tearDown(self) -> None:
        if self.old_provider is None:
            os.environ.pop("CKB_TEST_PROVIDER", None)
        else:
            os.environ["CKB_TEST_PROVIDER"] = self.old_provider
        self.temporary.cleanup()

    def _add_complete_mutable_fixture(self) -> None:
        from ckb_core.workspace_notes import record_note
        from test_scope_extension import ScopeExtensionTest

        # Reuse the reviewed reference and three-gap fixture already accepted
        # by scope-extension tests, then bring work records to exactly 48.
        ScopeExtensionTest.add_preserved_layers(self)
        body = self.root / "extra-record.md"
        for index in range(47, 49):
            body.write_text(f"第 {index} 条工作记录说明完整迁移的固定行为和实际验证结果。\n", encoding="utf-8")
            record_note(self.output, "session", f"迁移工作记录 {index:02d}", body, reindex=False)
        for vault in ("human", "markdown"):
            user = self.output / vault / "user"
            user.mkdir(parents=True, exist_ok=True)
            (user / "学习笔记一.md").write_text("# 学习笔记一\n\n第一份原文必须保持不变。\n", encoding="utf-8")
            (user / "学习笔记二.md").write_text("# 学习笔记二\n\n第二份原文必须保持不变。\n", encoding="utf-8")

    def _manifest(self) -> Path:
        from ckb_core.common import json_load, json_write, sha256_file
        from ckb_core.gitrepo import preflight
        from ckb_core.scope_extension import _tree_manifest

        state = json_load(self.output / "state.json")
        scope = json_load(self.output / "scope.json")
        target = preflight(self.repo)
        tree = _tree_manifest(self.output)
        records = {
            relative: sha256_file(self.output / relative)
            for relative in (
                "state.json",
                "scope.json",
                "catalog.json",
                "graph.json",
                "audit/global.json",
                ".complete",
                ".machine.complete",
                ".human.complete",
            )
        }
        backup_root = self.root / "backups"
        quarantine_root = self.root / "quarantine"
        manifest = self.root / "manifest.json"
        json_write(
            manifest,
            {
                "schema_version": 1,
                "batch_id": "fixture-batch",
                "allowed_roots": [str(self.root.resolve()), str(ROOT.resolve())],
                "projects": [
                    {
                        "project_id": "project-a",
                        "output": str(self.output.resolve()),
                        "repository": str(self.repo.resolve()),
                        "staging": str(self.staging.resolve()),
                        "source": {
                            "ckb_version": "5.4.0",
                            "schema_version": 4,
                            "protocol_version": "1.5.0",
                            "release_commit": "2d1ddc4de65c36c2ebe244e3d0556d4b613b2d3d",
                        },
                        "target": {
                            "ckb_version": "5.4.0",
                            "schema_version": 4,
                            "protocol_version": "1.5.0",
                            "release_commit": "2d1ddc4de65c36c2ebe244e3d0556d4b613b2d3d",
                        },
                        "origin_snapshot": {"commit": state["repository"]["commit"], "tree": state["repository"]["tree"]},
                        "target_snapshot": {"commit": target["commit"], "tree": target["tree"]},
                        "format": state["format"],
                        "scope_selectors": scope["selectors"],
                        "runtime": {"python": str(Path(sys.executable).resolve()), "ckb": str((ROOT / "scripts/ckb.py").resolve())},
                        "workspace_roots": [],
                        "harnesses": ["codex", "generic"],
                        "origin": {
                            "tree": {key: tree[key] for key in ("algorithm", "file_count", "byte_count", "sha256")},
                            "records": records,
                        },
                        "strategies": ["compatible-migration", "delta-review", "cold-build"],
                        "cutover": {"output": str(self.output.resolve()), "backup_root": str(backup_root.resolve())},
                        "rollback": {"quarantine_root": str(quarantine_root.resolve())},
                    }
                ],
            },
        )
        return manifest

    def test_plan_apply_audit_cutover_and_exact_rollback(self) -> None:
        from ckb_core.knowledge_batch_migration import (
            apply_knowledge_batch_plan,
            audit_knowledge_batch_state,
            create_knowledge_batch_plan,
            cutover_knowledge_batch_state,
            rollback_knowledge_batch_state,
        )
        from ckb_core.scope_extension import _tree_manifest

        self._add_complete_mutable_fixture()
        manifest = self._manifest()
        origin = _tree_manifest(self.output)
        before = self.output.stat().st_mtime_ns
        dry = create_knowledge_batch_plan(manifest)
        self.assertEqual("ready", dry["status"], dry["projects"])
        self.assertEqual(before, self.output.stat().st_mtime_ns)
        self.assertEqual(48, dry["projects"][0]["origin_layers"]["work_record_count"])
        self.assertEqual(1, dry["projects"][0]["origin_layers"]["reference_count"])
        self.assertEqual(3, dry["projects"][0]["origin_layers"]["gap_count"])
        plan_path = self.root / "plan.json"
        create_knowledge_batch_plan(manifest, plan_path)
        state_path = self.root / "state.json"
        applied = apply_knowledge_batch_plan(plan_path, state_path)
        applied_detail = json.loads((self.staging / "knowledge-batch/audit.json").read_text(encoding="utf-8")) if (self.staging / "knowledge-batch/audit.json").is_file() else applied
        self.assertEqual("ready", applied["status"], applied_detail)
        audited = audit_knowledge_batch_state(state_path)
        self.assertEqual("passed", audited["status"])
        cutover = cutover_knowledge_batch_state(state_path)
        self.assertEqual("passed", cutover["status"])
        self.assertEqual("cutover-complete", cutover["projects"][0]["status"])
        rolled = rollback_knowledge_batch_state(state_path)
        self.assertEqual("passed", rolled["status"])
        self.assertEqual("rolled-back", rolled["projects"][0]["status"])
        self.assertEqual(origin, _tree_manifest(self.output))

    def test_partial_apply_failure_can_resume_without_touching_origin(self) -> None:
        from ckb_core.knowledge_batch_migration import (
            apply_knowledge_batch_plan,
            create_knowledge_batch_plan,
            resume_knowledge_batch_state,
        )
        from ckb_core.scope_extension import _tree_manifest

        manifest = self._manifest()
        plan_path = self.root / "plan.json"
        create_knowledge_batch_plan(manifest, plan_path)
        state_path = self.root / "state.json"
        origin = _tree_manifest(self.output)
        failed = apply_knowledge_batch_plan(plan_path, state_path, faults={"project-a": "before-build"})
        self.assertEqual("failed", failed["status"])
        self.assertEqual(origin, _tree_manifest(self.output))
        resumed = resume_knowledge_batch_state(state_path)
        self.assertIn(resumed["status"], {"ready", "review-pending"})
        self.assertEqual(origin, _tree_manifest(self.output))

    def test_cold_build_has_zero_reuse_and_resume_obeys_review_gate(self) -> None:
        from ckb_core.common import json_load, json_write
        from ckb_core.knowledge_batch_migration import (
            _digest_value,
            apply_knowledge_batch_plan,
            create_knowledge_batch_plan,
            resume_knowledge_batch_state,
        )
        from test_scope_extension import review_all

        manifest = self._manifest()
        plan_path = self.root / "plan.json"
        create_knowledge_batch_plan(manifest, plan_path)
        plan = json_load(plan_path)
        plan["projects"][0]["status"] = "cold-build-required"
        plan["projects"][0]["reason"] = "fixture-forces-cold-build"
        plan["projects"][0]["strategy"] = "cold-build"
        body = {key: value for key, value in plan.items() if key not in {"plan_digest", "plan_path"}}
        plan["plan_digest"] = _digest_value(body)
        json_write(plan_path, plan)
        state_path = self.root / "state.json"
        applied = apply_knowledge_batch_plan(plan_path, state_path)
        self.assertEqual("review-pending", applied["status"])
        migration_plan = json_load(self.staging / "migration/plan.json")
        self.assertEqual("cold-build", migration_plan["mode"])
        self.assertEqual(0, migration_plan["files"]["reused_count"])
        self.assertEqual(0, migration_plan["entities"]["reused_review_count"])
        self.assertGreater(migration_plan["entities"]["delta_review_count"], 0)
        review_all(self.staging)
        resumed = resume_knowledge_batch_state(state_path)
        self.assertEqual("ready", resumed["status"], resumed)


if __name__ == "__main__":
    unittest.main()
