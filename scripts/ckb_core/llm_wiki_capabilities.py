"""Bounded LLM Wiki capability matrix, compact reading entry, and maintenance gate."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .common import CkbError, json_load, json_write, utc_now


STATUS_ABSORBED = "已吸收"
STATUS_CANDIDATE = "待吸收"
STATUS_EXCLUDED = "明确排除"
STATUS_BENCHMARK = "需要 benchmark"
CAPABILITY_STATUSES = (
    STATUS_ABSORBED,
    STATUS_CANDIDATE,
    STATUS_EXCLUDED,
    STATUS_BENCHMARK,
)


CAPABILITIES: tuple[dict[str, str], ...] = (
    {
        "id": "fixed-source-compile",
        "area": "编译",
        "name": "固定 Git 快照代码编译",
        "status": STATUS_ABSORBED,
        "input": "干净 Git commit 中受支持语言的 tracked 源码",
        "output": "完整机器图、SQLite、保守中文人类页和来源链接",
        "dependencies": "Git、Tree-sitter、对应语言服务器；版本由 toolchain.lock.json 锁定",
        "license": "CKB 原生实现；第三方运行时按锁文件和 THIRD_PARTY_NOTICES.md 聚合",
        "data_boundary": "只把固定 commit 的项目源码作为来源事实；工作树修改进入独立覆盖层",
        "completion_gate": "分段审阅、来源、中文、关系、机器层和人类层全局审计全部通过",
        "batch": "既有能力",
    },
    {
        "id": "segmented-recovery",
        "area": "编译",
        "name": "分段恢复与增量迁移",
        "status": STATUS_ABSORBED,
        "input": "大型代码仓库或上一版已审计知识库与新 Git commit",
        "output": "可恢复 chunk、复用事实、delta 审阅包和当前版本完整输出",
        "dependencies": "Python 标准库、Git 和现有解析/语义运行时",
        "license": "无新增依赖；沿用 CKB 与锁定运行时许可证",
        "data_boundary": "仅复用 path、language、blob 和审阅字段形状完全匹配的事实",
        "completion_gate": "迁移审计与当前版本全部完成门同时通过",
        "batch": "既有能力",
    },
    {
        "id": "deterministic-query",
        "area": "查询",
        "name": "确定性 SQLite 查询",
        "status": STATUS_ABSORBED,
        "input": "自然语言问题、固定预算、页面上限和 fast/precise 档位",
        "output": "可复查得分、来源范围和预算化 Agent pack",
        "dependencies": "Python sqlite3/FTS5；不调用向量模型或网络模型",
        "license": "Python/SQLite 随现有运行时；无新增模型许可证",
        "data_boundary": "只检索机器知识库、审核笔记、反馈和工作树覆盖层",
        "completion_gate": "重复查询排序一致、来源可打开、预算不超限且无隐藏模型调用",
        "batch": "既有能力",
    },
    {
        "id": "compact-agent-brief",
        "area": "阅读入口",
        "name": "紧凑 Agent 阅读入口",
        "status": STATUS_ABSORBED,
        "input": "问题、预算、页面上限和检索档位",
        "output": "只返回 pack/record、开放反馈数、阅读入口和源码回退判断的紧凑 JSON",
        "dependencies": "复用现有 retrieve，不新增依赖",
        "license": "CKB 原生实现",
        "data_boundary": "完整候选、词项和得分保留在检索 record；首轮上下文不展开它们",
        "completion_gate": "与同参数 retrieve 绑定同一类事实，省略大字段且 Agent pack 可打开",
        "batch": "本批次",
    },
    {
        "id": "durable-query-promotion",
        "area": "查询",
        "name": "查询结论审阅后晋升",
        "status": STATUS_ABSORBED,
        "input": "简体中文分析正文与真实 query/pack",
        "output": "analysis/change/experiment/pitfall/session 记录、双镜像和机器索引",
        "dependencies": "record、work-record index 和两个 SQLite 索引",
        "license": "CKB 原生实现",
        "data_boundary": "Agent 结论进入可变知识记录，不伪装成固定源码事实",
        "completion_gate": "中文、回链、镜像、元数据、工作记录索引和 SQLite 表示一致",
        "batch": "既有能力",
    },
    {
        "id": "location-feedback-audit",
        "area": "反馈审计",
        "name": "定位式反馈闭环",
        "status": STATUS_ABSORBED,
        "input": "目标页、行范围、文本窗口、严重程度、作者和中文评论",
        "output": "开放反馈、定位结果、决议、归档记录和检索暴露",
        "dependencies": "Python 标准库与现有 Obsidian 接口",
        "license": "按 LLM Wiki 交互思想独立实现；未复制无明确许可证的参考源码",
        "data_boundary": "反馈不改固定事实；采纳必须指向已验证实现或正式知识记录",
        "completion_gate": "锚点可解析、决议字段完整、开放/归档互斥且反馈不删除",
        "batch": "既有能力",
    },
    {
        "id": "readability-link-lint",
        "area": "知识维护",
        "name": "链接、孤页、导航与人类可读性检查",
        "status": STATUS_ABSORBED,
        "input": "生成的人类页、工作记录、双链、标签和投影清单",
        "output": "死链、孤页、重复标题、索引覆盖、中文和镜像审计",
        "dependencies": "Python 标准库和现有投影元数据",
        "license": "CKB 原生实现",
        "data_boundary": "只检查生成器拥有内容和正式可变记录；不遍历 Obsidian 私有状态",
        "completion_gate": "可发现、可理解、可行动、可信任四类门全部通过",
        "batch": "既有能力",
    },
    {
        "id": "maintenance-gate",
        "area": "知识维护",
        "name": "聚合维护门",
        "status": STATUS_ABSORBED,
        "input": "一个已生成的 CKB OUTPUT",
        "output": "workspace-meta/maintenance/latest.json 与各审计的紧凑聚合",
        "dependencies": "复用反馈、Agent Policy、人类层、机器层和 Agent index 审计",
        "license": "CKB 原生实现",
        "data_boundary": "只写机器维护报告和既有审计文件；不创建或改写知识页面",
        "completion_gate": "所有子审计通过，SQLite integrity 为 ok，报告可重开且状态一致",
        "batch": "本批次",
    },
    {
        "id": "hidden-background-processes",
        "area": "知识维护",
        "name": "非交互子进程后台运行",
        "status": STATUS_ABSORBED,
        "input": "Git、LSP、构建器和插件 stdio 等非交互命令",
        "output": "捕获的 stdout/stderr 与退出码，不额外弹出控制台窗口",
        "dependencies": "Windows CREATE_NO_WINDOW / Node windowsHide；其他平台保持原调用",
        "license": "Python/Node 平台 API；无新增依赖",
        "data_boundary": "仅改变窗口创建方式；命令、参数、权限、等待和输出语义保持不变",
        "completion_gate": "单元测试覆盖隐藏参数，真实命令输出和退出码与基线一致",
        "batch": "本批次",
    },
    {
        "id": "obsidian-reading-entry",
        "area": "阅读入口",
        "name": "Obsidian 导航、源码链接与选区学习",
        "status": STATUS_ABSORBED,
        "input": "INDEX/WIKI/RECORDS、知识页选区和用户问题",
        "output": "任务导览、可点击源码、右侧解释、追问和每日学习笔记",
        "dependencies": "Obsidian；可选 Companion 复用锁定 Claudian Provider 架构",
        "license": "插件复用 MIT Claudian；来源和 NOTICE 随包分发",
        "data_boundary": "插件只作用于明确安装的 vault；解释证据与人类学习笔记分层",
        "completion_gate": "输出契约、stdio 检索、Provider 凭据、审计和学习笔记写入通过",
        "batch": "既有能力",
    },
    {
        "id": "reviewed-text-reference-ingest",
        "area": "文档吸收",
        "name": "审阅文本参考资料层",
        "status": STATUS_ABSORBED,
        "input": "用户提供的 UTF-8 Markdown/TXT、来源元数据和明确许可说明",
        "output": "不可变参考副本、至多一个来源摘要、引用账本和机器全文索引",
        "dependencies": "Python 标准库与现有 SQLite FTS；不抓网页、不解析二进制",
        "license": "保留原文许可证与来源；无许可字段时保持待审阅，不进入完成态",
        "data_boundary": "独立 references 层；不成为代码实体、不修改固定源码图、不自动扩散概念页",
        "completion_gate": "字节来源、许可、摘要中文、引用范围、单来源页面配额和回滚全部通过",
        "batch": "本批次",
    },
    {
        "id": "machine-operation-journal",
        "area": "知识维护",
        "name": "有界机器操作日志",
        "status": STATUS_ABSORBED,
        "input": "compile/query/record/audit/maintenance 的完成结果",
        "output": "按日分片的机器 JSONL 和 latest 摘要，不生成每日人类页面",
        "dependencies": "Python 标准库",
        "license": "CKB 原生实现",
        "data_boundary": "不记录原始对话、秘密或全文输出；只记录操作类型、对象、状态和证据路径",
        "completion_gate": "固定字段、去重、大小上限、隐私过滤、索引和清理策略通过测试",
        "batch": "本批次",
    },
    {
        "id": "research-gap-register",
        "area": "知识维护",
        "name": "研究缺口与待补来源登记",
        "status": STATUS_ABSORBED,
        "input": "检索证据不足、互相矛盾的来源或 deferred 反馈",
        "output": "机器缺口记录和 RECORDS 中的单一人工入口",
        "dependencies": "SQLite 与现有 feedback/record",
        "license": "CKB 原生实现",
        "data_boundary": "缺口是待验证主张，不进入已确认事实或自动生成页面",
        "completion_gate": "状态机、来源关联、去重、关闭证据和页面数量上限通过",
        "batch": "本批次",
    },
    {
        "id": "external-raw-as-code-fact",
        "area": "文档吸收",
        "name": "把外部文档伪装成代码来源实体",
        "status": STATUS_EXCLUDED,
        "input": "网页、PDF、文章或普通笔记",
        "output": "无",
        "dependencies": "无",
        "license": "不适用",
        "data_boundary": "固定源码事实层只接受 Git blob 与受支持代码语言；外部资料必须分层",
        "completion_gate": "审计持续确认外部文档未进入 files/entities/source_ranges",
        "batch": "长期排除",
    },
    {
        "id": "duplicate-local-web-viewer",
        "area": "阅读入口",
        "name": "复制一套本地 Web Wiki 查看器",
        "status": STATUS_EXCLUDED,
        "input": "现有人类 Markdown vault",
        "output": "无新增查看器",
        "dependencies": "无",
        "license": "避免复制参考项目中许可证未确认的查看器源码",
        "data_boundary": "Obsidian 与普通 Markdown 保持唯一人类阅读表面",
        "completion_gate": "发行包不包含第二套页面渲染、反馈格式或锚点逻辑",
        "batch": "长期排除",
    },
    {
        "id": "large-binary-copy",
        "area": "文档吸收",
        "name": "复制大型二进制到知识库",
        "status": STATUS_EXCLUDED,
        "input": "视频、模型、数据集、安装包和大型 PDF",
        "output": "只允许未来候选中的受审阅指针记录",
        "dependencies": "无",
        "license": "原二进制许可证和分发权保持外部管理",
        "data_boundary": "知识库不复制大型二进制，不扩大 Git、备份和索引成本",
        "completion_gate": "路径、大小和文件类型门阻止二进制进入受管资料层",
        "batch": "长期排除",
    },
    {
        "id": "semantic-vector-retrieval",
        "area": "查询",
        "name": "qmd/向量语义检索",
        "status": STATUS_BENCHMARK,
        "input": "同一问题集、固定代码知识库和候选向量索引",
        "output": "与纯 SQLite 基线可比较的质量、延迟、内存、token 和维护成本",
        "dependencies": "候选工具与模型只在隔离 benchmark 中安装和锁定",
        "license": "benchmark 前核验工具、模型、权重和分发许可证；当前发行包不携带",
        "data_boundary": "不上传私有源码；只允许本地索引；效果门通过前不进入默认路径",
        "completion_gate": "下游定位质量或上下文成本显著优于基线，且冷/热启动和资源上限通过",
        "batch": "benchmark",
    },
    {
        "id": "pdf-web-ocr-extraction",
        "area": "文档吸收",
        "name": "PDF、网页和 OCR 自动提取",
        "status": STATUS_BENCHMARK,
        "input": "许可明确的 PDF、网页快照或图片",
        "output": "带页码/URL/字符范围的标准化文本与提取诊断",
        "dependencies": "候选提取器、浏览器或 OCR 只在隔离 benchmark 中使用",
        "license": "逐个锁定提取器及模型许可证；网页版权和访问条款单独记录",
        "data_boundary": "不默认联网、不绕过访问控制、不把提取文本混入代码事实层",
        "completion_gate": "来源定位、乱码率、表格/代码保真、失败诊断、资源和回滚达到阈值",
        "batch": "benchmark",
    },
    {
        "id": "automatic-page-fanout",
        "area": "编译",
        "name": "单文档自动扩散概念/实体页",
        "status": STATUS_BENCHMARK,
        "input": "受审阅参考文档和候选概念/实体",
        "output": "受页面配额约束的摘要或概念更新",
        "dependencies": "可能需要 Agent 分类；先用确定性候选和离线评测",
        "license": "不复制参考 Skill 模板源码；生成内容保留来源许可和引用",
        "data_boundary": "默认零自动新增概念页；benchmark 只在隔离样例库运行",
        "completion_gate": "人类查找任务收益明确、页面增量受限、中文与引用真实性全部通过",
        "batch": "benchmark",
    },
)


def capability_matrix() -> dict[str, Any]:
    counts = Counter(item["status"] for item in CAPABILITIES)
    return {
        "schema_version": 1,
        "status": "ready",
        "matrix_version": "2026-08-31.2",
        "source": "LLM Wiki five-operation model adapted through independent CKB implementations",
        "reference_license_boundary": "Only behavior and interface ideas are used; no LLM Wiki source is copied because its local reference has no confirmed license notice.",
        "status_order": list(CAPABILITY_STATUSES),
        "counts": {name: counts.get(name, 0) for name in CAPABILITY_STATUSES},
        "capabilities": [dict(item) for item in CAPABILITIES],
    }


def render_capability_matrix_markdown() -> str:
    matrix = capability_matrix()
    lines = [
        "# LLM Wiki 功能吸收矩阵",
        "",
        "> 本矩阵封闭每项能力的输入、输出、依赖、许可证、数据边界和完成门；状态只使用“已吸收、待吸收、明确排除、需要 benchmark”。",
        "",
        "## 状态汇总",
        "",
        "| 状态 | 数量 |",
        "|---|---:|",
    ]
    for status in CAPABILITY_STATUSES:
        lines.append(f"| {status} | {matrix['counts'][status]} |")
    lines.extend(
        [
            "",
            "## 功能总览",
            "",
            "| 领域 | 功能 | 状态 | 批次 |",
            "|---|---|---|---|",
        ]
    )
    for item in CAPABILITIES:
        lines.append(f"| {item['area']} | {item['name']} | {item['status']} | {item['batch']} |")
    lines.extend(["", "## 逐项边界", ""])
    for item in CAPABILITIES:
        lines.extend(
            [
                f"### {item['name']}",
                "",
                f"- 状态：**{item['status']}**",
                f"- 领域：{item['area']}",
                f"- 输入：{item['input']}",
                f"- 输出：{item['output']}",
                f"- 依赖：{item['dependencies']}",
                f"- 许可证：{item['license']}",
                f"- 数据边界：{item['data_boundary']}",
                f"- 完成门：{item['completion_gate']}",
                f"- 批次：{item['batch']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 当前批次原则",
            "",
            "- 本批次吸收研究缺口登记：待验证主张保存在机器层，只在 RECORDS 中生成一个汇总入口，不为每项缺口创建页面。",
            "- 审阅文本资料层已进入默认本地路径；固定源码事实层仍不接收外部文档。",
            "- 向量检索、PDF/网页/OCR 和自动页面扩散只在隔离 benchmark 中比较，不进入默认发行路径。",
            "- 本地 Web 查看器、大型二进制复制和外部文档伪装成代码实体保持明确排除。",
            "",
        ]
    )
    return "\n".join(lines)


def write_capability_matrix(path: Path, format_name: str) -> dict[str, Any]:
    path = path.resolve()
    if path.exists():
        raise CkbError(f"capability matrix target already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if format_name == "markdown":
        path.write_text(render_capability_matrix_markdown(), encoding="utf-8", newline="\n")
    else:
        json_write(path, capability_matrix())
    return {"schema_version": 1, "status": "written", "format": format_name, "path": str(path)}


def compact_agent_brief(output: Path, retrieval: dict[str, Any]) -> dict[str, Any]:
    output = output.resolve()
    entries = {
        name: str(path.resolve()) if path.is_file() else None
        for name, path in {
            "index": output / "human/INDEX.md",
            "records": output / "human/RECORDS.md",
            "wiki": output / "human/WIKI.md",
            "references": output / "human/REFERENCES.md",
        }.items()
    }
    feedback_documents = [
        {
            key: item.get(key)
            for key in ("document_id", "title", "tag", "human_file")
            if item.get(key) is not None
        }
        for item in retrieval.get("related_documents", [])
        if item.get("kind") == "feedback"
    ][:8]
    return {
        "schema_version": 1,
        "status": retrieval.get("status"),
        "question": retrieval.get("question"),
        "profile": retrieval.get("profile"),
        "budget": retrieval.get("budget"),
        "estimated_tokens": retrieval.get("estimated_tokens"),
        "pack": retrieval.get("pack"),
        "record": retrieval.get("record"),
        "open_feedback": int(retrieval.get("open_feedback", 0)),
        "feedback_documents": feedback_documents,
        "reading_entries": entries,
        "grep_fallback_required": bool(retrieval.get("grep_fallback_required")),
        "next": "open-pack" if retrieval.get("pack") else "inspect-retrieval-error",
        "omitted_from_context": [
            "terms",
            "anchors",
            "seed_entity_ids",
            "selected_entities",
            "related_documents",
            "retrieval_stats",
        ],
        "full_record_retained": True,
    }


def maintenance_check(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if not (output / "state.json").is_file():
        raise CkbError(f"CKB output is required: {output}")
    from .agent_index import audit_agent_index
    from .agent_protocol import audit_agent_protocol
    from .knowledge_layers import audit_human_layer
    from .machine_knowledge import audit_machine_knowledge
    from .operation_journal import audit_operation_journal
    from .research_gaps import audit_gap_register
    from .reference_documents import audit_references
    from .work_record_index import audit_work_record_index

    checks = {
        "agent_protocol": audit_agent_protocol(output),
        "work_record_index": audit_work_record_index(output),
        "agent_index": audit_agent_index(output),
        "machine_knowledge": audit_machine_knowledge(output),
        "human_layer": audit_human_layer(output),
        "references": audit_references(output),
        "operations": audit_operation_journal(output),
        "research_gaps": audit_gap_register(output),
    }
    failed = [name for name, result in checks.items() if result.get("status") != "passed"]
    readability_path = output / "human/readability-audit.json"
    readability = json_load(readability_path) if readability_path.is_file() else {"status": "missing"}
    if readability.get("status") != "passed":
        failed.append("human_readability")
    report = {
        "schema_version": 1,
        "status": "passed" if not failed else "failed",
        "checked_at_utc": utc_now(),
        "output": str(output),
        "page_writes": 0,
        "checks": checks,
        "human_readability": {
            "status": readability.get("status"),
            "path": str(readability_path.resolve()),
            "errors": readability.get("errors", []),
        },
        "capability_counts": capability_matrix()["counts"],
        "failed_checks": failed,
    }
    target = output / "workspace-meta/maintenance/latest.json"
    json_write(target, report)
    reopened = json_load(target)
    if reopened.get("status") != report["status"] or reopened.get("failed_checks") != failed:
        raise CkbError("maintenance report did not reopen with the verified state")
    return {**report, "report": str(target.resolve())}
