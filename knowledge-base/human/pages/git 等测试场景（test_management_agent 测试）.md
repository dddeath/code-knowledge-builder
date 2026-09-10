# git 等测试场景（test_management_agent 测试）

标签：#类型/代码

> 该测试文件覆盖管理身份登记、状态阻断、并发幂等、任务派发和真实复核。 它验证脏工作树可先绑定，同时派发、合并和知识事实边界继续生效。

## 什么时候需要修改

调整管理注册表、绑定生命周期、派发结构或复核规则时需要修改。

## 在代码中的位置

[打开源码：tests/test_management_agent.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_management_agent.py:1:1)  `tests/test_management_agent.py:1-489`

## 相关代码

- 主要代码单元是 [[git（test_management_agent 测试）]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 30 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ManagementSchemaPersistenceTest` | `ManagementSchemaPersistenceTest` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.setUp` | `setUp` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.tearDown` | `tearDown` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.payload` | `payload` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.test_public_schema_has_four_separate_capabilities_and_privacy_contract` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.test_canonical_input_drops_unrecognized_sensitive_content` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.test_unknown_harness_declares_only_generic_binding` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.test_malformed_registry_is_reported_without_replacement` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append` | 在注册表锁内追加带测试编号的审计事件，供并发写入完整性测试。 |
| `ManagementSchemaPersistenceTest.test_canonical_input_rejects_missing_identity` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementBindingLifecycleTest` | `ManagementBindingLifecycleTest` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.setUp` | `setUp` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.tearDown` | `tearDown` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.payload` | `payload` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_bind_is_idempotent_status_is_live_and_unbind_preserves_audit` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_conflicting_project_for_same_conversation_fails_without_rebinding` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_missing_repo_output_and_branch_fail_while_dirty_tree_can_bind` | 验证缺失对象和错误分支仍失败，同时脏工作树可绑定且状态继续阻止派发。 |
| `ManagementBindingLifecycleTest.test_non_git_unborn_and_missing_state_outputs_fail_preflight` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_missing_conversation_status_and_unbind_fail_without_creating_binding` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_same_workspace_routes_distinct_conversations_to_explicit_nested_repos` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_status_detects_head_drift_and_dirty_tree_after_binding` | 验证绑定后的 HEAD 漂移和工作树修改都会进入明确的阻断状态。 |
| `ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object.bind` | `bind` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object.unbind` | `unbind` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_context_rechecks_feedback_sqlite_and_maintenance_gates` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.ready_context` | `ready_context` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_task_dispatch_creates_independent_worktree_prompt_and_review_gate` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_task_dispatch_is_idempotent_and_blocks_integration_drift` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_task_review_records_literal_failure_without_merge` | 该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。 |

</details>
