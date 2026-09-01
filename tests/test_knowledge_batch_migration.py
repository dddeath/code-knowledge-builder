from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
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
        try:
            self.temporary.cleanup()
        except OSError:
            # Windows may release a recently relocated SQLite/plugin directory
            # one scheduling turn after the rollback verification closes it.
            time.sleep(0.2)
            shutil.rmtree(self.root, ignore_errors=True)

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

    def _build_additional_output(self, name: str) -> tuple[Path, Path, Path]:
        from ckb_core.pipeline import finalize, initialize
        from test_scope_extension import review_all

        repo = self.root / f"{name}-repo"
        output = self.root / f"{name}-knowledge"
        staging = self.root / f"{name}-staging"
        repo.mkdir()
        (repo / "app.py").write_text(f"def {name}(number):\n    return number * 2\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        initialize(repo, output, "markdown", ["app.py"], [f"python:app.py#{name}"], 0, "both", [])
        review_all(output)
        finalize(output)
        return repo, output, staging

    def _project_document(self, project_id: str, output: Path, repo: Path, staging: Path) -> dict[str, object]:
        from ckb_core.common import json_load, sha256_file
        from ckb_core.gitrepo import preflight
        from ckb_core.scope_extension import _tree_manifest

        state = json_load(output / "state.json")
        scope = json_load(output / "scope.json")
        target = preflight(repo)
        tree = _tree_manifest(output)
        records = {
            relative: sha256_file(output / relative)
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
        backup_root = self.root / f"{project_id}-backups"
        quarantine_root = self.root / f"{project_id}-quarantine"
        return {
            "project_id": project_id,
            "output": str(output.resolve()),
            "repository": str(repo.resolve()),
            "staging": str(staging.resolve()),
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
            "cutover": {"output": str(output.resolve()), "backup_root": str(backup_root.resolve())},
            "rollback": {"quarantine_root": str(quarantine_root.resolve())},
        }

    def _manifest(self, projects: list[dict[str, object]] | None = None) -> Path:
        from ckb_core.common import json_write

        manifest = self.root / "manifest.json"
        json_write(
            manifest,
            {
                "schema_version": 1,
                "batch_id": "fixture-batch",
                "allowed_roots": [str(self.root.resolve()), str(ROOT.resolve())],
                "projects": projects or [self._project_document("project-a", self.output, self.repo, self.staging)],
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

    def test_two_projects_isolate_partial_apply_cutover_and_subset_rollback(self) -> None:
        from ckb_core.knowledge_batch_migration import (
            apply_knowledge_batch_plan,
            create_knowledge_batch_plan,
            cutover_knowledge_batch_state,
            resume_knowledge_batch_state,
            rollback_knowledge_batch_state,
        )
        from ckb_core.scope_extension import _tree_manifest

        repo_b, output_b, staging_b = self._build_additional_output("second")
        project_a = self._project_document("project-a", self.output, self.repo, self.staging)
        project_b = self._project_document("project-b", output_b, repo_b, staging_b)
        manifest = self._manifest([project_a, project_b])
        origin_a = _tree_manifest(self.output)
        origin_b = _tree_manifest(output_b)
        plan_path = self.root / "plan.json"
        planned = create_knowledge_batch_plan(manifest, plan_path)
        self.assertEqual("ready", planned["status"], planned)
        state_path = self.root / "state.json"
        partial_apply = apply_knowledge_batch_plan(plan_path, state_path, faults={"project-a": "before-build"})
        self.assertEqual("partial", partial_apply["status"], partial_apply)
        statuses = {item["project_id"]: item["status"] for item in partial_apply["projects"]}
        self.assertEqual("failed", statuses["project-a"])
        self.assertEqual("ready", statuses["project-b"])
        self.assertEqual(origin_a, _tree_manifest(self.output))
        self.assertEqual(origin_b, _tree_manifest(output_b))
        resumed = resume_knowledge_batch_state(state_path)
        self.assertEqual("ready", resumed["status"], resumed)

        partial_cutover = cutover_knowledge_batch_state(
            state_path,
            faults={"project-a": "after-backup-rename"},
        )
        self.assertEqual("partial", partial_cutover["status"], partial_cutover)
        self.assertEqual(origin_a, _tree_manifest(self.output))
        self.assertNotEqual(origin_b, _tree_manifest(output_b))
        retried = cutover_knowledge_batch_state(state_path, ["project-a"])
        self.assertEqual("passed", retried["status"], retried)

        rolled_b = rollback_knowledge_batch_state(state_path, ["project-b"])
        self.assertEqual("passed", rolled_b["status"], rolled_b)
        self.assertEqual(origin_b, _tree_manifest(output_b))
        self.assertNotEqual(origin_a, _tree_manifest(self.output))
        rolled_a = rollback_knowledge_batch_state(state_path, ["project-a"])
        self.assertEqual("passed", rolled_a["status"], rolled_a)
        self.assertEqual(origin_a, _tree_manifest(self.output))

    def test_plan_classifies_required_origin_version_and_path_failures(self) -> None:
        from ckb_core.common import CkbError, json_load, json_write, sha256_file
        from ckb_core.knowledge_batch_migration import create_knowledge_batch_plan
        from ckb_core.scope_extension import _tree_manifest

        def case_project(name: str) -> tuple[Path, dict[str, object]]:
            output = self.root / f"case-{name}"
            shutil.copytree(self.output, output)
            project = self._project_document(name, output, self.repo, self.root / f"stage-{name}")
            return output, project

        def refresh(project: dict[str, object], output: Path, changed_records: tuple[str, ...] = ()) -> None:
            tree = _tree_manifest(output)
            origin = project["origin"]
            assert isinstance(origin, dict)
            origin["tree"] = {key: tree[key] for key in ("algorithm", "file_count", "byte_count", "sha256")}
            records = origin["records"]
            assert isinstance(records, dict)
            for relative in changed_records:
                records[relative] = sha256_file(output / relative)

        def plan_for(project: dict[str, object], suffix: str) -> dict[str, object]:
            manifest = self.root / f"manifest-{suffix}.json"
            json_write(
                manifest,
                {
                    "schema_version": 1,
                    "batch_id": f"batch-{suffix}",
                    "allowed_roots": [str(self.root.resolve()), str(ROOT.resolve())],
                    "projects": [project],
                },
            )
            return create_knowledge_batch_plan(manifest)

        missing, project = case_project("missing-state")
        (missing / "state.json").unlink()
        refresh(project, missing)
        result = plan_for(project, "missing-state")
        self.assertEqual("origin-record-missing", result["projects"][0]["failure"]["category"])

        no_facts, project = case_project("missing-facts")
        shutil.rmtree(no_facts / "facts")
        refresh(project, no_facts)
        result = plan_for(project, "missing-facts")
        self.assertEqual("origin-facts-missing", result["projects"][0]["failure"]["category"])

        corrupt_sqlite, project = case_project("bad-sqlite")
        (corrupt_sqlite / "machine/knowledge.sqlite").write_bytes(b"not-a-sqlite-database")
        refresh(project, corrupt_sqlite)
        result = plan_for(project, "bad-sqlite")
        self.assertEqual("origin-sqlite", result["projects"][0]["failure"]["category"])

        mirror, project = case_project("mirror-drift")
        page = next((mirror / "markdown/pages").glob("*.md"))
        page.write_text(page.read_text(encoding="utf-8") + "\n镜像漂移。\n", encoding="utf-8")
        refresh(project, mirror)
        result = plan_for(project, "mirror-drift")
        self.assertEqual("origin-mirror-drift", result["projects"][0]["failure"]["category"])

        unknown, project = case_project("unknown-version")
        state = json_load(unknown / "state.json")
        state["version"] = "9.9.9"
        json_write(unknown / "state.json", state)
        protocol = json_load(unknown / "workspace-meta/agent-protocol.json")
        protocol["protocol_version"] = "9.9.9"
        json_write(unknown / "workspace-meta/agent-protocol.json", protocol)
        source = project["source"]
        assert isinstance(source, dict)
        source.update({"ckb_version": "9.9.9", "protocol_version": "9.9.9"})
        refresh(project, unknown, ("state.json",))
        result = plan_for(project, "unknown-version")
        self.assertEqual("awaiting-review", result["projects"][0]["status"])
        self.assertEqual("source-release-unknown", result["projects"][0]["reason"])

        _output, project = case_project("target-low")
        target = project["target"]
        assert isinstance(target, dict)
        target.update(
            {
                "ckb_version": "5.3.0",
                "protocol_version": "1.4.0",
                "release_commit": "02b3f9bae10663f8d8d41626bb52454a226d4228",
            }
        )
        result = plan_for(project, "target-low")
        self.assertEqual("target-not-current", result["projects"][0]["failure"]["category"])

        _output, project = case_project("long-path")
        project["max_path"] = 80
        result = plan_for(project, "long-path")
        self.assertEqual("path-too-long", result["projects"][0]["failure"]["category"])

        _output, project = case_project("overlap")
        project["staging"] = project["output"]
        manifest = self.root / "manifest-overlap.json"
        json_write(
            manifest,
            {
                "schema_version": 1,
                "batch_id": "batch-overlap",
                "allowed_roots": [str(self.root.resolve()), str(ROOT.resolve())],
                "projects": [project],
            },
        )
        with self.assertRaises(CkbError):
            create_knowledge_batch_plan(manifest)


if __name__ == "__main__":
    unittest.main()
