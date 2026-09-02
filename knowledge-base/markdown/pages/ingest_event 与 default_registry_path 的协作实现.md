# ingest_event 与 default_registry_path 的协作实现

标签：#类型/代码

> 文件 `scripts/ckb_core/automation.py`负责接收多 Harness 事件，维持会话级 Skill 激活状态，并把待审阅事实写入机器层。 它属于自动采集与受控人类投影之间的会话生命周期边界，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当事件格式、会话身份、激活规则、并发锁或审阅流程变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1783`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[check_fact_freshness]]。
- 实现时会用到 [[check_fact_freshness 与 _root 的协作实现]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[doctor_report 与 _version_matches 的协作实现]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 主要代码单元是 [[ingest_event]]。
- 实现时会用到 [[record_note]]。
- 实现时会用到 [[record_note 与 page_tag 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.register]] 会使用这里提供的行为。
- [[AutomationTest.register 等测试场景]] 会使用这里提供的行为。
- [[FactFreshnessStateMachineTest 等测试场景]] 会使用这里提供的行为。
- [[SessionStdioLifecycleTests]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[ingest_event]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.register]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[FactFreshnessStateMachineTest 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 56 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `default_registry_path` | `default_registry_path` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_path_key` | `_path_key` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_is_within` | `_is_within` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_read_registry` | `_read_registry` 读取并判定多 Harness 会话自动化所需的数据或状态。 |
| `register_project` | `register_project` 登记并持久化多 Harness 会话自动化所需的数据或状态。 |
| `unregister_project` | `unregister_project` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `registry_status` | `registry_status` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_registration_for_event` | `_registration_for_event` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_event_path_text` | `_event_path_text` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_walk_values` | `_walk_values` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_first_scalar` | `_first_scalar` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_text_content` | `_text_content` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_event_name` | `_event_name` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_message_role` | `_message_role` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_normalized_skill_name` | `_normalized_skill_name` 解析并归一化多 Harness 会话自动化所需的数据或状态。 |
| `_skill_name` | `_skill_name` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_canonical_type` | `_canonical_type` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_extract_paths` | `_extract_paths` 解析并归一化多 Harness 会话自动化所需的数据或状态。 |
| `normalize_event` | `normalize_event` 解析并归一化多 Harness 会话自动化所需的数据或状态。 |
| `_redact_text` | `_redact_text` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `redact_event` | `redact_event` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `redact_event.redact` | `redact` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_automation_root` | `_automation_root` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `initialize_automation_database` | `initialize_automation_database` 创建并初始化多 Harness 会话自动化所需的数据或状态。 |
| `_git_status_paths` | `_git_status_paths` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_change_path_allowed` | `_change_path_allowed` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_working_file_state` | `_working_file_state` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_relative_changed_paths` | `_relative_changed_paths` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_drain_lock` | `_drain_lock` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `enqueue_event` | `enqueue_event` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_spool_events` | `_spool_events` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_session_key` | `_session_key` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `default_session_id` | `default_session_id` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_activation_key` | `_activation_key` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_record_skill_activation` | `_record_skill_activation` 登记并持久化多 Harness 会话自动化所需的数据或状态。 |
| `_skill_activation` | `_skill_activation` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `activate_skill_session` | `activate_skill_session` 登记并持久化多 Harness 会话自动化所需的数据或状态。 |
| `_remove_skill_activation` | `_remove_skill_activation` 受控释放或回滚多 Harness 会话自动化所需的数据或状态。 |
| `_explicit_skill_application` | `_explicit_skill_application` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_ensure_session` | `_ensure_session` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_resolve_turn` | `_resolve_turn` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_event_id` | `_event_id` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_pending_review_content` | `_pending_review_content` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_create_pending_review` | `_create_pending_review` 创建并初始化多 Harness 会话自动化所需的数据或状态。 |
| `_process_event` | `_process_event` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `drain_automation` | `drain_automation` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `retry_failed_automation` | `retry_failed_automation` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_hook_context` | `_hook_context` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `_hook_output` | `_hook_output` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `automation_status` | `automation_status` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `pending_automation_reviews` | `pending_automation_reviews` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `write_automation_review_template` | `write_automation_review_template` 生成并写入多 Harness 会话自动化所需的数据或状态。 |
| `_heading_errors` | `_heading_errors` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `review_automation` | `review_automation` 完成多 Harness 会话自动化中的一个明确步骤。 |
| `search_automation` | `search_automation` 检索并组织多 Harness 会话自动化所需的数据或状态。 |
| `automation_documents` | `automation_documents` 完成多 Harness 会话自动化中的一个明确步骤。 |

</details>
