# append 等测试场景

标签：#类型/代码

> 文件 `tests/test_management_agent.py`负责验证跨 Harness 对话绑定、仓库预检、任务派发和管理复查。 它属于管理 Agent 持久化与隔离开发流程的回归保护，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当绑定协议、Harness 能力、任务 worktree 或管理审阅门变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：tests/test_management_agent.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_management_agent.py:1:1)  `tests/test_management_agent.py:1-484`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[_Transport.close]]。
- 主要代码单元是 [[append]]。
- 实现时会用到 [[bind_conversation]]。
- 实现时会用到 [[bind_conversation 与 default_management_registry_path 的协作实现]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[audit_gap_register]] 关联到这里的验证场景。
- [[audit_operation_journal]] 关联到这里的验证场景。
- [[bind_conversation]] 关联到这里的验证场景。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 关联到这里的验证场景。
- [[maintenance_check 与 capability_matrix 的协作实现]] 关联到这里的验证场景。
- [[parser]] 会使用这里提供的行为。
- [[preflight]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[PdfReferenceExtractionTests]]
- [[PdfReferenceExtractionTests 等测试场景]]
- [[command 等测试场景]]
- [[main（benchmark_obsidian_canvas_navigation 测试）]]
- [[main（generate_large_fixture 测试）]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 30 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `git` | `git` 完成管理 Agent 回归验证中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest` | `setUp` 完成管理 Agent 回归验证中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.setUp` | `setUp` 完成管理 Agent 回归验证中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.tearDown` | `tearDown` 完成管理 Agent 回归验证中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.payload` | `payload` 完成管理 Agent 回归验证中的一个明确步骤。 |
| `ManagementSchemaPersistenceTest.test_public_schema_has_four_separate_capabilities_and_privacy_contract` | 该测试验证“public schema has four separa…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementSchemaPersistenceTest.test_canonical_input_drops_unrecognized_sensitive_content` | 该测试验证“canonical input drops unrecog…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementSchemaPersistenceTest.test_unknown_harness_declares_only_generic_binding` | 该测试验证“unknown harness declares only…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementSchemaPersistenceTest.test_malformed_registry_is_reported_without_replacement` | 该测试验证“malformed registry is reporte…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events` | 该测试验证“locked registry serializes co…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementSchemaPersistenceTest.test_canonical_input_rejects_missing_identity` | 该测试验证“canonical input rejects missi…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest` | `setUp` 完成管理 Agent 回归验证中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.setUp` | `setUp` 完成管理 Agent 回归验证中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.tearDown` | `tearDown` 完成管理 Agent 回归验证中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.payload` | `payload` 完成管理 Agent 回归验证中的一个明确步骤。 |
| `ManagementBindingLifecycleTest.test_bind_is_idempotent_status_is_live_and_unbind_preserves_audit` | 该测试验证“bind is idempotent status is …”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest.test_conflicting_project_for_same_conversation_fails_without_rebinding` | 该测试验证“conflicting project for same …”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest.test_missing_repo_output_branch_and_dirty_tree_fail_preflight` | 该测试验证“missing repo output branch an…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest.test_non_git_unborn_and_missing_state_outputs_fail_preflight` | 该测试验证“non git unborn and missing st…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest.test_missing_conversation_status_and_unbind_fail_without_creating_binding` | 该测试验证“missing conversation status a…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest.test_same_workspace_routes_distinct_conversations_to_explicit_nested_repos` | 该测试验证“same workspace routes distinc…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest.test_status_detects_head_drift_and_dirty_tree_after_binding` | 该测试验证“status detects head drift and…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object` | 该测试验证“concurrent repeated bind and …”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object.bind` | `bind` 登记并持久化管理 Agent 回归验证所需的数据或状态。 |
| `ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object.unbind` | `unbind` 受控释放或回滚管理 Agent 回归验证所需的数据或状态。 |
| `ManagementBindingLifecycleTest.test_context_rechecks_feedback_sqlite_and_maintenance_gates` | 该测试验证“context rechecks feedback sql…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest.ready_context` | `ready_context` 读取并判定管理 Agent 回归验证所需的数据或状态。 |
| `ManagementBindingLifecycleTest.test_task_dispatch_creates_independent_worktree_prompt_and_review_gate` | 该测试验证“task dispatch creates indepen…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest.test_task_dispatch_is_idempotent_and_blocks_integration_drift` | 该测试验证“task dispatch is idempotent a…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |
| `ManagementBindingLifecycleTest.test_task_review_records_literal_failure_without_merge` | 该测试验证“task review records literal f…”场景，保护管理 Agent 回归验证的预期结果与失败边界。 |

</details>
