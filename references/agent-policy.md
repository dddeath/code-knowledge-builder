# 跨 Harness Agent 检索与维护协议

## 目标

知识库不能依赖用户在每轮任务中重复点名 Skill。`agent-policy` 把必要约束投影为各 Harness 会自动发现的项目级指令，同时用确定性审计检查写入结果。

## 安装

在知识库已经完成 machine、human 与 markdown 投影后运行：

```powershell
& PYTHON scripts\ckb.py agent-policy install `
  --out OUTPUT `
  --workspace-root TASK_ROOT
```

`TASK_ROOT` 是 Agent 实际启动任务的目录，可以与 Git 仓库根目录分离。命令始终在以下知识库根写入精确生成的适配文件：

- `OUTPUT`
- `OUTPUT/human`
- `OUTPUT/markdown`

并在每个显式 `--workspace-root` 写入或更新一个带边界标记的受管区块，保留文件中原有的其他项目说明。重复安装只替换该区块，不重复追加。

## Harness 发现文件

| Harness | 入口 |
|---|---|
| Codex | `AGENTS.md` |
| OpenCode | `AGENTS.md` |
| Claude Code | `CLAUDE.md`，导入同目录 `AGENTS.md` |
| Gemini CLI | `GEMINI.md`，导入同目录 `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Cursor | `.cursor/rules/code-knowledge-builder.mdc`，`alwaysApply: true` |
| 其他 Harness | 启动时显式读取 `AGENTS.md` |

人类 Obsidian vault 通过忽略规则和本地 CSS 隐藏根目录的三个适配 Markdown 文件，避免把工作协议混入普通知识页导航。

## 强制读路径

1. `retrieve --profile fast`；
2. 读取返回的预算化 Agent pack；
3. 用 `entity`、`neighbors`、`source`、`changes` 缩小范围；
4. 仅在 `needs-source-read` 或已得到精确路径/行范围后读取源码；
5. `grep` 只补充精确范围，不替代机器库首轮检索。

这个顺序同时减少上下文消耗，并让每次结论带有可复查的实体、关系和源码范围。

## 强制写路径

- 生成器管理的代码页、索引页、投影清单和 SQLite 文件不直接编辑；
- 分析、修改、踩坑、实验和会话页使用 `record`；
- 非会话页必须通过 `--from-pack`、`--from-query` 或唯一 `--link` 连接已有知识页；
- 正文使用简体中文；
- 更新已有人工笔记使用同标题和 `--append`；
- Hook 只负责事件采集和审核后新建记录，更新其他已有页面使用显式命令，不按每轮对话扩散。

## 确定性审计

```powershell
& PYTHON scripts\ckb.py agent-policy check --out OUTPUT
```

检查内容包括：

1. 各 Harness 指令文件与当前协议完全一致；
2. workspace 受管区块存在且只有一份；
3. 人工笔记符合中文、标签和双链规则；
4. `human` 与 `markdown` 笔记集合和字节一致；
5. 每篇人工笔记都有 `workspace-meta/notes` 审阅元数据；
6. `agent-index.sqlite` 和 `machine/knowledge.sqlite` 中的笔记标题、路径、类型和正文与文件一致；
7. 两个 SQLite 数据库完整性检查通过。

任何检查失败时，本轮只能报告具体失败项；修复后重新运行本命令。

## conversation 级管理身份

项目级 `agent-policy` 说明知识库对所有 Agent 的固定读取和写入规则；conversation 级 `manager` 绑定在此基础上增加当前任务的 workspace、repo、knowledge base、integration branch 和 bound HEAD。它不替换 `AGENTS.md`，也不把对话正文写入项目指令。

```powershell
& PYTHON scripts\ckb.py manager bind `
  --conversation-id CONVERSATION_ID --harness HARNESS `
  --workspace-root WORKSPACE --repo REPO --out OUTPUT `
  --integration-branch INTEGRATION_BRANCH --registry MANAGER_REGISTRY

& PYTHON scripts\ckb.py manager context `
  --conversation-id CONVERSATION_ID --harness HARNESS `
  --question "QUESTION" --registry MANAGER_REGISTRY --format prompt
```

绑定前必须满足：workspace、repo 与 output 存在；repo 是所给 Git worktree 的根；当前分支就是 integration branch；该分支有 HEAD；integration worktree 干净。相同 Harness + conversation + project 重复绑定返回同一个 `binding_id`；同一身份指向另一项目时结构化失败。解绑只停止后续管理上下文获取，保留绑定和审计历史。

完整管理 Prompt 会列出 `brief`、feedback、gaps、reference、record、maintain 的精确入口，并重新报告 HEAD drift、dirty tree、开放 error feedback、两个 SQLite 完整性和 maintain 失败项。Prompt 审计缺少任一固定职责或命令时，context 增加 `management-prompt-audit-failed` 阻断项。
