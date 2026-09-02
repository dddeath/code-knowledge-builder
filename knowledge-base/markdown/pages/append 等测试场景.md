# append 等测试场景

标签：#类型/代码

> `tests/test_management_agent.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责以可执行样例验证 `test_management_agent.py` 覆盖的成功行为、失败边界和回归约束。

## 什么时候需要修改

当 `tests/test_management_agent.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_management_agent.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_management_agent.py:1:1)  `tests/test_management_agent.py:1-475`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[_Transport.close]]。
- 主要代码单元是 [[append]]。
- 实现时会用到 [[audit_global 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[bind_conversation]]。
- 实现时会用到 [[bind_conversation 与 default_management_registry_path 的协作实现]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。

## 谁会来到这里

- [[_Transport.close 与 _StartGate 的协作实现]] 关联到这里的验证场景。
- [[audit_gap_register]] 关联到这里的验证场景。
- [[audit_operation_journal]] 关联到这里的验证场景。
- [[bind_conversation]] 关联到这里的验证场景。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 关联到这里的验证场景。
- [[maintenance_check 与 capability_matrix 的协作实现]] 关联到这里的验证场景。
- [[parser]] 会使用这里提供的行为。
- [[preflight]] 关联到这里的验证场景。
- [[retrieve_machine]] 关联到这里的验证场景。
- [[run_keyword_provider]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[ScopeExtensionTest]]
- [[build_manual_index 等测试场景]]
- [[command 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 30 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `git` | `git` 是第 36-46 行的函数，供所属页面定位实现。 |
| `ManagementSchemaPersistenceTest` | `ManagementSchemaPersi...` 是第 49-125 行的类，供所属页面定位实现。 |
| `ManagementSchemaPersistenceTest.setUp` | `ManagementSchemaPersi...` 是第 50-55 行的函数，供所属页面定位实现。 |
| `ManagementSchemaPersistenceTest.tearDown` | `ManagementSchemaPersi...` 是第 57-58 行的函数，供所属页面定位实现。 |
| `ManagementSchemaPersistenceTest.payload` | `ManagementSchemaPersi...` 是第 60-70 行的函数，供所属页面定位实现。 |
| `ManagementSchemaPersistenceTest.test_public_schema_has_four_separate_capabilities_and_privacy_contract` | `ManagementSchemaPersi...` 是第 72-78 行的函数，供所属页面定位实现。 |
| `ManagementSchemaPersistenceTest.test_canonical_input_drops_unrecognized_sensitive_content` | `ManagementSchemaPersi...` 是第 80-94 行的函数，供所属页面定位实现。 |
| `ManagementSchemaPersistenceTest.test_unknown_harness_declares_only_generic_binding` | `ManagementSchemaPersi...` 是第 96-101 行的函数，供所属页面定位实现。 |
| `ManagementSchemaPersistenceTest.test_malformed_registry_is_reported_without_replacement` | `ManagementSchemaPersi...` 是第 103-108 行的函数，供所属页面定位实现。 |
| `ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events` | `ManagementSchemaPersi...` 是第 110-119 行的函数，供所属页面定位实现。 |
| `ManagementSchemaPersistenceTest.test_canonical_input_rejects_missing_identity` | `ManagementSchemaPersi...` 是第 121-125 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest` | `ManagementBindingLife...` 是第 128-470 行的类，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.setUp` | `ManagementBindingLife...` 是第 129-155 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.tearDown` | `ManagementBindingLife...` 是第 157-158 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.payload` | `ManagementBindingLife...` 是第 160-170 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_bind_is_idempotent_status_is_live_and_unbind_preserves_audit` | `ManagementBindingLife...` 是第 172-194 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_conflicting_project_for_same_conversation_fails_without_rebinding` | `ManagementBindingLife...` 是第 196-217 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_missing_repo_output_branch_and_dirty_tree_fail_preflight` | `ManagementBindingLife...` 是第 219-229 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_non_git_unborn_and_missing_state_outputs_fail_preflight` | `ManagementBindingLife...` 是第 231-248 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_missing_conversation_status_and_unbind_fail_without_creating_binding` | `ManagementBindingLife...` 是第 250-258 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_same_workspace_routes_distinct_conversations_to_explicit_nested_repos` | `ManagementBindingLife...` 是第 260-288 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_status_detects_head_drift_and_dirty_tree_after_binding` | `ManagementBindingLife...` 是第 290-300 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object` | `ManagementBindingLife...` 是第 302-320 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object.bind` | `ManagementBindingLife...` 是第 303-304 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object.unbind` | `ManagementBindingLife...` 是第 313-314 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_context_rechecks_feedback_sqlite_and_maintenance_gates` | `ManagementBindingLife...` 是第 322-352 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.ready_context` | `ManagementBindingLife...` 是第 354-361 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_task_dispatch_creates_independent_worktree_prompt_and_review_gate` | `ManagementBindingLife...` 是第 363-413 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_task_dispatch_is_idempotent_and_blocks_integration_drift` | `ManagementBindingLife...` 是第 415-448 行的函数，供所属页面定位实现。 |
| `ManagementBindingLifecycleTest.test_task_review_records_literal_failure_without_merge` | `ManagementBindingLife...` 是第 450-470 行的函数，供所属页面定位实现。 |

</details>
