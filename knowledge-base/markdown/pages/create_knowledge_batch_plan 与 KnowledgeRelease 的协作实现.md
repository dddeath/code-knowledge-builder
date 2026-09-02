# create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现

标签：#类型/代码

> `scripts/ckb_core/knowledge_batch_migration.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责完整知识库批量迁移的计划、隔离构建、审计、切换和精确回滚。

## 什么时候需要修改

当 `scripts/ckb_core/knowledge_batch_migration.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/knowledge_batch_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_batch_migration.py:1:1)  `scripts/ckb_core/knowledge_batch_migration.py:1-2076`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_agent_protocol]]。
- 实现时会用到 [[audit_agent_protocol 与 _default_python 的协作实现]]。
- 实现时会用到 [[audit_gap_register]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[audit_operation_journal]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[create_batch_plan 与 ProtocolRelease 的协作实现]]。
- 主要代码单元是 [[create_knowledge_batch_plan]]。
- 实现时会用到 [[finalize]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[ingest_reference 与 _root 的协作实现]]。
- 实现时会用到 [[refresh 等测试场景]]。
- 实现时会用到 [[start_scope_extension 与 _error 的协作实现]]。

## 谁会来到这里

- [[command 等测试场景]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[refresh 等测试场景]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[command 等测试场景]]
- [[refresh 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 61 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `KnowledgeRelease` | `KnowledgeRelease` 是第 113-121 行的类，供所属页面定位实现。 |
| `_canonical_bytes` | `_canonical_bytes` 是第 191-192 行的函数，供所属页面定位实现。 |
| `_digest_value` | `_digest_value` 是第 195-196 行的函数，供所属页面定位实现。 |
| `_reject_unknown` | `_reject_unknown` 是第 199-202 行的函数，供所属页面定位实现。 |
| `_object` | `_object` 是第 205-208 行的函数，供所属页面定位实现。 |
| `_absolute` | `_absolute` 是第 211-217 行的函数，供所属页面定位实现。 |
| `_within_any` | `_within_any` 是第 220-221 行的函数，供所属页面定位实现。 |
| `_normalized_protocol` | `_normalized_protocol` 是第 224-227 行的函数，供所属页面定位实现。 |
| `_release_for` | `_release_for` 是第 230-240 行的函数，供所属页面定位实现。 |
| `_release_chain` | `_release_chain` 是第 243-252 行的函数，供所属页面定位实现。 |
| `knowledge_version_matrix` | `knowledge_version_matrix` 是第 255-287 行的函数，供所属页面定位实现。 |
| `_validate_version` | `_validate_version` 是第 290-302 行的函数，供所属页面定位实现。 |
| `_validate_snapshot` | `_validate_snapshot` 是第 305-311 行的函数，供所属页面定位实现。 |
| `_validate_tree_summary` | `_validate_tree_summary` 是第 314-324 行的函数，供所属页面定位实现。 |
| `_validate_structural_manifest` | `_validate_structural_...` 是第 327-373 行的函数，供所属页面定位实现。 |
| `load_knowledge_batch_manifest` | `load_knowledge_batch_...` 是第 376-384 行的函数，供所属页面定位实现。 |
| `_file_record` | `_file_record` 是第 387-394 行的函数，供所属页面定位实现。 |
| `_origin_health` | `_origin_health` 是第 397-491 行的函数，供所属页面定位实现。 |
| `_origin_health.check` | `_origin_health.check` 是第 400-401 行的函数，供所属页面定位实现。 |
| `_complete_layer_inventory` | `_complete_layer_inven...` 是第 494-523 行的函数，供所属页面定位实现。 |
| `_sqlite_schema_versions` | `_sqlite_schema_versions` 是第 526-542 行的函数，供所属页面定位实现。 |
| `_normalized_scope` | `_normalized_scope` 是第 545-561 行的函数，供所属页面定位实现。 |
| `_path_risks` | `_path_risks` 是第 564-569 行的函数，供所属页面定位实现。 |
| `_operation_token` | `_operation_token` 是第 572-573 行的函数，供所属页面定位实现。 |
| `_project_operation_id` | `_project_operation_id` 是第 576-586 行的函数，供所属页面定位实现。 |
| `_paths_overlap` | `_paths_overlap` 是第 589-590 行的函数，供所属页面定位实现。 |
| `_validate_recovery_topology` | `_validate_recovery_to...` 是第 593-634 行的函数，供所属页面定位实现。 |
| `_validate_origin_record_keys` | `_validate_origin_reco...` 是第 637-660 行的函数，供所属页面定位实现。 |
| `_inspect_knowledge_project` | `_inspect_knowledge_pr...` 是第 663-885 行的函数，供所属页面定位实现。 |
| `_load_knowledge_batch_plan` | `_load_knowledge_batch...` 是第 959-972 行的函数，供所属页面定位实现。 |
| `_verify_plan_manifest_binding` | `_verify_plan_manifest...` 是第 975-990 行的函数，供所属页面定位实现。 |
| `_save_knowledge_state` | `_save_knowledge_state` 是第 993-995 行的函数，供所属页面定位实现。 |
| `_load_knowledge_state` | `_load_knowledge_state` 是第 998-1007 行的函数，供所属页面定位实现。 |
| `_state_event` | `_state_event` 是第 1010-1029 行的函数，供所属页面定位实现。 |
| `_new_knowledge_state` | `_new_knowledge_state` 是第 1032-1068 行的函数，供所属页面定位实现。 |
| `_summarize_knowledge_state` | `_summarize_knowledge_...` 是第 1071-1092 行的函数，供所属页面定位实现。 |
| `_manifest_matches` | `_manifest_matches` 是第 1095-1096 行的函数，供所属页面定位实现。 |
| `_manifest_delta` | `_manifest_delta` 是第 1099-1113 行的函数，供所属页面定位实现。 |
| `_verify_plan_bindings` | `_verify_plan_bindings` 是第 1116-1126 行的函数，供所属页面定位实现。 |
| `_knowledge_output_lock` | `_knowledge_output_lock` 是第 1129-1139 行的函数，供所属页面定位实现。 |
| `_detach_staging_workspace_roots` | `_detach_staging_works...` 是第 1142-1157 行的函数，供所属页面定位实现。 |
| `_cold_build` | `_cold_build` 是第 1160-1232 行的函数，供所属页面定位实现。 |
| `_project_record` | `_project_record` 是第 1235-1260 行的函数，供所属页面定位实现。 |
| `_pending_reviews` | `_pending_reviews` 是第 1263-1265 行的函数，供所属页面定位实现。 |
| `_mutable_preservation_check` | `_mutable_preservation...` 是第 1268-1280 行的函数，供所属页面定位实现。 |
| `_old_entity_id_errors` | `_old_entity_id_errors` 是第 1283-1289 行的函数，供所属页面定位实现。 |
| `_knowledge_project_audit` | `_knowledge_project_audit` 是第 1292-1424 行的函数，供所属页面定位实现。 |
| `_knowledge_project_audit.check` | `_knowledge_project_au...` 是第 1297-1298 行的函数，供所属页面定位实现。 |
| `_apply_one_project` | `_apply_one_project` 是第 1427-1503 行的函数，供所属页面定位实现。 |
| `apply_knowledge_batch_plan` | `apply_knowledge_batch...` 是第 1506-1552 行的函数，供所属页面定位实现。 |
| `resume_knowledge_batch_state` | `resume_knowledge_batc...` 是第 1555-1561 行的函数，供所属页面定位实现。 |
| `knowledge_batch_status` | `knowledge_batch_status` 是第 1564-1620 行的函数，供所属页面定位实现。 |
| `audit_knowledge_batch_state` | `audit_knowledge_batch...` 是第 1623-1679 行的函数，供所属页面定位实现。 |
| `_control_path` | `_control_path` 是第 1682-1683 行的函数，供所属页面定位实现。 |
| `_control_records` | `_control_records` 是第 1686-1695 行的函数，供所属页面定位实现。 |
| `_active_control` | `_active_control` 是第 1698-1709 行的函数，供所属页面定位实现。 |
| `_protocol_digest` | `_protocol_digest` 是第 1712-1718 行的函数，供所属页面定位实现。 |
| `_cutover_one` | `_cutover_one` 是第 1721-1880 行的函数，供所属页面定位实现。 |
| `cutover_knowledge_batch_state` | `cutover_knowledge_bat...` 是第 1883-1923 行的函数，供所属页面定位实现。 |
| `_rollback_one` | `_rollback_one` 是第 1926-2032 行的函数，供所属页面定位实现。 |
| `rollback_knowledge_batch_state` | `rollback_knowledge_ba...` 是第 2035-2075 行的函数，供所属页面定位实现。 |

</details>
