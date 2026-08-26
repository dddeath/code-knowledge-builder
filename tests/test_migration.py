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

from ckb_core.migration import audit_migration, migrate_output
from ckb_core.pipeline import build_chunk, finalize, initialize, review_pack


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
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
            item["evidence_note"] = "Agent 已重新打开固定 Git 源码范围，核对名称、签名、分支和调用关系后确认本条说明。"
            if pack["kind"] == "appendix-review":
                item["description_zh"] = "该局部代码负责完成所属流程中的辅助处理，并把结果交给主流程继续使用。"
            else:
                item["meaning_zh"] = "该代码页说明固定源码范围内的主要实现及其输入输出约定。"
                item["role_zh"] = "它负责组织当前代码单元的处理步骤，并与相邻函数形成可追踪的调用关系。"
                item["change_when_zh"] = "当输入约定、处理步骤、返回结果或调用关系变化时，需要修改该代码单元并同步验证。"
        review_path = output / "test-reviews" / f"{pack['id']}.json"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        review_pack(output, pack["id"], review_path)


class MigrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ckb-migration-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.old = self.root / "old-output"
        self.new = self.root / "new-output"
        self.repo.mkdir()
        (self.repo / "app.py").write_text(
            "from helper import double\n\ndef calculate(value):\n    return double(value)\n",
            encoding="utf-8",
        )
        (self.repo / "helper.py").write_text("def double(value):\n    return value * 2\n", encoding="utf-8")
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "version 5.0 fixture")
        self.old_provider = os.environ.get("CKB_TEST_PROVIDER")
        os.environ["CKB_TEST_PROVIDER"] = "deterministic-fixture"

    def tearDown(self) -> None:
        if self.old_provider is None:
            os.environ.pop("CKB_TEST_PROVIDER", None)
        else:
            os.environ["CKB_TEST_PROVIDER"] = self.old_provider
        self.temporary.cleanup()

    def test_exact_blob_facts_and_agent_reviews_are_reused(self) -> None:
        initialize(self.repo, self.old, "markdown", [], [], 1, "both", [])
        review_all(self.old)
        finalize(self.old)
        old_state_path = self.old / "state.json"
        old_state = json.loads(old_state_path.read_text(encoding="utf-8"))
        old_state["version"] = "5.0.0"
        old_state_path.write_text(json.dumps(old_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        old_graph = json.loads((self.old / "graph.json").read_text(encoding="utf-8"))
        old_projection = json.loads((self.old / "markdown/projection.json").read_text(encoding="utf-8"))
        old_entity_by_id = {item["id"]: item for item in old_graph["entities"]}
        old_app_title = next(
            page["title"]
            for page in old_projection["pages"]
            if old_entity_by_id[page["id"]]["kind"] == "file" and old_entity_by_id[page["id"]]["path"] == "app.py"
        )
        for vault in ("human", "markdown"):
            user_page = self.old / vault / "user" / "人工保留页.md"
            user_page.parent.mkdir(parents=True, exist_ok=True)
            user_page.write_text(f"# 人工保留页\n\n这是一份迁移期间必须保留的中文用户笔记，原链接为 [[{old_app_title}]]。\n", encoding="utf-8")

        (self.repo / "app.py").write_text(
            "from helper import double\n\ndef calculate_v2(value):\n    return double(value) + 1\n",
            encoding="utf-8",
        )
        (self.repo / "automation.py").write_text("def capture(event):\n    return event.get('type')\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "version 5.1 fixture")

        result = migrate_output(self.old, self.repo, self.new)
        self.assertEqual(result["status"], "pending-agent-review")
        plan = json.loads((self.new / "migration/plan.json").read_text(encoding="utf-8"))
        self.assertIn("helper.py", plan["files"]["reused"])
        self.assertGreater(plan["entities"]["reused_review_count"], 0)
        self.assertGreater(plan["entities"]["delta_review_count"], 0)
        catalog = json.loads((self.new / "catalog.json").read_text(encoding="utf-8"))
        helper = next(item for item in catalog["files"] if item["file"]["path"] == "helper.py")
        self.assertEqual(helper["migration_reuse"]["basis"], "exact-path-language-blob-and-passed-parse")
        self.assertTrue((self.new / "human/user/人工保留页.md").is_file())

        review_all(self.new)
        complete = finalize(self.new)
        self.assertEqual(complete["status"], "complete")
        migration_audit = audit_migration(self.new)
        self.assertEqual(migration_audit["status"], "passed")
        new_graph = json.loads((self.new / "graph.json").read_text(encoding="utf-8"))
        new_projection = json.loads((self.new / "markdown/projection.json").read_text(encoding="utf-8"))
        new_entity_by_id = {item["id"]: item for item in new_graph["entities"]}
        new_app_title = next(
            page["title"]
            for page in new_projection["pages"]
            if new_entity_by_id[page["id"]]["kind"] == "file" and new_entity_by_id[page["id"]]["path"] == "app.py"
        )
        migrated_note = (self.new / "human/user/人工保留页.md").read_text(encoding="utf-8")
        self.assertNotEqual(old_app_title, new_app_title)
        self.assertIn(f"[[{new_app_title}]]", migrated_note)
        self.assertNotIn(f"[[{old_app_title}]]", migrated_note)


if __name__ == "__main__":
    unittest.main()
