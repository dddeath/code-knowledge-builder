# 定位式人工反馈

## 目的

反馈闭环让人类在 Obsidian、其他本地查看器或命令行中指出知识页的具体文本，并让后续 Agent 确定性地重新定位、处理和归档。它不修改固定 Git 源码事实图，也不允许绕过 `record` 或生成器直接重写受管页面。

## 存储与可见性

- `workspace-meta/feedback/open/*.json`：开放反馈的规范记录。
- `workspace-meta/feedback/resolved/*.json`：已处理反馈的规范归档；记录只迁移，不删除。
- `human/feedback/open|resolved/*.md`：供人类阅读的中文反馈页。
- `markdown/feedback/open|resolved/*.md`：与 `human` 逐字一致的 Obsidian 兼容镜像。

可见页没有 YAML frontmatter、哈希或机器分类字段，仅保留一个 `#类型/反馈` 标签、目标页、行范围、反馈正文、锚点摘录和处理结果。

## 命令流程

开始任务时读取开放反馈：

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" feedback list --out "OUTPUT" --status open
```

新增反馈时指定知识根内的 Markdown 目标和 1 起始的闭区间。脚本从目标页自动截取原文、前后各最多 80 个字符，并验证 `human` 与 `markdown` 目标逐字一致：

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" feedback create --out "OUTPUT" `
  --target "pages\PAGE.md" --start-line 10 --end-line 12 `
  --comment "COMMENT.md" --severity warn --author "AUTHOR" --source manual
```

`--source` 接受 `manual`、`obsidian-plugin` 或 `web-viewer`。第三方界面只负责调用同一命令或生成同一字段，不拥有另一套判别逻辑。

处理前重新定位：

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" feedback locate --out "OUTPUT" --feedback "FEEDBACK_ID"
```

定位顺序固定为：原行范围、全文唯一原文、前后窗口消歧。三者均失败时返回 `stale`，开放反馈审计失败；Agent 应先重新确认目标，不得静默忽略。

处理决议包括：

- `accepted`：完全采纳，要求 `--applied-record` 指向知识输出内已存在的落实记录。
- `partial`：部分采纳，同样要求落实记录，并在中文说明中指出未采纳部分。
- `rejected`：不采纳，必须给出中文事实或范围理由。
- `deferred`：证据不足，保留在开放目录，并记录后续核验条件。

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" feedback resolve --out "OUTPUT" `
  --feedback "FEEDBACK_ID" --decision rejected --resolution "RESOLUTION.md"
& PYTHON "SKILL_DIR\scripts\ckb.py" feedback audit --out "OUTPUT"
```

## Agent 处理约束

1. 按 `error`、`warn`、`suggest`、`info` 的固定顺序查看反馈。
2. 任务涉及反馈目标时，先 `locate`，再读取目标及其现有来源链接。
3. `human/pages`、`markdown/pages`、`INDEX.md` 与 `WIKI.md` 仍由生成器管理。应修改源码、审阅事实或投影规则；需要保留分析时使用 `record`。
4. 采纳或部分采纳后，把变更页或分析页作为 `--applied-record`，再归档反馈。
5. 结束前执行 `feedback audit` 和 `agent-policy check`。开放锚点失效、镜像不一致、英文叙述或缺失落实记录都会阻止维护任务标记完成。

## 与 LLM Wiki 的吸收边界

完整的四态矩阵与每项输入、输出、依赖、许可证、数据边界和完成门见 [LLM Wiki 功能吸收矩阵](llm-wiki-capability-matrix.md)。本页只保留反馈能力的摘要映射。

| LLM Wiki 能力 | CKB 状态 | 对应实现 |
|---|---|---|
| compile | 已吸收 | 固定快照构建、分段恢复、规范图和双投影 |
| query | 已吸收 | SQLite 检索、常驻 stdio、预算化 Agent pack、`record` 回链 |
| lint | 已吸收 | 来源、实体、链接、中文、镜像、索引、协议和反馈审计 |
| audit | 本版吸收 | 定位式反馈、严重程度、决议、开放/归档状态和检索暴露 |
| raw ingest | 有界排除 | 任意网页、PDF 和文章不进入固定 Git 源码事实层 |
| 本地 Web 查看器 | 接口兼容 | 可调用 `feedback create`，本版不复制另一套页面渲染与锚点逻辑 |
| Obsidian 反馈入口 | 接口兼容 | `--source obsidian-plugin` 复用同一 CLI；核心 Skill 不强制安装社区插件 |

这一边界保留代码知识库的来源真实性，并吸收 LLM Wiki 对人类纠错、历史保留和维护闭环最有价值的部分。
