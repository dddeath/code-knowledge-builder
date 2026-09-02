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
DEEP_TARGET = "INDEX.md#让-Agent-精确定位"


def _reasons(result: dict[str, object]) -> list[str]:
    return [str(error["reason"]) for error in result["errors"]]  # type: ignore[index]


def _context(**sections: dict[str, object]) -> dict[str, object]:
    return {"sections": sections, "current_facts": []}


def _section_context(
    *,
    key_entities: list[str] | None = None,
    links: list[dict[str, str]] | None = None,
    metrics: list[str] | None = None,
    source_refs: list[dict[str, str]] | None = None,
    machine_evidence_refs: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    return {
        "key_entities": key_entities or [],
        "links": links or [],
        "metrics": metrics or [],
        "source_refs": source_refs or [],
        "machine_evidence_refs": machine_evidence_refs or [],
    }


def _deep_context(**sections: dict[str, object]) -> dict[str, object]:
    sections["deep-reading"] = _section_context(
        links=[{"target": DEEP_TARGET, "purpose": "继续定位相关源码与记录", "kind": "internal"}]
    )
    return _context(**sections)


class HumanPageTemplateRegistryTests(unittest.TestCase):
    def test_registry_has_one_v3_contract_for_every_human_page_type(self) -> None:
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
        self.assertEqual(3, HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION)
        self.assertEqual("3.0.0", HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION)
        self.assertEqual(expected, list_human_page_types())
        registry = human_page_template_registry_document()
        self.assertEqual(3, registry["schema_version"])
        self.assertEqual("3.0.0", registry["contract_version"])
        self.assertEqual(list(expected), registry["page_type_order"])
        self.assertEqual(list(expected), [item["page_type"] for item in registry["page_types"]])
        section_fields = {
            "required_content",
            "allowed_content",
            "forbidden_content",
            "length_budget",
            "key_entity_budget",
            "link_budget",
            "source_requirements",
            "freshness_rule",
            "disclosure_level",
            "empty_behavior",
        }
        for item in registry["page_types"]:
            self.assertTrue(item["reader_task"])
            self.assertTrue(item["required_sections"])
            for section in item["required_sections"] + item["optional_sections"]:
                self.assertTrue(section_fields.issubset(section))
                self.assertTrue(section["required_content"])
                self.assertTrue(section["allowed_content"])
                self.assertTrue(section["forbidden_content"])
                self.assertTrue(section["source_requirements"])
                self.assertTrue(section["freshness_rule"])
                self.assertIn(section["disclosure_level"], {"L1", "L2", "L3"})
                self.assertIn(section["empty_behavior"], {"error", "omit", "explicit-empty"})
                self.assertEqual("section", section["key_entity_budget"]["scope"])
                self.assertTrue(section["link_budget"]["target_types"])

    def test_registry_serialization_and_hash_are_byte_stable(self) -> None:
        first = serialize_human_page_template_registry()
        second = serialize_human_page_template_registry()
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))
        self.assertEqual(hashlib.sha256(first.encode("utf-8")).hexdigest(), human_page_template_registry_sha256())
        self.assertEqual(json.loads(first), human_page_template_registry_document())

    def test_query_returns_an_immutable_contract(self) -> None:
        contract = get_human_page_template("change")
        with self.assertRaises(FrozenInstanceError):
            contract.reader_task = "changed"  # type: ignore[misc]
        self.assertIs(contract, get_human_page_template("CHANGE"))

    def test_confirmed_v3_headings_are_exact(self) -> None:
        expected = {
            "INDEX": ("先选择你要完成的任务", "按职责浏览代码", "查找项目记录", "让 Agent 精确定位"),
            "WIKI": ("从哪里开始", "各类页面负责什么", "如何追踪方案与实现变化", "如何让 Agent 帮助阅读", "深入了解"),
            "RECORDS": ("先选择你要查找的内容", "分析与方案", "实现与修改", "实验与性能", "问题与限制", "会话与方案变化", "让 Agent 帮助查找"),
            "REFERENCES": ("这些资料能回答什么", "按主题选择资料", "让 Agent 帮助查找"),
            "responsibility": ("职责说明", "适用场景", "功能结果", "关联范围", "当前边界", "深入阅读"),
            "change": ("修改内容", "修改时间", "修改原因", "实现概述", "关联特性", "当前结果", "适用边界", "深入阅读"),
            "analysis": ("当前结论", "问题关联", "事实基础", "结论应用", "未决事项", "后续建议", "深入阅读"),
            "pitfall": ("问题现象", "触发条件", "影响范围", "原因说明", "处理方式", "当前结果", "适用边界", "深入阅读"),
            "experiment": ("实验问题", "比较对象", "功能与性能覆盖", "结果摘要", "结论", "适用边界", "后续工作", "深入阅读"),
            "session": ("任务目标", "执行范围", "关键决策与方案变化", "当前结果", "可用成果", "未决事项", "后续行动", "深入阅读"),
            "reference": ("资料概述", "适用问题", "关键结论", "来源", "适用边界", "深入阅读"),
            "learning-note": ("学习问题", "解释摘要", "应用方式", "关联内容"),
            "feedback": ("反馈内容", "影响范围", "当前状态", "后续行动"),
            "README": ("先选择你要完成的任务", "了解本项目知识库结构", "让 Agent 安装本项目", "让 Agent 解释自己的项目", "安装后继续指挥 Agent"),
        }
        for page_type, headings in expected.items():
            with self.subTest(page_type=page_type):
                self.assertEqual(headings, tuple(value.heading for value in get_human_page_template(page_type).required_sections))
        self.assertEqual(("查找外部资料",), tuple(value.heading for value in get_human_page_template("INDEX").optional_sections))
        self.assertEqual(("实验功能",), tuple(value.heading for value in get_human_page_template("README").optional_sections))
        self.assertEqual(3, get_human_page_template("README").first_screen.maximum_key_items)
        self.assertEqual(("后续问题",), tuple(value.heading for value in get_human_page_template("learning-note").optional_sections))
        self.assertEqual(("处理结论",), tuple(value.heading for value in get_human_page_template("feedback").optional_sections))

    def test_old_1_0_0_is_rejected_with_explicit_migration_rule(self) -> None:
        with self.assertRaisesRegex(CkbError, "显式按 V3 章节重写"):
            get_human_page_template("change", contract_version="1.0.0", schema_version=1)
        result = validate_human_page(
            "change",
            "# 旧页面\n",
            contract_version="1.0.0",
            schema_version=1,
        )
        self.assertEqual("failed", result["status"])
        self.assertEqual("contract-version-incompatible", result["errors"][0]["reason"])
        self.assertEqual("explicit-rewrite", result["errors"][0]["migration"]["mode"])

    def test_unknown_query_and_validator_type_fail_with_machine_readable_reasons(self) -> None:
        with self.assertRaisesRegex(CkbError, "未知人类页面类型"):
            get_human_page_template("unknown")
        result = validate_human_page("unknown", "# 未知页面\n", context=_context())
        self.assertEqual("failed", result["status"])
        self.assertEqual("unknown-page-type", result["errors"][0]["reason"])


class HumanPageTemplateValidationTests(unittest.TestCase):
    def test_every_page_type_accepts_one_minimal_v3_document(self) -> None:
        source = "vscode://file/E:/fixture/source.py:1:1"
        cases: dict[str, tuple[str, dict[str, object]]] = {
            "INDEX": ("""# 项目知识库

## 先选择你要完成的任务
选择职责、记录、资料或精确定位。
## 按职责浏览代码
进入职责说明页。
## 查找项目记录
进入项目记录导览。
## 让 Agent 精确定位
描述问题后由 Agent 返回源码范围。
""", _context()),
            "WIKI": ("""# 如何阅读知识库

## 从哪里开始
先按当前阅读任务选择入口。
## 各类页面负责什么
导航页负责选择，内容页负责解释。
## 如何追踪方案与实现变化
从项目记录进入职责与源码。
## 如何让 Agent 帮助阅读
描述目标并要求返回结论和来源。
## 深入了解
继续阅读职责、记录或资料。
""", _context()),
            "RECORDS": ("""# 项目记录

## 先选择你要查找的内容
按问题目的选择记录。
## 分析与方案
暂无相关记录。
## 实现与修改
暂无相关记录。
## 实验与性能
暂无相关记录。
## 问题与限制
暂无相关记录。
## 会话与方案变化
暂无相关记录。
## 让 Agent 帮助查找
说明问题和时间范围后返回记录摘要。
""", _context()),
            "REFERENCES": ("""# 外部资料

## 这些资料能回答什么
资料用于核对已审阅外部主张。
## 按主题选择资料
按检索主题进入摘要页。
## 让 Agent 帮助查找
描述问题后返回资料和原文范围。
""", _context()),
            "responsibility": ("""# 模板职责

## 职责说明
产生稳定的人类页面合同。
## 适用场景
需要生成或检查人类页面时使用。
## 功能结果
页面标题、预算和边界保持一致。
## 关联范围
`human_page_templates` 承担注册与验证。
## 当前边界
只覆盖 V3 人类页面合同。
## 深入阅读
[让 Agent 按本页问题继续定位](INDEX.md#让-Agent-精确定位)。
""", _deep_context(**{"related-scope": _section_context(key_entities=["human_page_templates"])})),
            "change": ("""# V3 页面合同

## 修改内容
人类页面按章节声明完整约束。
## 修改时间
该描述绑定 V3 合同。
## 修改原因
旧合同只表达标题和用途。
## 实现概述
`human_page_templates` 统一注册和验证。
## 关联特性
authoring 与 proposal 读取同一规范。
## 当前结果
候选页会检查章节预算和披露层级。
## 适用边界
只覆盖 V3 输入。
## 深入阅读
[让 Agent 按本页问题继续定位](INDEX.md#让-Agent-精确定位)。
""", _deep_context(implementation=_section_context(key_entities=["human_page_templates"]))),
            "analysis": ("""# V3 合同分析

## 当前结论
章节级合同适合统一生成和审阅。
## 问题关联
旧输入缺少披露与空值语义。
## 事实基础
注册表为每节保存相同字段。
## 结论应用
生成器读取字段后构造候选页。
## 未决事项
既有页面迁移留给后续集成。
## 后续建议
先在隔离输出验证候选页。
## 深入阅读
[让 Agent 按本页问题继续定位](INDEX.md#让-Agent-精确定位)。
""", _deep_context()),
            "pitfall": ("""# L4 证据泄漏

## 问题现象
普通人类页混入机器验证明细。
## 触发条件
把验证记录直接复制到正文。
## 影响范围
读者无法快速获得当前结论。
## 原因说明
摘要与机器证据没有分离。
## 处理方式
正文只保留概述并登记证据引用。
## 当前结果
人类页保持结论与边界。
## 适用边界
完整证据仍由机器层保存。
## 深入阅读
[让 Agent 按本页问题继续定位](INDEX.md#让-Agent-精确定位)。
""", _deep_context()),
            "experiment": ("""# 页面披露实验

## 实验问题
验证摘要能否保留功能与性能信息。
## 比较对象
比较 V3 摘要与旧式证据堆叠。
## 功能与性能覆盖
覆盖原生文本 PDF、扫描页、页码定位和代码块保留。
## 结果摘要
准确率 92%，延迟 120 ms。
## 结论
少量指标足以说明本组结果。
## 适用边界
代码布局仍有限制。
## 后续工作
扩展固定样本后再比较。
## 深入阅读
[让 Agent 按本页问题继续定位](INDEX.md#让-Agent-精确定位)。
""", _deep_context(summary=_section_context(metrics=["准确率 92%", "延迟 120 ms"]))),
            "session": ("""# V3 开发任务

## 任务目标
实现章节级人类页面合同。
## 执行范围
只修改模板、authoring、proposal 与 Prompt。
## 关键决策与方案变化
人类摘要与机器证据引用分离。
## 当前结果
模板注册表已具备完整章节字段。
## 可用成果
候选页可由结构化输入重新生成。
## 未决事项
正式投影迁移由后续集成执行。
## 后续行动
运行回归并交给管理任务复查。
## 深入阅读
[让 Agent 按本页问题继续定位](INDEX.md#让-Agent-精确定位)。
""", _deep_context()),
            "reference": (f"""# 页面设计资料

## 资料概述
资料说明渐进式披露方法。
## 适用问题
用于判断人类页应展示哪些信息。
## 关键结论
入口页只保留任务和直接结果。
## 来源
[打开归档资料]({source})用于核对原文。
## 适用边界
资料结论只覆盖已审阅范围。
## 深入阅读
[让 Agent 按本页问题继续定位](INDEX.md#让-Agent-精确定位)。
""", _deep_context(source=_section_context(links=[{"target": source, "purpose": "核对归档原文", "kind": "source"}]))),
            "learning-note": ("""# 页面合同学习

## 学习问题
怎样分离摘要与机器证据？
## 解释摘要
正文保存任务结论，机器引用保存完整证据。
## 应用方式
生成候选页时只渲染 human_summary。
## 关联内容
继续阅读模板职责说明。
""", _context()),
            "feedback": ("""# 页面合同反馈

## 反馈内容
请明确每节的链接预算。
## 影响范围
影响 change 页的深入阅读章节。
## 当前状态
反馈等待模板实现复核。
## 后续行动
实现后由管理任务审阅。
""", _context()),
            "README": ("""# Code Knowledge Builder

## 先选择你要完成的任务
首屏只选择了解结构、安装本项目或解释自己的项目。
## 了解本项目知识库结构
人类入口给出结论，机器入口保存完整事实。
## 让 Agent 安装本项目
把项目来源交给 Agent，并要求返回安装结果与边界。
## 让 Agent 解释自己的项目
把仓库和问题交给 Agent，并要求返回结论与来源。
## 安装后继续指挥 Agent
继续要求 Agent 阅读、定位、修改或核验指定问题。
""", _context()),
        }
        self.assertEqual(set(list_human_page_types()), set(cases))
        for page_type, (markdown, context) in cases.items():
            with self.subTest(page_type=page_type):
                result = validate_human_page(page_type, markdown, context=context)
                self.assertEqual("passed", result["status"], result["errors"])

    def test_section_budget_is_scoped_to_the_named_section(self) -> None:
        markdown = """# 模板职责

## 职责说明
产生稳定合同。
## 适用场景
生成人类页时使用。
## 功能结果
候选页返回清楚结果。
## 关联范围
列出关键实现。
## 当前边界
只覆盖模板层。
## 深入阅读
继续阅读项目记录。
"""
        result = validate_human_page(
            "responsibility",
            markdown,
            context=_context(**{"related-scope": _section_context(key_entities=["A", "B", "C", "D", "E", "F"])}),
        )
        self.assertIn("section-key-entity-budget", _reasons(result))
        error = next(value for value in result["errors"] if value["reason"] == "section-key-entity-budget")
        self.assertEqual("related-scope", error["section_id"])
        self.assertEqual(5, error["maximum"])

    def test_l3_allows_coverage_and_small_metrics_but_rejects_l4_shapes(self) -> None:
        base = """# 实验摘要

## 实验问题
验证披露边界。
## 比较对象
比较两种页面表示。
## 功能与性能覆盖
已测试原生文本 PDF、扫描页、页码定位和代码块保留；代码布局仍有限制。
## 结果摘要
准确率 92%，延迟 120 ms。
## 结论
少量指标足以支持本组判断。
## 适用边界
结论只覆盖固定样本。
## 后续工作
扩展样本后再比较。
## 深入阅读
[让 Agent 按本页问题继续定位](INDEX.md#让-Agent-精确定位)。
"""
        context = _deep_context(
            coverage=_section_context(),
            summary=_section_context(
                metrics=["准确率 92%", "延迟 120 ms"],
                machine_evidence_refs=[{"target": "artifacts/verification.json", "purpose": "复查完整命令与结果", "kind": "log"}],
            ),
        )
        context["current_facts"] = [
            {
                "section_id": "coverage",
                "claim": "已测试原生文本 PDF、扫描页、页码定位和代码块保留；代码布局仍有限制。",
                "source": "machine-evidence:coverage",
                "observed_at": "2026-09-02",
            }
        ]
        self.assertEqual("passed", validate_human_page("experiment", base, context=context)["status"])
        leaked = base.replace("准确率 92%，延迟 120 ms。", "专项测试 268/268 通过，exit_status=0。")
        result = validate_human_page("experiment", leaked, context=_deep_context())
        leaks = [value for value in result["errors"] if value["reason"] == "l4-evidence-leak"]
        self.assertTrue(leaks)
        self.assertEqual("summary", leaks[0]["section_id"])
        self.assertIn(leaks[0]["evidence_shape"], {"test-total", "raw-log"})

    def test_machine_evidence_ref_target_must_not_be_rendered(self) -> None:
        markdown = """# 页面合同分析

## 当前结论
章节级合同保持一致。
## 问题关联
用于分离人类摘要与机器证据。
## 事实基础
注册表保存结构化字段。
## 结论应用
生成器读取同一规范。
## 未决事项
正式迁移尚待集成。
## 后续建议
先验证候选页。
## 深入阅读
验证文件 artifacts/verification.json 记录完整结果；[让 Agent 按本页问题继续定位](INDEX.md#让-Agent-精确定位)。
"""
        result = validate_human_page(
            "analysis",
            markdown,
            context=_context(**{
                "deep-reading": _section_context(machine_evidence_refs=[
                    {"target": "artifacts/verification.json", "purpose": "复查完整验证", "kind": "log"}
                ], links=[{"target": DEEP_TARGET, "purpose": "继续定位相关源码与记录", "kind": "internal"}])
            }),
        )
        self.assertIn("l4-machine-evidence-rendered", _reasons(result))

    def test_visible_links_require_exact_registration_and_reject_unused_or_conflicting_targets(self) -> None:
        markdown = """# Code Knowledge Builder

## 先选择你要完成的任务
[阅读项目说明](guide.md)。
## 了解本项目知识库结构
区分人类与机器入口。
## 让 Agent 安装本项目
交给 Agent 完成安装。
## 让 Agent 解释自己的项目
交给 Agent 回答问题。
## 安装后继续指挥 Agent
继续指挥 Agent 阅读与修改。
"""
        undeclared = validate_human_page("README", markdown, context=_context())
        self.assertIn("link-context-missing", _reasons(undeclared))

        without_link = markdown.replace("[阅读项目说明](guide.md)。", "先选择一项任务。")
        unused = validate_human_page(
            "README",
            without_link,
            context=_context(**{
                "task-choice": _section_context(
                    links=[{"target": "guide.md", "purpose": "阅读项目说明", "kind": "internal"}]
                )
            }),
        )
        self.assertIn("link-context-unused", _reasons(unused))

        conflicting = validate_human_page(
            "README",
            markdown,
            context=_context(**{
                "task-choice": _section_context(
                    links=[
                        {"target": "guide.md", "purpose": "阅读项目说明", "kind": "internal"},
                        {"target": "guide.md", "purpose": "打开外部资料", "kind": "external"},
                    ]
                )
            }),
        )
        self.assertIn("link-target-conflict", _reasons(conflicting))

    def test_complete_test_total_shapes_are_l4_but_feature_coverage_is_not(self) -> None:
        template = """# 实验摘要

## 实验问题
验证测试摘要边界。
## 比较对象
比较人类摘要与机器证据。
## 功能与性能覆盖
已测试原生文本 PDF、扫描页、页码定位和代码块保留；代码布局仍有限制。
## 结果摘要
RESULT
## 结论
人类页只保留结论边界。
## 适用边界
结论只覆盖固定样例。
## 后续工作
继续扩展固定样例。
## 深入阅读
[让 Agent 按本页问题继续定位](INDEX.md#让-Agent-精确定位)。
"""
        for value in (
            "Ran 266 tests in 1126.469s; OK。",
            "266 tests passed。",
            "通过 266 项测试。",
            "测试总数：266。",
        ):
            with self.subTest(value=value):
                result = validate_human_page("experiment", template.replace("RESULT", value), context=_deep_context())
                leaks = [error for error in result["errors"] if error["reason"] == "l4-evidence-leak"]
                self.assertTrue(leaks)
                self.assertIn("test-total", {error["evidence_shape"] for error in leaks})

        positive = template.replace("RESULT", "覆盖原生文本 PDF、扫描页、页码定位和代码块保留。")
        context = _deep_context()
        context["current_facts"] = [{
            "section_id": "coverage",
            "claim": "已测试原生文本 PDF、扫描页、页码定位和代码块保留；代码布局仍有限制。",
            "source": "machine-evidence:coverage",
            "observed_at": "2026-09-02",
        }]
        result = validate_human_page("experiment", positive, context=context)
        self.assertNotIn("l4-evidence-leak", _reasons(result))

    def test_duplicate_heading_process_meta_and_purposeless_link_fail(self) -> None:
        duplicate = """# 分析

## 当前结论
第一条结论。
## 当前结论
第二条结论。
"""
        self.assertIn("duplicate-heading", _reasons(validate_human_page("analysis", duplicate, context=_context())))
        meta = """# 分析

## 当前结论
本页面用于说明合同。
"""
        self.assertIn("process-meta-copy", _reasons(validate_human_page("analysis", meta, context=_context())))
        readme = """# Code Knowledge Builder

## 先选择你要完成的任务
[这里](guide.md)
## 了解本项目知识库结构
区分人类与机器入口。
## 让 Agent 安装本项目
交给 Agent 完成安装。
## 让 Agent 解释自己的项目
交给 Agent 回答问题。
## 安装后继续指挥 Agent
继续指挥 Agent 阅读与修改。
"""
        no_purpose = _context(**{
            "task-choice": _section_context(
                links=[{"target": "guide.md", "purpose": "", "kind": "internal"}]
            )
        })
        self.assertIn("link-purpose-missing", _reasons(validate_human_page("README", readme, context=no_purpose)))

    def test_unverified_current_fact_requires_exact_source_and_time(self) -> None:
        markdown = """# 反馈

## 反馈内容
请补充适用边界。
## 影响范围
影响分析页。
## 当前状态
当前状态已经处理完成。
## 后续行动
无需新增动作。
"""
        failed = validate_human_page("feedback", markdown, context=_context())
        self.assertIn("current-fact-unverified", _reasons(failed))
        context = _context()
        context["current_facts"] = [{"section_id": "status", "claim": "当前状态已经处理完成。", "source": "feedback-record", "observed_at": "2026-09-02"}]
        self.assertEqual("passed", validate_human_page("feedback", markdown, context=context)["status"])


if __name__ == "__main__":
    unittest.main()
