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


HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION = 1
HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION = "1.0.0"
HUMAN_PAGE_TEMPLATE_REGISTRY_ID = "ckb-human-page-template-contracts"


@dataclass(frozen=True)
class SectionContract:
    """One semantic section, independent of its eventual generator."""

    section_id: str
    heading: str
    purpose: str
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
    *,
    level: int = 2,
    repeatable: bool = False,
    heading_pattern: str | None = None,
) -> SectionContract:
    return SectionContract(section_id, heading, purpose, level, repeatable, heading_pattern)


def _budget(
    minimum: int,
    maximum: int,
    rule: str,
    overflow: str,
    *,
    scope: str = "page",
) -> CountBudget:
    return CountBudget(minimum, maximum, scope, rule, overflow)


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
        reader_task="从首页按当前任务选择最短的阅读或检索入口。",
        entry_conditions=("每个已投影的人类知识库必须生成一次。", "入口只指向当前投影中实际存在的页面或命令。"),
        first_screen=_first(
            "用一句话说明知识库用途，并立即给出代码理解、工作记录、外部资料（存在时）和精确检索入口。",
            ("知识库用途", "按任务选择入口", "入口完成后得到什么"),
            5,
        ),
        required_sections=(
            _section("task-entry", "按任务选择入口", "让读者先选择任务，而不是浏览页面清单。"),
            _section("responsibility-entry", "按职责浏览代码", "进入少量职责聚合页。"),
            _section("work-record-entry", "工作记录", "进入 analysis、change、experiment、pitfall 和 session 导览。"),
            _section("exact-location", "精确定位", "把符号或源码范围定位交给确定性机器检索。"),
        ),
        optional_sections=(
            _section("reference-entry", "参考资料", "仅在存在已审阅 reference 时显示。"),
            _section("obsidian-entry", "在 Obsidian 中打开", "说明人类 vault 的打开入口。"),
            _section("logseq-entry", "在 Logseq 中打开", "说明 Logseq 文件图谱入口。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN
        + ("按字母列出的全部页面、实体目录或机器检索得分。", "把 README 安装说明或完整 WIKI 规则复制到首页。"),
        key_entity_budget=_budget(0, 5, "只统计首屏可见的任务入口；职责页列表不计为实现实体。", "移到对应导览页。"),
        source_link_budget=_budget(0, 0, "INDEX 不直接列源码范围。", "改用职责页或 brief 入口。"),
        link_requirements=("每个入口必须说明读者任务和到达后的结果。", "只链接当前投影中存在的页面或稳定命令入口。"),
        evidence_requirements=_evidence(
            ("projection_manifest", "link_target_set"), _CURRENT_FACT_RULE, ("projection_built_at", "observed_at")
        ),
        extension_points=("存在已审阅 reference 时增加一个参考资料入口。", "已安装的人类查看器可以增加一个打开入口。"),
        applicability_boundary="只负责导航，不承担架构解释、源码细节、安装教程或历史记录正文。",
    ),
    HumanPageTemplateContract(
        page_type="WIKI",
        reader_task="理解这套知识库的阅读顺序、页面职责、修改入口和 Agent 检索边界。",
        entry_conditions=("每个已投影的人类知识库必须生成一次。", "规则必须来自当前页面配置和已启用的投影能力。"),
        first_screen=_first(
            "先说明这不是机器实体清单，再给出代码事实、历史记录和精确检索三条阅读路径。",
            ("页面定位", "从哪里开始", "三类阅读路径"),
            5,
        ),
        required_sections=(
            _section("start", "从哪里开始", "按任务选择职责页、工作记录或机器检索。"),
            _section("retained-content", "页面只保留什么", "说明人类页保留和隐藏的信息。"),
            _section("change-entry", "如何寻找修改入口", "给出从职责到源码和测试的阅读顺序。"),
            _section("agent-retrieval", "Agent 确定性检索", "说明 brief、pack 和窄范围来源读取。"),
        ),
        optional_sections=(
            _section("language", "中文描述约定", "说明中文叙述与代码标识符边界。"),
            _section("page-config", "本次页面配置", "展示影响人类页面的少量已生效配置。"),
            _section("records", "工作记录如何查找", "说明记录导览与检索分工。"),
            _section("obsidian", "在 Obsidian 中打开", "说明 vault 入口。"),
            _section("logseq", "在 Logseq 中打开", "说明文件图谱入口。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN
        + ("完整 Schema、原始关系边、检索得分或 parser 字段说明。", "复制每种工作记录的具体正文模板。"),
        key_entity_budget=_budget(0, 7, "统计示例中直接点名的代码实体；命令名不计。", "将实现细节移到职责页或机器层。"),
        source_link_budget=_budget(0, 0, "WIKI 只解释阅读方法，不直接列源码范围。", "改链接职责页或检索入口。"),
        link_requirements=("链接必须对应一种阅读任务。", "工具命令必须说明何时使用和返回什么。"),
        evidence_requirements=_evidence(
            ("page_config", "projection_capabilities"), _CURRENT_FACT_RULE, ("configuration_built_at", "observed_at")
        ),
        extension_points=("已启用的查看器入口。", "已启用且经过审计的投影能力说明。"),
        applicability_boundary="说明阅读合同，不替代 README、职责页、工作记录或命令参考。",
    ),
    HumanPageTemplateContract(
        page_type="RECORDS",
        reader_task="按任务目的查找全部 analysis、change、experiment、pitfall 和 session 记录。",
        entry_conditions=("human 或 markdown 中存在工作记录目录。", "导览必须从完整记录集合确定性生成。"),
        first_screen=_first(
            "先解释五类记录分别解决什么任务，再给出快速查找方法。",
            ("导览用途", "先按任务选择", "快速查找"),
            5,
        ),
        required_sections=(
            _section("task-choice", "先按任务选择", "说明五类记录各自服务的读者任务。"),
            _section("quick-find", "快速查找", "说明标题浏览、稳定关键词和精确源码检索的分工。"),
            _section("analysis-records", "分析与决策", "列出全部 analysis 记录。"),
            _section("change-records", "实现与变更", "列出全部 change 记录。"),
            _section("experiment-records", "实验与量化结果", "列出全部 experiment 记录。"),
            _section("pitfall-records", "踩坑与限制", "列出全部 pitfall 记录。"),
            _section("session-records", "会话与任务过程", "列出全部 session 记录。"),
        ),
        optional_sections=(
            _section("gaps", "研究缺口与待补来源", "只汇总缺口数量并链接机器查询入口。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN
        + ("由单个查询手工挑选的记录子集。", "把研究缺口写成已确认事实或为每项缺口创建页面。"),
        key_entity_budget=_budget(0, 0, "RECORDS 只导航工作记录，不直接列实现实体。", "把实现实体放回具体记录或职责页。"),
        source_link_budget=_budget(0, 0, "RECORDS 不直接列源码范围。", "从具体记录进入证据或源码。"),
        link_requirements=("每条正式记录必须恰好出现一次。", "每个链接必须带一句中文摘要。", "空分类必须明确说明当前没有记录。"),
        evidence_requirements=_evidence(
            ("complete_record_set", "unique_titles", "kind_partition", "mirror_parity"),
            _CURRENT_FACT_RULE,
            ("index_refreshed_at", "observed_at"),
        ),
        extension_points=("存在 research gap register 时增加一个聚合入口。",),
        applicability_boundary="只导航正式工作记录，不替代记录正文、源码检索或缺口机器记录。",
    ),
    HumanPageTemplateContract(
        page_type="REFERENCES",
        reader_task="从导览选择一份已审阅外部资料，再进入中文摘要和精确原文范围。",
        entry_conditions=("至少存在一个 active 且 agent-reviewed 的 reference。", "每个 active source 最多对应一个人类摘要页。"),
        first_screen=_first(
            "先说明这里仅包含经过来源、许可和逐项引用审阅的外部资料。",
            ("导览用途", "审阅边界", "已审阅资料"),
            5,
        ),
        required_sections=(
            _section("reviewed-references", "已审阅资料", "列出每个 active reference 及其一句中文摘要。"),
        ),
        optional_sections=(),
        forbidden_content=_COMMON_FORBIDDEN
        + ("pending、superseded 或没有通过 review 的资料入口。", "把 reference 标题或摘要当作代码实体。"),
        key_entity_budget=_budget(0, 0, "REFERENCES 只导航资料，不直接列代码或资料内部实体。", "把资料实体留在 reference 正文或原文。"),
        source_link_budget=_budget(0, 0, "REFERENCES 只链接 reference 摘要页，不直接链接原文范围。", "从 reference 正文进入归档原文。"),
        link_requirements=("每个 active reference 必须恰好出现一次。", "每个链接必须带一句来自审阅摘要的中文说明。"),
        evidence_requirements=_evidence(
            ("active_reference_set", "review_status", "license_status", "mirror_parity"),
            _CURRENT_FACT_RULE,
            ("projection_built_at", "reviewed_at", "observed_at"),
        ),
        extension_points=(),
        applicability_boundary="只导航 active reference；来源、许可、主张和行范围保留在具体 reference 页面。",
    ),
    HumanPageTemplateContract(
        page_type="responsibility",
        reader_task="理解一个代码职责边界，判断何时修改，并找到关键实现与验证入口。",
        entry_conditions=("对象是 repository、module、boundary 或代码职责聚合页。", "内容来自固定源码快照与已审阅说明。"),
        first_screen=_first(
            "先给出职责结论和适用边界，再让读者决定是否进入源码。",
            ("职责概述", "修改时机", "适用边界"),
            5,
        ),
        required_sections=(
            _section("overview", "职责概述", "说明该范围产生什么结果以及不负责什么。"),
            _section("change-when", "什么时候需要修改", "列出会触发修改的读者场景。"),
            _section("implementation", "关键实现", "只列完成职责所需的少量关键实体。"),
            _section("verification", "验证入口", "说明修改后应验证的行为。"),
            _section("boundary", "适用边界", "说明本页覆盖范围和未继续展开的内容。"),
        ),
        optional_sections=(
            _section("related-code", "相关代码", "给出直接协作职责。"),
            _section("backlinks", "谁会来到这里", "给出直接调用或入口职责。"),
            _section("details", "内部细节", "折叠收纳必要的辅助实现。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN
        + ("完整函数、方法、门、状态字段和审计实体目录。", "脱离固定源码范围的推测性实现说明。"),
        key_entity_budget=_budget(1, 7, "统计正文中作为关键实现点名的类、函数、文件或测试入口。", "按职责分组，并把其余实体移到折叠细节或机器层。"),
        source_link_budget=_budget(1, 7, "统计可点击源码范围；同一实体的镜像链接只计一次。", "保留最能解释职责与验证的源码范围。"),
        link_requirements=("每个源码链接必须说明其职责。", "相关代码链接必须说明协作方向。", "验证入口必须指向测试或可复现命令。"),
        evidence_requirements=_evidence(
            ("source_snapshot", "source_ranges", "review_status", "verification_entry"),
            _CURRENT_FACT_RULE,
            ("source_commit", "reviewed_at", "observed_at"),
        ),
        extension_points=("boundary 页面可增加未展开代码范围。", "辅助实现可放入折叠的内部细节。"),
        applicability_boundary="适用于当前源码职责，不记录历史决策、完整变更过程或外部资料摘要。",
    ),
    HumanPageTemplateContract(
        page_type="change",
        reader_task="确认已经修改什么、为什么修改、怎样实现、如何验证以及在哪些边界内成立。",
        entry_conditions=("修改已经发生并有可复查实现。", "验证结果与适用边界已经形成。"),
        first_screen=_first(
            "首屏直接说明已成立的修改结果，不复述任务指令或调试过程。",
            ("修改内容", "成立状态", "主要边界"),
            3,
        ),
        required_sections=(
            _section("what", "修改内容", "说明用户可见或系统行为现在是什么。"),
            _section("when", "修改时间", "给出进入集成、稳定版本或当前描述基准的时间。"),
            _section("why", "修改原因", "说明原问题与本次修改目的。"),
            _section("how", "修改方式", "按职责说明少量关键实现，不展开内部状态机。"),
            _section("features", "关联特性", "说明直接受影响的能力与兼容关系。"),
            _section("verification-boundary", "验证结果与适用边界", "同时给出已验证行为、证据和未覆盖边界。"),
            _section("source-ranges", "关键源码范围", "列出理解和复查本次变化所需的最少源码范围。"),
        ),
        optional_sections=(
            _section("migration", "迁移说明", "仅在使用者必须执行迁移动作时出现。"),
            _section("rollback", "回滚入口", "仅在回滚动作属于人类使用合同的一部分时出现。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN
        + ("逐条调试日志、失败尝试和尚未成立的方案。", "把完整锁、状态字段或压力测试明细作为理解变化的前置条件。"),
        key_entity_budget=_budget(1, 3, "统计“修改方式”中承担独立职责的关键实现组。", "把细节移到机器验证记录，并保留三项以内的职责。"),
        source_link_budget=_budget(0, 5, "统计“关键源码范围”中的可点击源码链接；纯路径范围仍属于源码引用但不计链接。", "只保留实现、接入和验证的关键范围。"),
        link_requirements=("关联特性必须说明关系，不做孤立名称列表。", "验证证据链接必须说明它证明什么。", "源码范围必须带职责描述。"),
        evidence_requirements=_evidence(
            ("change_time", "baseline_or_version", "verification_result", "applicability_boundary", "source_ranges"),
            _CURRENT_FACT_RULE,
            ("changed_at", "verified_at", "observed_at"),
        ),
        extension_points=("确需用户动作时增加迁移说明。", "确需人类直接执行回滚时增加回滚入口。"),
        applicability_boundary="只描述已经成立且经过验证的变化，不承载提案、开发日志或未验证效果。",
    ),
    HumanPageTemplateContract(
        page_type="analysis",
        reader_task="读取一个已审阅判断，区分事实、推断、未知并据此决定下一步。",
        entry_conditions=("问题已经有足够证据形成可复用判断。", "至少回链一个知识页或精确来源。"),
        first_screen=_first(
            "先给结论和比较对象，再说明证据边界。",
            ("结论", "比较对象", "证据状态"),
            5,
        ),
        required_sections=(
            _section("conclusion", "结论", "直接回答分析问题。"),
            _section("facts", "已确认事实", "只列有来源支持的事实。"),
            _section("impact", "事实对当前问题的影响", "说明事实怎样改变判断。"),
            _section("unknowns", "仍需核验的内容", "列出缺失证据和核验入口。"),
            _section("next", "建议的下一步", "给出与结论一致的行动。"),
        ),
        optional_sections=(
            _section("alternatives", "方案比较", "使用同一协议比较互斥方案。"),
            _section("method", "分析方法", "仅在方法影响结论可信度时出现。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("把推断或待核验内容写成已确认效果。", "混用不同版本、协议或比较对象的数据。"),
        key_entity_budget=_budget(0, 5, "统计支撑结论的关键实现实体。", "将实体明细移到职责页或来源表。"),
        source_link_budget=_budget(0, 8, "统计直接支撑事实的源码或证据链接。", "保留能改变结论的证据。"),
        link_requirements=("每个来源链接必须对应一项事实或待核验内容。", "方案链接必须说明比较维度。"),
        evidence_requirements=_evidence(
            ("question", "comparison_object", "facts", "inferences", "unknowns"),
            _CURRENT_FACT_RULE,
            ("evidence_observed_at", "analysis_updated_at", "observed_at"),
        ),
        extension_points=("存在互斥方案时增加方案比较。", "方法影响可信度时增加分析方法。"),
        applicability_boundary="保存可复用判断，不替代实验原始记录、change 成品说明或 session 过程恢复。",
    ),
    HumanPageTemplateContract(
        page_type="pitfall",
        reader_task="识别一个可复现失败，判断触发条件并采用已经验证的规避方法。",
        entry_conditions=("失败已复现或有明确直接证据。", "根因与规避方法的证据边界清楚。"),
        first_screen=_first("先说明现象、触发条件和可用结论。", ("现象", "触发条件", "可用结论"), 4),
        required_sections=(
            _section("symptom", "现象", "给出可识别的失败结果。"),
            _section("trigger", "触发条件", "限定环境、输入和前置状态。"),
            _section("cause", "根因", "区分已确认根因和推断。"),
            _section("resolution", "解决方法", "给出已验证的窄范围动作。"),
            _section("verification", "验证结果", "说明修正前后行为。"),
            _section("boundary", "适用边界", "说明不适用环境和剩余限制。"),
        ),
        optional_sections=(
            _section("reproduction", "复现命令", "提供最小复现。"),
            _section("rollback", "回滚方法", "说明撤销规避动作。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("把上游一次失败重复描述成多项下游失败。", "没有复现或直接证据的确定性根因声明。"),
        key_entity_budget=_budget(0, 4, "统计复现、根因和修正直接涉及的实现实体。", "只保留能解释失败链的实体。"),
        source_link_budget=_budget(0, 6, "统计复现和根因的源码或日志证据链接。", "保留最小复现链。"),
        link_requirements=("证据链接必须说明它支持现象、根因还是验证。", "命令入口必须说明预期退出状态。"),
        evidence_requirements=_evidence(
            ("reproduction", "observed_failure", "cause_status", "verified_resolution"),
            _CURRENT_FACT_RULE,
            ("reproduced_at", "verified_at", "observed_at"),
        ),
        extension_points=("存在稳定最小复现时增加复现命令。", "规避动作可撤销时增加回滚方法。"),
        applicability_boundary="记录已观察失败和验证过的处理，不汇总一般性最佳实践。",
    ),
    HumanPageTemplateContract(
        page_type="experiment",
        reader_task="复查同一协议下的对照、变量、结果和结论边界。",
        entry_conditions=("协议、输入、对照和测量已经冻结。", "结果可由保存的证据复查。"),
        first_screen=_first("先给实验问题、比较对象和最重要结果。", ("实验问题", "比较对象", "主要结果"), 5),
        required_sections=(
            _section("question", "实验问题", "说明要验证的具体假设。"),
            _section("design", "实验设计", "冻结输入、顺序、工具和测量方法。"),
            _section("controls", "对照与变量", "区分基线、处理和受控变量。"),
            _section("results", "结果", "报告字面测量和退出状态。"),
            _section("conclusion", "结论", "只解释协议支持的结论。"),
            _section("boundary", "适用边界", "说明样本、压力和外推限制。"),
            _section("reproduction", "复现入口", "给出输入、命令和结果记录。"),
        ),
        optional_sections=(
            _section("iteration", "下一轮实验", "说明由当前证据触发的下一轮变量。"),
            _section("cost", "资源与成本", "在资源影响比较时单列。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("混合不同协议、样本或比较对象的数字。", "用准备、非劣或局部信号替代已经证明的效果。"),
        key_entity_budget=_budget(0, 5, "统计实验路径中必须理解的实现实体。", "把执行细节留在复现记录。"),
        source_link_budget=_budget(1, 8, "统计协议、输入、结果和分析脚本入口。", "优先保留可复现链。"),
        link_requirements=("每个结果链接必须标明协议和比较对象。", "复现入口必须同时覆盖输入、命令和字面输出。"),
        evidence_requirements=_evidence(
            ("protocol", "baseline", "variables", "measurements", "literal_results", "exit_statuses"),
            _CURRENT_FACT_RULE,
            ("protocol_frozen_at", "measured_at", "observed_at"),
        ),
        extension_points=("资源影响结论时增加资源与成本。", "当前证据明确下一变量时增加下一轮实验。"),
        applicability_boundary="只对冻结协议和样本负责，不把工程信号外推为普遍效果。",
    ),
    HumanPageTemplateContract(
        page_type="session",
        reader_task="恢复一次任务的目标、范围、结果、验证状态和继续入口。",
        entry_conditions=("任务需要跨会话恢复，或其边界与结果值得保留。", "过程信息只保留恢复任务所需的部分。"),
        first_screen=_first("先说明目标、当前状态和下一动作。", ("任务目标", "当前状态", "下一动作"), 5),
        required_sections=(
            _section("goal", "任务目标", "说明本次任务要成立的行为。"),
            _section("scope", "执行范围", "记录可读、可写与明确排除项。"),
            _section("results", "已完成结果", "列出已经成立的结果。"),
            _section("verification", "验证结果", "区分实际通过、失败和未运行。"),
            _section("continuation", "待继续事项", "只保留仍阻止完成或已确认的下一步。"),
        ),
        optional_sections=(
            _section("decisions", "关键决定", "保留影响后续工作的已确认取舍。"),
            _section("artifacts", "交付物", "列出可直接继续使用的文件。"),
            _section("rollback", "回滚入口", "列出本次任务拥有的回滚。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("完整对话、工具日志、思考过程或已撤回方案。", "把计划、命令启动或文件生成当作完成。"),
        key_entity_budget=_budget(0, 5, "统计继续任务必须知道的代码实体。", "将实现细节链接到 change 或职责页。"),
        source_link_budget=_budget(0, 8, "统计恢复任务必须打开的源码、测试和交付物入口。", "只保留继续执行所需入口。"),
        link_requirements=("每个交付物链接必须说明当前状态和用途。", "继续入口必须说明尚缺证据。"),
        evidence_requirements=_evidence(
            ("goal", "scope", "completed_results", "verification_status", "remaining_work"),
            _CURRENT_FACT_RULE,
            ("session_started_at", "last_verified_at", "observed_at"),
        ),
        extension_points=("存在跨任务约束时增加关键决定。", "存在可复用文件时增加交付物。"),
        applicability_boundary="用于恢复任务，不替代 change 最终说明、analysis 判断或原始运行日志。",
    ),
    HumanPageTemplateContract(
        page_type="reference",
        reader_task="理解一份已审阅外部资料的中文摘要，并逐项回到归档原文核对。",
        entry_conditions=("本地原文、来源、许可和精确行范围已经审阅。", "每个 active source 最多投影一个摘要页。"),
        first_screen=_first("先说明资料讲什么以及它能支持哪些问题。", ("资料主题", "适用问题", "审阅状态"), 5),
        required_sections=(
            _section("summary", "这份资料讲什么", "给出中文摘要和适用问题。"),
            _section("claims", "关键结论", "每项中文主张都回链精确原文范围。"),
            _section("source", "来源", "列出来源、作者或组织、许可和归档原文。"),
        ),
        optional_sections=(
            _section("limitations", "来源边界", "说明资料自身限制或冲突。"),
            _section("revision", "版本关系", "仅在人类需要区分修订时出现。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("没有精确原文范围的二手主张。", "把 reference 当作代码实体或当前产品事实。"),
        key_entity_budget=_budget(0, 5, "只统计理解资料所需且由原文点名的关键实体。", "其余实体留在原文或机器索引。"),
        source_link_budget=_budget(1, 8, "统计关键主张的精确原文范围与归档原文入口。", "合并重复主张并保留最直接证据。"),
        link_requirements=("每项关键结论必须链接精确原文行范围。", "来源入口必须标明来源、许可和归档对象。"),
        evidence_requirements=_evidence(
            ("origin", "license", "archived_source", "reviewed_claim_ranges"),
            _CURRENT_FACT_RULE,
            ("source_published_at", "reviewed_at", "observed_at"),
        ),
        extension_points=("资料自身存在限制时增加来源边界。", "人类必须理解修订关系时增加版本关系。"),
        applicability_boundary="只陈述已审阅外部资料及其来源边界，不自动成为代码事实或当前状态。",
    ),
    HumanPageTemplateContract(
        page_type="learning-note",
        reader_task="按日期回看一次选区问题、来源上下文和经过审计的解释。",
        entry_conditions=("解释已通过检索证据与审计。", "写入发生在当天学习页，失败结果不进入人类笔记。"),
        first_screen=_first("显示日期、学习类型和当天条目的用途。", ("日期", "#类型/学习", "当天条目说明"), 3),
        required_sections=(
            _section(
                "entry",
                "HH:MM:SS · SOURCE_TITLE",
                "每个条目给出时间、来源、执行器和问题。",
                repeatable=True,
                heading_pattern=r"^\d{2}:\d{2}:\d{2} · (?:追问 · )?.+$",
            ),
            _section(
                "question",
                "我的问题或我的追问",
                "保留读者实际提出的问题。",
                level=3,
                repeatable=True,
                heading_pattern=r"^我的(?:问题|追问)$",
            ),
            _section("explanation", "解释", "保存通过审计的最终解释。", level=3, repeatable=True),
        ),
        optional_sections=(
            _section("selection", "选中文本", "初次问题保存原选区。", level=3, repeatable=True),
            _section("parent-question", "承接问题", "追问保存其承接问题。", level=3, repeatable=True),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("Provider 原始思考、生成过程或失败响应。", "缺少来源页面、行范围或审计证据的解释。"),
        key_entity_budget=_budget(0, 3, "按单个学习条目统计解释所需的关键实体。", "把扩展实体链接到来源职责页。", scope="entry"),
        source_link_budget=_budget(1, 1, "每个条目恰好一个来源页面入口。", "保留选区的唯一来源页面。", scope="entry"),
        link_requirements=("每个条目必须链接来源页面，并在可用时给出行范围。", "追问必须保留承接问题。"),
        evidence_requirements=_evidence(
            ("source_page", "selection_or_parent_question", "retrieval_pack", "audit_status", "explanation"),
            _CURRENT_FACT_RULE,
            ("entry_created_at", "evidence_created_at", "observed_at"),
        ),
        extension_points=("追问条目可增加承接问题。", "初次问题可保留选中文本。"),
        applicability_boundary="用于学习回顾，不替代 analysis、reference 或源码职责页。",
    ),
    HumanPageTemplateContract(
        page_type="feedback",
        reader_task="查看一个定位到具体页面范围的反馈，并确认其状态与处理结果。",
        entry_conditions=("反馈锚定到 human/markdown 中的非 feedback 页面。", "反馈记录保留且不会删除。"),
        first_screen=_first("显示状态、严重程度、目标范围、来源和提交者。", ("状态", "严重程度", "目标", "来源"), 4),
        required_sections=(
            _section("comment", "反馈内容", "保存人类提交的中文意见。"),
            _section("anchor", "锚点摘录", "保存可重新定位的文本窗口。"),
        ),
        optional_sections=(
            _section("resolution", "处理结果", "resolved 记录必须说明决议、理由和落实记录。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("删除历史反馈或覆盖原始意见。", "采纳或部分采纳但没有落实记录。"),
        key_entity_budget=_budget(0, 1, "只统计反馈直接指向的页面或实体范围。", "将多目标意见拆成独立反馈。"),
        source_link_budget=_budget(0, 1, "统计唯一目标页面入口。", "保持一个反馈对应一个目标范围。"),
        link_requirements=("目标链接必须带包含行范围的锚点。", "落实记录必须说明决议怎样被执行。"),
        evidence_requirements=_evidence(
            ("target", "target_lines", "anchor_text", "status", "severity", "source"),
            _CURRENT_FACT_RULE,
            ("created_at", "resolved_at", "observed_at"),
        ),
        extension_points=("resolved 状态增加处理结果。", "deferred 状态可以保留中文暂缓理由。"),
        applicability_boundary="一个反馈只对应一个页面范围；不作为源码事实或已完成 change。",
    ),
    HumanPageTemplateContract(
        page_type="README",
        reader_task="先了解发布包结构，再让 Agent 安装 CKB 或解释使用者自己的项目。",
        entry_conditions=("发布包或项目根需要一个人类使用入口。", "版本、分支和目录事实必须来自发布清单或当前验证。"),
        first_screen=_first(
            "首屏只给产品结果和三个互斥任务：了解结构、安装本项目、解释自己的项目。",
            ("产品一句话", "了解本项目知识库结构", "让 Agent 安装本项目", "让 Agent 解释自己的项目"),
            3,
        ),
        required_sections=(
            _section("task-choice", "先选择你要完成的任务", "用三行任务表说明继续阅读和完成结果。"),
            _section("structure", "了解本项目知识库结构", "说明发布包和知识库人类/机器入口。"),
            _section("install", "让 Agent 安装本项目", "提供只负责安装的可复制 Prompt。"),
            _section("explain-own-project", "让 Agent 解释自己的项目", "提供建库或接管后回答问题的可复制 Prompt。"),
        ),
        optional_sections=(
            _section("verify-release", "验证发布包", "仅在发布验收需要人类直接执行时出现。"),
            _section("uninstall", "卸载与回滚", "仅在发布包提供稳定卸载入口时出现。"),
        ),
        forbidden_content=_COMMON_FORBIDDEN + ("首屏加入第四类任务、功能清单或实现架构展开。", "把安装和为业务仓库建库混成同一个 Prompt。"),
        key_entity_budget=_budget(0, 3, "只统计首屏任务，不统计目录树条目或 Prompt 步骤。", "将额外任务移到后续章节或独立文档。"),
        source_link_budget=_budget(0, 0, "README 不直接列项目源码范围。", "改链接知识库职责页或发布验证记录。"),
        link_requirements=("首屏三条链接必须分别说明继续阅读和完成结果。", "外部项目来源链接必须使用描述性文字。", "Prompt 内的路径或分支必须说明用途。"),
        evidence_requirements=_evidence(
            ("release_version", "publication_manifest", "directory_contract", "installation_probe"),
            _CURRENT_FACT_RULE,
            ("release_built_at", "verified_at", "observed_at"),
        ),
        extension_points=("发布验收确需人类动作时增加验证发布包。", "存在稳定卸载入口时增加卸载与回滚。"),
        applicability_boundary="README 只负责了解结构、安装本项目和解释自己的项目，不展开生成器内部实现。",
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
            f"contract_version={HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION}"
        )
    contract = _CONTRACT_BY_CASEFOLD.get(str(page_type).strip().casefold())
    if contract is None:
        raise CkbError(f"未知人类页面类型：{page_type}；可用类型：{list(_PAGE_TYPE_ORDER)}")
    return contract


def _section_document(section: SectionContract) -> dict[str, Any]:
    return {
        "heading": section.heading,
        "heading_pattern": section.heading_pattern,
        "level": section.level,
        "purpose": section.purpose,
        "repeatable": section.repeatable,
        "section_id": section.section_id,
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
        "optional_sections": [_section_document(section) for section in contract.optional_sections],
        "page_type": contract.page_type,
        "reader_task": contract.reader_task,
        "required_sections": [_section_document(section) for section in contract.required_sections],
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
    r"(?:当前(?:状态|边界|版本|发布|知识库|实现|行为|结果|配置|默认|要求)|目前|现行|最新|截至|现在(?:是|为))"
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


def _matches_section(heading: Mapping[str, Any], section: SectionContract) -> bool:
    if int(heading["level"]) != section.level:
        return False
    text = str(heading["text"])
    if section.heading_pattern:
        return re.fullmatch(section.heading_pattern, text) is not None
    return text == section.heading


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


def validate_human_page(
    page_type: str,
    markdown: str,
    *,
    context: Mapping[str, Any] | None = None,
    contract_version: str = HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
    schema_version: int = HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Validate one page without network, LLM, mutable state, or hidden defaults.

    ``context`` owns information Markdown cannot classify reliably:

    - ``key_entities``: implementation entities counted by the page contract;
    - ``links``: optional ``target``, ``purpose``, and ``kind`` evidence;
    - ``current_facts``: exact fact line plus non-empty ``source`` and ISO
      ``observed_at``.
    """

    errors: list[dict[str, Any]] = []
    canonical_page_type = str(page_type).strip()
    if not _compatible_version(contract_version, schema_version):
        errors.append(
            _validation_error(
                "contract-version-incompatible",
                "人类页面模板合同版本不兼容。",
                actual={"schema_version": schema_version, "contract_version": contract_version},
                expected={
                    "schema_version": HUMAN_PAGE_TEMPLATE_SCHEMA_VERSION,
                    "contract_version": HUMAN_PAGE_TEMPLATE_CONTRACT_VERSION,
                },
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
        errors.append(
            _validation_error(
                "unknown-page-type",
                f"未知人类页面类型：{page_type}。",
                available=list(_PAGE_TYPE_ORDER),
            )
        )
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

    headings = _headings(markdown)
    h1 = [heading for heading in headings if heading["level"] == 1]
    if len(h1) != 1:
        errors.append(
            _validation_error(
                "title-heading-count",
                "人类页面必须且只能包含一个一级标题。",
                count=len(h1),
                lines=[heading["line"] for heading in h1],
            )
        )
    for section in contract.required_sections:
        matches = [heading for heading in headings if _matches_section(heading, section)]
        if not matches:
            errors.append(
                _validation_error(
                    "required-section-missing",
                    f"{contract.page_type} 页面缺少必填章节：{section.heading}。",
                    section_id=section.section_id,
                    heading=section.heading,
                    level=section.level,
                )
            )

    by_heading: dict[tuple[int, str], list[int]] = {}
    for heading in headings:
        by_heading.setdefault((int(heading["level"]), str(heading["text"])), []).append(int(heading["line"]))
    all_sections = contract.required_sections + contract.optional_sections
    for (level, text), lines in sorted(by_heading.items()):
        if len(lines) < 2:
            continue
        repeatable = any(
            section.repeatable
            and level == section.level
            and ((section.heading_pattern and re.fullmatch(section.heading_pattern, text)) or (not section.heading_pattern and text == section.heading))
            for section in all_sections
        )
        if not repeatable:
            errors.append(
                _validation_error(
                    "duplicate-heading",
                    f"人类页面包含重复标题：{text}。",
                    heading=text,
                    level=level,
                    lines=lines,
                )
            )

    visible_text = "\n".join(line for _line_number, line in _visible_lines(markdown))
    for pattern in _META_PATTERNS:
        match = pattern.search(visible_text)
        if match:
            line_number = visible_text[: match.start()].count("\n") + 1
            errors.append(
                _validation_error(
                    "process-meta-copy",
                    "人类页面包含制作过程元文案或占位符。",
                    text=match.group(0),
                    visible_line=line_number,
                )
            )

    key_entities = _context_sequence(context, "key_entities", errors)
    invalid_entities = [value for value in key_entities if not isinstance(value, str) or not value.strip()]
    if invalid_entities:
        errors.append(_validation_error("validation-context-invalid", "key_entities 只能包含非空字符串。", field="key_entities"))
    entity_count = len({str(value).strip() for value in key_entities if isinstance(value, str) and value.strip()})
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

    link_context = _context_sequence(context, "links", errors)
    purpose_by_target: dict[str, str] = {}
    kind_by_target: dict[str, str] = {}
    for index, item in enumerate(link_context):
        if not isinstance(item, Mapping):
            errors.append(_validation_error("validation-context-invalid", "links 条目必须是对象。", field=f"links[{index}]"))
            continue
        target = str(item.get("target") or "").strip()
        purpose = str(item.get("purpose") or "").strip()
        kind = str(item.get("kind") or "internal").strip()
        if not target or kind not in {"internal", "external", "source", "evidence"}:
            errors.append(_validation_error("validation-context-invalid", "links 条目需要 target，且 kind 必须是 internal、external、source 或 evidence。", field=f"links[{index}]"))
            continue
        purpose_by_target[target] = purpose
        kind_by_target[target] = kind
        if not purpose:
            errors.append(
                _validation_error(
                    "link-purpose-missing",
                    f"链接 {target} 没有说明阅读目的。",
                    target=target,
                )
            )
    source_link_count = 0
    for link in _link_occurrences(markdown):
        target = str(link["target"])
        label = re.sub(r"[`*_]", "", str(link["label"])).strip()
        explicit_purpose = purpose_by_target.get(target, "")
        if label in _AMBIGUOUS_LINK_LABELS and not explicit_purpose:
            errors.append(
                _validation_error(
                    "link-purpose-missing",
                    f"链接文字“{label}”没有说明阅读目的。",
                    label=label,
                    target=target,
                )
            )
        kind = kind_by_target.get(target)
        if kind == "source" or (kind is None and target.casefold().startswith("vscode://file/")):
            source_link_count += 1
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
        claim = _normalize_fact_line(str(item.get("claim") or ""))
        if not claim:
            errors.append(_validation_error("validation-context-invalid", "current_facts 条目需要非空 claim。", field=f"current_facts[{index}]"))
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
                    "含当前状态的事实必须提供逐行匹配的 source 与 observed_at。",
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
            "source_link_count": source_link_count,
            "verified_current_fact_count": sum(
                1
                for _line_number, line in _visible_lines(markdown)
                if _CURRENT_FACT_RE.search(_normalize_fact_line(line))
                and _normalize_fact_line(line) in fact_evidence
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
