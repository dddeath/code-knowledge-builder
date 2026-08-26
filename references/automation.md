# 会话与修改自动同步

本模式把 Codex、Claude Code、OpenCode、DeepSeek Harness（DSH）、Gemini CLI、GitHub Copilot、Cursor 和其他 Agent Harness 的生命周期事件收敛为同一套 CKB 机器协议。Harness 只负责发送事件；项目启用、工作区到源码仓库的映射、脱敏、幂等、恢复、修改范围、机器检索、Agent 审阅和人类投影均由确定性 Python 核心负责。

## 固定边界

- **显式项目启用**：事件只有在注册表中匹配已启用的仓库根和 Harness 时才写入；其他目录返回 `ignored`。
- **机器层优先**：原始轮次经过脱敏后进入 `machine/automation.sqlite` 和写前队列。逐轮对话不会直接膨胀为人类 Markdown 页面。
- **Agent 审阅后晋升**：`Stop` 或等价事件只产生 `pending-agent-review`。Agent 重新核对修改路径、源码和验证证据，提交简体中文审阅后，脚本才调用正式 `record_note` 投影到 `human` 与 `markdown`。
- **不解析 transcript**：Codex 与 Claude Code 都把 transcript 路径视为便利字段而非稳定协议。本实现只使用事件直接提供的 prompt、最终回答、工具输入/结果、会话标识和工作目录。
- **不阻塞 Harness 行为**：同步 Hook 不作权限或完成决策。Hook 入口发生错误时输出该 Harness 可接受的空对象并写诊断，不把知识库故障变成代码操作故障。
- **用户文件与知识基线分离**：自动化记录当前工作树证据，不改写固定源码快照，也不改变 `.complete` 所描述的基线 commit。

官方事件依据：

- [Codex Hooks](https://learn.chatgpt.com/docs/hooks)
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks)
- [OpenCode Plugins](https://opencode.ai/docs/plugins/)
- [OpenCode V2 Plugins](https://opencode.ai/v2/docs/build/plugins)
- [DSH Codex Hooks Bridge](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/hooks/hooks-codex/README.zh.md)
- [DSH Session Event Model](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/session.md)
- [Gemini CLI Hooks Reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/reference.md)
- [GitHub Copilot Hooks Reference](https://docs.github.com/en/copilot/reference/hooks-reference)
- [Cursor Hooks](https://cursor.com/docs/hooks)

## 注册项目

默认注册表为：

- Windows：`%USERPROFILE%\.ckb\automation-registry.json`
- macOS/Linux：`~/.ckb/automation-registry.json`
- 环境变量 `CKB_AUTOMATION_REGISTRY` 可以指定另一路径。

只启用明确选择的 Harness：

```powershell
& PYTHON scripts\ckb.py automation register `
  --repo REPO `
  --out OUTPUT `
  --registry REGISTRY `
  --harness codex `
  --harness claude `
  --harness opencode `
  --harness dsh `
  --harness gemini `
  --harness copilot `
  --harness cursor `
  --harness generic
```

同一注册表允许多个仓库。默认情况下，事件的 `cwd` 位于对应仓库内部。若 Harness 任务目录是源码仓库的父级隔离工作区，重复使用 `--workspace-root` 显式建立事件入口映射：

```powershell
& PYTHON scripts\ckb.py automation register `
  --repo "E:\workspace\source" `
  --out "E:\workspace\knowledge-base" `
  --workspace-root "E:\workspace" `
  --harness codex --harness claude --harness opencode --harness dsh
```

此时 Hook 可以从 `E:\workspace` 运行，但 Git status、变化路径、源码检查和知识链接始终以 `E:\workspace\source` 为边界。`E:\workspace\work` 下的验证脚本不会映射成源码变化。直接仓库匹配优先于 workspace 匹配；同优先级选择最深根；同一 workspace root 不得同时指向两个仓库。注册表 schema 2 会只读兼容 schema 1，并在下一次注册写入时升级。`--max-field-chars` 控制单字段保留上限，重复 `--redact REGEX` 增加项目自定义脱敏模式。

注销不会删除既有知识记录：

```powershell
& PYTHON scripts\ckb.py automation unregister --repo REPO --registry REGISTRY
```

## 统一事件协议

核心规范只保留九种事件：

| 规范事件 | 含义 | 主要结果 |
|---|---|---|
| `session.start` | Harness 会话建立或恢复 | 建立会话、保存初始 Git 工作树范围 |
| `turn.prompt` | 用户消息进入当前轮次 | 保存脱敏 prompt，建立或复用活动 turn |
| `turn.assistant` | Harness 提供 Assistant 消息 | 更新本轮最终说明候选 |
| `tool.result` | 工具成功或失败后 | 保存工具证据和可确定的项目内路径 |
| `file.changed` | Harness 文件观察事件 | 保存项目内文件变化证据 |
| `turn.stop` | 一轮最终回答完成 | 聚合本轮并生成机器层待审阅记录 |
| `compact.before` | 上下文压缩前 | 保存检查点事件 |
| `compact.after` | 上下文压缩后 | 保存压缩完成事件 |
| `session.end` | 主会话结束 | 关闭会话；活动轮次存在时先生成待审阅记录 |

Harness 有原生 turn ID 时直接使用；Claude Code 等未提供 turn ID 的事件，脚本按会话内活动轮次和固定序号归并。相同 prompt 在活动轮次内重试会去重；上一轮完成后再次提交相同 prompt 会建立新轮次。工具事件优先使用 Harness 的 tool-use ID。

其他 Harness 通过 `automation render --harness generic` 获得 JSON Schema。最小事件为：

```json
{
  "canonical_type": "turn.prompt",
  "event_id": "HARNESS_EVENT_ID",
  "session_id": "HARNESS_SESSION_ID",
  "turn_id": "HARNESS_TURN_ID",
  "cwd": "/absolute/project/path",
  "prompt": "用户请求"
}
```

调用入口：

```powershell
Get-Content EVENT.json -Raw |
  & PYTHON scripts\ckb.py automation ingest --harness generic --registry REGISTRY
```

提供稳定 `event_id` 可获得最强幂等保证。

## 写前队列、幂等与恢复

每个已登记输出增加：

```text
OUTPUT/
|-- machine/
|   `-- automation.sqlite
`-- workspace-meta/automation/
    |-- spool/
    |   |-- pending/
    |   |-- processed/
    |   `-- failed/
    `-- pending-reviews/
```

事件先原子写入 `pending`，再在单仓库 drain 锁和 SQLite `BEGIN IMMEDIATE` 事务中处理。成功事件按稳定事件 ID 进入 `processed`；重复事件不重复增加 turn、路径或审阅记录。进程在写入队列后中断时，下一次 Hook 或手动 `drain` 会继续处理。

```powershell
& PYTHON scripts\ckb.py automation drain --out OUTPUT
& PYTHON scripts\ckb.py automation retry --out OUTPUT
& PYTHON scripts\ckb.py automation status --out OUTPUT
```

`retry` 只重放失败队列中的原始脱敏事件。确定性输入错误会再次进入失败区；修复注册、路径或版本问题后再重试。`status` 必须报告 SQLite `integrity_check=ok`、零待处理队列和零失败事件，才能把同步链路视为稳定。

## 脱敏规则

写入机器层前递归处理 JSON：

- 敏感键名：API Key、Token、Authorization、Password、Secret、Cookie、Private Key；
- Bearer/Basic Authorization；
- 常见凭据赋值；
- PEM Private Key 区块；
- 项目注册时配置的自定义正则；
- 超过字段上限的文本。

机器事件只保存替换后的值、脱敏计数和类型，原值不进入 spool、SQLite、阅读包或人类页面。附件和大型工具输出仍受字段上限约束。

## Agent 审阅与人类投影

查看待审阅记录：

```powershell
& PYTHON scripts\ckb.py automation pending --out OUTPUT
& PYTHON scripts\ckb.py automation review-template `
  --out OUTPUT --review-id REVIEW_ID --write REVIEW.json
```

Agent 必须重新打开变化路径和关联知识页，把机器草稿重写成简体中文正文。修改记录正文必须含：

```markdown
## 修改内容

## 修改原因

## 验证结果
```

审阅 JSON 必须满足：

- `status: agent-reviewed`；
- `title` 是简洁的人类页面标题；
- `body` 指向已核实的中文 Markdown；
- `evidence_note` 使用中文说明审阅方法；
- `source_checks` 与机器记录的 changed-path 集合完全一致；
- 每个 source check 都是 `agent-reviewed` 并含中文证据；
- 可选 `linked_pages` 必须精确匹配知识页；省略时由路径确定性映射。

提交：

```powershell
& PYTHON scripts\ckb.py automation review --out OUTPUT --review REVIEW.json
```

通过后只生成一份正式人类笔记，human/markdown 镜像保持一致，机器记录更新为 `agent-reviewed`。审阅失败时原记录继续保持 `pending-agent-review`。

## Harness 适配包

所有配置都由脚本写入一个空的隔离目录；脚本不会合并或覆盖现有 Harness 配置。确认生成内容后，再按各 Harness 的配置合并方式安装。

```powershell
& PYTHON scripts\ckb.py automation render `
  --harness codex|claude|opencode|opencode-v2|dsh|gemini|copilot|cursor|generic `
  --destination BUNDLE `
  --python PYTHON `
  --ckb SKILL_DIR\scripts\ckb.py `
  --registry REGISTRY
```

### Codex

生成一个带 `.codex-plugin/plugin.json` 和 `hooks/hooks.json` 的配套 Plugin。它监听 `SessionStart`、`UserPromptSubmit`、修改相关 `PostToolUse`、`PreCompact`、`PostCompact`、`Stop` 和 `SessionEnd`。安装或更新后，在新 Codex 任务中运行 `/hooks`，检查来源、命令和 matcher，并信任当前定义；Hook 内容变化后重新审阅。

`Stop` 是每轮主要持久化点。`SessionEnd` 只有三秒预算，仅关闭会话和处理已在本地的轻量状态。

### Claude Code

生成隔离的 `.claude/settings.json`。把其中的 `hooks` 对象合并到目标项目现有设置；保留其他权限、插件和项目配置。适配器监听成功和失败的工具结果、直接 `FileChanged`、`StopFailure`，并在 `Stop` 使用 `last_assistant_message`，避免依赖 Stop 时可能尚未刷新完整的 transcript。Claude 的 timeout 单位是秒，`SessionEnd` 输出不参与决策，因此只执行轻量入队。

### OpenCode

`opencode` 生成稳定 Plugin API 文件，使用 `session.created`、`message.updated`、`file.edited`、`session.idle`、`session.deleted` 和 `tool.execute.after`。将文件放入项目 `.opencode/plugins/`。

`opencode-v2` 生成当前 V2 beta API 文件，使用 `ctx.session.hook("context")`、`ctx.tool.hook("execute.after")` 和公共事件流；同时兼容过渡期 `session.idle` 与当前 `session.execution.succeeded.1` / `session.execution.failed.1` 终态。它只用于与 V2 Plugin API 版本匹配的 OpenCode；升级 OpenCode 后重新生成并运行 canary。V2 API 仍处于 beta，因此 `integration.json` 固定适配器版本，不能把 stable 与 V2 文件混装。

### DeepSeek Harness

DSH 生成 Codex 方言的四事件 Hook 配置和 `cordis.yml.fragment`，供官方 `@deepseek-ai/dsh-hooks-codex` 桥接器加载。当前桥接覆盖 `SessionStart`、`UserPromptSubmit`、`PostToolUse` 和 `Stop`；每轮 `Stop` 已提供主要持久化，未把 `SessionEnd` 当作完成前提。

桥接器版本必须与 DSH CLI generation 对齐，并通过 profile loader 复用宿主核心包；不要在 profile 下复制第二套 `@deepseek-ai/dsh-*` 核心依赖。安装后用一条真实 prompt、一次文件修改和一次 Stop canary 验证四个事件。

### Gemini CLI

生成隔离的 `.gemini/settings.json`。协议映射为：`SessionStart` → 会话开始，`BeforeAgent` → 用户轮次，`AfterTool` → 工具结果，`AfterAgent` → 轮次完成，`PreCompress` → 压缩前检查点，`SessionEnd` → 会话关闭。Gemini timeout 的单位是毫秒；`AfterAgent.prompt_response` 是最终回答来源；`SessionEnd` 是 best-effort，因此每轮持久化只依赖 `AfterAgent`。

### GitHub Copilot

生成 `.github/hooks/code-knowledge-builder.json`，使用 PascalCase 的 VS Code 兼容事件名，从而接收 snake_case payload。配置同时写入 `bash` 与 `powershell`，覆盖本地 Copilot CLI；云端 Agent 只使用其 Linux 沙箱中的 `bash`，因此本地绝对 Python/CKB 路径只适用于本地 CLI。云端适配需要把 CKB 脚本随仓库提供或改接 generic HTTPS 接收端，本发行版不会把本机路径误标为云端可用。

### Cursor

生成 `.cursor/hooks.json`，映射 `sessionStart`、`beforeSubmitPrompt`、`postToolUse`、`postToolUseFailure`、`afterFileEdit`、`afterAgentResponse`、`preCompact`、`stop` 和 `sessionEnd`。项目配置只在可信 workspace 中运行；适配器依靠事件 `cwd` 或 Hook 进程工作目录以及 `CURSOR_PROJECT_DIR` 所指向的工作区，再由注册表映射到固定源码仓库。

### 其他 Harness

使用 generic JSON Schema 和 stdin CLI。Harness 至少发送 `session.start`、`turn.prompt`、修改相关 `tool.result`、`turn.stop`；提供 `session.end` 和 compact 事件可改善恢复记录，但不是每轮持久化的必要条件。

## 完成门

会话与修改自动同步只有同时满足以下条件才视为通过：

1. 未登记项目零写入；
2. 相同事件重放不增加事件、turn 或待审阅数量；
3. 并发事件零丢失、零重复；
4. 敏感原值在 spool、SQLite 和人类层均为零；
5. Stop 后产生一条且仅一条待审阅记录；
6. Git 路径、工具路径和输出路径只保留仓库内部目标；
7. `automation.sqlite` 完整性为 `ok`；
8. 中断队列可以 drain，失败队列可以显式 retry；
9. 未审阅记录可被机器 FTS 检索，但没有人类文件；
10. Agent 审阅的路径集合、中文正文和证据全部通过后，human/markdown 才生成一致页面；
11. 各 Harness 配置通过 JSON/语法检查，已安装 Harness 还需真实 canary；
12. 自动化同步状态与固定基线 `.complete` 分开，不用 Hook 成功冒充源码知识图谱重新完成。
13. workspace-root 事件只保留源码仓库内部路径，兄弟 `work`、知识库和构建输出路径全部被过滤；
14. Harness 协议使用各自原生事件名、字段和 timeout 单位，适配器只在规范化边界后共享逻辑。
