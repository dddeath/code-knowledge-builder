# render_integration 与 harness_retrieval_contract 的协作实现

标签：#类型/代码

> `scripts/ckb_core/automation_integrations.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责为不同 Harness 生成事件接入脚本和固定配置。

## 什么时候需要修改

当 `scripts/ckb_core/automation_integrations.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-656`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[render_integration]]。

## 谁会来到这里

- 与 [[render_integration]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 20 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `harness_retrieval_contract` | 该函数生成跨 Harness 适配器或来源分离的检索契约。 |
| `_looks_windows` | `_looks_windows` 是第 19-21 行的函数，供所属页面定位实现。 |
| `_wsl_launch_path` | `_wsl_launch_path` 是第 24-32 行的函数，供所属页面定位实现。 |
| `_commands` | `_commands` 是第 35-41 行的函数，供所属页面定位实现。 |
| `_powershell_command` | `_powershell_command` 是第 44-62 行的函数，供所属页面定位实现。 |
| `_powershell_command.quote` | `_powershell_command.q...` 是第 45-46 行的函数，供所属页面定位实现。 |
| `_codex_windows_bridge` | `_codex_windows_bridge` 是第 65-78 行的函数，供所属页面定位实现。 |
| `_handler` | `_handler` 是第 81-90 行的函数，供所属页面定位实现。 |
| `_codex_hooks` | `_codex_hooks` 是第 93-121 行的函数，供所属页面定位实现。 |
| `_claude_hooks` | `_claude_hooks` 是第 124-143 行的函数，供所属页面定位实现。 |
| `_claude_hooks.handler` | `_claude_hooks.handler` 是第 125-126 行的函数，供所属页面定位实现。 |
| `_gemini_hooks` | `_gemini_hooks` 是第 146-159 行的函数，供所属页面定位实现。 |
| `_gemini_hooks.handler` | `_gemini_hooks.handler` 是第 147-148 行的函数，供所属页面定位实现。 |
| `_copilot_hooks` | `_copilot_hooks` 是第 162-188 行的函数，供所属页面定位实现。 |
| `_copilot_hooks.handler` | `_copilot_hooks.handler` 是第 163-172 行的函数，供所属页面定位实现。 |
| `_cursor_hooks` | `_cursor_hooks` 是第 191-211 行的函数，供所属页面定位实现。 |
| `_cursor_hooks.handler` | `_cursor_hooks.handler` 是第 192-196 行的函数，供所属页面定位实现。 |
| `_opencode_stable_plugin` | `_opencode_stable_plugin` 是第 214-292 行的函数，供所属页面定位实现。 |
| `_opencode_v2_plugin` | `_opencode_v2_plugin` 是第 295-388 行的函数，供所属页面定位实现。 |
| `_generic_schema` | `_generic_schema` 是第 391-429 行的函数，供所属页面定位实现。 |

</details>
