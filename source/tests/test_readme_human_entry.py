from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
FIXTURE = ROOT / "tests" / "fixtures" / "human-maintenance-prompts" / "readme-v5.json"


def _section(markdown: str, heading: str, next_heading: str | None) -> str:
    start = markdown.index(f"## {heading}\n")
    end = len(markdown) if next_heading is None else markdown.index(f"## {next_heading}\n", start + 1)
    return markdown[start:end]


class ReadmeHumanEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.markdown = README.read_text(encoding="utf-8")
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_first_screen_contains_only_three_human_tasks_and_direct_results(self) -> None:
        first_screen = self.markdown.split("\n---\n", 1)[0]
        task_links = re.findall(r"^\| \[([^]]+)\]\(#[^)]+\) \| ([^|]+) \|$", first_screen, flags=re.MULTILINE)
        expected = [(value["task"], value["direct_result"]) for value in self.fixture["first_screen_tasks"]]
        self.assertEqual(expected, [(task, result.strip()) for task, result in task_links])
        self.assertNotIn("安装后继续指挥 Agent", first_screen)
        for forbidden in ("```", "ckb.py", "python.exe", "SQLite", "manifest", "maintain", "审计", "回滚探针"):
            self.assertNotIn(forbidden, first_screen)

    def test_required_headings_are_exact_and_ordered(self) -> None:
        headings = re.findall(r"^## (.+)$", self.markdown, flags=re.MULTILINE)
        self.assertEqual(self.fixture["headings"], headings)

    def test_each_task_card_reuses_the_accepted_direct_result_and_prompt(self) -> None:
        names = self.fixture["headings"]
        section_keys = {
            "了解本项目知识库结构": "structure",
            "让 Agent 安装本项目": "install",
            "让 Agent 解释自己的项目": "explain",
            "安装后继续指挥 Agent": "continue",
        }
        for index, heading in enumerate(names[1:], start=1):
            next_heading = names[index + 1] if index + 1 < len(names) else None
            body = _section(self.markdown, heading, next_heading)
            card = self.fixture["task_cards"][section_keys[heading]]
            self.assertIn(card["direct_result"], body)
            self.assertIn(card["copy_to_agent"], body)
            self.assertIn("### 只验收最终结果", body)

    def test_install_and_explain_prompts_keep_separate_responsibilities(self) -> None:
        install = _section(self.markdown, "让 Agent 安装本项目", "让 Agent 解释自己的项目")
        explain = _section(self.markdown, "让 Agent 解释自己的项目", "安装后继续指挥 Agent")
        self.assertIn("不为业务仓库建立知识库", install)
        self.assertNotIn("repository=", install)
        self.assertNotIn("回答 question=", install)
        self.assertIn("建立或接管知识库", explain)
        self.assertIn("不重复安装项目", explain)
        self.assertNotIn("项目来源=", explain)
        self.assertNotIn("发布版本=", explain)

    def test_follow_up_navigation_separates_existing_reading_from_maintenance(self) -> None:
        continuation = _section(self.markdown, "安装后继续指挥 Agent", None)
        reading = continuation.index("### 阅读已有知识库")
        managed = continuation.index("### 建立或接管知识库")
        self.assertLess(reading, managed)
        for purpose in ("记录可复用结论", "维护现有知识库", "迁移到新的源码版本", "接入 Harness"):
            self.assertGreater(continuation.index(purpose), managed)
        self.assertIn("完整验证明细仅在我明确要求时读取", continuation)


if __name__ == "__main__":
    unittest.main()
