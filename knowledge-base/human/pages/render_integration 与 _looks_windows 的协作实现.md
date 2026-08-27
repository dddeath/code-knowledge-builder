# render_integration 与 _looks_windows 的协作实现

标签：#类型/代码

> 该代码页汇总 Codex、Claude Code、OpenCode、DSH、Gemini、Copilot、Cursor 和 generic 的 Hook/Plugin 配置生成器。 它为各 Harness 生成原生事件适配，并声明 session 必须明确应用 `code-knowledge-builder`；Claude 和 OpenCode 还输出原生 Skill/command 激活事件。

## 什么时候需要修改

当宿主协议、事件名称、timeout、Skill 调用事件或配置格式变化时，需要修改本页并重跑 JSON 与 JavaScript 语法检查。

## 在代码中的位置

[打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-502`

## 相关代码

- 实现时会用到 [[AutomationTest.event]]。
- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[LspClient.start 与 _version_matches 的协作实现]]。
- 实现时会用到 [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]]。
- 实现时会用到 [[execute]]。
- 主要代码单元是 [[render_integration]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[LspClient.start 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[ensure_local_openers 与 default_openers 的协作实现]] 会使用这里提供的行为。
- [[render_integration]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]

## 内部细节

<details><summary>查看本页收纳的 17 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_looks_windows` | 根据可执行文件路径判断适配包是否面向 Windows。 |
| `_commands` | 生成 POSIX 与 Windows cmd 两种 CKB Hook 命令。 |
| `_powershell_command` | 生成带安全单引号转义的 PowerShell Hook 命令。 |
| `_powershell_command.quote` | `quote` 负责执行其命名职责对应的确定性处理，并把结果交给所属主流程。 |
| `_handler` | 构造 Codex 兼容 command Hook 的超时和状态字段。 |
| `_codex_hooks` | 生成 Codex/DSH 生命周期 Hook，并在说明中固定显式 Skill 应用后的同步边界。 |
| `_claude_hooks` | 生成 Claude Hooks，并增加 UserPromptExpansion 与 Skill 工具的原生激活监听。 |
| `_claude_hooks.handler` | `handler` 负责执行其命名职责对应的确定性处理，并把结果交给所属主流程。 |
| `_gemini_hooks` | 按毫秒超时生成 Gemini CLI 生命周期 Hook 配置。 |
| `_gemini_hooks.handler` | `handler` 负责执行其命名职责对应的确定性处理，并把结果交给所属主流程。 |
| `_copilot_hooks` | 生成同时包含 bash 与 PowerShell 的 Copilot VS Code 兼容配置。 |
| `_copilot_hooks.handler` | `handler` 负责执行其命名职责对应的确定性处理，并把结果交给所属主流程。 |
| `_cursor_hooks` | 生成 Cursor 项目级会话、工具、文件和停止事件配置。 |
| `_cursor_hooks.handler` | `handler` 负责执行其命名职责对应的确定性处理，并把结果交给所属主流程。 |
| `_opencode_stable_plugin` | 生成 OpenCode stable Plugin，监听消息、命令、工具和 session 事件并输出精确 Skill 激活事件。 |
| `_opencode_v2_plugin` | 生成 OpenCode V2 Plugin，通过 context、tool hook 与事件流同步 Skill 激活和会话证据。 |
| `_generic_schema` | 生成含 `skill.applied`、精确 skill name 与显式布尔证据的通用事件 Schema。 |

</details>
