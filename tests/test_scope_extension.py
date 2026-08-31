from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from ckb_core.common import CkbError
from ckb_core.pipeline import build_chunk, finalize, initialize, review_pack
from ckb_core.scope_extension import (
    _tree_manifest,
    audit_scope_extension,
    cutover_scope_extension,
    extension_status,
    rollback_scope_extension,
    start_scope_extension,
)


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
        (self.repo / "duplicate.py").write_text("def repeated():\n    return 1\n\ndef repeated():\n    return 2\n", encoding="utf-8")
        (self.repo / "ignored.txt").write_text("not tracked source", encoding="utf-8")
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "scope fixture")
        self.old_provider = os.environ.get("CKB_TEST_PROVIDER")
        os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"
        initialize(self.repo, self.output, "markdown", [], ["python:app.py#first"], 0, "both", [])
        review_all(self.output)
        finalize(self.output)
        for vault in ("human", "markdown"):
            page = self.output / vault / "user" / "学习笔记一.md"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text("# 学习笔记一\n\n这是必须按原字节保留的第一份学习笔记。\n", encoding="utf-8")
            page2 = self.output / vault / "user" / "学习笔记二.md"
            page2.write_text("# 学习笔记二\n\n这是必须按原字节保留的第二份学习笔记。\n", encoding="utf-8")

    def tearDown(self) -> None:
        if self.old_provider is None:
            os.environ.pop("CKB_TEST_PROVIDER", None)
        else:
            os.environ["CKB_TEST_PROVIDER"] = self.old_provider
        self.temporary.cleanup()

    def test_union_delta_idempotence_cutover_and_byte_exact_rollback(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
