# bind_conversation 与 default_management_registry_path 的协作实现

标签：#类型/代码

> 该模块把 Harness 对话绑定到项目管理身份，并提供状态恢复、任务派发和复核入口。 它集中维护对话与仓库关系，确保开发任务从已确认的 integration HEAD 建立独立 worktree。

## 什么时候需要修改

调整绑定身份、Harness 能力、派发前提、管理 Prompt 或复核结构时需要修改。

## 在代码中的位置

[打开源码：scripts/ckb_core/management_agent.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/management_agent.py:1:1)  `scripts/ckb_core/management_agent.py:1-1399`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[append 等测试场景]]。
- 实现时会用到 [[audit_gap_register 与 _root 的协作实现]]。
- 主要代码单元是 [[bind_conversation]]。
- 实现时会用到 [[check_fact_freshness]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[maintenance_check]]。
- 实现时会用到 [[maintenance_check 与 capability_matrix 的协作实现]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[validate_human_maintenance_invocation 与 ParameterSpec 的协作实现]]。

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

<details><summary>查看本页收纳的 42 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `default_management_registry_path` | `default_management_registry_path` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `management_human_maintenance_prompt_contract` | 该函数完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `_path_key` | `_path_key` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_normalized_path` | `_normalized_path` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_empty_registry` | `_empty_registry` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_read_registry` | `_read_registry` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_registry_lock` | `_registry_lock` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_locked_registry` | `_locked_registry` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_audit_event` | `_audit_event` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_capability` | `_capability` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `harness_capabilities` | `harness_capabilities` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `binding_schema` | `binding_schema` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `canonical_binding_input` | `canonical_binding_input` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_privacy_errors` | `_privacy_errors` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `audit_manager_registry` | `audit_manager_registry` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_git` | `_git` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_is_within` | `_is_within` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_git_preflight` | 核对管理 workspace、知识库、Git 根、integration branch 和 HEAD，并把工作树脏状态作为结果返回而不是阻止身份登记。 |
| `_binding_identity` | `_binding_identity` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_binding_project` | `_binding_project` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_binding_id` | `_binding_id` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_find_binding` | `_find_binding` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_runtime_state` | `_runtime_state` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `binding_status` | 重新读取绑定仓库的分支、HEAD、工作树和知识事实新鲜度，并据此报告 ready 或 blocked。 |
| `unbind_conversation` | `unbind_conversation` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_sqlite_integrity` | `_sqlite_integrity` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_feedback_snapshot` | `_feedback_snapshot` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_knowledge_snapshot` | `_knowledge_snapshot` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_single_quote` | `_single_quote` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_manager_commands` | `_manager_commands` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_management_prompt` | `_management_prompt` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `audit_management_prompt` | `audit_management_prompt` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `management_context` | `management_context` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_task_id` | `_task_id` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_task_artifact_root` | `_task_artifact_root` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_find_task` | `_find_task` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_record_task_collaboration` | `_record_task_collaboration` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_bounded_values` | `_bounded_values` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `_task_prompt` | `_task_prompt` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。 |
| `create_management_task` | 只在绑定状态、知识库状态和 Git 派发条件满足时，从固定 HEAD 创建独立开发 worktree。 |
| `management_task_status` | 核对开发 worktree、提交、验证记录和 integration HEAD，计算是否达到合并就绪状态。 |
| `review_management_task` | 执行任务约定的真实测试并把退出状态和输出摘要写入结构化复核记录。 |

</details>
