# ingest_event 与 default_registry_path 的协作实现

标签：#类型/代码

> `scripts/ckb_core/automation.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责跨 Harness 自动化事件、会话状态、任务队列和 SQLite 状态的确定性处理。

## 什么时候需要修改

当 `scripts/ckb_core/automation.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1744`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[doctor_report 与 _version_matches 的协作实现]]。
- 实现时会用到 [[execute]]。
- 主要代码单元是 [[ingest_event]]。
- 实现时会用到 [[record_note]]。
- 实现时会用到 [[record_note 与 page_tag 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.register]] 会使用这里提供的行为。
- [[AutomationTest.register 等测试场景]] 会使用这里提供的行为。
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
- [[KeywordFallbackRetrievalWiringTests]]
- [[KeywordFallbackRetrievalWiringTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 56 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `default_registry_path` | `default_registry_path` 是第 127-129 行的函数，供所属页面定位实现。 |
| `_path_key` | `_path_key` 是第 132-135 行的函数，供所属页面定位实现。 |
| `_is_within` | `_is_within` 是第 138-141 行的函数，供所属页面定位实现。 |
| `_read_registry` | `_read_registry` 是第 144-171 行的函数，供所属页面定位实现。 |
| `register_project` | `register_project` 是第 174-246 行的函数，供所属页面定位实现。 |
| `unregister_project` | `unregister_project` 是第 249-261 行的函数，供所属页面定位实现。 |
| `registry_status` | `registry_status` 是第 264-273 行的函数，供所属页面定位实现。 |
| `_registration_for_event` | `_registration_for_event` 是第 276-293 行的函数，供所属页面定位实现。 |
| `_event_path_text` | `_event_path_text` 是第 296-324 行的函数，供所属页面定位实现。 |
| `_walk_values` | `_walk_values` 是第 327-335 行的函数，供所属页面定位实现。 |
| `_first_scalar` | `_first_scalar` 是第 338-355 行的函数，供所属页面定位实现。 |
| `_text_content` | `_text_content` 是第 358-373 行的函数，供所属页面定位实现。 |
| `_event_name` | `_event_name` 是第 376-384 行的函数，供所属页面定位实现。 |
| `_message_role` | `_message_role` 是第 387-388 行的函数，供所属页面定位实现。 |
| `_normalized_skill_name` | `_normalized_skill_name` 是第 391-393 行的函数，供所属页面定位实现。 |
| `_skill_name` | `_skill_name` 是第 396-413 行的函数，供所属页面定位实现。 |
| `_canonical_type` | `_canonical_type` 是第 416-463 行的函数，供所属页面定位实现。 |
| `_extract_paths` | `_extract_paths` 是第 466-476 行的函数，供所属页面定位实现。 |
| `normalize_event` | `normalize_event` 是第 479-549 行的函数，供所属页面定位实现。 |
| `_redact_text` | `_redact_text` 是第 552-576 行的函数，供所属页面定位实现。 |
| `redact_event` | `redact_event` 是第 579-602 行的函数，供所属页面定位实现。 |
| `redact_event.redact` | `redact_event.redact` 是第 583-597 行的函数，供所属页面定位实现。 |
| `_automation_root` | `_automation_root` 是第 605-609 行的函数，供所属页面定位实现。 |
| `initialize_automation_database` | `initialize_automation...` 是第 612-724 行的函数，供所属页面定位实现。 |
| `_git_status_paths` | `_git_status_paths` 是第 727-747 行的函数，供所属页面定位实现。 |
| `_change_path_allowed` | `_change_path_allowed` 是第 750-752 行的函数，供所属页面定位实现。 |
| `_working_file_state` | `_working_file_state` 是第 755-770 行的函数，供所属页面定位实现。 |
| `_relative_changed_paths` | `_relative_changed_paths` 是第 773-804 行的函数，供所属页面定位实现。 |
| `_drain_lock` | `_drain_lock` 是第 808-835 行的函数，供所属页面定位实现。 |
| `enqueue_event` | `enqueue_event` 是第 838-845 行的函数，供所属页面定位实现。 |
| `_spool_events` | `_spool_events` 是第 848-849 行的函数，供所属页面定位实现。 |
| `_session_key` | `_session_key` 是第 852-853 行的函数，供所属页面定位实现。 |
| `default_session_id` | `default_session_id` 是第 856-861 行的函数，供所属页面定位实现。 |
| `_activation_key` | `_activation_key` 是第 864-865 行的函数，供所属页面定位实现。 |
| `_record_skill_activation` | `_record_skill_activation` 是第 868-905 行的函数，供所属页面定位实现。 |
| `_skill_activation` | `_skill_activation` 是第 908-922 行的函数，供所属页面定位实现。 |
| `activate_skill_session` | `activate_skill_session` 是第 925-967 行的函数，供所属页面定位实现。 |
| `_remove_skill_activation` | `_remove_skill_activation` 是第 970-982 行的函数，供所属页面定位实现。 |
| `_explicit_skill_application` | `_explicit_skill_appli...` 是第 985-995 行的函数，供所属页面定位实现。 |
| `_ensure_session` | `_ensure_session` 是第 998-1027 行的函数，供所属页面定位实现。 |
| `_resolve_turn` | `_resolve_turn` 是第 1030-1083 行的函数，供所属页面定位实现。 |
| `_event_id` | `_event_id` 是第 1086-1107 行的函数，供所属页面定位实现。 |
| `_pending_review_content` | `_pending_review_content` 是第 1110-1136 行的函数，供所属页面定位实现。 |
| `_create_pending_review` | `_create_pending_review` 是第 1139-1212 行的函数，供所属页面定位实现。 |
| `_process_event` | `_process_event` 是第 1215-1301 行的函数，供所属页面定位实现。 |
| `drain_automation` | `drain_automation` 是第 1304-1350 行的函数，供所属页面定位实现。 |
| `retry_failed_automation` | `retry_failed_automation` 是第 1353-1367 行的函数，供所属页面定位实现。 |
| `_hook_context` | `_hook_context` 是第 1370-1376 行的函数，供所属页面定位实现。 |
| `_hook_output` | `_hook_output` 是第 1379-1391 行的函数，供所属页面定位实现。 |
| `automation_status` | `automation_status` 是第 1507-1534 行的函数，供所属页面定位实现。 |
| `pending_automation_reviews` | `pending_automation_re...` 是第 1537-1559 行的函数，供所属页面定位实现。 |
| `write_automation_review_template` | `write_automation_revi...` 是第 1562-1602 行的函数，供所属页面定位实现。 |
| `_heading_errors` | `_heading_errors` 是第 1605-1613 行的函数，供所属页面定位实现。 |
| `review_automation` | `review_automation` 是第 1616-1690 行的函数，供所属页面定位实现。 |
| `search_automation` | `search_automation` 是第 1693-1719 行的函数，供所属页面定位实现。 |
| `automation_documents` | `automation_documents` 是第 1722-1743 行的函数，供所属页面定位实现。 |

</details>
