from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from ckb_core.common import CkbError
from ckb_core.human_page_templates import (
    HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
    get_human_page_template,
    human_page_template_registry_document,
    human_page_template_registry_sha256,
    list_human_page_types,
    serialize_human_page_template_registry,
    validate_human_page,
)


FIXTURES = SKILL_ROOT / "tests/fixtures/human-page-templates"


def _reasons(result: dict[str, object]) -> list[str]:
    return [str(error["reason"]) for error in result["errors"]]  # type: ignore[index]


def _source_context(target: str, purpose: str, key_entities: list[str] | None = None) -> dict[str, object]:
    return {
        "key_entities": key_entities or [],
        "links": [{"target": target, "purpose": purpose, "kind": "source"}],
        "current_facts": [],
    }


class HumanPageTemplateRegistryTests(unittest.TestCase):
    def test_registry_has_one_versioned_contract_for_every_human_page_type(self) -> None:
        expected = (
            "INDEX",
            "WIKI",
            "RECORDS",
            "REFERENCES",
            "responsibility",
            "change",
            "analysis",
            "pitfall",
            "experiment",
            "session",
            "reference",
            "learning-note",
            "feedback",
            "README",
        )
        self.assertEqual(expected, list_human_page_types())
        registry = human_page_template_registry_document()
        self.assertEqual(HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION, registry["schema_version"])
        self.assertEqual(HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION, registry["contract_version"])
        self.assertEqual(list(expected), registry["page_type_order"])
        self.assertEqual(list(expected), [item["page_type"] for item in registry["page_types"]])
        for item in registry["page_types"]:
            self.assertTrue(item["reader_task"])
            self.assertTrue(item["entry_conditions"])
            self.assertTrue(item["first_screen"]["responsibility"])
            self.assertTrue(item["required_sections"])
            self.assertTrue(item["forbidden_content"])
            self.assertIn("maximum", item["key_entity_budget"])
            self.assertIn(item["key_entity_budget"]["scope"], {"page", "entry"})
            self.assertIn("maximum", item["source_link_budget"])
            self.assertIn(item["source_link_budget"]["scope"], {"page", "entry"})
            self.assertTrue(item["link_requirements"])
            self.assertTrue(item["evidence_requirements"]["required_fields"])
            self.assertIn("extension_points", item)
            self.assertIsInstance(item["extension_points"], list)
            self.assertTrue(item["applicability_boundary"])

    def test_registry_serialization_and_hash_are_byte_stable(self) -> None:
        first = serialize_human_page_template_registry()
        second = serialize_human_page_template_registry()
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))
        parsed = json.loads(first)
        self.assertEqual(list(list_human_page_types()), parsed["page_type_order"])
        self.assertEqual(hashlib.sha256(first.encode("utf-8")).hexdigest(), human_page_template_registry_sha256())

    def test_query_returns_an_immutable_contract(self) -> None:
        contract = get_human_page_template("change")
        with self.assertRaises(FrozenInstanceError):
            contract.reader_task = "changed"  # type: ignore[misc]
        self.assertIs(contract, get_human_page_template("CHANGE"))

    def test_change_contract_matches_the_accepted_section_contract_without_body_literals(self) -> None:
        contract = get_human_page_template("change")
        self.assertEqual(
            (
                "修改内容",
                "修改时间",
                "修改原因",
                "修改方式",
                "关联特性",
                "验证结果与适用边界",
                "关键源码范围",
            ),
            tuple(section.heading for section in contract.required_sections),
        )
        serialized = json.dumps(human_page_template_registry_document(), ensure_ascii=False)
        self.assertNotIn("Agent 会话级 stdio 生命周期变更", serialized)
        self.assertEqual(3, contract.key_entity_budget.maximum)

    def test_readme_contract_keeps_the_three_accepted_reader_tasks(self) -> None:
        contract = get_human_page_template("README")
        self.assertEqual(
            (
                "先选择你要完成的任务",
                "了解本项目知识库结构",
                "让 Agent 安装本项目",
                "让 Agent 解释自己的项目",
            ),
            tuple(section.heading for section in contract.required_sections),
        )
        self.assertEqual(3, contract.first_screen.maximum_key_items)

    def test_unknown_query_and_incompatible_query_fail_with_chinese_diagnostics(self) -> None:
        with self.assertRaisesRegex(CkbError, "未知人类页面类型"):
            get_human_page_template("unknown")
        with self.assertRaisesRegex(CkbError, "版本不兼容"):
            get_human_page_template("change", contract_version="2.0.0")


class HumanPageTemplateValidationTests(unittest.TestCase):
    def test_every_page_type_accepts_one_minimal_contract_document(self) -> None:
        source = "vscode://file/E:/fixture/source.py:1:1"
        cases: dict[str, tuple[str, dict[str, object]]] = {
            "INDEX": (
                """# 项目知识库

## 按任务选择入口
按任务选择职责、记录或检索。
## 按职责浏览代码
进入职责导览。
## 工作记录
进入工作记录导览。
## 精确定位
使用 brief 定位来源。
""",
                {"key_entities": [], "links": [], "current_facts": []},
            ),
            "WIKI": (
                """# 如何阅读知识库

## 从哪里开始
先选择读者任务。
## 页面只保留什么
只保留完成任务所需信息。
## 如何寻找修改入口
从职责进入源码和测试。
## Agent 确定性检索
先读取紧凑 pack。
""",
                {"key_entities": [], "links": [], "current_facts": []},
            ),
            "RECORDS": (
                """# 工作记录导览

## 先按任务选择
按结论、变化、实验、踩坑或会话选择记录。
## 快速查找
先按标题浏览，再使用稳定关键词。
## 分析与决策
- 当前没有这一类记录。
## 实现与变更
- 当前没有这一类记录。
## 实验与量化结果
- 当前没有这一类记录。
## 踩坑与限制
- 当前没有这一类记录。
## 会话与任务过程
- 当前没有这一类记录。
""",
                {"key_entities": [], "links": [], "current_facts": []},
            ),
            "REFERENCES": (
                """# 参考资料导览

## 已审阅资料
- [[确定性检索资料]] — 说明可复查的检索顺序。
""",
                {
                    "key_entities": [],
                    "links": [{"target": "确定性检索资料", "purpose": "阅读已审阅资料摘要", "kind": "internal"}],
                    "current_facts": [],
                },
            ),
            "responsibility": (
                (FIXTURES / "responsibility-valid.md").read_text(encoding="utf-8"),
                _source_context(source, "打开会话生命周期实现", ["start_session"]),
            ),
            "change": (
                """# 会话行为变更

## 修改内容
会话检索复用进程。
## 修改时间
合并时间见验证记录。
## 修改原因
原有进程没有会话所有者。
## 修改方式
生命周期管理负责创建和释放。
## 关联特性
与检索回退直接关联。
## 验证结果与适用边界
连续检索通过，缺少结束事件时显式关闭。
## 关键源码范围
- `session_stdio.py`：负责生命周期。
""",
                {"key_entities": ["lifecycle"], "links": [], "current_facts": []},
            ),
            "analysis": (
                """# 检索策略分析

## 结论
先使用紧凑检索。
## 已确认事实
检索保存来源范围。
## 事实对当前问题的影响
任务先缩小到少量文件。
## 仍需核验的内容
需要复测特殊语言仓库。
## 建议的下一步
使用固定问题集验证。
""",
                {"key_entities": [], "links": [], "current_facts": []},
            ),
            "pitfall": (
                """# Windows 路径踩坑

## 现象
混合路径导致入口失效。
## 触发条件
WSL Python 接收 Windows 根路径。
## 根因
运行时解释了错误的路径根。
## 解决方法
使用项目绑定的 Windows Python。
## 验证结果
同一命令返回正确页面。
## 适用边界
只涉及 Windows 知识库路径。
""",
                {"key_entities": [], "links": [], "current_facts": []},
            ),
            "experiment": (
                f"""# 检索实验

## 实验问题
比较两条检索路径。
## 实验设计
固定输入和顺序。
## 对照与变量
只改变检索档位。
## 结果
记录字面输出。
## 结论
紧凑路径满足本组任务。
## 适用边界
结论只覆盖固定样本。
## 复现入口
[打开实验记录]({source})
""",
                _source_context(source, "打开固定实验结果"),
            ),
            "session": (
                """# 模板合同任务

## 任务目标
建立类型化合同。
## 执行范围
只修改合同和测试。
## 已完成结果
注册表已生成。
## 验证结果
稳定序列化通过。
## 待继续事项
等待后续接入正式审计。
""",
                {"key_entities": [], "links": [], "current_facts": []},
            ),
            "reference": (
                f"""# 外部资料

## 这份资料讲什么
资料说明确定性检索方法。
## 关键结论
- 每项结论回链原文。
## 来源
- [打开归档原文]({source})
""",
                _source_context(source, "核对归档原文"),
            ),
            "learning-note": (
                """# 2026-09-02 学习笔记

标签：#类型/学习

> 汇总当天经过审计的解释。

## 09:30:00 · 来源页面

来源：[[source|来源页面]]

### 我的问题

这个合同解决什么问题？

### 选中文本

> 类型化模板合同

### 解释

它让生成和审计读取同一组字段。
""",
                _source_context("source", "打开选区来源页面"),
            ),
            "feedback": (
                """# 关于职责页的反馈

状态：待处理

## 反馈内容
请说明验证入口。
## 锚点摘录
> 什么时候需要修改
""",
                {"key_entities": [], "links": [], "current_facts": []},
            ),
            "README": (
                """# Code Knowledge Builder

## 先选择你要完成的任务
选择了解结构、安装或解释项目。
## 了解本项目知识库结构
区分人类入口和机器入口。
## 让 Agent 安装本项目
安装 Prompt 只完成安装验收。
## 让 Agent 解释自己的项目
解释 Prompt 为目标仓库建库并回答问题。
""",
                {"key_entities": ["结构", "安装", "解释"], "links": [], "current_facts": []},
            ),
        }
        self.assertEqual(set(list_human_page_types()), set(cases))
        for page_type, (markdown, context) in cases.items():
            with self.subTest(page_type=page_type):
                result = validate_human_page(page_type, markdown, context=context)
                self.assertEqual("passed", result["status"], result["errors"])

    def test_learning_note_budgets_are_applied_per_repeated_entry(self) -> None:
        markdown = """# 2026-09-02 学习笔记

## 09:30:00 · 第一页
来源：[[source-one|第一页]]
### 我的问题
第一个问题是什么？
### 解释
第一条解释。

## 10:00:00 · 第二页
来源：[[source-two|第二页]]
### 我的追问
第二个问题是什么？
### 解释
第二条解释。
"""
        context = {
            "key_entities": ["ENTITY_1", "ENTITY_2", "ENTITY_3", "ENTITY_4"],
            "links": [
                {"target": "source-one", "purpose": "打开第一条选区来源", "kind": "source"},
                {"target": "source-two", "purpose": "打开第二条选区来源", "kind": "source"},
            ],
            "current_facts": [],
        }
        result = validate_human_page("learning-note", markdown, context=context)
        self.assertEqual("passed", result["status"], result["errors"])
        contract = get_human_page_template("learning-note")
        self.assertEqual("entry", contract.key_entity_budget.scope)
        self.assertEqual("entry", contract.source_link_budget.scope)

    def test_missing_required_section_fails_deterministically(self) -> None:
        markdown = (FIXTURES / "change-missing-section.md").read_text(encoding="utf-8")
        result = validate_human_page(
            "change",
            markdown,
            context={"key_entities": ["session_stdio"], "links": [], "current_facts": []},
        )
        self.assertEqual("failed", result["status"])
        self.assertIn("required-section-missing", _reasons(result))
        missing = next(error for error in result["errors"] if error["reason"] == "required-section-missing")
        self.assertEqual("修改原因", missing["heading"])

    def test_duplicate_heading_fails_deterministically(self) -> None:
        markdown = (FIXTURES / "analysis-duplicate-heading.md").read_text(encoding="utf-8")
        result = validate_human_page("analysis", markdown)
        self.assertIn("duplicate-heading", _reasons(result))
        duplicate = next(error for error in result["errors"] if error["reason"] == "duplicate-heading")
        self.assertEqual([3, 7], duplicate["lines"])

    def test_key_entity_budget_uses_explicit_context_and_fails_at_eight(self) -> None:
        markdown = (FIXTURES / "responsibility-valid.md").read_text(encoding="utf-8")
        context = json.loads((FIXTURES / "responsibility-too-many-entities.json").read_text(encoding="utf-8"))
        result = validate_human_page("responsibility", markdown, context=context)
        self.assertIn("key-entity-budget", _reasons(result))
        error = next(error for error in result["errors"] if error["reason"] == "key-entity-budget")
        self.assertEqual(8, error["actual"])
        self.assertEqual(7, error["maximum"])

    def test_unverified_current_fact_fails_and_exact_evidence_passes(self) -> None:
        markdown = (FIXTURES / "change-untrusted-current-fact.md").read_text(encoding="utf-8")
        base_context = {"key_entities": ["session_stdio"], "links": [], "current_facts": []}
        failed = validate_human_page("change", markdown, context=base_context)
        self.assertIn("current-fact-unverified", _reasons(failed))
        passed = validate_human_page(
            "change",
            markdown,
            context={
                **base_context,
                "current_facts": [
                    {
                        "claim": "当前状态已经覆盖所有 Harness。",
                        "source": "verification.json",
                        "observed_at": "2026-09-02",
                    }
                ],
            },
        )
        self.assertEqual("passed", passed["status"], passed["errors"])

    def test_process_meta_copy_and_purposeless_link_fail(self) -> None:
        meta = (FIXTURES / "analysis-process-meta-copy.md").read_text(encoding="utf-8")
        self.assertIn("process-meta-copy", _reasons(validate_human_page("analysis", meta)))
        readme = (FIXTURES / "readme-purposeless-link.md").read_text(encoding="utf-8")
        result = validate_human_page(
            "README",
            readme,
            context={"key_entities": ["结构", "安装", "解释"], "links": [], "current_facts": []},
        )
        self.assertIn("link-purpose-missing", _reasons(result))

    def test_unknown_type_and_incompatible_version_return_machine_failures(self) -> None:
        unknown = validate_human_page("unknown", "# 页面\n")
        self.assertEqual(["unknown-page-type"], _reasons(unknown))
        incompatible = validate_human_page("change", "# 页面\n", contract_version="2.0.0")
        self.assertEqual(["contract-version-incompatible"], _reasons(incompatible))
        self.assertEqual(
            {"schema_version": HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION, "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION},
            incompatible["errors"][0]["expected"],
        )


if __name__ == "__main__":
    unittest.main()
