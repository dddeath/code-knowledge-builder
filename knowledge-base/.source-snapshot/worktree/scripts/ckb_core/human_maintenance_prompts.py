"""Deterministic, parameterized Prompts for human-facing CKB maintenance.

The registry in this module is descriptive orchestration only.  It maps one
human-selected action to existing CKB commands and explicit dependencies; it
does not execute business commands or own a second workflow state machine.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from .common import CkbError


HUMAN_MAINTENANCE_PROMPT_SCHEMA_VERSION = 1
HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION = "1.0.0"
HUMAN_MAINTENANCE_PROMPT_REGISTRY_ID = "ckb-human-maintenance-prompts"

_ACTION_NAME = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
_PARAMETER_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_MAPPINGS = {"existing-command", "external-dependency", "pending-capability"}
_REQUIREMENT_STATES = {"required", "conditional", "not-required", "dependency"}
_INSTALL_PARAMETERS = {"source", "release_branch", "project_root", "skill_root", "manifest_verifier"}
_BUILD_PARAMETERS = {"repository", "knowledge_base", "question", "format", "workspace_root", "scope_path"}


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    type_name: str
    description_zh: str
    required: bool = False
    default: str | int | bool | None = None
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommandStep:
    step_id: str
    instruction_zh: str
    mapping: str
    command_template: str | None = None
    required_for_audit: bool = False
    when_parameter: str | None = None
    when_values: tuple[str, ...] = ()
    input_parameters: tuple[str, ...] = ()
    allowed_exit_statuses: tuple[int, ...] = (0,)
    result_statuses: tuple[str, ...] = ()
    output_mode: str = "json"


@dataclass(frozen=True)
class RollbackContract:
    requirement: str
    description_zh: str
    command_template: str | None = None
    mapping: str = "existing-command"
    dependency_zh: str | None = None


@dataclass(frozen=True)
class ActionContract:
    action: str
    purpose_zh: str
    parameters: tuple[ParameterSpec, ...]
    execution_steps: tuple[CommandStep, ...]
    stop_conditions: tuple[str, ...]
    human_confirmation_points: tuple[str, ...]
    requirements: tuple[tuple[str, str], ...]
    acceptance_summary_fields: tuple[str, ...]
    rollback: RollbackContract
    dependencies: tuple[str, ...] = ()


def _p(
    name: str,
    type_name: str,
    description_zh: str,
    *,
    required: bool = False,
    default: str | int | bool | None = None,
    choices: Sequence[str] = (),
) -> ParameterSpec:
    return ParameterSpec(name, type_name, description_zh, required, default, tuple(choices))


def _s(
    step_id: str,
    instruction_zh: str,
    mapping: str,
    command_template: str | None = None,
    *,
    required_for_audit: bool = False,
    when_parameter: str | None = None,
    when_values: Sequence[str] = (),
    input_parameters: Sequence[str] = (),
    allowed_exit_statuses: Sequence[int] = (0,),
    result_statuses: Sequence[str] = (),
    output_mode: str = "json",
) -> CommandStep:
    return CommandStep(
        step_id,
        instruction_zh,
        mapping,
        command_template,
        required_for_audit,
        when_parameter,
        tuple(when_values),
        tuple(input_parameters),
        tuple(allowed_exit_statuses),
        tuple(result_statuses),
        output_mode,
    )


def _requirements(
    brief: str,
    source: str,
    maintain: str,
    human_review: str,
) -> tuple[tuple[str, str], ...]:
    return (
        ("brief", brief),
        ("source", source),
        ("maintain", maintain),
        ("human_review", human_review),
    )


_PYTHON = _p("python", "command", "运行 CKB 的 Python 命令。", default="python")
_CKB = _p("ckb", "path", "已安装的 scripts/ckb.py 路径。", default="<path:已安装的scripts/ckb.py>")
_OUT = _p("knowledge_base", "path", "目标知识库 OUTPUT。", required=True)
_CONFIRM = lambda action: _p(  # noqa: E731 - compact immutable registry declaration
    "confirm",
    "confirmation",
    f"人类明确选择此 action；固定值为 {action}。",
    required=True,
    choices=(action,),
)


_ACTIONS: tuple[ActionContract, ...] = (
    ActionContract(
        action="install-project",
        purpose_zh="只安装 Code Knowledge Builder 项目、Skill 与运行环境，不为业务仓库建库。",
        parameters=(
            _p("source", "url", "项目发布来源。", required=True),
            _p("release_branch", "git-ref", "明确的发布分支或标签。", required=True),
            _p("project_root", "path", "项目安装目录。", default="<path:Harness标准项目目录>"),
            _p("skill_root", "path", "Skill 安装目录。", default="<path:Harness标准Skill目录>"),
            _p("published_out", "path", "发布包自带稳定知识库的隔离检索副本。", default="<path:项目内knowledge-base隔离副本>"),
            _p("manifest_verifier", "path", "发布包完整性校验脚本。", default="<path:delivery/verify-publication.py>"),
            _p("scope", "enum", "安装职责边界。", default="project-and-skill-only", choices=("project-and-skill-only",)),
            _CONFIRM("install-project"),
            _PYTHON,
            _CKB,
        ),
        execution_steps=(
            _s("download-release", "下载固定发布分支及 Git LFS 内容。", "external-dependency"),
            _s("verify-publication", "运行发布包自带校验器并核对 publication-manifest.json。", "external-dependency"),
            _s("install-skill", "通过当前 Harness 的 Skill 安装入口安装同一发布包中的 Skill。", "external-dependency"),
            _s(
                "doctor",
                "验证 Python、解析器、SQLite 和本地依赖。",
                "existing-command",
                "& {python} {ckb} doctor --json",
                required_for_audit=True,
                input_parameters=("python", "ckb"),
                result_statuses=("ready",),
            ),
            _s(
                "runtime-plan",
                "只读取运行环境部署计划；需要部署时在下一人工确认点停止。",
                "existing-command",
                "& {python} {ckb} runtime plan --json",
                required_for_audit=True,
                input_parameters=("python", "ckb"),
                result_statuses=("ready", "planned"),
            ),
            _s(
                "brief-probe",
                "在发布知识库隔离副本上执行不修改业务仓库的最小检索探针。",
                "existing-command",
                "& {python} {ckb} brief --out {published_out} '安装验收检索探针' --budget 600 --max-pages 2 --profile fast",
                required_for_audit=True,
                input_parameters=("published_out",),
                result_statuses=("passed",),
            ),
        ),
        stop_conditions=(
            "发布分支、manifest 或 Git LFS 内容无法核对时停止。",
            "Harness 缺少可调用的 Skill 安装入口时报告 external dependency，不把安装描述为完成。",
            "doctor 或检索探针未得到完成结果时停止；命令启动提示不算验收。",
            "发现 repository、knowledge_base 或 question 等业务建库参数时拒绝混合职责。",
        ),
        human_confirmation_points=(
            "下载前确认 source 与 release_branch。",
            "runtime plan 显示需要部署或变更运行环境时，执行 deploy 前再次确认。",
        ),
        requirements=_requirements("required", "required", "not-required", "required"),
        acceptance_summary_fields=(
            "project_location",
            "release_ref",
            "release_commit",
            "skill_location",
            "runtime_result",
            "git_lfs_result",
            "publication_verification",
            "brief_probe",
        ),
        rollback=RollbackContract(
            "dependency",
            "安装回滚依赖 Harness 的 Skill 卸载入口与安装目录清单；CKB 当前没有统一 install rollback 命令。",
            mapping="external-dependency",
            dependency_zh="Harness Skill 卸载能力和仅含本次安装路径的删除清单",
        ),
        dependencies=("Git/Git LFS", "发布包校验器", "Harness Skill 安装与卸载入口"),
    ),
    ActionContract(
        action="adopt-existing",
        purpose_zh="核对并接管已经存在的 CKB 输出；版本不匹配时停止并转入 migrate。",
        parameters=(
            _p("repository", "path", "与现有知识库绑定的干净 Git 仓库。", required=True),
            _OUT,
            _p("question", "text", "接管后用于真实检索验证的问题。", required=True),
            _p("workspace_root", "path", "Agent Policy 所在工作区。", default="<path:repository父目录>"),
            _p("scope", "enum", "只接管现有 OUTPUT。", default="existing-output-only", choices=("existing-output-only",)),
            _CONFIRM("adopt-existing"),
            _PYTHON,
            _CKB,
        ),
        execution_steps=(
            _s("git-source-check", "核对 repository 当前提交和干净状态。", "external-dependency"),
            _s(
                "output-status",
                "读取现有知识库完成状态和固定源码版本。",
                "existing-command",
                "& {python} {ckb} status --out {knowledge_base} --json",
                required_for_audit=True,
                input_parameters=("knowledge_base", "repository"),
                result_statuses=("complete", "passed", "ready"),
            ),
            _s(
                "agent-policy-check",
                "核对项目级 Agent 使用规则；缺失时先停在人工确认点。",
                "existing-command",
                "& {python} {ckb} agent-policy check --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base", "workspace_root"),
                result_statuses=("passed",),
            ),
            _s(
                "brief",
                "执行真实 brief 并打开返回的 Agent pack。",
                "existing-command",
                "& {python} {ckb} brief --out {knowledge_base} {question} --budget 1800 --max-pages 8 --profile fast",
                required_for_audit=True,
                input_parameters=("knowledge_base", "question"),
                result_statuses=("passed",),
            ),
            _s(
                "maintain",
                "运行聚合维护门。",
                "existing-command",
                "& {python} {ckb} maintain --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("passed",),
            ),
        ),
        stop_conditions=(
            "现有 OUTPUT 不完整、固定 commit 与 repository 不一致或工作树不干净时停止。",
            "需要迁移时返回 action=migrate 所需参数，不在 adopt-existing 中隐式迁移。",
            "Agent Policy 缺失时，在写入受管区块前取得人工确认。",
        ),
        human_confirmation_points=(
            "确认现有 OUTPUT 与 repository 的绑定关系。",
            "需要安装或修复 Agent Policy 时确认 workspace_root 和受管文件范围。",
        ),
        requirements=_requirements("required", "required", "required", "conditional"),
        acceptance_summary_fields=(
            "fixed_source_commit",
            "knowledge_base_location",
            "human_entry",
            "coverage",
            "agent_policy",
            "sqlite_integrity",
            "brief_result",
            "maintenance_result",
        ),
        rollback=RollbackContract(
            "dependency",
            "接管本身不复制状态；若写入 Agent Policy，回滚依赖受管区块安装前备份。",
            mapping="external-dependency",
            dependency_zh="Agent Policy 受管文件的安装前字节备份",
        ),
    ),
    ActionContract(
        action="build-new",
        purpose_zh="从已经安装的 Skill 开始，为一个干净 Git 提交建立新知识库。",
        parameters=(
            _p("repository", "path", "具有提交的干净 Git 仓库。", required=True),
            _OUT,
            _p("question", "text", "建库后用于真实检索验证的问题。", required=True),
            _p("workspace_root", "path", "安装 Agent Policy 的工作区。", default="<path:repository父目录>"),
            _p("format", "enum", "输出投影格式。", default="markdown", choices=("markdown", "logseq-db", "both")),
            _p("scope", "enum", "构建覆盖范围。", default="entire-repository", choices=("entire-repository", "explicit-paths")),
            _p("scope_path", "path-list", "scope=explicit-paths 时使用的逗号分隔路径。", default="<paths:none>"),
            _p("pack_id", "id", "当前 review pack ID。", default="<id:命令返回的PACK_ID>"),
            _p("review_file", "path", "填写后的 review JSON。", default="<path:REVIEW.json>"),
            _CONFIRM("build-new"),
            _PYTHON,
            _CKB,
        ),
        execution_steps=(
            _s("git-source-check", "核对 repository 的 commit、tree 和干净状态。", "external-dependency"),
            _s(
                "doctor",
                "验证已经安装的 CKB 运行环境；不重复安装项目或 Skill。",
                "existing-command",
                "& {python} {ckb} doctor --json",
                required_for_audit=True,
                input_parameters=("python", "ckb"),
                result_statuses=("ready",),
            ),
            _s(
                "build-start",
                "建立固定源码快照并运行到第一个 Agent review 门。",
                "existing-command",
                "& {python} {ckb} run --repo {repository} --out {knowledge_base} --format {format}{scope_flags}",
                required_for_audit=True,
                input_parameters=("repository", "knowledge_base", "format", "scope", "scope_path"),
                allowed_exit_statuses=(0, 4),
                result_statuses=("initialized", "pending-agent-review", "ready-to-finalize", "complete"),
                output_mode="text-or-json",
            ),
            _s(
                "review-pack",
                "逐项重新打开源码范围，填写简体中文审阅并提交当前 review pack；对每个 pack 重复。",
                "existing-command",
                "& {python} {ckb} review-pack --out {knowledge_base} --pack {pack_id} --review {review_file}",
                required_for_audit=True,
                input_parameters=("knowledge_base", "pack_id", "review_file"),
                result_statuses=("passed", "next-review-pack", "ready-to-merge"),
                output_mode="text-or-json",
            ),
            _s(
                "build-resume",
                "在每次审阅后继续同一构建，直至 ready-to-finalize。",
                "existing-command",
                "& {python} {ckb} run --out {knowledge_base} --resume",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                allowed_exit_statuses=(0, 4),
                result_statuses=("pending-agent-review", "ready-to-finalize", "complete"),
                output_mode="text-or-json",
            ),
            _s(
                "finalize",
                "执行全部来源、中文、镜像、SQLite 和投影完成门。",
                "existing-command",
                "& {python} {ckb} finalize --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("complete", "passed"),
            ),
            _s(
                "agent-policy-install",
                "把现有 Agent Policy 受管区块安装到 workspace_root。",
                "existing-command",
                "& {python} {ckb} agent-policy install --out {knowledge_base} --workspace-root {workspace_root} --python {python} --ckb {ckb}",
                required_for_audit=True,
                input_parameters=("knowledge_base", "workspace_root", "python", "ckb"),
                result_statuses=("installed",),
            ),
            _s(
                "agent-policy-check",
                "独立核对 Agent Policy。",
                "existing-command",
                "& {python} {ckb} agent-policy check --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("passed",),
            ),
            _s(
                "brief",
                "对 question 执行真实 brief，打开 Agent pack 并按其来源回答。",
                "existing-command",
                "& {python} {ckb} brief --out {knowledge_base} {question} --budget 1800 --max-pages 8 --profile fast",
                required_for_audit=True,
                input_parameters=("knowledge_base", "question"),
                result_statuses=("passed",),
            ),
            _s(
                "maintain",
                "运行聚合维护门。",
                "existing-command",
                "& {python} {ckb} maintain --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("passed",),
            ),
        ),
        stop_conditions=(
            "repository 不是干净 Git commit、OUTPUT 与源码重叠或已存在未声明内容时停止。",
            "每次退出码 4 都只表示人工审阅检查点；不得作为构建完成。",
            "缺少源码审阅、finalize、真实 brief 或 maintain 结果时不得通过验收。",
            "本 action 从已安装 Skill 开始，出现 source、release_branch、project_root 或 skill_root 时拒绝重复安装职责。",
        ),
        human_confirmation_points=(
            "确认 repository、knowledge_base、format 和 scope。",
            "没有 Git 提交时，使用 --init-git 前单独确认创建仓库和首个提交。",
            "每个 review pack 都由 Agent 重新打开来源范围后提交人工审阅。",
            "安装 Agent Policy 前确认 workspace_root。",
        ),
        requirements=_requirements("required", "required", "required", "required"),
        acceptance_summary_fields=(
            "fixed_source_commit",
            "knowledge_base_location",
            "human_entry",
            "coverage",
            "pending_reviews",
            "sqlite_integrity",
            "mirror_result",
            "brief_result",
            "feedback_result",
            "gap_result",
            "maintenance_result",
        ),
        rollback=RollbackContract(
            "dependency",
            "新建 OUTPUT 的回滚必须只删除或恢复本 action 拥有的隔离目录和 Agent Policy 受管区块。",
            mapping="external-dependency",
            dependency_zh="OUTPUT 创建前目录状态与 Agent Policy 安装前字节备份",
        ),
    ),
    ActionContract(
        action="explain",
        purpose_zh="只使用已经存在且通过审计的知识库回答一个问题，不安装、不建库、不迁移。",
        parameters=(
            _OUT,
            _p("question", "text", "要回答的项目问题。", required=True),
            _p("repository", "path", "可选源码仓库，仅用于核对 pack 返回的精确范围。", default="<path:knowledge-base绑定仓库>"),
            _p("profile", "enum", "检索档位。", default="fast", choices=("fast", "precise")),
            _p("budget", "integer", "Agent pack token 预算。", default=1800),
            _p("max_pages", "integer", "首轮最多知识页数。", default=8),
            _p("scope", "enum", "只读解释边界。", default="read-only", choices=("read-only",)),
            _PYTHON,
            _CKB,
        ),
        execution_steps=(
            _s(
                "brief",
                "执行 brief 并打开其返回的 Markdown Agent pack；保留 JSON record 作为来源记录。",
                "existing-command",
                "& {python} {ckb} brief --out {knowledge_base} {question} --budget {budget_raw} --max-pages {max_pages_raw} --profile {profile}",
                required_for_audit=True,
                input_parameters=("knowledge_base", "question", "budget", "max_pages", "profile"),
                result_statuses=("passed",),
            ),
            _s(
                "source-narrow-read",
                "只有 pack 请求 source read 或给出精确符号/范围时，使用 entity、neighbors、source 或 changes 窄读。",
                "existing-command",
                "& {python} {ckb} source --out {knowledge_base} '<selector:pack返回的符号>' --context-lines 3",
                input_parameters=("knowledge_base", "repository"),
                result_statuses=("ready", "passed"),
            ),
        ),
        stop_conditions=(
            "知识库不存在、未完成或固定源码不匹配时停止并返回 adopt-existing、build-new 或 migrate 的显式选择。",
            "pack 证据不足时列出待核验项，不把推断写成已确认事实。",
            "不得执行安装、建库、迁移或写入记录。",
        ),
        human_confirmation_points=(),
        requirements=_requirements("required", "required", "not-required", "not-required"),
        acceptance_summary_fields=(
            "answer",
            "fixed_source_commit",
            "agent_pack",
            "source_ranges",
            "confirmed_facts",
            "inferences",
            "pending_verification",
        ),
        rollback=RollbackContract("not-required", "只读解释不产生需要回滚的业务状态。"),
    ),
    ActionContract(
        action="record",
        purpose_zh="通过现有 record 命令写入一条有来源回链的简体中文工作记录。",
        parameters=(
            _OUT,
            _p("kind", "enum", "记录类型。", required=True, choices=("analysis", "change", "pitfall", "experiment", "session")),
            _p("title", "text", "记录标题。", required=True),
            _p("body", "path", "简体中文正文文件。", required=True),
            _p("pack", "path", "brief 返回的 JSON record 路径，不是 Markdown pack。", required=True),
            _p("question", "text", "生成来源 pack 的问题。", default="<text:与记录相同的检索问题>"),
            _p("append", "boolean", "是否按同标题追加。", default=False),
            _p("scope", "enum", "单条 record 边界。", default="single-record", choices=("single-record",)),
            _CONFIRM("record"),
            _PYTHON,
            _CKB,
        ),
        execution_steps=(
            _s(
                "brief",
                "先执行 brief，打开 Agent pack 并使用其 JSON record 路径。",
                "existing-command",
                "& {python} {ckb} brief --out {knowledge_base} {question} --budget 1800 --max-pages 8 --profile fast",
                required_for_audit=True,
                input_parameters=("knowledge_base", "question", "pack"),
                result_statuses=("passed",),
            ),
            _s(
                "record",
                "写入单条记录；正文和来源必须先人工审阅。",
                "existing-command",
                "& {python} {ckb} record --out {knowledge_base} --kind {kind} --title {title} --body {body} --from-pack {pack}{append_flag}",
                required_for_audit=True,
                input_parameters=("knowledge_base", "kind", "title", "body", "pack", "append"),
                result_statuses=("recorded", "appended", "passed", "ready"),
                output_mode="text-or-json",
            ),
            _s(
                "maintain",
                "核对 human/markdown 镜像、记录元数据和两个 SQLite。",
                "existing-command",
                "& {python} {ckb} maintain --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("passed",),
            ),
        ),
        stop_conditions=(
            "正文缺少简体中文、pack 不是 JSON record、来源回链不唯一或不匹配时停止。",
            "kind=change 时正文缺少修改内容、修改原因和验证结果时停止。",
            "未准备写入前基线与外部恢复步骤时，把 rollback 标为 dependency 并停止完成声明。",
        ),
        human_confirmation_points=("确认 kind、title、body、pack 和 append 后再写入。", "重新打开记录与镜像后确认正文和来源。"),
        requirements=_requirements("required", "required", "required", "required"),
        acceptance_summary_fields=(
            "record_path",
            "mirror_path",
            "source_pack",
            "record_kind",
            "record_title",
            "sqlite_result",
            "maintenance_result",
        ),
        rollback=RollbackContract(
            "dependency",
            "record 当前没有独立 rollback 命令；写入前必须保存受影响文件和逻辑 SQLite 基线。",
            mapping="external-dependency",
            dependency_zh="受影响文件字节基线、SQLite 逻辑基线和隔离恢复脚本",
        ),
    ),
    ActionContract(
        action="feedback",
        purpose_zh="通过现有 feedback 状态机创建或处理一条定位式人工反馈。",
        parameters=(
            _OUT,
            _p("operation", "enum", "反馈动作。", default="resolve", choices=("create", "resolve")),
            _p("feedback_id", "id", "resolve 使用的反馈 ID。", default="<id:FEEDBACK_ID>"),
            _p("target", "path", "create 使用的人类页面相对路径。", default="<path:pages/PAGE.md>"),
            _p("start_line", "integer", "create 使用的起始行。", default=1),
            _p("end_line", "integer", "create 使用的结束行。", default=1),
            _p("comment", "path", "create 使用的中文意见文件。", default="<path:COMMENT.md>"),
            _p("severity", "enum", "严重程度。", default="suggest", choices=("error", "warn", "suggest", "info")),
            _p("author", "text", "反馈提交者。", default="<text:AUTHOR>"),
            _p("source", "enum", "反馈入口。", default="manual", choices=("manual", "obsidian-plugin", "web-viewer")),
            _p("decision", "enum", "resolve 决议。", default="deferred", choices=("accepted", "partial", "rejected", "deferred")),
            _p("resolution", "path", "resolve 使用的中文说明文件。", default="<path:RESOLUTION.md>"),
            _p("applied_record", "path", "accepted/partial 的落实记录。", default="<path:none>"),
            _p("scope", "enum", "单条反馈边界。", default="single-feedback", choices=("single-feedback",)),
            _CONFIRM("feedback"),
            _PYTHON,
            _CKB,
        ),
        execution_steps=(
            _s(
                "feedback-list",
                "按固定优先级读取开放反馈。",
                "existing-command",
                "& {python} {ckb} feedback list --out {knowledge_base} --status open",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("ready",),
            ),
            _s(
                "feedback-locate",
                "处理前重新定位目标范围。",
                "existing-command",
                "& {python} {ckb} feedback locate --out {knowledge_base} --feedback {feedback_id}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("resolve",),
                input_parameters=("knowledge_base", "feedback_id"),
                result_statuses=("passed",),
            ),
            _s(
                "feedback-create",
                "创建一条反馈，不直接编辑生成器管理页面。",
                "existing-command",
                "& {python} {ckb} feedback create --out {knowledge_base} --target {target} --start-line {start_line_raw} --end-line {end_line_raw} --comment {comment} --severity {severity} --author {author} --source {source}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("create",),
                input_parameters=("knowledge_base", "target", "start_line", "end_line", "comment", "severity", "author", "source"),
                result_statuses=("open", "ready"),
            ),
            _s(
                "feedback-resolve",
                "依据人工决议归档或保留反馈；accepted/partial 必须给出 applied_record。",
                "existing-command",
                "& {python} {ckb} feedback resolve --out {knowledge_base} --feedback {feedback_id} --decision {decision} --resolution {resolution}{applied_record_flag}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("resolve",),
                input_parameters=("knowledge_base", "feedback_id", "decision", "resolution", "applied_record"),
                result_statuses=("ready", "resolved", "deferred"),
                output_mode="text-or-json",
            ),
            _s(
                "feedback-audit",
                "核对定位、镜像和决议记录。",
                "existing-command",
                "& {python} {ckb} feedback audit --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("passed",),
            ),
            _s(
                "maintain",
                "运行聚合维护门。",
                "existing-command",
                "& {python} {ckb} maintain --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("passed",),
            ),
        ),
        stop_conditions=(
            "locate 返回 stale 时停止并请求重新确认目标。",
            "accepted/partial 没有知识库内已存在 applied_record 时停止。",
            "反馈记录只迁移不删除；不得把删除历史当作回滚。",
        ),
        human_confirmation_points=("create 前确认目标行范围和意见。", "resolve 前确认 decision、中文理由和 applied_record。"),
        requirements=_requirements("not-required", "required", "required", "required"),
        acceptance_summary_fields=(
            "feedback_id",
            "operation",
            "anchor_status",
            "decision",
            "applied_record",
            "feedback_audit",
            "maintenance_result",
        ),
        rollback=RollbackContract("not-required", "feedback 是保留历史的四态记录；通过新决议继续演进，不删除旧记录。"),
    ),
    ActionContract(
        action="reference",
        purpose_zh="导入一份本地 UTF-8 Markdown/TXT，完成逐行来源审阅、审计和维护。",
        parameters=(
            _OUT,
            _p("source", "path", "本地 Markdown/TXT 来源。", required=True),
            _p("title", "text", "参考资料标题。", required=True),
            _p("origin", "text", "明确来源。", required=True),
            _p("license", "text", "明确许可证或用户许可声明。", required=True),
            _p("author", "text", "作者或组织。", default="<text:none>"),
            _p("revision_of", "id", "可选上一修订 ID。", default="<id:none>"),
            _p("reference_id", "id", "ingest 返回的 reference ID。", default="<id:REFERENCE_ID>"),
            _p("review_file", "path", "填写后的 reference review JSON。", default="<path:REVIEW.json>"),
            _p("scope", "enum", "单一来源边界。", default="single-reference", choices=("single-reference",)),
            _CONFIRM("reference"),
            _PYTHON,
            _CKB,
        ),
        execution_steps=(
            _s(
                "reference-ingest",
                "归档原文字节并停在 Agent review 门。",
                "existing-command",
                "& {python} {ckb} reference ingest --out {knowledge_base} --source {source} --title {title} --origin {origin} --license {license}{author_flag}{revision_flag}",
                required_for_audit=True,
                input_parameters=("knowledge_base", "source", "title", "origin", "license", "author", "revision_of"),
                allowed_exit_statuses=(0, 4),
                result_statuses=("pending-agent-review", "ready"),
                output_mode="text-or-json",
            ),
            _s(
                "reference-review-template",
                "从现有状态机取得审阅模板。",
                "existing-command",
                "& {python} {ckb} reference review-template --out {knowledge_base} --reference {reference_id} --write {review_file}",
                required_for_audit=True,
                input_parameters=("knowledge_base", "reference_id", "review_file"),
                result_statuses=("written", "ready"),
                output_mode="text-or-json",
            ),
            _s(
                "reference-review",
                "重新打开归档原文，逐项核对行范围、source_text、中文主张与 evidence_note 后提交。",
                "existing-command",
                "& {python} {ckb} reference review --out {knowledge_base} --review {review_file}",
                required_for_audit=True,
                input_parameters=("knowledge_base", "review_file", "source"),
                result_statuses=("passed", "agent-reviewed", "ready"),
                output_mode="text-or-json",
            ),
            _s(
                "reference-audit",
                "核对原文、许可、摘要、镜像和 SQLite。",
                "existing-command",
                "& {python} {ckb} reference audit --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("passed",),
            ),
            _s(
                "maintain",
                "运行聚合维护门。",
                "existing-command",
                "& {python} {ckb} maintain --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("passed",),
            ),
        ),
        stop_conditions=(
            "来源不是本地 UTF-8 Markdown/TXT、超过 2 MiB 或许可证不明确时停止。",
            "未重新打开归档原文或 source_text 与行范围不一致时停止。",
            "退出码 4 只表示待审阅；reference audit 与 maintain 未通过时不得完成。",
        ),
        human_confirmation_points=("确认全文归档权限、title、origin 和 license。", "逐项核对归档原文和 review JSON 后提交。"),
        requirements=_requirements("not-required", "required", "required", "required"),
        acceptance_summary_fields=(
            "reference_id",
            "archived_source",
            "source_sha256",
            "review_record",
            "human_summary",
            "reference_audit",
            "maintenance_result",
        ),
        rollback=RollbackContract(
            "required",
            "使用现有 reference rollback 恢复该修订拥有的归档、manifest、页面和索引。",
            "& {python} {ckb} reference rollback --out {knowledge_base} --reference {reference_id}",
            "existing-command",
        ),
    ),
    ActionContract(
        action="gap",
        purpose_zh="依据知识库内持久证据创建或关闭一个机器层研究缺口。",
        parameters=(
            _OUT,
            _p("operation", "enum", "缺口动作。", default="create", choices=("create", "resolve")),
            _p("question", "text", "形成缺口证据的检索问题。", default="<text:待核验问题>"),
            _p("kind", "enum", "缺口类型。", default="insufficient-evidence", choices=("insufficient-evidence", "conflicting-sources", "deferred-feedback")),
            _p("summary", "path", "创建时使用的简体中文摘要。", default="<path:SUMMARY.md>"),
            _p("evidence", "path-list", "知识库内一至十二个持久证据路径，逗号分隔。", default="<paths:machine/agent-packs/PACK.json>"),
            _p("gap_id", "id", "resolve 使用的 gap ID。", default="<id:GAP_ID>"),
            _p("resolution", "path", "resolve 使用的中文闭环说明。", default="<path:RESOLUTION.md>"),
            _p("scope", "enum", "单一 gap 边界。", default="single-gap", choices=("single-gap",)),
            _CONFIRM("gap"),
            _PYTHON,
            _CKB,
        ),
        execution_steps=(
            _s(
                "brief",
                "用 brief 生成或重新核对缺口所依据的持久证据。",
                "existing-command",
                "& {python} {ckb} brief --out {knowledge_base} {question} --budget 1800 --max-pages 8 --profile fast",
                required_for_audit=True,
                input_parameters=("knowledge_base", "question", "evidence"),
                result_statuses=("passed",),
            ),
            _s(
                "gap-create",
                "创建 pending claim；不得把 gap 写成已审阅事实。",
                "existing-command",
                "& {python} {ckb} gaps create --out {knowledge_base} --kind {kind} --summary {summary} --evidence {evidence}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("create",),
                input_parameters=("knowledge_base", "kind", "summary", "evidence"),
                result_statuses=("open", "deferred", "ready"),
                output_mode="text-or-json",
            ),
            _s(
                "gap-resolve",
                "仅以新的闭环证据关闭缺口。",
                "existing-command",
                "& {python} {ckb} gaps resolve --out {knowledge_base} --gap {gap_id} --resolution {resolution} --evidence {evidence}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("resolve",),
                input_parameters=("knowledge_base", "gap_id", "resolution", "evidence"),
                result_statuses=("resolved", "ready"),
                output_mode="text-or-json",
            ),
            _s(
                "gap-audit",
                "核对 schema、证据边界、索引和零页面配额。",
                "existing-command",
                "& {python} {ckb} gaps audit --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("passed",),
            ),
            _s(
                "maintain",
                "运行聚合维护门。",
                "existing-command",
                "& {python} {ckb} maintain --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("passed",),
            ),
        ),
        stop_conditions=(
            "evidence 不在 OUTPUT 内、不是持久文件或包含未经核验的对话正文时停止。",
            "resolve 没有中文闭环说明和新证据时停止。",
            "gap 记录保留历史且没有 delete/rollback 命令；不得通过删除掩盖缺口。",
        ),
        human_confirmation_points=("确认 gap 只表示待验证主张。", "resolve 前确认闭环证据足以支持关闭。"),
        requirements=_requirements("required", "required", "required", "required"),
        acceptance_summary_fields=(
            "gap_id",
            "operation",
            "gap_status",
            "evidence_paths",
            "gap_audit",
            "maintenance_result",
        ),
        rollback=RollbackContract("not-required", "gap 是保留历史的 open/deferred/resolved 状态记录；没有删除式回滚。"),
    ),
    ActionContract(
        action="maintain",
        purpose_zh="运行现有聚合维护门并返回每项字面结果，不把命令启动当作通过。",
        parameters=(
            _OUT,
            _p("scope", "enum", "单一 OUTPUT 维护边界。", default="single-output", choices=("single-output",)),
            _CONFIRM("maintain"),
            _PYTHON,
            _CKB,
        ),
        execution_steps=(
            _s(
                "maintain",
                "执行反馈、Agent Policy、记录、参考资料、缺口、操作日志、可读性、机器库和索引聚合门。",
                "existing-command",
                "& {python} {ckb} maintain --out {knowledge_base}",
                required_for_audit=True,
                input_parameters=("knowledge_base",),
                result_statuses=("passed",),
            ),
        ),
        stop_conditions=("status 不是 passed 或 failed_checks 非空时停止完成声明并返回原始失败项。",),
        human_confirmation_points=("确认只维护指定 knowledge_base，不扫描或修改其他 OUTPUT。",),
        requirements=_requirements("not-required", "not-required", "required", "not-required"),
        acceptance_summary_fields=("maintenance_result", "failed_checks", "sqlite_integrity", "mirror_result", "agent_policy_result"),
        rollback=RollbackContract("not-required", "maintain 是现有聚合审计入口；本 action 不引入另一套状态或回滚。"),
    ),
    ActionContract(
        action="migrate",
        purpose_zh="把旧完整知识库迁移到新干净 Git commit 的隔离 staging OUTPUT。",
        parameters=(
            _p("from_out", "path", "已通过全局审计的旧 OUTPUT。", required=True),
            _p("repository", "path", "目标新 commit 的干净 Git 仓库。", required=True),
            _p("staging_out", "path", "与源码和正式 OUTPUT 分离的暂存目录。", required=True),
            _p("format", "enum", "可选投影格式覆盖。", default="markdown", choices=("markdown", "logseq-db", "both")),
            _p("pack_id", "id", "当前 delta review pack。", default="<id:DELTA_PACK>"),
            _p("review_file", "path", "填写后的 delta review JSON。", default="<path:REVIEW.json>"),
            _p("scope", "enum", "只写隔离 staging。", default="isolated-staging", choices=("isolated-staging",)),
            _CONFIRM("migrate"),
            _PYTHON,
            _CKB,
        ),
        execution_steps=(
            _s("migration-source-check", "核对旧 OUTPUT 完成标记、目标 commit、tree、clean 和目录不重叠。", "external-dependency"),
            _s(
                "migrate-start",
                "启动单库增量迁移并写入 staging。",
                "existing-command",
                "& {python} {ckb} migrate start --from-out {from_out} --repo {repository} --out {staging_out} --format {format}",
                required_for_audit=True,
                input_parameters=("from_out", "repository", "staging_out", "format"),
                allowed_exit_statuses=(0, 4),
                result_statuses=("pending-agent-review", "ready-to-finalize"),
                output_mode="text-or-json",
            ),
            _s(
                "migrate-status",
                "读取迁移计划、复用和 delta review 状态。",
                "existing-command",
                "& {python} {ckb} migrate status --out {staging_out}",
                required_for_audit=True,
                input_parameters=("staging_out",),
                allowed_exit_statuses=(0, 4),
                result_statuses=("pending-agent-review", "ready-to-finalize", "passed"),
            ),
            _s(
                "review-pack",
                "重新打开 delta 来源范围并提交人工审阅。",
                "existing-command",
                "& {python} {ckb} review-pack --out {staging_out} --pack {pack_id} --review {review_file}",
                required_for_audit=True,
                input_parameters=("staging_out", "pack_id", "review_file"),
                result_statuses=("passed", "next-review-pack", "ready-to-merge"),
                output_mode="text-or-json",
            ),
            _s(
                "merge-staging",
                "在 staging 内合并审阅批次，不切换正式目录。",
                "existing-command",
                "& {python} {ckb} merge --out {staging_out}",
                required_for_audit=True,
                input_parameters=("staging_out",),
                result_statuses=("passed", "ready-to-finalize"),
                output_mode="text-or-json",
            ),
            _s(
                "migrate-audit",
                "执行增量迁移审计。",
                "existing-command",
                "& {python} {ckb} migrate audit --out {staging_out}",
                required_for_audit=True,
                input_parameters=("staging_out",),
                result_statuses=("passed",),
            ),
            _s(
                "finalize",
                "在 staging 执行完整当前版本完成门。",
                "existing-command",
                "& {python} {ckb} finalize --out {staging_out}",
                required_for_audit=True,
                input_parameters=("staging_out",),
                result_statuses=("complete", "passed"),
            ),
            _s(
                "maintain",
                "在 staging 运行聚合维护门。",
                "existing-command",
                "& {python} {ckb} maintain --out {staging_out}",
                required_for_audit=True,
                input_parameters=("staging_out",),
                result_statuses=("passed",),
            ),
        ),
        stop_conditions=(
            "旧 OUTPUT 未完成、目标仓库不干净、目录重叠或 staging 已含未声明内容时停止。",
            "delta review 未完成、migrate audit/finalize/maintain 未通过时停止。",
            "本 action 不执行正式目录切换；切换和恢复旧目录名需另行人工确认。",
        ),
        human_confirmation_points=("确认 from_out、目标 commit、staging_out 和 format。", "逐项审阅 delta pack。", "任何正式 cutover 前另行确认备份名和 Hook 注册恢复步骤。"),
        requirements=_requirements("not-required", "required", "required", "required"),
        acceptance_summary_fields=(
            "old_source_commit",
            "new_source_commit",
            "staging_output",
            "reuse_counts",
            "delta_review_counts",
            "migration_audit",
            "finalize_result",
            "maintenance_result",
        ),
        rollback=RollbackContract(
            "dependency",
            "单库 migrate 只生成 staging；正式切换回滚依赖同卷旧目录备份和旧 Hook 注册项。",
            mapping="external-dependency",
            dependency_zh="正式 OUTPUT 目录备份、同卷改名计划和 Hook 注册恢复记录",
        ),
    ),
    ActionContract(
        action="template",
        purpose_zh="使用现有 template proposal 状态机管理 V3 章节合同扩展，并使用 page-author 分离 human_summary 与 machine_evidence_refs，执行 init/inspect/render/validate/package；package 只写隔离 staging。",
        parameters=(
            _OUT,
            _p(
                "operation",
                "enum",
                "现有 template 或 page-author CLI 动作。",
                default="list",
                choices=(
                    "list", "show", "init", "validate", "propose", "audit", "rollback",
                    "page-init", "page-inspect", "page-render", "page-validate", "page-package",
                ),
            ),
            _p("template_status", "enum", "list 使用的状态过滤。", default="all", choices=("all", "builtin", "pending", "approved", "rejected", "superseded")),
            _p("template_name", "text", "init 创建 skeleton 时使用的模板名。", default="output-local-template"),
            _p("proposal_file", "path", "init 的写入目标或 validate/propose 的 proposal JSON。", default="<path:PROPOSAL.json>"),
            _p("proposal_id", "id", "show/audit/rollback 使用的 proposal ID。", default="<id:TEMPLATE_PROPOSAL_ID>"),
            _p("decision", "enum", "audit 的人类决议。", default="return", choices=("approve", "reject", "return")),
            _p("reviewer_kind", "enum", "audit/rollback 的审阅者类型，固定为 human。", default="human", choices=("human",)),
            _p("reviewer_id", "text", "audit/rollback 的明确人类审阅者 ID。", default="<text:HUMAN_REVIEWER>"),
            _p("conclusion", "text", "audit 的人类结论；rollback 时作为撤销理由。", default="<text:HUMAN_CONCLUSION>"),
            _p("version", "semver", "audit/rollback 前从 proposal/show 核对的版本。", default="<semver:PROPOSAL_VERSION>"),
            _p("content_hash", "sha256", "audit/rollback 前从 proposal/show 核对的小写 SHA-256。", default="<sha256:PROPOSAL_CONTENT_HASH>"),
            _p(
                "human_confirmation",
                "confirmation",
                "audit/rollback 的显式人类确认；其他 operation 固定为 none。",
                default="none",
                choices=("none", "template-audit", "template-rollback", "page-package"),
            ),
            _p("page_type", "text", "page-author 使用的人类页面类型。", default="change"),
            _p("page_mode", "enum", "page-author 编写模式。", default="new", choices=("new", "supplement", "revise")),
            _p("authoring_input", "path", "page-render/page-validate/page-package 使用的 JSON 输入。", default="<path:PAGE_AUTHOR_INPUT.json>"),
            _p("page_source", "path", "page-inspect 只读打开的现有草稿或页面。", default="<path:SOURCE.md>"),
            _p("workspace_root", "path", "page-author 输入、来源和 staging 的固定工作区根。", default="<path:WORKSPACE_ROOT>"),
            _p("source_sha256", "sha256", "page-inspect 的可选来源 SHA-256。", default="<sha256:none>"),
            _p("staging", "path", "page-package 使用的新 staging 目录；不得进入受管投影。", default="<path:staging/page-author-package>"),
            _p("contract_version", "semver", "page-author 使用的人类页面合同版本；V3 固定为 3.0.0。", default="3.0.0"),
            _p("schema_version", "integer", "page-author 使用的人类页面 schema 版本；V3 固定为 3。", default=3),
            _p("scope", "enum", "只读 builtin registry 与 output-local proposal store 边界。", default="output-local-template-store", choices=("output-local-template-store",)),
            _PYTHON,
            _CKB,
        ),
        execution_steps=(
            _s(
                "template-list",
                "列出 builtin 和 output-local templates，不改变状态。",
                "existing-command",
                "& {python} {ckb} template list --out {knowledge_base} --status {template_status}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("list",),
                input_parameters=("knowledge_base", "operation", "template_status"),
                result_statuses=("ready",),
            ),
            _s(
                "template-show",
                "读取一个 builtin 或 output-local template 及完整历史。",
                "existing-command",
                "& {python} {ckb} template show --out {knowledge_base} --template {proposal_id}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("show",),
                input_parameters=("knowledge_base", "operation", "proposal_id"),
                result_statuses=("ready",),
            ),
            _s(
                "template-init",
                "写出 target-pinned proposal skeleton；此步骤不创建 proposal store。",
                "existing-command",
                "& {python} {ckb} template init --out {knowledge_base} --write {proposal_file} --name {template_name}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("init",),
                input_parameters=("knowledge_base", "operation", "proposal_file", "template_name"),
                result_statuses=("written",),
            ),
            _s(
                "template-validate",
                "离线验证 proposal JSON、目标 registry、版本和内容哈希；writes 必须为 0。",
                "existing-command",
                "& {python} {ckb} template validate --out {knowledge_base} --proposal {proposal_file}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("validate",),
                input_parameters=("knowledge_base", "operation", "proposal_file"),
                result_statuses=("passed",),
            ),
            _s(
                "template-propose",
                "提交 proposal 到 output-local store；Agent 或 human 提交都只能得到 pending，不能在此步骤启用内容。",
                "existing-command",
                "& {python} {ckb} template propose --out {knowledge_base} --proposal {proposal_file}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("propose",),
                input_parameters=("knowledge_base", "operation", "proposal_file"),
                result_statuses=("pending",),
            ),
            _s(
                "template-review-show",
                "在 audit/rollback 前重新读取 proposal、version、content_hash、当前状态和历史。",
                "existing-command",
                "& {python} {ckb} template show --out {knowledge_base} --template {proposal_id}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("audit", "rollback"),
                input_parameters=("knowledge_base", "operation", "proposal_id", "version", "content_hash"),
                result_statuses=("ready",),
            ),
            _s(
                "template-audit",
                "仅以明确人类审阅者、结论、version、content hash 和确认参数记录 approve/reject/return。",
                "existing-command",
                "& {python} {ckb} template audit --out {knowledge_base} --proposal {proposal_id} --decision {decision} --reviewer-kind {reviewer_kind} --reviewer-id {reviewer_id} --conclusion {conclusion} --version {version} --expected-content-hash {content_hash}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("audit",),
                input_parameters=("knowledge_base", "operation", "proposal_id", "decision", "reviewer_kind", "reviewer_id", "conclusion", "version", "content_hash", "human_confirmation"),
                result_statuses=("approved", "rejected", "returned"),
            ),
            _s(
                "template-rollback",
                "仅由明确人类审阅者撤销一个 active approved extension，并保留 proposal/audit/rollback 历史。",
                "existing-command",
                "& {python} {ckb} template rollback --out {knowledge_base} --proposal {proposal_id} --reviewer-kind {reviewer_kind} --reviewer-id {reviewer_id} --reason {conclusion} --expected-content-hash {content_hash}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("rollback",),
                input_parameters=("knowledge_base", "operation", "proposal_id", "reviewer_kind", "reviewer_id", "conclusion", "version", "content_hash", "human_confirmation"),
                result_statuses=("rolled-back",),
            ),
            _s(
                "page-author-init",
                "读取冻结 V3 页面合同，返回指定 page_type/mode 的最小类型化字段和每节必填、允许、禁止、预算、来源、时效、披露、空值约束，不写文件。",
                "existing-command",
                "& {python} {ckb} page-author init --page-type {page_type} --mode {page_mode} --contract-version {contract_version} --schema-version {schema_version_raw}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("page-init",),
                input_parameters=("operation", "page_type", "page_mode", "contract_version", "schema_version"),
                result_statuses=("ready",),
            ),
            _s(
                "page-author-inspect",
                "只读检查 supplement/revise 来源、SHA-256、现有章节和冲突，不直接编辑受管页面。",
                "existing-command",
                "& {python} {ckb} page-author inspect --page-type {page_type} --mode {page_mode} --source {page_source} --workspace-root {workspace_root}{source_sha256_flag} --contract-version {contract_version} --schema-version {schema_version_raw}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("page-inspect",),
                input_parameters=("operation", "page_type", "page_mode", "page_source", "workspace_root", "source_sha256", "contract_version", "schema_version"),
                result_statuses=("ready",),
            ),
            _s(
                "page-author-render",
                "从类型化 JSON 只渲染各节 human_summary，machine_evidence_refs 保持在结构化输入中；随后立即运行页面合同验证，不写受管投影。",
                "existing-command",
                "& {python} {ckb} page-author render --input {authoring_input} --workspace-root {workspace_root}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("page-render",),
                input_parameters=("operation", "authoring_input", "workspace_root"),
                result_statuses=("ready",),
            ),
            _s(
                "page-author-validate",
                "确定性验证候选 Markdown 的结构、章节预算、链接、当前事实、来源、L1-L3 披露和适用边界，并拒绝 L4 证据泄漏。",
                "existing-command",
                "& {python} {ckb} page-author validate --input {authoring_input}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("page-validate",),
                input_parameters=("operation", "authoring_input"),
                result_statuses=("passed",),
            ),
            _s(
                "page-author-package",
                "只把已验证 body.md、machine-only manifest.json 和文件型 evidence 副本写入新的 staging 目录；manifest 将文件 target 规范化为 manifest-parent 相对路径，URI target 保持原值，再返回正式 next_entry。",
                "existing-command",
                "& {python} {ckb} page-author package --input {authoring_input} --workspace-root {workspace_root} --staging {staging}",
                required_for_audit=True,
                when_parameter="operation",
                when_values=("page-package",),
                input_parameters=("operation", "authoring_input", "workspace_root", "staging", "human_confirmation"),
                result_statuses=("ready",),
            ),
        ),
        stop_conditions=(
            "propose 字面结果不是 status=pending 时停止；Agent propose 不得自动进入 audit。",
            "audit/rollback 缺少 human_confirmation、proposal_id、version、content_hash、human reviewer 或 conclusion 时拒绝。",
            "audit 前 proposal 不是 pending、version/content hash 漂移或 reviewer_kind 不是 human 时停止。",
            "rollback 前 proposal 不是 active approved extension、version/content hash 漂移或 reviewer_kind 不是 human 时停止。",
            "page-inspect 使用 mode=new 时拒绝；new 直接从 page-init 开始。",
            "page-package 缺少 human_confirmation=page-package，或 staging 位于 human/markdown/machine/SQLite、已存在或超出 workspace_root 时拒绝。",
            "page-package 只返回 body、manifest、package-owned evidence、section_evidence 哈希和正式 next_entry；整包移动后每个文件 target 仍必须可从 manifest.parent 重开并核验。",
            "contract_version=1.0.0 或 schema_version=1 的旧输入必须显式按 V3 章节重写，不得静默套用新标题。",
        ),
        human_confirmation_points=(
            "operation=audit 时人类逐项核对 proposal/version/content_hash，填写 reviewer、conclusion，并设置 human_confirmation=template-audit。",
            "operation=rollback 时人类核对 active approval 和相同 content_hash，填写 reviewer、conclusion，并设置 human_confirmation=template-rollback。",
            "operation=page-package 时人类确认候选 validation 已通过和 staging 边界，并设置 human_confirmation=page-package。",
        ),
        requirements=_requirements("not-required", "conditional", "not-required", "conditional"),
        acceptance_summary_fields=(
            "operation",
            "proposal_id",
            "version",
            "content_hash",
            "proposal_status",
            "active",
            "reviewer",
            "conclusion",
            "history_result",
            "page_authoring_status",
            "authoring_operation",
            "page_type",
            "page_mode",
            "candidate_sha256",
            "section_contract_result",
            "disclosure_result",
            "machine_evidence_separation",
            "section_evidence_sha256",
            "staging_path",
            "next_entry",
            "direct_projection_write",
        ),
        rollback=RollbackContract(
            "conditional",
            "audit approve 后使用现有 template rollback；page-package 只拥有新 staging 目录及其中的 body.md、manifest.json 和 evidence 副本，回滚删除该目录而不删除 workspace_root 原文件；其他 operation 不需要回滚。",
            "& {python} {ckb} template rollback --out {knowledge_base} --proposal {proposal_id} --reviewer-kind {reviewer_kind} --reviewer-id {reviewer_id} --reason {conclusion} --expected-content-hash {content_hash}",
        ),
        dependencies=(),
    ),
)


_ACTION_BY_NAME = {contract.action: contract for contract in _ACTIONS}


def _check_registry() -> None:
    if len(_ACTIONS) != len(_ACTION_BY_NAME):
        raise RuntimeError("human maintenance prompt registry contains duplicate actions")
    for contract in _ACTIONS:
        if not _ACTION_NAME.fullmatch(contract.action):
            raise RuntimeError(f"invalid human maintenance action: {contract.action}")
        names = [parameter.name for parameter in contract.parameters]
        if len(names) != len(set(names)):
            raise RuntimeError(f"duplicate parameters in action: {contract.action}")
        if any(not _PARAMETER_NAME.fullmatch(name) for name in names):
            raise RuntimeError(f"invalid parameter name in action: {contract.action}")
        if contract.rollback.requirement not in _REQUIREMENT_STATES:
            raise RuntimeError(f"invalid rollback requirement in action: {contract.action}")
        if contract.rollback.mapping not in _MAPPINGS:
            raise RuntimeError(f"invalid rollback mapping in action: {contract.action}")
        requirement_names = [name for name, _state in contract.requirements]
        if requirement_names != ["brief", "source", "maintain", "human_review"]:
            raise RuntimeError(f"invalid requirement order in action: {contract.action}")
        if any(state not in _REQUIREMENT_STATES for _name, state in contract.requirements):
            raise RuntimeError(f"invalid requirement state in action: {contract.action}")
        step_ids = [step.step_id for step in contract.execution_steps]
        if len(step_ids) != len(set(step_ids)):
            raise RuntimeError(f"duplicate step ids in action: {contract.action}")
        for step in contract.execution_steps:
            if step.mapping not in _MAPPINGS:
                raise RuntimeError(f"invalid mapping in action: {contract.action}/{step.step_id}")
            if step.required_for_audit and (step.mapping != "existing-command" or not step.command_template):
                raise RuntimeError(f"invalid audited step in action: {contract.action}/{step.step_id}")
            if step.when_parameter and step.when_parameter not in names:
                raise RuntimeError(f"unknown condition parameter in action: {contract.action}/{step.step_id}")
            if any(name not in names for name in step.input_parameters):
                raise RuntimeError(f"unknown step input in action: {contract.action}/{step.step_id}")


_check_registry()


def list_human_maintenance_actions() -> tuple[str, ...]:
    return tuple(contract.action for contract in _ACTIONS)


def get_human_maintenance_action(action: str) -> ActionContract:
    normalized = str(action).strip()
    contract = _ACTION_BY_NAME.get(normalized)
    if contract is None:
        raise CkbError(f"未知 human maintenance action：{action}；可用 action：{list(list_human_maintenance_actions())}")
    return contract


def _parameter_document(parameter: ParameterSpec) -> dict[str, Any]:
    return {
        "name": parameter.name,
        "type": parameter.type_name,
        "description_zh": parameter.description_zh,
        "required": parameter.required,
        "default": parameter.default,
        "choices": list(parameter.choices),
    }


def _step_document(step: CommandStep) -> dict[str, Any]:
    return {
        "step_id": step.step_id,
        "instruction_zh": step.instruction_zh,
        "mapping": step.mapping,
        "command_template": step.command_template,
        "required_for_audit": step.required_for_audit,
        "when": {step.when_parameter: list(step.when_values)} if step.when_parameter else None,
        "input_parameters": list(step.input_parameters),
        "allowed_exit_statuses": list(step.allowed_exit_statuses),
        "result_statuses": list(step.result_statuses),
        "output_mode": step.output_mode,
    }


def human_maintenance_action_document(contract: ActionContract | str) -> dict[str, Any]:
    if isinstance(contract, str):
        contract = get_human_maintenance_action(contract)
    return {
        "action": contract.action,
        "purpose_zh": contract.purpose_zh,
        "parameters": [_parameter_document(parameter) for parameter in contract.parameters],
        "execution_steps": [_step_document(step) for step in contract.execution_steps],
        "stop_conditions": list(contract.stop_conditions),
        "human_confirmation_points": list(contract.human_confirmation_points),
        "requirements": {name: state for name, state in contract.requirements},
        "acceptance_summary_fields": list(contract.acceptance_summary_fields),
        "rollback": {
            "requirement": contract.rollback.requirement,
            "description_zh": contract.rollback.description_zh,
            "command_template": contract.rollback.command_template,
            "mapping": contract.rollback.mapping,
            "dependency_zh": contract.rollback.dependency_zh,
        },
        "dependencies": list(contract.dependencies),
    }


def human_maintenance_registry_document() -> dict[str, Any]:
    return {
        "schema_version": HUMAN_MAINTENANCE_PROMPT_SCHEMA_VERSION,
        "contract_version": HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION,
        "registry_id": HUMAN_MAINTENANCE_PROMPT_REGISTRY_ID,
        "action_order": list(list_human_maintenance_actions()),
        "actions": [human_maintenance_action_document(contract) for contract in _ACTIONS],
    }


def serialize_human_maintenance_registry() -> str:
    return json.dumps(human_maintenance_registry_document(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def human_maintenance_registry_sha256() -> str:
    return hashlib.sha256(serialize_human_maintenance_registry().encode("utf-8")).hexdigest()


def _error(reason: str, message: str, **fields: Any) -> dict[str, Any]:
    return {"reason": reason, "message": message, **fields}


def _parse_parameter_items(items: Sequence[str]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    parsed: dict[str, str] = {}
    errors: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        value = str(item)
        if "=" not in value:
            errors.append(_error("invalid-parameter-syntax", "参数必须使用 key=value。", index=index, value=value))
            continue
        key, raw = value.split("=", 1)
        key = key.strip()
        if not _PARAMETER_NAME.fullmatch(key):
            errors.append(_error("invalid-parameter-name", "参数名必须使用小写字母、数字或下划线。", index=index, parameter=key))
            continue
        if key in parsed:
            errors.append(_error("duplicate-parameter", "同一参数不得重复。", index=index, parameter=key))
            continue
        if not raw or len(raw) > 4096 or any(character in raw for character in ("\x00", "\r", "\n")):
            errors.append(_error("invalid-parameter-value", "参数值必须是单行非空文本且不超过 4096 字符。", index=index, parameter=key))
            continue
        parsed[key] = raw
    return parsed, errors


def _normalize_value(spec: ParameterSpec, raw: str | int | bool) -> tuple[str | int | bool | None, dict[str, Any] | None]:
    if spec.type_name == "integer":
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None, _error("invalid-parameter-type", "参数必须是整数。", parameter=spec.name, expected="integer")
        if value < 1 or value > 1_000_000:
            return None, _error("invalid-parameter-range", "整数参数超出 1..1000000。", parameter=spec.name)
        return value, None
    if spec.type_name == "boolean":
        if isinstance(raw, bool):
            return raw, None
        lowered = str(raw).strip().lower()
        if lowered not in {"true", "false"}:
            return None, _error("invalid-parameter-type", "布尔参数只能是 true 或 false。", parameter=spec.name, expected="boolean")
        return lowered == "true", None
    value = str(raw).strip()
    if not value:
        return None, _error("invalid-parameter-value", "参数值不得为空。", parameter=spec.name)
    if spec.choices and value not in spec.choices:
        reason = "conflicting-scope" if spec.name == "scope" else "invalid-parameter-choice"
        return None, _error(reason, "参数值不在固定选项中。", parameter=spec.name, value=value, choices=list(spec.choices))
    return value, None


def validate_human_maintenance_invocation(action: str, items: Sequence[str]) -> dict[str, Any]:
    parsed, errors = _parse_parameter_items(items)
    contract = _ACTION_BY_NAME.get(str(action).strip())
    if contract is None:
        errors.append(_error("unknown-action", "未知 human maintenance action。", action=action, available=list(list_human_maintenance_actions())))
        return {
            "schema_version": HUMAN_MAINTENANCE_PROMPT_SCHEMA_VERSION,
            "contract_version": HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION,
            "registry_sha256": human_maintenance_registry_sha256(),
            "action": str(action),
            "status": "failed",
            "parameters": {},
            "errors": errors,
        }

    specs = {parameter.name: parameter for parameter in contract.parameters}
    unknown = sorted(set(parsed) - set(specs))
    if action == "install-project" and set(parsed) & _BUILD_PARAMETERS:
        errors.append(_error("mixed-install-build-responsibility", "install-project 不接收业务建库或解释参数。", parameters=sorted(set(parsed) & _BUILD_PARAMETERS)))
    if action in {"adopt-existing", "build-new", "explain"} and set(parsed) & _INSTALL_PARAMETERS:
        errors.append(_error("mixed-install-build-responsibility", "建库、接管或解释 action 不接收项目安装参数。", parameters=sorted(set(parsed) & _INSTALL_PARAMETERS)))
    for name in unknown:
        errors.append(_error("unknown-parameter", "action 不接受此参数。", parameter=name, action=action))

    normalized: dict[str, str | int | bool] = {}
    for spec in contract.parameters:
        if spec.name in parsed:
            raw: str | int | bool = parsed[spec.name]
        elif spec.default is not None:
            raw = spec.default
        elif spec.required:
            reason = "missing-human-confirmation" if spec.name == "confirm" else "missing-required-parameter"
            errors.append(_error(reason, "缺少必填参数。", parameter=spec.name, action=action))
            continue
        else:
            continue
        value, value_error = _normalize_value(spec, raw)
        if value_error:
            errors.append(value_error)
        elif value is not None:
            normalized[spec.name] = value

    if action == "build-new" and normalized.get("scope") == "explicit-paths" and normalized.get("scope_path") == "<paths:none>":
        errors.append(_error("conflicting-scope", "scope=explicit-paths 时必须提供 scope_path。", parameter="scope_path"))
    if action == "feedback" and normalized.get("operation") == "resolve" and normalized.get("decision") in {"accepted", "partial"}:
        if normalized.get("applied_record") == "<path:none>":
            errors.append(_error("missing-applied-record", "accepted/partial 必须提供 applied_record。", parameter="applied_record"))
    if action == "reference" and str(normalized.get("license", "")).strip().casefold() in {"unknown", "none", "待定"}:
        errors.append(_error("invalid-license", "reference 必须提供明确许可证或用户许可声明。", parameter="license"))
    if action == "template":
        operation = normalized.get("operation")
        expected_confirmation = {
            "audit": "template-audit",
            "rollback": "template-rollback",
            "page-package": "page-package",
        }.get(str(operation), "none")
        if normalized.get("human_confirmation") != expected_confirmation:
            reason = "missing-human-confirmation" if expected_confirmation != "none" else "unexpected-human-confirmation"
            errors.append(
                _error(
                    reason,
                    "template audit/rollback 必须提供与 operation 一致的显式人类确认，其他 operation 固定为 none。",
                    parameter="human_confirmation",
                    expected=expected_confirmation,
                )
            )
        if operation in {"audit", "rollback"}:
            required_values = {
                "proposal_id": normalized.get("proposal_id"),
                "reviewer_id": normalized.get("reviewer_id"),
                "conclusion": normalized.get("conclusion"),
                "version": normalized.get("version"),
                "content_hash": normalized.get("content_hash"),
            }
            for name, value in required_values.items():
                if _is_placeholder(value):
                    errors.append(
                        _error(
                            "missing-human-review-field",
                            "template audit/rollback 不得保留人类审阅字段类型槽。",
                            parameter=name,
                            operation=operation,
                        )
                    )
            if not re.fullmatch(r"\d+\.\d+\.\d+", str(normalized.get("version", ""))):
                errors.append(_error("invalid-template-version", "template version 必须是 MAJOR.MINOR.PATCH。", parameter="version"))
            if not re.fullmatch(r"[0-9a-f]{64}", str(normalized.get("content_hash", ""))):
                errors.append(_error("invalid-template-content-hash", "template content_hash 必须是小写 SHA-256。", parameter="content_hash"))
        if operation == "page-inspect" and normalized.get("page_mode") == "new":
            errors.append(_error("invalid-page-author-mode", "page-inspect 只接受 supplement 或 revise。", parameter="page_mode"))
        if operation in {"page-init", "page-inspect"} and (
            normalized.get("contract_version") != "3.0.0" or normalized.get("schema_version") != 3
        ):
            errors.append(
                _error(
                    "page-author-v3-required",
                    "page-author 必须使用 contract_version=3.0.0 与 schema_version=3；旧输入需要显式重写。",
                    actual={
                        "contract_version": normalized.get("contract_version"),
                        "schema_version": normalized.get("schema_version"),
                    },
                )
            )
        if operation == "page-package":
            for name in ("authoring_input", "workspace_root", "staging"):
                if _is_placeholder(normalized.get(name)):
                    errors.append(
                        _error(
                            "missing-page-author-field",
                            "page-package 必须提供具体 input、workspace_root 和 staging。",
                            parameter=name,
                        )
                    )
            staging = str(normalized.get("staging", "")).replace("\\", "/").casefold()
            if any(part in {"human", "markdown", "machine"} for part in staging.split("/")) or staging.endswith((".sqlite", ".db")):
                errors.append(_error("managed-target-forbidden", "page-package staging 不得位于受管投影或 SQLite 路径。", parameter="staging"))

    return {
        "schema_version": HUMAN_MAINTENANCE_PROMPT_SCHEMA_VERSION,
        "contract_version": HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION,
        "registry_sha256": human_maintenance_registry_sha256(),
        "action": action,
        "status": "passed" if not errors else "failed",
        "parameters": normalized,
        "errors": errors,
    }


def _quote(value: Any) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _format_values(parameters: Mapping[str, Any]) -> dict[str, str]:
    values = {name: _quote(value) for name, value in parameters.items()}
    values.update({f"{name}_raw": str(value) for name, value in parameters.items()})
    values["append_flag"] = " --append" if parameters.get("append") is True else ""
    author = str(parameters.get("author", "<text:none>"))
    values["author_flag"] = "" if author == "<text:none>" else f" --author {_quote(author)}"
    revision = str(parameters.get("revision_of", "<id:none>"))
    values["revision_flag"] = "" if revision == "<id:none>" else f" --revision-of {_quote(revision)}"
    applied = str(parameters.get("applied_record", "<path:none>"))
    values["applied_record_flag"] = "" if applied == "<path:none>" else f" --applied-record {_quote(applied)}"
    context = str(parameters.get("context", "<path:none>"))
    values["context_flag"] = "" if context == "<path:none>" else f" --context {_quote(context)}"
    source_sha256 = str(parameters.get("source_sha256", "<sha256:none>"))
    values["source_sha256_flag"] = "" if source_sha256 == "<sha256:none>" else f" --expected-sha256 {_quote(source_sha256)}"
    scope = str(parameters.get("scope", ""))
    scope_path = str(parameters.get("scope_path", "<paths:none>"))
    values["scope_flags"] = "" if scope != "explicit-paths" else "".join(f" --scope-path {_quote(item.strip())}" for item in scope_path.split(",") if item.strip())
    return values


def active_command_steps(contract: ActionContract, parameters: Mapping[str, Any]) -> tuple[CommandStep, ...]:
    return tuple(
        step
        for step in contract.execution_steps
        if step.when_parameter is None or str(parameters.get(step.when_parameter)) in step.when_values
    )


def render_step_command(step: CommandStep, parameters: Mapping[str, Any]) -> str | None:
    if step.command_template is None:
        return None
    try:
        return step.command_template.format_map(_format_values(parameters)).strip()
    except KeyError as exc:
        raise CkbError(f"Prompt command template 缺少参数：step={step.step_id}, parameter={exc.args[0]}") from exc


def _effective_requirement_state(
    contract: ActionContract,
    requirement: str,
    declared_state: str,
    parameters: Mapping[str, Any],
) -> str:
    if contract.action != "template":
        return declared_state
    operation = str(parameters.get("operation"))
    if requirement == "source":
        return "required" if operation in {
            "validate", "propose", "audit", "rollback",
            "page-inspect", "page-render", "page-validate", "page-package",
        } else "not-required"
    if requirement == "human_review":
        return "required" if operation in {"audit", "rollback", "page-package"} else "not-required"
    return declared_state


def _effective_rollback_requirement(contract: ActionContract, parameters: Mapping[str, Any]) -> str:
    if contract.action == "template":
        if parameters.get("operation") == "page-package":
            return "dependency"
        return "required" if parameters.get("operation") == "audit" and parameters.get("decision") == "approve" else "not-required"
    return contract.rollback.requirement


def _effective_rollback_mapping_and_command(
    contract: ActionContract,
    parameters: Mapping[str, Any],
    requirement: str,
) -> tuple[str, str | None]:
    if contract.action == "template" and parameters.get("operation") == "page-package":
        return "external-dependency", None
    command = render_step_command(
        CommandStep("rollback", "", contract.rollback.mapping, contract.rollback.command_template), parameters
    ) if contract.rollback.command_template and requirement in {"required", "dependency"} else None
    return contract.rollback.mapping, command


def _acceptance_template(contract: ActionContract, parameters: Mapping[str, Any]) -> dict[str, Any]:
    command_items = []
    for step in active_command_steps(contract, parameters):
        if step.mapping == "existing-command" and step.required_for_audit:
            command_items.append(
                {
                    "step_id": step.step_id,
                    "command": render_step_command(step, parameters),
                    "inputs": {name: parameters[name] for name in step.input_parameters if name in parameters},
                    "literal_output": "<literal-output>",
                    "exit_status": "<integer>",
                }
            )
    requirement_items = {}
    for name, declared_state in contract.requirements:
        state = _effective_requirement_state(contract, name, declared_state, parameters)
        expected = "passed" if state == "required" else "not-applicable" if state == "conditional" else state
        requirement_items[name] = {"status": expected, "evidence": ["<evidence>"] if state in {"required", "conditional"} else []}
    rollback_requirement = _effective_rollback_requirement(contract, parameters)
    rollback_mapping, rollback_command = _effective_rollback_mapping_and_command(
        contract, parameters, rollback_requirement
    )
    rollback_status = {
        "required": "ready",
        "dependency": "dependency-ready",
        "not-required": "not-required",
        "conditional": "not-applicable",
    }[rollback_requirement]
    return {
        "schema_version": HUMAN_MAINTENANCE_PROMPT_SCHEMA_VERSION,
        "contract_version": HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION,
        "registry_sha256": human_maintenance_registry_sha256(),
        "action": contract.action,
        "parameters": dict(parameters),
        "commands": command_items,
        "requirements": requirement_items,
        "acceptance": {field: f"<value:{field}>" for field in contract.acceptance_summary_fields},
        "rollback": {
            "status": rollback_status,
            "mapping": rollback_mapping,
            "command": rollback_command,
            "evidence": ["<rollback-evidence>"] if rollback_requirement in {"required", "dependency"} else [],
        },
    }


def human_maintenance_delivery_template(action: str, items: Sequence[str]) -> dict[str, Any]:
    """Return the same action-specific delivery shape embedded in a rendered Prompt."""

    validation = validate_human_maintenance_invocation(action, items)
    if validation["status"] != "passed":
        reasons = ", ".join(str(error["reason"]) for error in validation["errors"])
        raise CkbError(f"human maintenance delivery template 参数无效：{reasons}")
    return _acceptance_template(get_human_maintenance_action(action), validation["parameters"])


def _is_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped.startswith("<") and stripped.endswith(">")
    if isinstance(value, Mapping):
        return any(_is_placeholder(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_is_placeholder(item) for item in value)
    return False


def _summary_parameter_items(contract: ActionContract, value: Any) -> tuple[list[str], list[dict[str, Any]]]:
    if not isinstance(value, Mapping):
        return [], [_error("invalid-summary-parameters", "delivery parameters 必须是 JSON 对象。")]
    items: list[str] = []
    known = {parameter.name for parameter in contract.parameters}
    for name in sorted(set(str(key) for key in value) - known):
        items.append(f"{name}={value[name]}")
    for parameter in contract.parameters:
        if parameter.name not in value:
            continue
        raw = value[parameter.name]
        if isinstance(raw, bool):
            rendered = "true" if raw else "false"
        elif isinstance(raw, (str, int)) and not isinstance(raw, bool):
            rendered = str(raw)
        else:
            return [], [
                _error(
                    "invalid-summary-parameter-type",
                    "delivery parameter 只能是字符串、整数或布尔值。",
                    parameter=parameter.name,
                )
            ]
        items.append(f"{parameter.name}={rendered}")
    return items, []


def _literal_result_error(step: CommandStep, literal_output: Any) -> dict[str, Any] | None:
    if not isinstance(literal_output, str) or not literal_output.strip() or _is_placeholder(literal_output):
        return _error("missing-literal-output", "命令证据必须包含实际字面输出。", step_id=step.step_id)
    stripped = literal_output.strip()
    lowered = stripped.casefold()
    startup_markers = (
        "started",
        "running",
        "launched",
        "queued",
        "command started",
        "command accepted",
        "已启动",
        "开始执行",
        "正在执行",
    )
    if any(lowered == marker or lowered.startswith(marker + ":") for marker in startup_markers):
        return _error("command-start-is-not-completion", "命令启动提示不算完成结果。", step_id=step.step_id)
    parsed: Any = None
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        if step.output_mode == "json":
            return _error("command-output-not-json", "该步骤要求完整 JSON 字面输出。", step_id=step.step_id)
    if parsed is not None:
        if not isinstance(parsed, Mapping):
            return _error("command-output-not-object", "JSON 字面输出必须是对象。", step_id=step.step_id)
        status = parsed.get("status")
        if step.result_statuses and status not in step.result_statuses:
            return _error(
                "command-result-not-complete",
                "字面输出的 status 不是该步骤登记的完成状态。",
                step_id=step.step_id,
                status=status,
                allowed=list(step.result_statuses),
            )
        if isinstance(status, str) and status.casefold() in {"started", "running", "queued", "planned"} and status not in step.result_statuses:
            return _error("command-start-is-not-completion", "命令启动或计划状态不算完成结果。", step_id=step.step_id)
    elif step.output_mode == "text-or-json" and len(stripped) < 4:
        return _error("command-output-too-short", "文本字面输出不足以确认命令结果。", step_id=step.step_id)
    return None


def _expected_rollback(contract: ActionContract, parameters: Mapping[str, Any]) -> dict[str, Any]:
    return _acceptance_template(contract, parameters)["rollback"]


def audit_human_maintenance_delivery(action: str, summary: Any) -> dict[str, Any]:
    """Deterministically audit one Agent delivery summary without executing it."""

    errors: list[dict[str, Any]] = []
    contract = _ACTION_BY_NAME.get(str(action).strip())
    if contract is None:
        errors.append(_error("unknown-action", "未知 human maintenance action。", action=action))
        return {
            "schema_version": HUMAN_MAINTENANCE_PROMPT_SCHEMA_VERSION,
            "contract_version": HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION,
            "registry_sha256": human_maintenance_registry_sha256(),
            "action": str(action),
            "status": "failed",
            "errors": errors,
        }
    if not isinstance(summary, Mapping):
        errors.append(_error("invalid-delivery-summary", "交付摘要必须是 JSON 对象。"))
        return {
            "schema_version": HUMAN_MAINTENANCE_PROMPT_SCHEMA_VERSION,
            "contract_version": HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION,
            "registry_sha256": human_maintenance_registry_sha256(),
            "action": contract.action,
            "status": "failed",
            "errors": errors,
        }

    if summary.get("schema_version") != HUMAN_MAINTENANCE_PROMPT_SCHEMA_VERSION:
        errors.append(_error("schema-version-mismatch", "交付摘要 schema_version 不匹配。"))
    if summary.get("contract_version") != HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION:
        errors.append(_error("contract-version-mismatch", "交付摘要 contract_version 不匹配。"))
    if summary.get("registry_sha256") != human_maintenance_registry_sha256():
        errors.append(_error("registry-hash-mismatch", "交付摘要 registry_sha256 不匹配。"))
    if summary.get("action") != contract.action:
        errors.append(_error("delivery-action-mismatch", "交付摘要必须返回同一 action。", expected=contract.action, actual=summary.get("action")))

    parameter_items, parameter_errors = _summary_parameter_items(contract, summary.get("parameters"))
    errors.extend(parameter_errors)
    validation = validate_human_maintenance_invocation(contract.action, parameter_items) if not parameter_errors else None
    if validation is not None and validation["status"] != "passed":
        errors.append(
            _error(
                "invalid-summary-parameters",
                "交付摘要 parameters 未通过同一 action 参数校验。",
                validation_errors=validation["errors"],
            )
        )
    parameters: Mapping[str, Any] = validation["parameters"] if validation and validation["status"] == "passed" else {}
    if parameters and dict(summary.get("parameters", {})) != dict(parameters):
        errors.append(_error("noncanonical-summary-parameters", "交付摘要 parameters 必须等于 Prompt 的规范化参数。"))
    if parameters and _is_placeholder(parameters):
        errors.append(_error("unresolved-parameter-slot", "实际交付摘要不得保留类型槽。"))

    active_steps = {
        step.step_id: step
        for step in active_command_steps(contract, parameters)
        if step.mapping == "existing-command"
    } if parameters else {}
    required_steps = {step_id for step_id, step in active_steps.items() if step.required_for_audit}
    commands = summary.get("commands")
    command_by_id: dict[str, Mapping[str, Any]] = {}
    if not isinstance(commands, list):
        errors.append(_error("invalid-command-evidence", "commands 必须是数组。"))
    else:
        for index, item in enumerate(commands):
            if not isinstance(item, Mapping):
                errors.append(_error("invalid-command-evidence", "每项 command evidence 必须是对象。", index=index))
                continue
            step_id = item.get("step_id")
            if not isinstance(step_id, str):
                errors.append(_error("missing-command-step-id", "command evidence 缺少 step_id。", index=index))
                continue
            if step_id in command_by_id:
                errors.append(_error("duplicate-command-evidence", "同一 step_id 不得重复。", step_id=step_id))
                continue
            if step_id not in active_steps:
                errors.append(_error("unexpected-command-evidence", "command evidence 不属于当前 action/parameters。", step_id=step_id))
                continue
            command_by_id[step_id] = item
        for step_id in sorted(required_steps - set(command_by_id)):
            errors.append(_error("missing-command-evidence", "缺少必需命令证据。", step_id=step_id))

    for step_id, item in command_by_id.items():
        step = active_steps[step_id]
        expected_command = render_step_command(step, parameters)
        if item.get("command") != expected_command:
            errors.append(_error("command-mismatch", "实际 command 与 Prompt 登记命令不一致。", step_id=step_id, expected=expected_command))
        expected_inputs = {name: parameters[name] for name in step.input_parameters if name in parameters}
        if item.get("inputs") != expected_inputs or not isinstance(item.get("inputs"), Mapping):
            errors.append(_error("command-inputs-mismatch", "命令 inputs 必须等于登记的规范参数。", step_id=step_id, expected=expected_inputs))
        exit_status = item.get("exit_status")
        if isinstance(exit_status, bool) or not isinstance(exit_status, int):
            errors.append(_error("missing-exit-status", "命令证据必须包含整数 exit_status。", step_id=step_id))
        elif exit_status not in step.allowed_exit_statuses:
            errors.append(
                _error(
                    "unexpected-exit-status",
                    "命令退出状态不在该步骤登记范围。",
                    step_id=step_id,
                    actual=exit_status,
                    allowed=list(step.allowed_exit_statuses),
                )
            )
        output_error = _literal_result_error(step, item.get("literal_output"))
        if output_error:
            errors.append(output_error)

    requirements = summary.get("requirements")
    if not isinstance(requirements, Mapping):
        errors.append(_error("invalid-requirement-evidence", "requirements 必须是对象。"))
    else:
        expected_names = {name for name, _state in contract.requirements}
        if set(requirements) != expected_names:
            errors.append(_error("requirement-set-mismatch", "requirements 字段集合必须与 action contract 完全一致。", expected=sorted(expected_names)))
        for name, declared_state in contract.requirements:
            state = _effective_requirement_state(contract, name, declared_state, parameters)
            item = requirements.get(name)
            if not isinstance(item, Mapping):
                errors.append(_error("missing-requirement-evidence", "缺少 requirement evidence。", requirement=name))
                continue
            status = item.get("status")
            evidence = item.get("evidence")
            if not isinstance(evidence, list):
                errors.append(_error("invalid-requirement-evidence", "requirement evidence 必须是数组。", requirement=name))
                continue
            if state == "required" and (status != "passed" or not evidence or _is_placeholder(evidence)):
                errors.append(_error("required-gate-not-passed", "required gate 必须有 passed 状态和实际证据。", requirement=name))
            elif state == "conditional" and status not in {"passed", "not-applicable"}:
                errors.append(_error("conditional-gate-invalid", "conditional gate 只能是 passed 或 not-applicable。", requirement=name))
            elif state == "conditional" and status == "passed" and (not evidence or _is_placeholder(evidence)):
                errors.append(_error("conditional-gate-missing-evidence", "通过的 conditional gate 必须有实际证据。", requirement=name))
            elif state == "not-required" and (status != "not-required" or evidence):
                errors.append(_error("not-required-gate-mismatch", "not-required gate 不得伪造通过证据。", requirement=name))
            elif state == "dependency" and (status != "dependency-ready" or not evidence or _is_placeholder(evidence)):
                errors.append(_error("dependency-gate-not-ready", "dependency gate 必须有 dependency-ready 状态和实际证据。", requirement=name))

    acceptance = summary.get("acceptance")
    expected_fields = set(contract.acceptance_summary_fields)
    if not isinstance(acceptance, Mapping):
        errors.append(_error("invalid-acceptance-summary", "acceptance 必须是对象。"))
    else:
        if set(acceptance) != expected_fields:
            errors.append(_error("acceptance-field-mismatch", "acceptance 字段集合必须与 action contract 完全一致。", expected=sorted(expected_fields)))
        for field in contract.acceptance_summary_fields:
            value = acceptance.get(field)
            if value is None or value == "" or _is_placeholder(value):
                errors.append(_error("missing-acceptance-value", "acceptance 字段必须包含实际值。", field=field))

    rollback = summary.get("rollback")
    expected_rollback = _expected_rollback(contract, parameters) if parameters else None
    if not isinstance(rollback, Mapping):
        errors.append(_error("invalid-rollback-summary", "rollback 必须是对象。"))
    elif expected_rollback is not None:
        if rollback.get("status") != expected_rollback["status"]:
            errors.append(_error("rollback-status-mismatch", "rollback status 与 action contract 不一致。"))
        if rollback.get("mapping") != expected_rollback["mapping"]:
            errors.append(_error("rollback-mapping-mismatch", "rollback mapping 与 action contract 不一致。"))
        if rollback.get("command") != expected_rollback["command"]:
            errors.append(_error("rollback-command-mismatch", "rollback command 与 action contract 不一致。"))
        evidence = rollback.get("evidence")
        rollback_requirement = _effective_rollback_requirement(contract, parameters)
        if rollback_requirement in {"required", "dependency"}:
            if not isinstance(evidence, list) or not evidence or _is_placeholder(evidence):
                errors.append(_error("rollback-evidence-missing", "required/dependency rollback 必须有实际准备证据。"))
        elif evidence not in ([], None):
            errors.append(_error("unexpected-rollback-evidence", "not-required rollback 不得伪造执行证据。"))

    return {
        "schema_version": HUMAN_MAINTENANCE_PROMPT_SCHEMA_VERSION,
        "contract_version": HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION,
        "registry_sha256": human_maintenance_registry_sha256(),
        "action": contract.action,
        "status": "passed" if not errors else "failed",
        "checked_command_steps": sorted(command_by_id),
        "required_command_steps": sorted(required_steps),
        "errors": errors,
    }


def audit_human_maintenance_delivery_file(action: str, path: Path) -> dict[str, Any]:
    try:
        summary = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {
            "schema_version": HUMAN_MAINTENANCE_PROMPT_SCHEMA_VERSION,
            "contract_version": HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION,
            "registry_sha256": human_maintenance_registry_sha256(),
            "action": str(action),
            "status": "failed",
            "checked_command_steps": [],
            "required_command_steps": [],
            "errors": [_error("delivery-summary-read-failed", "无法读取结构化交付摘要。", detail=str(exc))],
        }
    return audit_human_maintenance_delivery(action, summary)


def render_human_maintenance_prompt(action: str, items: Sequence[str]) -> str:
    validation = validate_human_maintenance_invocation(action, items)
    if validation["status"] != "passed":
        reasons = ", ".join(str(error["reason"]) for error in validation["errors"])
        raise CkbError(f"human maintenance Prompt 参数无效：{reasons}")
    contract = get_human_maintenance_action(action)
    parameters = validation["parameters"]
    lines = [
        "# Code Knowledge Builder 人类维护 Prompt",
        "",
        f"action={contract.action}",
        f"contract_version={HUMAN_MAINTENANCE_PROMPT_CONTRACT_VERSION}",
        f"registry_sha256={human_maintenance_registry_sha256()}",
    ]
    for parameter in contract.parameters:
        if parameter.name in parameters:
            value = parameters[parameter.name]
            rendered = str(value).lower() if isinstance(value, bool) else str(value)
            lines.append(f"{parameter.name}={rendered}")
    lines.extend(
        [
            "",
            "请严格执行上面的单一 action。正文参数已经确定；带 `<type:...>` 的值是显式类型槽，不得自行猜测。",
            "不要复制新的执行状态机，只调用下面登记的现有 CKB 能力；外部依赖或待完成功能必须保持原标记。",
            "",
            "## 目标",
            "",
            contract.purpose_zh,
            "",
            "## 固定执行顺序",
            "",
        ]
    )
    for index, step in enumerate(active_command_steps(contract, parameters), 1):
        if step.mapping == "existing-command":
            lines.append(f"{index}. {step.instruction_zh}")
            command = render_step_command(step, parameters)
            if command:
                lines.extend(["", "```powershell", command, "```", ""])
        elif step.mapping == "external-dependency":
            lines.append(f"{index}. 外部依赖：{step.instruction_zh} 当前 CKB 不拥有该执行状态；缺失时停止。")
        else:
            lines.append(f"{index}. 待完成能力：{step.instruction_zh} 不渲染为已支持命令。")
    lines.extend(["", "## 人工确认点", ""])
    if contract.human_confirmation_points:
        lines.extend(f"- {point}" for point in contract.human_confirmation_points)
    else:
        lines.append("- 本 action 是只读操作，不要求额外人工确认。")
    lines.extend(["", "## 停止条件", ""])
    lines.extend(f"- {condition}" for condition in contract.stop_conditions)
    lines.extend(["", "## 验收要求", ""])
    for name, declared_state in contract.requirements:
        state = _effective_requirement_state(contract, name, declared_state, parameters)
        lines.append(f"- {name}={state}")
    rollback_requirement = _effective_rollback_requirement(contract, parameters)
    lines.append(f"- rollback={rollback_requirement}：{contract.rollback.description_zh}")
    if contract.rollback.dependency_zh:
        lines.append(f"- rollback_dependency={contract.rollback.dependency_zh}")
    if contract.dependencies:
        lines.append("- dependencies=" + "；".join(contract.dependencies))
    lines.extend(
        [
            "",
            "## 结构化交付摘要",
            "",
            "完成后只把真实命令、实际输入、字面输出和退出状态填入下列同 action 摘要。命令已启动、计划执行或占位值均不算完成。",
            "",
            "```json",
            json.dumps(human_maintenance_delivery_template(action, items), ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)
