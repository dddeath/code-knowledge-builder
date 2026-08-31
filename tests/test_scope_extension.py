from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from ckb_core.common import CkbError, json_load, json_write, sha256_file, stable_id, utc_now
from ckb_core.pipeline import build_chunk, finalize, initialize, review_pack
from ckb_core.reference_documents import _render_reference_page
from ckb_core.research_gaps import _index_value
from ckb_core.scope_extension import (
    _tree_manifest,
    audit_scope_extension,
    cutover_scope_extension,
    extension_status,
    rollback_scope_extension,
    start_scope_extension,
)
from ckb_core.workspace_notes import record_note


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        raise RuntimeError(completed.stderr)
    return completed.stdout.strip()


def review_all(output: Path) -> None:
    state = json.loads((output / "state.json").read_text(encoding="utf-8"))
    for batch in state["parse_batches"]:
        if not (output / "chunks" / batch["id"] / "candidate.json").is_file():
            build_chunk(output, batch["id"], "all")
    state = json.loads((output / "state.json").read_text(encoding="utf-8"))
    for pack in state["review_packs"]:
        if pack["status"] == "passed":
            continue
        template = json.loads(Path(pack["review_template_path"]).read_text(encoding="utf-8"))
        for item in template["reviews"]:
            item["status"] = "agent-reviewed"
            item["evidence_note"] = "Agent 已重新打开固定 Git 源码范围，逐项核对名称、范围、分支和调用关系后确认说明。"
            if pack["kind"] == "appendix-review":
                item["description_zh"] = "该局部代码负责完成所属流程中的辅助步骤，并把确定结果交给主流程继续使用。"
            else:
                item["meaning_zh"] = "该代码页说明固定源码范围内的主要实现、输入条件和输出结果。"
                item["role_zh"] = "它负责组织当前代码单元的执行步骤，并与相邻函数形成可追踪的调用关系。"
                item["change_when_zh"] = "当输入约定、执行步骤、返回结果或调用关系变化时，需要修改并重新核对该代码单元。"
        path = output / "test-reviews" / f"{pack['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_pack(output, pack["id"], path)


class ScopeExtensionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-scope-extension-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.output = self.root / "knowledge"
        self.staging = self.root / "staging"
        self.repo.mkdir()
        (self.repo / "app.py").write_text("def first(value):\n    return value + 1\n", encoding="utf-8")
        (self.repo / "extra.py").write_text("def second(value):\n    return value * 2\n", encoding="utf-8")
        (self.repo / "third.py").write_text("def third(value):\n    return value - 3\n", encoding="utf-8")
        (self.repo / "duplicate.py").write_text("def repeated():\n    return 1\n\ndef repeated():\n    return 2\n", encoding="utf-8")
        (self.repo / "ignored.txt").write_text("not tracked source", encoding="utf-8")
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "scope fixture")
        self.old_provider = os.environ.get("CKB_TEST_PROVIDER")
        os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"
        initialize(self.repo, self.output, "markdown", ["app.py"], ["python:app.py#first"], 0, "both", [])
        review_all(self.output)
        finalize(self.output)
        for vault in ("human", "markdown"):
            page = self.output / vault / "user" / "学习笔记一.md"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text("# 学习笔记一\n\n这是必须按原字节保留的第一份学习笔记。\n", encoding="utf-8")
            page2 = self.output / vault / "user" / "学习笔记二.md"
            page2.write_text("# 学习笔记二\n\n这是必须按原字节保留的第二份学习笔记。\n", encoding="utf-8")

    def add_preserved_layers(self) -> None:
        gap_records = []
        gap_root = self.output / "workspace-meta/gaps/records"
        for index in range(3):
            summary = f"第 {index + 1} 项资料仍缺少固定问题集和独立验证证据，需要后续补充。"
            gap_id = stable_id("gap", "insufficient-evidence", summary, "audit/global.json")
            stamp = utc_now()
            record = {
                "schema_version": 1,
                "gap_id": gap_id,
                "kind": "insufficient-evidence",
                "status": "open",
                "summary_zh": summary,
                "evidence_paths": ["audit/global.json"],
                "created_at_utc": stamp,
                "updated_at_utc": stamp,
                "resolution_zh": None,
                "resolution_evidence_paths": [],
            }
            json_write(gap_root / f"{gap_id}.json", record)
            gap_records.append(record)
        gap_records.sort(key=lambda item: item["gap_id"])
        json_write(self.output / "workspace-meta/gaps/index.json", _index_value(gap_records))

        reference_root = self.output / "references"
        raw = reference_root / "raw/fixed-reference--r1.md"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text(
            "# 固定参考资料\n\n"
            "这份资料要求所有扩展都保留原中心，并在隔离目录完成审计。\n"
            "正式切换前必须验证备份，回滚后必须重新核对完整性。\n",
            encoding="utf-8",
        )
        reference_id = stable_id("reference", "固定参考资料".casefold(), "本地测试资料".casefold(), sha256_file(raw))
        review_path = reference_root / f"reviews/{reference_id}.json"
        review = {
            "schema_version": 1,
            "reference_id": reference_id,
            "status": "agent-reviewed",
            "title": "固定参考资料",
            "source_file": str(raw.resolve()),
            "source_sha256": sha256_file(raw),
            "summary_zh": "这份资料规定追加中心的保留、隔离审计、备份验证和完整回滚要求。",
            "claims": [
                {
                    "claim_zh": "追加中心需要保留原中心并在隔离目录审计，切换和回滚都要验证完整性。",
                    "start_line": 3,
                    "end_line": 4,
                    "source_text": "这份资料要求所有扩展都保留原中心，并在隔离目录完成审计。\n正式切换前必须验证备份，回滚后必须重新核对完整性。",
                    "evidence_note": "已重新打开归档原文第 3 至 4 行并核对保留、切换和回滚要求。",
                }
            ],
        }
        json_write(review_path, review)
        manifest = {
            "schema_version": 1,
            "reference_id": reference_id,
            "status": "agent-reviewed",
            "title": "固定参考资料",
            "origin": "本地测试资料",
            "author": "Fixture",
            "license": "CC0-1.0",
            "copy_permission": "full-text",
            "source_type": "markdown",
            "source_suffix": ".md",
            "source_file": str(raw.resolve()),
            "source_relative": raw.relative_to(self.output).as_posix(),
            "source_sha256": sha256_file(raw),
            "source_size": raw.stat().st_size,
            "revision": 1,
            "supersedes": None,
            "review_template": str((reference_root / f"review-templates/{reference_id}.json").resolve()),
            "review_file": str(review_path.resolve()),
            "human_file": "references/固定参考资料.md",
            "ingested_at_utc": utc_now(),
        }
        json_write(reference_root / f"manifests/{reference_id}.json", manifest)
        page_text = _render_reference_page(manifest, review)
        index_text = "# 参考资料导览\n\n标签：#类型/导览\n\n## 已审阅资料\n\n- [[固定参考资料]] — 追加中心的保留和回滚要求。\n"
        for vault in ("human", "markdown"):
            page = self.output / vault / "references/固定参考资料.md"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(page_text, encoding="utf-8", newline="\n")
            (self.output / vault / "REFERENCES.md").write_text(index_text, encoding="utf-8", newline="\n")
        json_write(
            reference_root / "projection.json",
            {
                "schema_version": 1,
                "status": "ready",
                "page_count": 1,
                "page_limit_per_source": 1,
                "pages": [{"reference_id": reference_id, "title": "固定参考资料", "file": "references/固定参考资料.md", "summary_zh": review["summary_zh"], "revision": 1}],
                "files": ["REFERENCES.md", "references/固定参考资料.md"],
                "projected_at_utc": utc_now(),
            },
        )
        note_body = self.root / "work-record.md"
        for index in range(46):
            note_body.write_text(f"第 {index + 1} 条工作记录说明固定测试行为和实际验证结果。\n", encoding="utf-8")
            record_note(self.output, "session", f"迁移工作记录 {index + 1:02d}", note_body, reindex=False)

    def tearDown(self) -> None:
        if self.old_provider is None:
            os.environ.pop("CKB_TEST_PROVIDER", None)
        else:
            os.environ["CKB_TEST_PROVIDER"] = self.old_provider
        self.temporary.cleanup()

    def test_union_delta_idempotence_cutover_and_byte_exact_rollback(self) -> None:
        self.add_preserved_layers()
        origin = _tree_manifest(self.output)
        started = start_scope_extension(
            self.output, self.repo, self.staging, ["python:extra.py#second"], 0, "both"
        )
        self.assertEqual(started["status"], "pending-agent-review")
        plan_path = self.staging / "scope-extension/plan.json"
        first_plan = plan_path.read_bytes()
        plan = json.loads(first_plan)
        self.assertEqual(plan["delta"]["entries"]["removed"], [])
        self.assertEqual(plan["delta"]["paths"]["removed"], [])
        self.assertIn("python:app.py#first", plan["selectors"]["target_entries"])
        self.assertIn("python:extra.py#second", plan["selectors"]["target_entries"])
        self.assertGreater(plan["reuse"]["file_count"], 0)
        self.assertGreater(plan["reuse"]["review_entity_count"], 0)
        self.assertGreater(plan["reuse"]["delta_review_entity_count"], 0)
        self.assertEqual(plan["preservation"]["origin_layers"]["work_record_count"], 46)
        self.assertEqual(plan["preservation"]["origin_layers"]["reference_count"], 1)
        self.assertEqual(plan["preservation"]["origin_layers"]["gap_count"], 3)
        for vault in ("human", "markdown"):
            self.assertEqual(
                (self.output / vault / "user/学习笔记一.md").read_bytes(),
                (self.staging / vault / "user/学习笔记一.md").read_bytes(),
            )
            self.assertEqual(
                (self.output / vault / "user/学习笔记二.md").read_bytes(),
                (self.staging / vault / "user/学习笔记二.md").read_bytes(),
            )

        repeated = start_scope_extension(
            self.output, self.repo, self.staging, ["python:extra.py#second"], 0, "both"
        )
        self.assertEqual(repeated["operation_id"], started["operation_id"])
        self.assertEqual(plan_path.read_bytes(), first_plan)
        review_all(self.staging)
        audited = audit_scope_extension(self.staging)
        self.assertEqual(audited["status"], "ready", audited)
        self.assertTrue(all(item["passed"] for item in audited["sqlite"]))
        connection = sqlite3.connect(self.staging / "machine/knowledge.sqlite")
        try:
            old_matches = connection.execute("SELECT count(*) FROM entities WHERE source_path='app.py' AND qualified_name='first'").fetchone()[0]
            new_matches = connection.execute("SELECT count(*) FROM entities WHERE source_path='extra.py' AND qualified_name='second'").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(old_matches, 1)
        self.assertEqual(new_matches, 1)
        cutover = cutover_scope_extension(self.staging)
        self.assertEqual(cutover["status"], "cutover-complete")
        self.assertEqual(extension_status(self.output)["status"], "cutover-complete")
        self.assertFalse(self.staging.exists())
        rolled = rollback_scope_extension(self.output)
        self.assertEqual(rolled["status"], "rolled-back")
        self.assertEqual(_tree_manifest(self.output), origin)
        self.assertTrue(all(item["passed"] for item in rolled["sqlite"]))

    def test_cutover_failure_restores_origin(self) -> None:
        origin = _tree_manifest(self.output)
        start_scope_extension(self.output, self.repo, self.staging, ["python:extra.py#second"], 0, "both")
        review_all(self.staging)
        self.assertEqual(audit_scope_extension(self.staging)["status"], "ready")
        with self.assertRaisesRegex(CkbError, "cutover-failed"):
            cutover_scope_extension(self.staging, fault="after-backup-rename")
        self.assertEqual(_tree_manifest(self.output), origin)
        self.assertTrue(self.staging.is_dir())
        self.assertEqual(cutover_scope_extension(self.staging)["status"], "cutover-complete")
        self.assertEqual(rollback_scope_extension(self.output)["status"], "rolled-back")
        self.assertEqual(_tree_manifest(self.output), origin)

    def test_audit_drift_and_rollback_failure_are_recoverable(self) -> None:
        origin = _tree_manifest(self.output)
        start_scope_extension(self.output, self.repo, self.staging, ["python:extra.py#second"], 0, "both")
        review_all(self.staging)
        plan_path = self.staging / "scope-extension/plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["review"]["delta_entity_ids"].append(plan["review"]["reused_entity_ids"][0])
        json_write(plan_path, plan)
        failed = audit_scope_extension(self.staging)
        self.assertEqual(failed["status"], "failed")
        self.assertFalse(next(item for item in failed["checks"] if item["name"] == "exact-delta-review-set")["passed"])
        plan["review"]["delta_entity_ids"].pop()
        json_write(plan_path, plan)
        self.assertEqual(audit_scope_extension(self.staging)["status"], "ready")
        concurrent = self.output / "concurrent-write.txt"
        concurrent.write_text("concurrent drift", encoding="utf-8")
        with self.assertRaisesRegex(CkbError, "origin-drift"):
            cutover_scope_extension(self.staging)
        concurrent.unlink()
        cutover_scope_extension(self.staging)
        with self.assertRaisesRegex(CkbError, "rollback-failed"):
            rollback_scope_extension(self.output, fault="after-modified-rename")
        self.assertNotEqual(_tree_manifest(self.output), origin)
        self.assertEqual(rollback_scope_extension(self.output)["status"], "rolled-back")
        self.assertEqual(_tree_manifest(self.output), origin)

    def test_fixed_failure_categories(self) -> None:
        cases = [
            (["rust:extra.rs#second"], "unsupported-language"),
            (["python:missing.py#missing"], "entry-resolution"),
            (["python:duplicate.py#repeated"], "entry-resolution"),
            (["python:extra.py#second", "python:extra.py#second"], "duplicate-entry"),
            (["python:app.py#first"], "entry-already-present"),
            (["python:ignored.txt#ignored"], "entry-resolution"),
        ]
        for index, (entries, category) in enumerate(cases):
            with self.subTest(category=category):
                with self.assertRaisesRegex(CkbError, category):
                    start_scope_extension(self.output, self.repo, self.root / f"failed-{index}", entries, 0, "both")

        with self.assertRaisesRegex(CkbError, "overlapping-output"):
            start_scope_extension(self.output, self.repo, self.output / "nested", ["python:extra.py#second"], 0, "both")
        occupied = self.root / "occupied"
        occupied.mkdir()
        (occupied / "unrelated.txt").write_text("unrelated", encoding="utf-8")
        with self.assertRaisesRegex(CkbError, "staging-not-empty"):
            start_scope_extension(self.output, self.repo, occupied, ["python:extra.py#second"], 0, "both")

    def test_sequential_extensions_form_an_unwindable_active_chain(self) -> None:
        self.add_preserved_layers()
        initial = _tree_manifest(self.output)

        first_started = start_scope_extension(
            self.output, self.repo, self.staging, ["python:extra.py#second"], 0, "both"
        )
        review_all(self.staging)
        self.assertEqual(audit_scope_extension(self.staging)["status"], "ready")
        first_cutover = cutover_scope_extension(self.staging)
        first_operation = first_started["operation_id"]
        self.assertEqual(first_cutover["parent_operation_id"], None)
        self.assertEqual(first_cutover["chain_depth"], 1)
        first_tree = _tree_manifest(self.output)

        second_staging = self.root / "staging-second"
        second_started = start_scope_extension(
            self.output, self.repo, second_staging, ["python:third.py#third"], 0, "both"
        )
        review_all(second_staging)
        self.assertEqual(audit_scope_extension(second_staging)["status"], "ready")
        with self.assertRaisesRegex(CkbError, "cutover-failed"):
            cutover_scope_extension(second_staging, fault="after-backup-rename")
        self.assertEqual(_tree_manifest(self.output), first_tree)
        status_after_failure = extension_status(self.output)
        self.assertEqual(status_after_failure["active_operation_id"], first_operation)

        second_cutover = cutover_scope_extension(second_staging)
        second_operation = second_started["operation_id"]
        self.assertEqual(second_cutover["parent_operation_id"], first_operation)
        self.assertEqual(second_cutover["chain_depth"], 2)
        active = extension_status(self.output)
        self.assertEqual(active["active_operation_id"], second_operation)
        self.assertEqual(active["parent_operation_id"], first_operation)

        first_control_path = Path(first_cutover["control"])
        second_control = Path(second_cutover["control"])
        saved_first = json_load(first_control_path)
        saved_second = json_load(second_control)
        legacy_first = json.loads(json.dumps(saved_first))
        legacy_second = json.loads(json.dumps(saved_second))
        for value in (legacy_first, legacy_second):
            value.pop("parent_operation_id", None)
            value.pop("chain_depth", None)
        json_write(first_control_path, legacy_first)
        json_write(second_control, legacy_second)
        inferred = extension_status(self.output)
        self.assertEqual(inferred["active_operation_id"], second_operation)
        self.assertEqual(inferred["parent_operation_id"], first_operation)
        self.assertEqual(inferred["chain_depth"], 2)
        json_write(first_control_path, saved_first)
        json_write(second_control, saved_second)

        drifted = json.loads(json.dumps(saved_second))
        drifted["parent_operation_id"] = "scope-extension-missing-parent"
        json_write(second_control, drifted)
        with self.assertRaisesRegex(CkbError, "control-record-drift"):
            extension_status(self.output)
        json_write(second_control, saved_second)

        duplicate_id = "scope-extension-duplicate-active"
        duplicate_path = self.output.parent / f".{self.output.name}.scope-extension-{duplicate_id}.json"
        duplicate = json.loads(json.dumps(saved_second))
        duplicate["operation_id"] = duplicate_id
        json_write(duplicate_path, duplicate)
        with self.assertRaisesRegex(CkbError, "control-record-active-ambiguous"):
            extension_status(self.output)
        duplicate_path.unlink()

        second_rollback = rollback_scope_extension(self.output)
        self.assertEqual(second_rollback["operation_id"], second_operation)
        self.assertEqual(second_rollback["reactivated_operation_id"], first_operation)
        self.assertEqual(_tree_manifest(self.output), first_tree)
        reactivated = extension_status(self.output)
        self.assertEqual(reactivated["active_operation_id"], first_operation)
        connection = sqlite3.connect(self.output / "machine/knowledge.sqlite")
        try:
            self.assertEqual(connection.execute("SELECT count(*) FROM entities WHERE qualified_name='first'").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM entities WHERE qualified_name='second'").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM entities WHERE qualified_name='third'").fetchone()[0], 0)
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            connection.close()
        compatibility = sqlite3.connect(self.output / "agent-index.sqlite")
        try:
            self.assertEqual(compatibility.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(compatibility.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            compatibility.close()

        first_rollback = rollback_scope_extension(self.output)
        self.assertEqual(first_rollback["operation_id"], first_operation)
        self.assertEqual(first_rollback["reactivated_operation_id"], None)
        self.assertEqual(_tree_manifest(self.output), initial)
        final_status = extension_status(self.output)
        self.assertEqual(final_status["status"], "rolled-back")
        self.assertEqual(final_status["active_operation_id"], None)
        repeated = rollback_scope_extension(self.output)
        self.assertTrue(repeated["idempotent"])
        self.assertEqual(repeated["operation_id"], first_operation)


if __name__ == "__main__":
    unittest.main()
