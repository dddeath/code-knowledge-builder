"""Versioned, deterministic contracts for every human-readable CKB page type.

The registry in this module is the single field definition consumed by later
page generators, template proposal review, Prompt maintenance, and readability
audits.  This task intentionally does not connect the contracts to the current
projection pipeline: existing pages remain unchanged until a later integration
explicitly opts in.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from .common import CkbError


HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION = 3
HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION = "3.0.0"
HUMAN_PAGE_TEMPLATE_REGISTRY_ID = "ckb-human-page-template-contracts"


@dataclass(frozen=True)
class SectionContract:
    """One complete human-section contract shared by every V3 consumer."""

    section_id: str
    heading: str
    purpose: str
    required_content: tuple[str, ...]
    allowed_content: tuple[str, ...]
    forbidden_content: tuple[str, ...]
    length_budget: "LengthBudget"
    key_entity_budget: "CountBudget"
    link_budget: "LinkBudget"
    source_requirements: tuple[str, ...]
    freshness_rule: str
    disclosure_level: str
    empty_behavior: str
    level: int = 2
    repeatable: bool = False
    heading_pattern: str | None = None


@dataclass(frozen=True)
class CountBudget:
    minimum: int
    maximum: int
    scope: str
    counting_rule: str
    overflow_action: str


@dataclass(frozen=True)
class LengthBudget:
    minimum_characters: int
    maximum_characters: int
    maximum_paragraphs: int
    maximum_list_items: int
    maximum_metrics: int
    counting_rule: str
    overflow_action: str


@dataclass(frozen=True)
class LinkBudget:
    minimum: int
    maximum: int
    target_types: tuple[str, ...]
    counting_rule: str
    overflow_action: str


@dataclass(frozen=True)
class FirstScreenContract:
    responsibility: str
    required_elements: tuple[str, ...]
    maximum_key_items: int


@dataclass(frozen=True)
class EvidenceContract:
    required_fields: tuple[str, ...]
    current_fact_rule: str
    freshness_fields: tuple[str, ...]


@dataclass(frozen=True)
class HumanPageTemplateContract:
    page_type: str
    reader_task: str
    entry_conditions: tuple[str, ...]
    first_screen: FirstScreenContract
    required_sections: tuple[SectionContract, ...]
    optional_sections: tuple[SectionContract, ...]
    forbidden_content: tuple[str, ...]
    key_entity_budget: CountBudget
    source_link_budget: CountBudget
    link_requirements: tuple[str, ...]
    evidence_requirements: EvidenceContract
    extension_points: tuple[str, ...]
    applicability_boundary: str


def _section(
    section_id: str,
    heading: str,
    purpose: str,
    disclosure_level: str,
    *,
    required_content: Sequence[str] | None = None,
    allowed_content: Sequence[str] | None = None,
    forbidden_content: Sequence[str] | None = None,
    length_budget: LengthBudget | None = None,
    key_entity_budget: CountBudget | None = None,
    link_budget: LinkBudget | None = None,
    source_requirements: Sequence[str] | None = None,
    freshness_rule: str | None = None,
    empty_behavior: str = "error",
    level: int = 2,
    repeatable: bool = False,
    heading_pattern: str | None = None,
) -> SectionContract:
    if disclosure_level not in {"L1", "L2", "L3"}:
        raise RuntimeError(f"human page section has an invalid disclosure level: {section_id}")
    defaults = {
        "L1": (360, 2, 5, 0, 3, 3),
        "L2": (600, 3, 6, 2, 3, 4),
        "L3": (800, 4, 8, 3, 4, 5),
    }[disclosure_level]
    maximum_characters, maximum_paragraphs, maximum_items, maximum_metrics, maximum_entities, maximum_links = defaults
    return SectionContract(
        section_id=section_id,
        heading=heading,
        purpose=purpose,
        required_content=tuple(required_content or (purpose,)),
        allowed_content=tuple(
            allowed_content
            or (
                "围绕本章节目的给出结论优先的简体中文说明。",
                "仅保留帮助读者完成当前任务的少量实体、指标和描述性链接。",
            )
        ),
        forbidden_content=tuple(
            forbidden_content
            or (
                "完整命令、完整测试数量、逐门清单、原始日志、完整哈希、退出状态、SQLite 或 manifest 明细。",
                "maintain 子项、回滚探针和其他 L4 机器证据正文。",
                "制作过程、调试记录、待填写占位符和已撤回方案。",
            )
        ),
        length_budget=length_budget
        or LengthBudget(
            minimum_characters=1,
            maximum_characters=maximum_characters,
            maximum_paragraphs=maximum_paragraphs,
            maximum_list_items=maximum_items,
            maximum_metrics=maximum_metrics,
            counting_rule="统计本章节 human_summary 的 Unicode 字符、非空段落、Markdown 列表项和显式登记的人类指标。",
            overflow_action="保留结论与边界，把完整证据移到 machine_evidence_refs 指向的机器记录。",
        ),
        key_entity_budget=key_entity_budget
        or CountBudget(
            minimum=0,
            maximum=maximum_entities,
            scope="section",
            counting_rule="统计本章节结构化输入中直接点名的关键实体。",
            overflow_action="合并为职责描述，或移动到深入阅读所指向的职责页和机器记录。",
        ),
        link_budget=link_budget
        or LinkBudget(
            minimum=0,
            maximum=maximum_links,
            target_types=("internal", "external", "source", "experiment", "reference", "work-record"),
            counting_rule="统计本章节 human_summary 中出现且在结构化输入登记用途的描述性链接。",
            overflow_action="只保留能直接支撑本章节结论或下一步阅读的链接。",
        ),
        source_requirements=tuple(
            source_requirements
            or (
                "时效性事实由 source_refs 或 machine_evidence_refs 绑定可复查来源。",
            )
        ),
        freshness_rule=freshness_rule
        or (
            "使用“当前”“已支持”“已测试”等表述时，必须在 current_facts 中逐行登记 source 与 observed_at；"
            "L4 字面证据只写入 machine_evidence_refs，不进入 human_summary。"
        ),
        disclosure_level=disclosure_level,
        empty_behavior=empty_behavior,
        level=level,
        repeatable=repeatable,
        heading_pattern=heading_pattern,
    )


def _optional_section(
    section_id: str,
    heading: str,
    purpose: str,
    disclosure_level: str,
    **kwargs: Any,
) -> SectionContract:
    return _section(
        section_id,
        heading,
        purpose,
        disclosure_level,
        empty_behavior="omit",
        **kwargs,
    )


def _budget(
    minimum: int,
    maximum: int,
    rule: str,
    overflow: str,
    *,
    scope: str = "page",
) -> CountBudget:
    return CountBudget(minimum, maximum, scope, rule, overflow)


def _section_entity_budget(minimum: int, maximum: int, rule: str) -> CountBudget:
    return CountBudget(minimum, maximum, "section", rule, "压缩为职责说明，或移动到深入阅读与机器记录。")


def _section_length_budget(
    maximum_characters: int,
    maximum_paragraphs: int,
    maximum_list_items: int,
    maximum_metrics: int = 0,
) -> LengthBudget:
    return LengthBudget(
        1,
        maximum_characters,
        maximum_paragraphs,
        maximum_list_items,
        maximum_metrics,
        "统计本章节 human_summary 的 Unicode 字符、非空段落、Markdown 列表项和显式登记的人类指标。",
        "保留直接结果与可复制 Prompt，把完整证据移到 machine_evidence_refs。",
    )


def _section_link_budget(
    minimum: int,
    maximum: int,
    rule: str,
    *target_types: str,
) -> LinkBudget:
    return LinkBudget(
        minimum,
        maximum,
        tuple(target_types or ("internal", "source", "experiment", "reference", "work-record")),
        rule,
        "只保留直接支撑本章节结论或后续阅读的描述性链接。",
    )


def _first(responsibility: str, elements: Sequence[str], maximum: int) -> FirstScreenContract:
    return FirstScreenContract(responsibility, tuple(elements), maximum)


def _evidence(fields: Sequence[str], current_rule: str, freshness: Sequence[str]) -> EvidenceContract:
    return EvidenceContract(tuple(fields), current_rule, tuple(freshness))


_COMMON_FORBIDDEN = (
    "制作过程元文案、待填写占位符和对 Agent 下一步动作的自我说明",
    "内部稳定 ID、完整提交哈希、机器分类字段和原始关系标签",
    "与读者任务无关的完整实现实体、门、状态字段或审计实体清单",
    "链接文字只有“这里”“详情”“更多”等而没有说明阅读目的",
)

_CURRENT_FACT_RULE = (
    "正文中含当前状态、当前边界、当前版本、目前、现行、最新、截至等时效性事实的行，"
    "必须由 validation context 提供逐行匹配的 source 与 observed_at。"
)


_CONTRACTS: tuple[HumanPageTemplateContract, ...] = (
    HumanPageTemplateContract(
        page_type="INDEX",
        reader_task="从入口页按任务选择职责、项目记录、外部资料或 Agent 精确定位。",
        entry_conditions=("每个人类投影生成一个入口页。", "只链接当前投影存在的导航目标。"),
        first_screen=_first("只说明读者可以完成哪些任务以及直接得到什么。", ("任务选择", "职责浏览", "项目记录", "Agent 定位"), 4),
        required_sections=(
            _section("task-choice", "先选择你要完成的任务", "说明入口页可以完成的任务和每条路径的直接结果。", "L1"),
            _section("responsibility-entry", "按职责浏览代码", "按职责进入少量正式内容页，不展示实体清单。", "L1"),
            _section("record-entry", "查找项目记录", "进入分析、修改、实验、问题和会话记录。", "L1"),
            _section("agent-location", "让 Agent 精确定位", "提供最小 Agent 指挥语句，把精确实体与源码定位交给机器检索。", "L1"),
        ),
        optional_sections=(
            _optional_section("reference-entry", "查找外部资料", "仅在存在已审阅资料时进入资料导览。", "L1"),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("按字母展开全部页面或实体。", "把 L4 机器证据复制到入口页。"),
        key_entity_budget=_budget(0, 4, "只统计首屏任务入口。", "移到对应正式内容页。"),
        source_link_budget=_budget(0, 0, "入口页不直接列源码范围。", "改用职责页或 Agent 定位。"),
        link_requirements=("每个入口说明读者任务和直接结果。", "查找外部资料只在已有审阅资料时出现。"),
        evidence_requirements=_evidence(("projection_manifest", "link_target_set"), _CURRENT_FACT_RULE, ("projection_built_at", "observed_at")),
        extension_points=("已审阅资料存在时显示查找外部资料。",),
        applicability_boundary="INDEX 只承担 L1 任务导航，不解释实现、历史或机器审计明细。",
    ),
    HumanPageTemplateContract(
        page_type="WIKI",
        reader_task="理解人类知识层的进入顺序、页面职责、变化追踪和 Agent 阅读方式。",
        entry_conditions=("每个人类投影生成一个阅读说明页。", "内容与当前页面类型和导航合同一致。"),
        first_screen=_first("先给开始入口和页面职责，再说明如何继续追踪。", ("开始位置", "页面职责", "变化追踪"), 4),
        required_sections=(
            _section("start", "从哪里开始", "按阅读任务选择入口。", "L1"),
            _section("page-responsibilities", "各类页面负责什么", "说明导航页与正式内容页分别产生什么结果。", "L1"),
            _section("trace-change", "如何追踪方案与实现变化", "说明从记录到职责、源码和验证概述的阅读路径。", "L1"),
            _section("agent-reading", "如何让 Agent 帮助阅读", "提供最小 Agent 指挥方式，不展开命令教程。", "L1"),
            _section("deep-reading", "深入了解", "指向职责、项目记录与资料层的描述性入口。", "L1"),
        ),
        optional_sections=(),
        forbidden_content=_COMMON_FORBIDDEN + ("完整 Schema、关系边、检索得分或 parser 字段。", "人类命令行教程。"),
        key_entity_budget=_budget(0, 5, "只统计示例中点名的任务对象。", "把实现对象移到职责页。"),
        source_link_budget=_budget(0, 0, "WIKI 不直接列源码范围。", "从职责页进入源码。"),
        link_requirements=("链接必须对应明确阅读任务。", "Agent Prompt 必须说明返回结果。"),
        evidence_requirements=_evidence(("page_type_registry", "projection_capabilities"), _CURRENT_FACT_RULE, ("configuration_built_at", "observed_at")),
        extension_points=(),
        applicability_boundary="WIKI 只解释 L1 阅读方法，不替代正式内容页或机器命令参考。",
    ),
    HumanPageTemplateContract(
        page_type="RECORDS",
        reader_task="按目的查找完整项目记录集合。",
        entry_conditions=("human 或 markdown 中存在工作记录目录。", "从完整记录集合确定性生成。"),
        first_screen=_first("先按任务选择记录类型，再提供 Agent 查找入口。", ("任务选择", "分析", "修改", "实验", "问题"), 5),
        required_sections=(
            _section("task-choice", "先选择你要查找的内容", "说明各类项目记录回答什么问题。", "L1"),
            _section("analysis", "分析与方案", "列出全部 analysis 记录及一句结论摘要。", "L1"),
            _section("change", "实现与修改", "列出全部 change 记录及一句结果摘要。", "L1"),
            _section("experiment", "实验与性能", "列出全部 experiment 记录及一句边界摘要。", "L1"),
            _section("pitfall", "问题与限制", "列出全部 pitfall 记录及一句触发条件摘要。", "L1"),
            _section("session", "会话与方案变化", "列出全部 session 记录及一句恢复用途摘要。", "L1"),
            _section("agent-find", "让 Agent 帮助查找", "提供按目的和来源查找项目记录的最小 Agent 指挥方式。", "L1"),
        ),
        optional_sections=(),
        forbidden_content=_COMMON_FORBIDDEN + ("由单个查询挑选的记录子集。", "把会话日志或机器操作记录投影为普通正文。"),
        key_entity_budget=_budget(0, 0, "RECORDS 不直接列实现实体。", "在具体记录中说明实体。"),
        source_link_budget=_budget(0, 0, "RECORDS 不直接列源码范围。", "从具体记录进入来源。"),
        link_requirements=("每条正式记录恰好出现一次。", "每条链接带一句中文用途摘要。", "空分类明确暂无。"),
        evidence_requirements=_evidence(("complete_record_set", "unique_titles", "kind_partition", "mirror_parity"), _CURRENT_FACT_RULE, ("index_refreshed_at", "observed_at")),
        extension_points=(),
        applicability_boundary="RECORDS 只承担 L1 项目记录导航，不替代记录正文或机器证据。",
    ),
    HumanPageTemplateContract(
        page_type="REFERENCES",
        reader_task="按问题和主题选择已审阅外部资料。",
        entry_conditions=("至少存在一个 active 且 agent-reviewed 的 reference。", "每个 active source 最多一个人类摘要页。"),
        first_screen=_first("先说明资料可回答的问题，再按主题选择并交给 Agent 精确查找。", ("可回答的问题", "主题入口", "Agent 查找"), 3),
        required_sections=(
            _section("answers", "这些资料能回答什么", "概括已审阅资料集合可支撑的问题边界。", "L1"),
            _section("topics", "按主题选择资料", "列出每个 active reference 及一句中文摘要。", "L1"),
            _section("agent-find", "让 Agent 帮助查找", "提供按问题查找资料和精确原文范围的最小 Agent 指挥方式。", "L1"),
        ),
        optional_sections=(),
        forbidden_content=_COMMON_FORBIDDEN + ("pending、superseded 或未审阅资料。", "把资料标题当作代码实体。"),
        key_entity_budget=_budget(0, 0, "REFERENCES 不直接列代码实体。", "把资料实体留在具体 reference。"),
        source_link_budget=_budget(0, 0, "REFERENCES 不直接列归档原文范围。", "从具体 reference 进入来源。"),
        link_requirements=("每个 active reference 恰好出现一次。", "每条链接说明资料主题和用途。"),
        evidence_requirements=_evidence(("active_reference_set", "review_status", "license_status", "mirror_parity"), _CURRENT_FACT_RULE, ("projection_built_at", "reviewed_at", "observed_at")),
        extension_points=(),
        applicability_boundary="REFERENCES 只承担 L1 资料导航，来源主张和行范围保留在 reference 页与机器层。",
    ),
    HumanPageTemplateContract(
        page_type="responsibility",
        reader_task="理解一个代码职责范围的适用场景、功能结果、关联范围与当前边界。",
        entry_conditions=("对象是 repository、module、boundary 或代码职责聚合页。", "内容来自固定源码快照与审阅说明。"),
        first_screen=_first("首屏给出职责、适用场景与功能结果。", ("职责", "场景", "结果"), 3),
        required_sections=(
            _section("responsibility", "职责说明", "说明该范围负责产生什么结果。", "L2"),
            _section("scenarios", "适用场景", "列出读者应进入或修改该范围的场景。", "L2"),
            _section("results", "功能结果", "概述当前功能与测试覆盖，不展开 L4 明细。", "L2"),
            _section("related-scope", "关联范围", "说明直接协作的职责、源码或测试入口。", "L2", key_entity_budget=_section_entity_budget(1, 5, "统计承担本职责的关键实现组。")),
            _section("boundary", "当前边界", "说明适用范围、已知限制和未覆盖内容。", "L2"),
            _section("deep-reading", "深入阅读", "保留至少一个带目的说明的源码、实验、资料、工作记录或既有 Agent 提问入口。", "L2", link_budget=_section_link_budget(1, 4, "统计可执行的深层阅读入口。", "internal", "source", "experiment", "reference", "work-record")),
        ),
        optional_sections=(),
        forbidden_content=_COMMON_FORBIDDEN + ("完整函数、方法、门和状态字段目录。", "脱离固定源码范围的推测。"),
        key_entity_budget=_budget(1, 7, "统计正文直接点名的关键实现。", "按职责分组。"),
        source_link_budget=_budget(0, 7, "统计可点击源码范围。", "保留最能解释职责的来源。"),
        link_requirements=("源码链接说明职责。", "测试、实验、资料与工作记录链接说明阅读目的。"),
        evidence_requirements=_evidence(("source_snapshot", "source_ranges", "review_status", "test_coverage_summary"), _CURRENT_FACT_RULE, ("source_commit", "reviewed_at", "observed_at")),
        extension_points=(),
        applicability_boundary="responsibility 是 L2 当前职责说明，不记录完整历史、命令或机器审计。",
    ),
    HumanPageTemplateContract(
        page_type="change",
        reader_task="确认修改内容、时间、原因、实现概述、结果与适用边界。",
        entry_conditions=("修改已经发生并有可复查实现。", "当前结果和边界已有验证概述。"),
        first_screen=_first("首屏直接说明修改内容、时间和原因。", ("内容", "时间", "原因"), 3),
        required_sections=(
            _section("what", "修改内容", "说明用户可见或系统行为现在是什么。", "L2"),
            _section("when", "修改时间", "说明该描述绑定的集成、稳定版本或时间基准。", "L2"),
            _section("why", "修改原因", "说明原问题和本次修改目的。", "L2"),
            _section("implementation", "实现概述", "按职责说明少量关键实现。", "L2", key_entity_budget=_section_entity_budget(1, 3, "统计本次变化的关键实现组。")),
            _section("features", "关联特性", "说明直接受影响的能力和兼容关系。", "L2"),
            _section("result", "当前结果", "概述已验证行为，不列完整命令、数量、门或日志。", "L2"),
            _section("boundary", "适用边界", "说明当前结果覆盖范围与限制。", "L2"),
            _section("deep-reading", "深入阅读", "保留至少一个带目的说明的源码、实验、资料、工作记录或既有 Agent 提问入口。", "L2", link_budget=_section_link_budget(1, 4, "统计可执行的深层阅读入口。", "internal", "source", "experiment", "reference", "work-record")),
        ),
        optional_sections=(),
        forbidden_content=_COMMON_FORBIDDEN + ("逐条调试日志、失败尝试和未成立方案。", "完整验证清单或回滚探针。"),
        key_entity_budget=_budget(1, 5, "统计实现概述中点名的关键实现组。", "保留三项以内主要职责。"),
        source_link_budget=_budget(0, 5, "统计描述性源码链接。", "只保留实现、接入和验证概述所需范围。"),
        link_requirements=("关联特性说明关系。", "深入阅读链接说明它用于复查什么。"),
        evidence_requirements=_evidence(("change_time", "baseline_or_version", "verification_summary", "applicability_boundary", "source_ranges"), _CURRENT_FACT_RULE, ("changed_at", "verified_at", "observed_at")),
        extension_points=(),
        applicability_boundary="change 是 L2 已成立变化说明，不承载提案、开发日志或 L4 验证记录。",
    ),
    HumanPageTemplateContract(
        page_type="analysis",
        reader_task="读取当前结论、事实基础、应用方式、未知与后续建议。",
        entry_conditions=("问题已有足够证据形成可复用判断。", "至少回链一个知识页或精确来源。"),
        first_screen=_first("先给当前结论、问题关联与事实边界。", ("结论", "问题", "事实"), 3),
        required_sections=(
            _section("conclusion", "当前结论", "直接回答分析问题并说明比较对象。", "L2"),
            _section("problem", "问题关联", "说明该结论解决什么决策或实现问题。", "L2"),
            _section("facts", "事实基础", "区分已确认事实、推断和证据来源。", "L2"),
            _section("application", "结论应用", "说明结论如何用于当前任务。", "L2"),
            _section("unknowns", "未决事项", "列出缺失证据和核验入口。", "L2"),
            _section("next", "后续建议", "给出与当前结论一致的行动。", "L2"),
            _section("deep-reading", "深入阅读", "保留至少一个带目的说明的源码、实验、资料、工作记录或既有 Agent 提问入口。", "L2", link_budget=_section_link_budget(1, 4, "统计可执行的深层阅读入口。", "internal", "source", "experiment", "reference", "work-record")),
        ),
        optional_sections=(),
        forbidden_content=_COMMON_FORBIDDEN + ("把推断或待核验内容写成已确认效果。", "混用不同版本或比较对象。"),
        key_entity_budget=_budget(0, 5, "统计支撑结论的关键实体。", "将实体明细移到职责页。"),
        source_link_budget=_budget(0, 8, "统计直接支撑事实的来源链接。", "保留能改变结论的证据。"),
        link_requirements=("每个来源链接对应事实或未决事项。", "工作记录链接说明结论关系。"),
        evidence_requirements=_evidence(("question", "comparison_object", "facts", "inferences", "unknowns"), _CURRENT_FACT_RULE, ("evidence_observed_at", "analysis_updated_at", "observed_at")),
        extension_points=(),
        applicability_boundary="analysis 是 L2 可复用判断，不替代实验原始记录、change 成品或 session 恢复记录。",
    ),
    HumanPageTemplateContract(
        page_type="pitfall",
        reader_task="识别问题现象、触发条件、影响、原因、处理结果与适用边界。",
        entry_conditions=("问题已复现或有直接证据。", "原因状态和处理边界清楚。"),
        first_screen=_first("先说明问题现象、触发条件和影响范围。", ("现象", "条件", "影响"), 3),
        required_sections=(
            _section("symptom", "问题现象", "给出可识别的问题结果。", "L2"),
            _section("trigger", "触发条件", "限定环境、输入和前置状态。", "L2"),
            _section("impact", "影响范围", "说明问题影响的功能与读者任务。", "L2"),
            _section("cause", "原因说明", "区分已确认原因和推断。", "L2"),
            _section("resolution", "处理方式", "给出经过验证的窄范围处理。", "L2"),
            _section("result", "当前结果", "概述处理前后行为，不复制复现日志。", "L2"),
            _section("boundary", "适用边界", "说明不适用环境和剩余限制。", "L2"),
            _section("deep-reading", "深入阅读", "保留至少一个带目的说明的源码、实验、工作记录或既有 Agent 提问入口。", "L2", link_budget=_section_link_budget(1, 4, "统计可执行的深层阅读入口。", "internal", "source", "experiment", "work-record")),
        ),
        optional_sections=(),
        forbidden_content=_COMMON_FORBIDDEN + ("把一次上游失败重复成多项下游失败。", "没有证据的确定性根因。"),
        key_entity_budget=_budget(0, 4, "统计解释问题链的关键实体。", "只保留直接相关实体。"),
        source_link_budget=_budget(0, 6, "统计现象、原因和结果的描述性来源链接。", "保留最短证据链。"),
        link_requirements=("链接说明支持现象、原因、处理还是结果。",),
        evidence_requirements=_evidence(("observed_failure", "trigger", "impact", "cause_status", "verified_resolution"), _CURRENT_FACT_RULE, ("reproduced_at", "verified_at", "observed_at")),
        extension_points=(),
        applicability_boundary="pitfall 是 L2 问题与处理说明，不承载原始日志或完整复现命令。",
    ),
    HumanPageTemplateContract(
        page_type="experiment",
        reader_task="理解实验问题、比较对象、功能与性能覆盖、少量关键指标和结论边界。",
        entry_conditions=("协议、输入、比较对象和测量已冻结。", "L4 复现证据保存在机器记录或外部验证工件。"),
        first_screen=_first("先给实验问题、比较对象与结果摘要。", ("问题", "比较对象", "摘要"), 3),
        required_sections=(
            _section("question", "实验问题", "说明实验要回答的具体问题。", "L3"),
            _section("comparison", "比较对象", "说明基线、处理和同协议边界。", "L3"),
            _section("coverage", "功能与性能覆盖", "概述测试了哪些功能或性能维度。", "L3"),
            _section("summary", "结果摘要", "保留少量关键指标和直接结果，不列测试总数或日志。", "L3"),
            _section("conclusion", "结论", "只解释冻结协议支持的结论。", "L3"),
            _section("boundary", "适用边界", "说明样本、压力与外推限制。", "L3"),
            _section("next", "后续工作", "说明由证据触发的下一步。", "L3"),
            _section("deep-reading", "深入阅读", "保留至少一个指向协议、实验记录、相关实现或既有 Agent 提问入口的描述性链接。", "L3", link_budget=_section_link_budget(1, 5, "统计可执行的深层阅读入口。", "internal", "source", "experiment", "reference", "work-record")),
        ),
        optional_sections=(),
        forbidden_content=_COMMON_FORBIDDEN + ("完整测试命令、总数、逐门清单、日志、哈希和退出状态。", "混合不同协议或比较对象的数字。"),
        key_entity_budget=_budget(0, 5, "统计理解实验所需的实现实体。", "把执行细节留在机器记录。"),
        source_link_budget=_budget(0, 8, "统计协议、结果和实现的描述性链接。", "优先保留可解释结论的来源。"),
        link_requirements=("结果来源说明比较对象和协议。", "L4 工件通过 machine_evidence_refs 登记而不投影正文。"),
        evidence_requirements=_evidence(("protocol", "comparison_object", "coverage", "key_metrics", "conclusion_boundary"), _CURRENT_FACT_RULE, ("protocol_frozen_at", "measured_at", "observed_at")),
        extension_points=(),
        applicability_boundary="experiment 是 L3 实验摘要，只对冻结协议与样本负责；复现明细保留在 L4。",
    ),
    HumanPageTemplateContract(
        page_type="session",
        reader_task="恢复任务目标、范围、关键决策、当前结果、成果、未决事项和后续行动。",
        entry_conditions=("任务需要跨会话恢复或结果值得保留。", "过程只保留继续工作所需内容。"),
        first_screen=_first("先说明任务目标、执行范围与关键决策。", ("目标", "范围", "决策"), 3),
        required_sections=(
            _section("goal", "任务目标", "说明本次任务要成立的行为。", "L2"),
            _section("scope", "执行范围", "记录可读、可写和明确排除项。", "L2"),
            _section("decisions", "关键决策与方案变化", "保留影响后续工作的已确认决策和方案变化，不复制对话。", "L2"),
            _section("result", "当前结果", "列出已经成立的结果与验证概述。", "L2"),
            _section("artifacts", "可用成果", "列出可直接继续使用的成果及用途。", "L2"),
            _section("unknowns", "未决事项", "只保留仍阻止完成或需要核验的内容。", "L2"),
            _section("next", "后续行动", "给出继续任务的明确入口。", "L2"),
            _section("deep-reading", "深入阅读", "保留至少一个带目的说明的源码、记录、成果或既有 Agent 提问入口。", "L2", link_budget=_section_link_budget(1, 4, "统计可执行的深层阅读入口。", "internal", "source", "experiment", "reference", "work-record")),
        ),
        optional_sections=(),
        forbidden_content=_COMMON_FORBIDDEN + ("完整对话、工具日志、思考过程或已撤回方案。", "把命令启动或文件生成当作完成。"),
        key_entity_budget=_budget(0, 5, "统计恢复任务必须知道的实体。", "将实现细节链接到 change 或职责页。"),
        source_link_budget=_budget(0, 8, "统计恢复任务所需的源码、记录和成果入口。", "只保留继续执行所需入口。"),
        link_requirements=("每个成果链接说明状态和用途。", "未决事项与后续行动说明尚缺证据。"),
        evidence_requirements=_evidence(("goal", "scope", "decisions", "completed_results", "remaining_work"), _CURRENT_FACT_RULE, ("session_started_at", "last_verified_at", "observed_at")),
        extension_points=(),
        applicability_boundary="session 是 L2 任务恢复记录，不替代 change、analysis 或原始运行日志。",
    ),
    HumanPageTemplateContract(
        page_type="reference",
        reader_task="理解资料概述、适用问题、关键结论、来源和适用边界。",
        entry_conditions=("本地原文、来源、许可和精确行范围已经审阅。", "每个 active source 最多一个摘要页。"),
        first_screen=_first("先说明资料概述、适用问题和关键结论。", ("概述", "问题", "结论"), 3),
        required_sections=(
            _section("summary", "资料概述", "给出已审阅资料的中文摘要。", "L3"),
            _section("questions", "适用问题", "说明资料可以支持哪些问题。", "L3"),
            _section("claims", "关键结论", "列出少量已审阅主张。", "L3"),
            _section("source", "来源", "说明来源、许可和归档对象。", "L3", link_budget=_section_link_budget(1, 4, "统计来源与归档原文入口。", "reference", "source")),
            _section("boundary", "适用边界", "说明资料自身限制、修订关系或冲突。", "L3"),
            _section("deep-reading", "深入阅读", "保留至少一个精确原文、相关分析或既有 Agent 提问入口。", "L3", link_budget=_section_link_budget(1, 5, "统计可执行的深层阅读入口。", "internal", "source", "experiment", "reference", "work-record")),
        ),
        optional_sections=(),
        forbidden_content=_COMMON_FORBIDDEN + ("没有原文范围支持的二手主张。", "把资料当作当前代码事实。"),
        key_entity_budget=_budget(0, 5, "统计理解资料所需的关键实体。", "其余实体留在原文索引。"),
        source_link_budget=_budget(1, 8, "统计来源和精确原文链接。", "合并重复主张。"),
        link_requirements=("来源入口标明来源、许可和归档对象。", "关键结论可由 Agent 回到精确原文范围。"),
        evidence_requirements=_evidence(("origin", "license", "archived_source", "reviewed_claim_ranges"), _CURRENT_FACT_RULE, ("source_published_at", "reviewed_at", "observed_at")),
        extension_points=(),
        applicability_boundary="reference 是 L3 已审阅资料摘要，不自动成为代码事实或当前产品状态。",
    ),
    HumanPageTemplateContract(
        page_type="learning-note",
        reader_task="回看一个学习问题、解释摘要、应用方式与关联内容。",
        entry_conditions=("解释已通过检索证据和审计。", "失败响应和 Provider 过程不进入人类笔记。"),
        first_screen=_first("先说明学习问题和解释摘要。", ("问题", "解释"), 2),
        required_sections=(
            _section("question", "学习问题", "保留读者实际提出的问题。", "L2"),
            _section("summary", "解释摘要", "保存通过审计的最终解释摘要。", "L2"),
            _section("application", "应用方式", "说明读者如何把解释用于代码阅读或任务。", "L2"),
            _section("related", "关联内容", "保留少量带目的说明的来源页面或记录链接。", "L2"),
        ),
        optional_sections=(
            _optional_section("next", "后续问题", "仅在读者明确保留下一问题时出现。", "L2"),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("Provider 原始思考、生成过程或失败响应。", "缺少来源与审计证据的解释。"),
        key_entity_budget=_budget(0, 3, "统计解释所需关键实体。", "把扩展实体链接到职责页。"),
        source_link_budget=_budget(0, 3, "统计来源页面和关联记录入口。", "只保留直接相关来源。"),
        link_requirements=("关联内容链接说明学习用途。",),
        evidence_requirements=_evidence(("question", "source_page", "retrieval_pack", "audit_status", "explanation"), _CURRENT_FACT_RULE, ("entry_created_at", "evidence_created_at", "observed_at")),
        extension_points=("存在明确下一问题时显示后续问题。",),
        applicability_boundary="learning-note 是 L2 学习摘要，不替代 analysis、reference 或完整源码职责页。",
    ),
    HumanPageTemplateContract(
        page_type="feedback",
        reader_task="查看反馈内容、影响范围、状态相关处理结论与后续行动。",
        entry_conditions=("反馈定位到具体人类页面范围。", "反馈历史保留且不删除。"),
        first_screen=_first("先说明反馈内容、影响范围和当前状态。", ("内容", "影响", "状态"), 3),
        required_sections=(
            _section("comment", "反馈内容", "保存人类提交的中文意见。", "L2"),
            _section("impact", "影响范围", "说明反馈影响的页面、章节或读者任务。", "L2"),
            _section("status", "当前状态", "说明反馈处于待处理、暂缓或已处理状态。", "L2"),
            _section("next", "后续行动", "说明下一步处理或明确暂无动作。", "L2"),
        ),
        optional_sections=(
            _optional_section("resolution", "处理结论", "resolved 状态说明决议、理由和落实记录。", "L2"),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("删除历史反馈或覆盖原始意见。", "采纳或部分采纳但没有落实记录。"),
        key_entity_budget=_budget(0, 1, "只统计反馈直接指向的页面或实体。", "多目标意见拆分反馈。"),
        source_link_budget=_budget(0, 1, "统计唯一目标页面入口。", "保持一个反馈一个范围。"),
        link_requirements=("目标链接带定位范围和用途。", "处理结论链接说明如何落实。"),
        evidence_requirements=_evidence(("target", "target_lines", "anchor_text", "status", "severity", "source"), _CURRENT_FACT_RULE, ("created_at", "resolved_at", "observed_at")),
        extension_points=("resolved 状态显示处理结论。",),
        applicability_boundary="feedback 是 L2 单一页面范围的反馈记录，不作为源码事实或 change 成果。",
    ),
    HumanPageTemplateContract(
        page_type="README",
        reader_task="了解知识库结构，让 Agent 安装项目、解释自己的项目，并在安装后继续指挥 Agent。",
        entry_conditions=("发布包或项目根需要人类任务入口。", "版本与目录事实来自发布清单或当前验证。"),
        first_screen=_first("首屏只用三行任务表说明了解结构、安装本项目和解释自己的项目。", ("了解结构", "安装本项目", "解释自己的项目"), 3),
        required_sections=(
            _section("task-choice", "先选择你要完成的任务", "用任务表说明读者可以直接得到什么。", "L1"),
            _section("structure", "了解本项目知识库结构", "任务卡必须分别说明“你会直接得到”和“复制给 Agent”，Prompt 只解释人类入口、机器入口和直接结果。", "L1", length_budget=_section_length_budget(1000, 8, 8)),
            _section("install", "让 Agent 安装本项目", "任务卡必须分别说明“你会直接得到”和“复制给 Agent”，Prompt 只负责安装和验收。", "L1", length_budget=_section_length_budget(1000, 8, 8)),
            _section("explain", "让 Agent 解释自己的项目", "任务卡必须分别说明“你会直接得到”和“复制给 Agent”，Prompt 负责接管或建库后回答问题。", "L1", length_budget=_section_length_budget(1000, 8, 8)),
            _section("continue", "安装后继续指挥 Agent", "任务卡必须分别说明“你会直接得到”和“复制给 Agent”，Prompt 负责阅读、定位、修改或核验一个任务。", "L1", length_budget=_section_length_budget(1000, 8, 8)),
        ),
        optional_sections=(
            _optional_section("experiments", "实验功能", "仅在发布包明确标注实验能力时说明其直接结果与边界。", "L1"),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("人类命令行安装教程。", "把安装与解释业务仓库混成一个 Prompt。", "发布门、完整哈希、测试总数和回滚探针。"),
        key_entity_budget=_budget(0, 3, "只统计首屏三项任务。", "将安装后的继续指挥放入后续章节。"),
        source_link_budget=_budget(0, 0, "README 不直接列源码范围。", "改用知识库职责页或 Agent 定位。"),
        link_requirements=("每个任务说明直接结果。", "Prompt 中路径或分支说明用途。", "外部来源使用描述性链接。"),
        evidence_requirements=_evidence(("release_version", "publication_manifest", "directory_contract", "installation_probe"), _CURRENT_FACT_RULE, ("release_built_at", "verified_at", "observed_at")),
        extension_points=("发布包明确包含实验能力时显示实验功能。",),
        applicability_boundary="README 是 L1 人类任务入口，只说明如何指挥 Agent 和人类直接得到什么。",
    ),
)

_CONTRACT_BY_CASEFOLD = {contract.page_type.casefold(): contract for contract in _CONTRACTS}
_PAGE_TYPE_ORDER = tuple(contract.page_type for contract in _CONTRACTS)


def _check_registry() -> None:
    if len(_CONTRACTS) != len(_CONTRACT_BY_CASEFOLD):
        raise RuntimeError("human page template registry contains duplicate page types")
    for contract in _CONTRACTS:
        required_ids = [section.section_id for section in contract.required_sections]
        optional_ids = [section.section_id for section in contract.optional_sections]
        if len(required_ids) != len(set(required_ids)) or len(optional_ids) != len(set(optional_ids)):
            raise RuntimeError(f"human page template contains duplicate section ids: {contract.page_type}")
        if set(required_ids) & set(optional_ids):
            raise RuntimeError(f"human page template section is both required and optional: {contract.page_type}")
        for section in contract.required_sections + contract.optional_sections:
            if not all(
                (
                    section.required_content,
                    section.allowed_content,
                    section.forbidden_content,
                    section.source_requirements,
                    section.freshness_rule,
                )
            ):
                raise RuntimeError(f"human page template contains an incomplete section contract: {contract.page_type}.{section.section_id}")
            if section.disclosure_level not in {"L1", "L2", "L3"}:
                raise RuntimeError(f"human page template contains an invalid disclosure level: {contract.page_type}.{section.section_id}")
            if section.empty_behavior not in {"error", "omit", "explicit-empty"}:
                raise RuntimeError(f"human page template contains an invalid empty behavior: {contract.page_type}.{section.section_id}")
            length = section.length_budget
            if (
                length.minimum_characters < 0
                or length.maximum_characters < length.minimum_characters
                or min(length.maximum_paragraphs, length.maximum_list_items, length.maximum_metrics) < 0
            ):
                raise RuntimeError(f"human page template contains an invalid section length budget: {contract.page_type}.{section.section_id}")
            if section.key_entity_budget.scope != "section":
                raise RuntimeError(f"human page section key entity budget must use section scope: {contract.page_type}.{section.section_id}")
            if (
                section.key_entity_budget.minimum < 0
                or section.key_entity_budget.maximum < section.key_entity_budget.minimum
                or section.link_budget.minimum < 0
                or section.link_budget.maximum < section.link_budget.minimum
                or not section.link_budget.target_types
            ):
                raise RuntimeError(f"human page template contains an invalid section count budget: {contract.page_type}.{section.section_id}")
        for value in (contract.key_entity_budget, contract.source_link_budget):
            if value.minimum < 0 or value.maximum < value.minimum:
                raise RuntimeError(f"human page template contains an invalid budget: {contract.page_type}")
            if value.scope not in {"page", "entry"}:
                raise RuntimeError(f"human page template contains an invalid budget scope: {contract.page_type}")


_check_registry()


def list_human_page_types() -> tuple[str, ...]:
    """Return the registry order as an immutable tuple."""

    return _PAGE_TYPE_ORDER


def _compatible_version(contract_version: str, schema_version: int) -> bool:
    return (
        schema_version == HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION
        and contract_version == HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION
    )


def get_human_page_template(
    page_type: str,
    *,
    contract_version: str = HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    schema_version: int = HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
) -> HumanPageTemplateContract:
    """Read one immutable contract or fail with a stable Chinese diagnostic."""

    if not _compatible_version(contract_version, schema_version):
        raise CkbError(
            "人类页面模板合同版本不兼容："
            f"schema_version={schema_version}, contract_version={contract_version}; "
            f"当前要求 schema_version={HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION}, "
            f"contract_version={HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION}；"
            "旧 1.0.0 页面必须显式按 V3 章节重写，不静默迁移。"
        )
    contract = _CONTRACT_BY_CASEFOLD.get(str(page_type).strip().casefold())
    if contract is None:
        raise CkbError(f"未知人类页面类型：{page_type}；可用类型：{list(_PAGE_TYPE_ORDER)}")
    return contract


def human_page_section_document(section: SectionContract) -> dict[str, Any]:
    return {
        "allowed_content": list(section.allowed_content),
        "disclosure_level": section.disclosure_level,
        "empty_behavior": section.empty_behavior,
        "forbidden_content": list(section.forbidden_content),
        "freshness_rule": section.freshness_rule,
        "heading": section.heading,
        "heading_pattern": section.heading_pattern,
        "key_entity_budget": _budget_document(section.key_entity_budget),
        "level": section.level,
        "length_budget": {
            "counting_rule": section.length_budget.counting_rule,
            "maximum_characters": section.length_budget.maximum_characters,
            "maximum_list_items": section.length_budget.maximum_list_items,
            "maximum_metrics": section.length_budget.maximum_metrics,
            "maximum_paragraphs": section.length_budget.maximum_paragraphs,
            "minimum_characters": section.length_budget.minimum_characters,
            "overflow_action": section.length_budget.overflow_action,
        },
        "link_budget": {
            "counting_rule": section.link_budget.counting_rule,
            "maximum": section.link_budget.maximum,
            "minimum": section.link_budget.minimum,
            "overflow_action": section.link_budget.overflow_action,
            "target_types": list(section.link_budget.target_types),
        },
        "purpose": section.purpose,
        "repeatable": section.repeatable,
        "required_content": list(section.required_content),
        "section_id": section.section_id,
        "source_requirements": list(section.source_requirements),
    }


def _budget_document(budget: CountBudget) -> dict[str, Any]:
    return {
        "counting_rule": budget.counting_rule,
        "maximum": budget.maximum,
        "minimum": budget.minimum,
        "overflow_action": budget.overflow_action,
        "scope": budget.scope,
    }


def human_page_template_document(contract: HumanPageTemplateContract) -> dict[str, Any]:
    """Return a detached JSON-compatible representation of one contract."""

    return {
        "applicability_boundary": contract.applicability_boundary,
        "entry_conditions": list(contract.entry_conditions),
        "evidence_requirements": {
            "current_fact_rule": contract.evidence_requirements.current_fact_rule,
            "freshness_fields": list(contract.evidence_requirements.freshness_fields),
            "required_fields": list(contract.evidence_requirements.required_fields),
        },
        "extension_points": list(contract.extension_points),
        "first_screen": {
            "maximum_key_items": contract.first_screen.maximum_key_items,
            "required_elements": list(contract.first_screen.required_elements),
            "responsibility": contract.first_screen.responsibility,
        },
        "forbidden_content": list(contract.forbidden_content),
        "key_entity_budget": _budget_document(contract.key_entity_budget),
        "link_requirements": list(contract.link_requirements),
        "optional_sections": [human_page_section_document(section) for section in contract.optional_sections],
        "page_type": contract.page_type,
        "reader_task": contract.reader_task,
        "required_sections": [human_page_section_document(section) for section in contract.required_sections],
        "source_link_budget": _budget_document(contract.source_link_budget),
    }


def human_page_template_registry_document(
    *,
    contract_version: str = HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    schema_version: int = HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
) -> dict[str, Any]:
    if not _compatible_version(contract_version, schema_version):
        get_human_page_template(
            "INDEX", contract_version=contract_version, schema_version=schema_version
        )
    return {
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "page_type_order": list(_PAGE_TYPE_ORDER),
        "page_types": [human_page_template_document(contract) for contract in _CONTRACTS],
        "registry_id": HUMAN_PAGE_TEMPLATE_REGISTRY_ID,
        "schema_version": HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
        "status": "ready",
    }


def serialize_human_page_template_registry(
    *,
    contract_version: str = HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    schema_version: int = HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
) -> str:
    """Serialize with stable key ordering, page ordering, whitespace, and newline."""

    document = human_page_template_registry_document(
        contract_version=contract_version, schema_version=schema_version
    )
    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def human_page_template_registry_sha256() -> str:
    return hashlib.sha256(serialize_human_page_template_registry().encode("utf-8")).hexdigest()


_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_CURRENT_FACT_RE = re.compile(
    r"(?:当前(?:状态|边界|版本|发布|知识库|实现|行为|结果|配置|默认|要求)|目前|现行|最新|截至|现在(?:是|为)|现已|已支持|已测试|验证通过)"
)
_OBSERVED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ][0-9:.+-]+Z?)?$")
_INLINE_LINK_RE = re.compile(r"(?<!!)\[([^\]\n]+)\]\(([^)\n]+)\)")
_WIKILINK_RE = re.compile(r"\[\[([^\]|#\n]+)(?:[|#]([^\]\n]+))?\]\]")
_AMBIGUOUS_LINK_LABELS = {"这里", "详情", "更多", "链接", "点击", "查看", "继续"}
_META_PATTERNS = (
    re.compile(r"(?:本页|本页面|本文档)用于"),
    re.compile(r"(?:我|我们)(?:将|会)(?:先|在|继续|接下来)?"),
    re.compile(r"这里(?:将|会)(?:介绍|说明|展示|生成|列出)"),
    re.compile(r"(?:TODO|TBD|PLACEHOLDER|待填写|待补充正文)", re.IGNORECASE),
)
_LINK_KINDS = {"internal", "external", "source", "experiment", "reference", "work-record"}
_SOURCE_REF_KINDS = {"source", "experiment", "reference", "work-record", "projection", "release", "review"}
_MACHINE_EVIDENCE_KINDS = {
    "command",
    "test-total",
    "gate-list",
    "log",
    "hash",
    "exit-status",
    "sqlite",
    "manifest",
    "maintain",
    "rollback-probe",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SECTION_CONTEXT_FIELDS = {"key_entities", "links", "metrics", "source_refs", "machine_evidence_refs"}
_L4_EVIDENCE_SHAPES = (
    (
        "complete-command",
        re.compile(
            r"(?im)^\s*(?:&\s+['\"]?[A-Z]:\\|(?:python(?:\.exe)?|powershell(?:\.exe)?|git|ckb\.py)\s+[^\n]*(?:ckb\.py|--out|--repo|--staging|--discover))"
        ),
    ),
    (
        "test-total",
        re.compile(
            r"(?i)(?:"
            r"\b\d+\s*/\s*\d+\b|"
            r"\bRan\s+\d+\s+tests?\b|"
            r"\b\d+\s+tests?\b|"
            r"(?:共|总计|合计)\s*\d+\s*(?:项|个)?\s*测试|"
            r"通过\s*\d+\s*项测试|"
            r"测试\s*(?:总数|总计)\s*[:：=]?\s*\d+"
            r")"
        ),
    ),
    ("gate-list", re.compile(r"(?im)^\s*[-*+]\s*[^\n]*(?:gate|门)[^\n]*(?:passed|通过)")),
    ("raw-log", re.compile(r"(?im)^\s*(?:stdout|stderr|exit(?:_status)?|returncode)\s*[:=]")),
    ("full-hash", re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{40}(?:[0-9a-f]{24})?(?![0-9a-f])")),
    ("sqlite-state", re.compile(r"(?i)(?:PRAGMA\s+(?:integrity_check|quick_check)|(?:SQLite|agent-index\.sqlite|knowledge\.sqlite)[^\n]*(?:\bok\b|passed|通过))")),
    ("manifest-detail", re.compile(r"(?im)(?:publication-manifest\.json\s*[:=]|^\s*\"(?:path|sha256)\"\s*:)")),
    ("maintain-detail", re.compile(r"(?im)(?:^\s*maintain\s+--|\bmaintain\s*[:=][^\n]*(?:passed|failed|通过|失败|exit))")),
    ("rollback-probe", re.compile(r"(?i)(?:rollback|回滚)[^\n]*(?:probe|探针)[^\n]*(?:exit|passed|命令|输出|通过)")),
)


def _visible_lines(markdown: str) -> list[tuple[int, str]]:
    visible: list[tuple[int, str]] = []
    fence: str | None = None
    for line_number, raw in enumerate(markdown.splitlines(), start=1):
        stripped = raw.lstrip()
        marker = stripped[:3]
        if marker in {"```", "~~~"}:
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            continue
        if fence is None:
            visible.append((line_number, raw))
    return visible


def _headings(markdown: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line_number, line in _visible_lines(markdown):
        match = _HEADING_RE.match(line.strip())
        if match:
            result.append({"level": len(match.group(1)), "text": match.group(2).strip(), "line": line_number})
    return result


def _section_bodies(markdown: str, headings: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    lines = markdown.splitlines()
    result: list[dict[str, Any]] = []
    for index, heading in enumerate(headings):
        start = int(heading["line"])
        end = len(lines)
        for following in headings[index + 1 :]:
            if int(following["level"]) <= int(heading["level"]):
                end = int(following["line"]) - 1
                break
        result.append({**heading, "body": "\n".join(lines[start:end]).strip()})
    return result


def _matches_section(heading: Mapping[str, Any], section: SectionContract) -> bool:
    if int(heading["level"]) != section.level:
        return False
    value = str(heading["text"])
    if section.heading_pattern:
        return re.fullmatch(section.heading_pattern, value) is not None
    return value == section.heading


def _effective_budget(
    budget: CountBudget,
    contract: HumanPageTemplateContract,
    headings: Sequence[Mapping[str, Any]],
) -> tuple[int, int, int]:
    units = 1
    if budget.scope == "entry":
        entry = next((section for section in contract.required_sections if section.section_id == "entry"), None)
        if entry is None:
            raise RuntimeError(f"entry-scoped budget has no entry section: {contract.page_type}")
        units = max(1, sum(1 for heading in headings if _matches_section(heading, entry)))
    return budget.minimum * units, budget.maximum * units, units


def _normalize_fact_line(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^(?:>|[-*+]\s+|\d+[.)]\s+)+", "", value).strip()
    return value


def _validation_error(reason: str, message: str, **fields: Any) -> dict[str, Any]:
    return {"reason": reason, "message": message, **fields}


def _context_sequence(context: Mapping[str, Any], name: str, errors: list[dict[str, Any]]) -> list[Any]:
    value = context.get(name, [])
    if not isinstance(value, list):
        errors.append(_validation_error("validation-context-invalid", f"validation context 的 {name} 必须是数组。", field=name))
        return []
    return value


def _link_occurrences(markdown: str) -> list[dict[str, Any]]:
    text = "\n".join(line for _line_number, line in _visible_lines(markdown))
    links: list[dict[str, Any]] = []
    for match in _INLINE_LINK_RE.finditer(text):
        links.append({"label": match.group(1).strip(), "target": match.group(2).strip()})
    for match in _WIKILINK_RE.finditer(text):
        target = match.group(1).strip()
        alias = (match.group(2) or "").strip()
        links.append({"label": alias or target, "target": target})
    return links


def _paragraph_count(body: str) -> int:
    return len([value for value in re.split(r"\n\s*\n", body.strip()) if value.strip()]) if body.strip() else 0


def _list_item_count(body: str) -> int:
    return sum(1 for line in body.splitlines() if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", line))


def _normalized_text_list(value: Any, field: str, errors: list[dict[str, Any]]) -> list[str]:
    if not isinstance(value, list):
        errors.append(_validation_error("validation-context-invalid", f"{field} 必须是数组。", field=field))
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(_validation_error("validation-context-invalid", f"{field} 只能包含非空字符串。", field=f"{field}[{index}]"))
            continue
        result.append(item.strip())
    return result


def _normalized_ref_list(
    value: Any,
    field: str,
    allowed_kinds: set[str],
    errors: list[dict[str, Any]],
    *,
    allow_sha256: bool = False,
) -> list[dict[str, str]]:
    if not isinstance(value, list):
        errors.append(_validation_error("validation-context-invalid", f"{field} 必须是数组。", field=field))
        return []
    result: list[dict[str, str]] = []
    by_target: dict[str, dict[str, str]] = {}
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            errors.append(_validation_error("validation-context-invalid", f"{field} 条目必须是对象。", field=f"{field}[{index}]"))
            continue
        allowed_fields = {"target", "purpose", "kind"} | ({"sha256"} if allow_sha256 else set())
        unknown = sorted(set(item) - allowed_fields)
        target = str(item.get("target") or "").strip()
        purpose = str(item.get("purpose") or "").strip()
        kind = str(item.get("kind") or "").strip()
        digest = str(item.get("sha256") or "").strip().casefold()
        if unknown or not target or kind not in allowed_kinds or (digest and not _SHA256_RE.fullmatch(digest)):
            errors.append(
                _validation_error(
                    "validation-context-invalid",
                    f"{field} 条目需要 target、purpose 和允许的 kind。",
                    field=f"{field}[{index}]",
                    allowed_kinds=sorted(allowed_kinds),
                    unknown_fields=unknown,
                )
            )
            continue
        if not purpose:
            errors.append(
                _validation_error(
                    "link-purpose-missing" if field.endswith(".links") else "reference-purpose-missing",
                    f"{field} 条目必须说明用途。",
                    field=f"{field}[{index}]",
                    target=target,
                )
            )
            continue
        normalized = {"target": target, "purpose": purpose, "kind": kind}
        if digest:
            normalized["sha256"] = digest
        previous = by_target.get(target)
        if previous is not None:
            conflict = previous != normalized
            errors.append(
                _validation_error(
                    "link-target-conflict" if conflict else "link-target-duplicate",
                    "同一章节内的结构化引用 target 重复或冲突。",
                    field=f"{field}[{index}]",
                    target=target,
                    previous=previous,
                    current=normalized,
                )
            )
            continue
        by_target[target] = normalized
        result.append(normalized)
    return result


def validate_human_page(
    page_type: str,
    markdown: str,
    *,
    context: Mapping[str, Any] | None = None,
    contract_version: str = HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    schema_version: int = HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Validate one V3 page and its section-scoped authoring metadata.

    ``context.sections`` keeps per-section key entities, human metrics,
    descriptive links, source refs, and L4-only ``machine_evidence_refs``.
    Only a section's ``human_summary`` is rendered into Markdown.  Current or
    tested claims remain line-bound through ``context.current_facts``.
    """

    errors: list[dict[str, Any]] = []
    canonical_page_type = str(page_type).strip()
    if not _compatible_version(contract_version, schema_version):
        errors.append(
            _validation_error(
                "contract-version-incompatible",
                "人类页面模板合同版本不兼容；旧 1.0.0 输入必须显式迁移到 V3，不能套用 V3 标题。",
                actual={"schema_version": schema_version, "contract_version": contract_version},
                expected={
                    "schema_version": HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
                    "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
                },
                migration={"from": "1.0.0", "to": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION, "mode": "explicit-rewrite"},
            )
        )
        return {
            "contract_version": contract_version,
            "errors": errors,
            "page_type": canonical_page_type,
            "schema_version": schema_version,
            "status": "failed",
        }
    contract = _CONTRACT_BY_CASEFOLD.get(canonical_page_type.casefold())
    if contract is None:
        errors.append(_validation_error("unknown-page-type", f"未知人类页面类型：{page_type}。", available=list(_PAGE_TYPE_ORDER)))
        return {
            "contract_version": contract_version,
            "errors": errors,
            "page_type": canonical_page_type,
            "schema_version": schema_version,
            "status": "failed",
        }
    canonical_page_type = contract.page_type
    if not isinstance(markdown, str) or not markdown.strip():
        errors.append(_validation_error("page-empty", "人类页面正文不能为空。"))
        return {
            "contract_version": contract_version,
            "errors": errors,
            "page_type": canonical_page_type,
            "schema_version": schema_version,
            "status": "failed",
        }
    if not isinstance(context, Mapping) and context is not None:
        errors.append(_validation_error("validation-context-invalid", "validation context 必须是 JSON 对象。"))
        context = {}
    context = context or {}
    unknown_context = sorted(set(context) - {"sections", "current_facts"})
    if unknown_context:
        errors.append(_validation_error("validation-context-invalid", "validation context 包含未知字段。", fields=unknown_context))

    section_contexts_value = context.get("sections", {})
    if not isinstance(section_contexts_value, Mapping):
        errors.append(_validation_error("validation-context-invalid", "validation context 的 sections 必须是对象。", field="sections"))
        section_contexts_value = {}
    all_contract_sections = contract.required_sections + contract.optional_sections
    section_by_id = {section.section_id: section for section in all_contract_sections}
    unknown_section_contexts = sorted(set(section_contexts_value) - set(section_by_id))
    if unknown_section_contexts:
        errors.append(
            _validation_error(
                "validation-context-invalid",
                "validation context 包含当前页面类型未定义的章节。",
                fields=[f"sections.{value}" for value in unknown_section_contexts],
            )
        )

    headings = _headings(markdown)
    parsed_sections = _section_bodies(markdown, headings)
    h1 = [heading for heading in headings if heading["level"] == 1]
    if len(h1) != 1:
        errors.append(_validation_error("title-heading-count", "人类页面必须且只能包含一个一级标题。", count=len(h1), lines=[heading["line"] for heading in h1]))

    by_heading: dict[tuple[int, str], list[int]] = {}
    for heading in headings:
        by_heading.setdefault((int(heading["level"]), str(heading["text"])), []).append(int(heading["line"]))
    for (level, value), lines in sorted(by_heading.items()):
        if len(lines) < 2:
            continue
        matching_contracts = [
            section
            for section in all_contract_sections
            if level == section.level
            and ((section.heading_pattern and re.fullmatch(section.heading_pattern, value)) or (not section.heading_pattern and value == section.heading))
        ]
        if not matching_contracts:
            continue
        repeatable = any(
            section.repeatable
            and level == section.level
            and ((section.heading_pattern and re.fullmatch(section.heading_pattern, value)) or (not section.heading_pattern and value == section.heading))
            for section in all_contract_sections
        )
        if not repeatable:
            errors.append(_validation_error("duplicate-heading", f"人类页面包含重复标题：{value}。", heading=value, level=level, lines=lines))

    visible_text = "\n".join(line for _line_number, line in _visible_lines(markdown))
    for pattern in _META_PATTERNS:
        match = pattern.search(visible_text)
        if match:
            errors.append(
                _validation_error(
                    "process-meta-copy",
                    "人类页面包含制作过程元文案或占位符。",
                    text=match.group(0),
                    visible_line=visible_text[: match.start()].count("\n") + 1,
                )
            )

    page_entities: set[str] = set()
    source_link_count = 0
    section_metrics: dict[str, dict[str, int]] = {}
    for section in all_contract_sections:
        matches = [value for value in parsed_sections if _matches_section(value, section)]
        if section in contract.required_sections and not matches:
            errors.append(
                _validation_error(
                    "required-section-missing",
                    f"{contract.page_type} 页面缺少必填章节：{section.heading}。",
                    section_id=section.section_id,
                    heading=section.heading,
                    level=section.level,
                )
            )
            continue
        if not matches:
            continue
        section_context = section_contexts_value.get(section.section_id, {})
        if not isinstance(section_context, Mapping):
            errors.append(_validation_error("validation-context-invalid", "章节 context 必须是对象。", field=f"sections.{section.section_id}"))
            section_context = {}
        unknown_fields = sorted(set(section_context) - _SECTION_CONTEXT_FIELDS)
        if unknown_fields:
            errors.append(
                _validation_error(
                    "validation-context-invalid",
                    "章节 context 包含未知字段。",
                    fields=[f"sections.{section.section_id}.{value}" for value in unknown_fields],
                )
            )
        entities = _normalized_text_list(section_context.get("key_entities", []), f"sections.{section.section_id}.key_entities", errors)
        metrics = _normalized_text_list(section_context.get("metrics", []), f"sections.{section.section_id}.metrics", errors)
        links = _normalized_ref_list(section_context.get("links", []), f"sections.{section.section_id}.links", _LINK_KINDS, errors)
        _normalized_ref_list(
            section_context.get("source_refs", []),
            f"sections.{section.section_id}.source_refs",
            _SOURCE_REF_KINDS,
            errors,
            allow_sha256=True,
        )
        machine_refs = _normalized_ref_list(
            section_context.get("machine_evidence_refs", []),
            f"sections.{section.section_id}.machine_evidence_refs",
            _MACHINE_EVIDENCE_KINDS,
            errors,
            allow_sha256=True,
        )
        page_entities.update(entities)
        entity_count = len(set(entities))
        if not section.key_entity_budget.minimum <= entity_count <= section.key_entity_budget.maximum:
            errors.append(
                _validation_error(
                    "section-key-entity-budget",
                    f"章节 {section.heading} 的关键实体数量为 {entity_count}，合同要求 {section.key_entity_budget.minimum}..{section.key_entity_budget.maximum}。",
                    section_id=section.section_id,
                    actual=entity_count,
                    minimum=section.key_entity_budget.minimum,
                    maximum=section.key_entity_budget.maximum,
                )
            )
        bodies = [str(value.get("body") or "").strip() for value in matches]
        body = "\n\n".join(value for value in bodies if value)
        if not body:
            reason = "section-empty" if section.empty_behavior == "error" else "empty-section-must-be-omitted"
            errors.append(_validation_error(reason, f"章节 {section.heading} 为空；empty_behavior={section.empty_behavior}。", section_id=section.section_id))
            continue
        length = section.length_budget
        characters = len(body)
        paragraphs = _paragraph_count(body)
        list_items = _list_item_count(body)
        metric_count = len(set(metrics))
        missing_metrics = [value for value in metrics if value not in body]
        if missing_metrics:
            errors.append(
                _validation_error(
                    "validation-context-invalid",
                    "章节登记的人类指标必须出现在 human_summary 中。",
                    section_id=section.section_id,
                    metrics=missing_metrics,
                )
            )
        if (
            characters < length.minimum_characters
            or characters > length.maximum_characters
            or paragraphs > length.maximum_paragraphs
            or list_items > length.maximum_list_items
            or metric_count > length.maximum_metrics
        ):
            errors.append(
                _validation_error(
                    "section-length-budget",
                    f"章节 {section.heading} 超出长度或数量预算。",
                    section_id=section.section_id,
                    actual={"characters": characters, "paragraphs": paragraphs, "list_items": list_items, "metrics": metric_count},
                    maximum={
                        "characters": length.maximum_characters,
                        "paragraphs": length.maximum_paragraphs,
                        "list_items": length.maximum_list_items,
                        "metrics": length.maximum_metrics,
                    },
                )
            )
        occurrences = _link_occurrences(body)
        if not section.link_budget.minimum <= len(occurrences) <= section.link_budget.maximum:
            errors.append(
                _validation_error(
                    "section-link-budget",
                    f"章节 {section.heading} 的链接数量为 {len(occurrences)}，合同要求 {section.link_budget.minimum}..{section.link_budget.maximum}。",
                    section_id=section.section_id,
                    actual=len(occurrences),
                    minimum=section.link_budget.minimum,
                    maximum=section.link_budget.maximum,
                )
            )
        section_declared = {item["target"]: item for item in links}
        occurrence_targets: set[str] = set()
        for link in occurrences:
            target = str(link["target"])
            occurrence_targets.add(target)
            label = re.sub(r"[`*_]", "", str(link["label"])).strip()
            item = section_declared.get(target)
            if item is None:
                errors.append(
                    _validation_error(
                        "link-context-missing",
                        "每个可见 Markdown 链接都必须在所属章节的 links 中登记 target、kind 和 purpose。",
                        section_id=section.section_id,
                        target=target,
                        label=label,
                    )
                )
                continue
            kind = item["kind"]
            purpose = item["purpose"]
            if kind not in section.link_budget.target_types:
                errors.append(
                    _validation_error(
                        "section-link-target-type",
                        f"章节 {section.heading} 不允许 {kind} 类型链接。",
                        section_id=section.section_id,
                        target=target,
                        kind=kind,
                        allowed=list(section.link_budget.target_types),
                    )
                )
            if label in _AMBIGUOUS_LINK_LABELS and not purpose:
                errors.append(_validation_error("link-purpose-missing", f"链接文字“{label}”没有说明阅读目的。", label=label, target=target, section_id=section.section_id))
            if kind == "source":
                source_link_count += 1
        for target in sorted(set(section_declared) - occurrence_targets):
            errors.append(
                _validation_error(
                    "link-context-unused",
                    "章节 links 中登记的 target 必须在 human_summary 中实际出现。",
                    section_id=section.section_id,
                    target=target,
                )
            )
        for item in machine_refs:
            if item["target"] in body:
                errors.append(
                    _validation_error(
                        "l4-machine-evidence-rendered",
                        "machine_evidence_refs 的 L4 目标不得出现在 human_summary。",
                        section_id=section.section_id,
                        evidence_kind=item["kind"],
                        target=item["target"],
                    )
                )
        for evidence_shape, pattern in _L4_EVIDENCE_SHAPES:
            match = pattern.search(body)
            if match:
                errors.append(
                    _validation_error(
                        "l4-evidence-leak",
                        "L1-L3 人类章节包含应留在机器层或外部验证工件的 L4 证据形态。",
                        section_id=section.section_id,
                        disclosure_level=section.disclosure_level,
                        evidence_shape=evidence_shape,
                        text=match.group(0)[:160],
                    )
                )
        section_metrics[section.section_id] = {
            "characters": characters,
            "paragraphs": paragraphs,
            "list_items": list_items,
            "metrics": metric_count,
            "key_entities": entity_count,
            "links": len(occurrences),
            "machine_evidence_refs": len(machine_refs),
        }

    entity_count = len(page_entities)
    entity_budget = contract.key_entity_budget
    entity_minimum, entity_maximum, entity_units = _effective_budget(entity_budget, contract, headings)
    if entity_count < entity_minimum or entity_count > entity_maximum:
        errors.append(
            _validation_error(
                "key-entity-budget",
                f"{contract.page_type} 页面的关键实体数量为 {entity_count}，合同要求 {entity_minimum}..{entity_maximum}。",
                actual=entity_count,
                minimum=entity_minimum,
                maximum=entity_maximum,
                scope=entity_budget.scope,
                scope_units=entity_units,
                overflow_action=entity_budget.overflow_action,
            )
        )
    source_budget = contract.source_link_budget
    source_minimum, source_maximum, source_units = _effective_budget(source_budget, contract, headings)
    if source_link_count < source_minimum or source_link_count > source_maximum:
        errors.append(
            _validation_error(
                "source-link-budget",
                f"{contract.page_type} 页面的源码链接数量为 {source_link_count}，合同要求 {source_minimum}..{source_maximum}。",
                actual=source_link_count,
                minimum=source_minimum,
                maximum=source_maximum,
                scope=source_budget.scope,
                scope_units=source_units,
                overflow_action=source_budget.overflow_action,
            )
        )

    fact_context = _context_sequence(context, "current_facts", errors)
    fact_evidence: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(fact_context):
        if not isinstance(item, Mapping):
            errors.append(_validation_error("validation-context-invalid", "current_facts 条目必须是对象。", field=f"current_facts[{index}]"))
            continue
        unknown = sorted(set(item) - {"claim", "source", "observed_at", "section_id"})
        claim = _normalize_fact_line(str(item.get("claim") or ""))
        if unknown or not claim:
            errors.append(_validation_error("validation-context-invalid", "current_facts 条目字段无效。", field=f"current_facts[{index}]", unknown_fields=unknown))
            continue
        fact_evidence[claim] = item
    for line_number, line in _visible_lines(markdown):
        normalized = _normalize_fact_line(line)
        if not normalized or normalized.startswith("#") or not _CURRENT_FACT_RE.search(normalized):
            continue
        evidence = fact_evidence.get(normalized)
        source = str(evidence.get("source") or "").strip() if evidence else ""
        observed_at = str(evidence.get("observed_at") or "").strip() if evidence else ""
        if not source or not _OBSERVED_AT_RE.fullmatch(observed_at):
            errors.append(
                _validation_error(
                    "current-fact-unverified",
                    "含当前、已支持或已测试状态的事实必须提供逐行匹配的 source 与 observed_at。",
                    claim=normalized,
                    line=line_number,
                )
            )

    return {
        "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
        "errors": errors,
        "metrics": {
            "heading_count": len(headings),
            "key_entity_count": entity_count,
            "section_metrics": section_metrics,
            "source_link_count": source_link_count,
            "verified_current_fact_count": sum(
                1
                for _line_number, line in _visible_lines(markdown)
                if _CURRENT_FACT_RE.search(_normalize_fact_line(line)) and _normalize_fact_line(line) in fact_evidence
            ),
        },
        "page_type": canonical_page_type,
        "registry_sha256": human_page_template_registry_sha256(),
        "schema_version": HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
    }

def _load_context(path: Path | None) -> Mapping[str, Any]:
    if path is None:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CkbError(f"模板 validation context 不是有效 JSON：{path}：{exc}") from exc
    if not isinstance(value, Mapping):
        raise CkbError(f"模板 validation context 必须是 JSON 对象：{path}")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CKB 人类页面模板合同只读查询与确定性验证")
    subparsers = parser.add_subparsers(dest="command", required=True)
    registry = subparsers.add_parser("registry", help="输出稳定序列化的完整模板注册表")
    registry.add_argument("--contract-version", default=HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION)
    registry.add_argument("--schema-version", type=int, default=HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION)
    query = subparsers.add_parser("get", help="查询一个页面类型合同")
    query.add_argument("--page-type", required=True)
    query.add_argument("--contract-version", default=HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION)
    query.add_argument("--schema-version", type=int, default=HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION)
    validate = subparsers.add_parser("validate", help="验证一个 Markdown 页面")
    validate.add_argument("--page-type", required=True)
    validate.add_argument("--input", type=Path, required=True)
    validate.add_argument("--context", type=Path)
    validate.add_argument("--contract-version", default=HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION)
    validate.add_argument("--schema-version", type=int, default=HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "registry":
            print(
                serialize_human_page_template_registry(
                    contract_version=args.contract_version,
                    schema_version=args.schema_version,
                ),
                end="",
            )
            return 0
        if args.command == "get":
            contract = get_human_page_template(
                args.page_type,
                contract_version=args.contract_version,
                schema_version=args.schema_version,
            )
            result = {
                "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
                "page_type": human_page_template_document(contract),
                "registry_sha256": human_page_template_registry_sha256(),
                "schema_version": HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
                "status": "ready",
            }
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        markdown = args.input.read_text(encoding="utf-8-sig")
        result = validate_human_page(
            args.page_type,
            markdown,
            context=_load_context(args.context),
            contract_version=args.contract_version,
            schema_version=args.schema_version,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["status"] == "passed" else 2
    except (CkbError, OSError, UnicodeError) as exc:
        result = {
            "contract_version": getattr(args, "contract_version", HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION),
            "errors": [_validation_error("command-input-invalid", str(exc))],
            "schema_version": getattr(args, "schema_version", HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION),
            "status": "failed",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
