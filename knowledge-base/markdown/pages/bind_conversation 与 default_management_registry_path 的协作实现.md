# bind_conversation 与 default_management_registry_path 的协作实现

标签：#类型/代码

> `scripts/ckb_core/management_agent.py` 页面绑定固定源码第 1-1355 行，说明该文件在管理对话绑定、任务派发和审阅上下文中的整体职责。 该文件负责管理对话绑定、任务派发和审阅上下文，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `scripts/ckb_core/management_agent.py` 中 `scripts/ckb_core/management_agent.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/management_agent.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/management_agent.py:1:1)  `scripts/ckb_core/management_agent.py:1-1355`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[append 等测试场景]]。
- 实现时会用到 [[audit_gap_register 与 _root 的协作实现]]。
- 实现时会用到 [[audit_global 与 _replace_output_prefix 的协作实现]]。
- 主要代码单元是 [[bind_conversation]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[maintenance_check]]。
- 实现时会用到 [[maintenance_check 与 capability_matrix 的协作实现]]。
- 实现时会用到 [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]]。
- 实现时会用到 [[retrieve_machine]]。

## 谁会来到这里

- [[HumanMaintenancePromptRegistryTests]] 会使用这里提供的行为。
- [[append]] 会使用这里提供的行为。
- [[append 等测试场景]] 会使用这里提供的行为。
- [[bind_conversation]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[render_integration]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register]]
- [[AutomationTest.register 等测试场景]]
- [[CanvasBenchmarkContractTests]]
- [[CanvasBenchmarkContractTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 41 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `default_management_registry_path` | `default_management_registry_path` 用于完成局部输入校验、转换或状态更新。 |
| `management_human_maintenance_prompt_contract` | `management_human_maintenance_prompt…` 用于完成局部输入校验、转换或状态更新。 |
| `_path_key` | `_path_key` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_normalized_path` | `_normalized_path` 在 `management_agent.py` 中用于解析、规范化并冻结调用输入。 |
| `_empty_registry` | `_empty_registry` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_read_registry` | `_read_registry` 在 `management_agent.py` 中用于读取、规范化并返回既有状态。 |
| `_registry_lock` | `_registry_lock` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_locked_registry` | `_locked_registry` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_audit_event` | `_audit_event` 在 `management_agent.py` 中用于校验输入、状态、证据或输出合同。 |
| `_capability` | `_capability` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `harness_capabilities` | `harness_capabilities` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `binding_schema` | `binding_schema` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `canonical_binding_input` | `canonical_binding_input` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_privacy_errors` | `_privacy_errors` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `audit_manager_registry` | `audit_manager_registry` 在 `management_agent.py` 中用于校验输入、状态、证据或输出合同。 |
| `_git` | `_git` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_is_within` | `_is_within` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_git_preflight` | `_git_preflight` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_binding_identity` | `_binding_identity` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_binding_project` | `_binding_project` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_binding_id` | `_binding_id` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_find_binding` | `_find_binding` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_runtime_state` | `_runtime_state` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `binding_status` | `binding_status` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `unbind_conversation` | `unbind_conversation` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_sqlite_integrity` | `_sqlite_integrity` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_feedback_snapshot` | `_feedback_snapshot` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_knowledge_snapshot` | `_knowledge_snapshot` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_single_quote` | `_single_quote` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_manager_commands` | `_manager_commands` 在 `management_agent.py` 中用于编排命令入口、执行顺序和退出结果。 |
| `_management_prompt` | `_management_prompt` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `audit_management_prompt` | `audit_management_prompt` 在 `management_agent.py` 中用于校验输入、状态、证据或输出合同。 |
| `management_context` | `management_context` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_task_id` | `_task_id` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_task_artifact_root` | `_task_artifact_root` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_find_task` | `_find_task` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_bounded_values` | `_bounded_values` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `_task_prompt` | `_task_prompt` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `create_management_task` | `create_management_task` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `management_task_status` | `management_task_status` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |
| `review_management_task` | `review_management_task` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。 |

</details>
