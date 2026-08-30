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
