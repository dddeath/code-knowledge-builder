# create_batch_plan 与 ProtocolRelease 的协作实现

标签：#类型/代码

> `scripts/ckb_core/agent_protocol_batch.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责批量升级 Agent Protocol，包括计划、锁、备份、审计、切换和回滚。

## 什么时候需要修改

当 `scripts/ckb_core/agent_protocol_batch.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_protocol_batch.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol_batch.py:1:1)  `scripts/ckb_core/agent_protocol_batch.py:1-1714`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_agent_protocol]]。
- 实现时会用到 [[audit_agent_protocol 与 _default_python 的协作实现]]。
- 实现时会用到 [[audit_operation_journal 与 _root 的协作实现]]。
- 实现时会用到 [[audit_output_contract 与 _default_ckb 的协作实现]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[contracts 的协作边界（2ef5688e）]]。
- 主要代码单元是 [[create_batch_plan]]。
- 实现时会用到 [[ingest]]。
- 实现时会用到 [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]]。
- 实现时会用到 [[retrieve]]。
- 实现时会用到 [[start_scope_extension 与 _error 的协作实现]]。

## 谁会来到这里

- [[AgentProtocolBatchApplyTests]] 会使用这里提供的行为。
- [[AgentProtocolBatchApplyTests 等测试场景]] 会使用这里提供的行为。
- [[create_batch_plan]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[run]] 会使用这里提供的行为。
- [[run 等测试场景]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[RecordReplaceTests]]
- [[RecordReplaceTests 等测试场景]]
- [[command 等测试场景]]
- [[refresh 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 61 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ProtocolRelease` | `ProtocolRelease` 是第 68-73 行的类，供所属页面定位实现。 |
| `supported_upgrade_path` | `supported_upgrade_path` 是第 112-126 行的函数，供所属页面定位实现。 |
| `version_matrix` | `version_matrix` 是第 129-143 行的函数，供所属页面定位实现。 |
| `reject_unknown_fields` | `reject_unknown_fields` 是第 146-149 行的函数，供所属页面定位实现。 |
| `require_absolute_path` | `require_absolute_path` 是第 152-158 行的函数，供所属页面定位实现。 |
| `BatchProjectError` | `BatchProjectError` 是第 161-164 行的类，供所属页面定位实现。 |
| `BatchProjectError.__init__` | `BatchProjectError.__i...` 是第 162-164 行的函数，供所属页面定位实现。 |
| `_canonical_bytes` | `_canonical_bytes` 是第 167-170 行的函数，供所属页面定位实现。 |
| `_digest_value` | `_digest_value` 是第 173-174 行的函数，供所属页面定位实现。 |
| `_sha256_bytes` | `_sha256_bytes` 是第 177-178 行的函数，供所属页面定位实现。 |
| `_single_quote` | `_single_quote` 是第 181-182 行的函数，供所属页面定位实现。 |
| `command_examples_for_version` | `command_examples_for_...` 是第 185-224 行的函数，供所属页面定位实现。 |
| `protocol_text_for_version` | `protocol_text_for_ver...` 是第 227-378 行的函数，供所属页面定位实现。 |
| `adapter_texts_for_version` | `adapter_texts_for_ver...` 是第 381-382 行的函数，供所属页面定位实现。 |
| `_record_roots` | `_record_roots` 是第 385-391 行的函数，供所属页面定位实现。 |
| `_tracked_paths` | `_tracked_paths` 是第 394-419 行的函数，供所属页面定位实现。 |
| `snapshot_files` | `snapshot_files` 是第 422-435 行的函数，供所属页面定位实现。 |
| `snapshot_digest` | `snapshot_digest` 是第 438-439 行的函数，供所属页面定位实现。 |
| `_normalized_managed_block` | `_normalized_managed_b...` 是第 442-447 行的函数，供所属页面定位实现。 |
| `_validate_workspace_managed` | `_validate_workspace_m...` 是第 450-465 行的函数，供所属页面定位实现。 |
| `_validate_internal_adapters` | `_validate_internal_ad...` 是第 468-482 行的函数，供所属页面定位实现。 |
| `_within_any` | `_within_any` 是第 485-486 行的函数，供所属页面定位实现。 |
| `_validate_structural_manifest` | `_validate_structural_...` 是第 489-527 行的函数，供所属页面定位实现。 |
| `load_batch_manifest` | `load_batch_manifest` 是第 530-538 行的函数，供所属页面定位实现。 |
| `_inspect_project` | `_inspect_project` 是第 541-654 行的函数，供所属页面定位实现。 |
| `_load_batch_plan` | `_load_batch_plan` 是第 717-732 行的函数，供所属页面定位实现。 |
| `_json_bytes` | `_json_bytes` 是第 735-736 行的函数，供所属页面定位实现。 |
| `_replace_workspace_block_bytes` | `_replace_workspace_bl...` 是第 739-759 行的函数，供所属页面定位实现。 |
| `_target_record` | `_target_record` 是第 762-811 行的函数，供所属页面定位实现。 |
| `_desired_project_files` | `_desired_project_files` 是第 814-863 行的函数，供所属页面定位实现。 |
| `_state_file` | `_state_file` 是第 866-873 行的函数，供所属页面定位实现。 |
| `_write_bytes_atomic` | `_write_bytes_atomic` 是第 876-881 行的函数，供所属页面定位实现。 |
| `_desired_inventory` | `_desired_inventory` 是第 884-897 行的函数，供所属页面定位实现。 |
| `_create_backup` | `_create_backup` 是第 900-932 行的函数，供所属页面定位实现。 |
| `_restore_backup` | `_restore_backup` 是第 935-950 行的函数，供所属页面定位实现。 |
| `_commit_desired` | `_commit_desired` 是第 953-964 行的函数，供所属页面定位实现。 |
| `_descriptor_lock` | `_descriptor_lock` 是第 967-984 行的函数，供所属页面定位实现。 |
| `_descriptor_unlock` | `_descriptor_unlock` 是第 987-996 行的函数，供所属页面定位实现。 |
| `_descriptor_bytes` | `_descriptor_bytes` 是第 999-1006 行的函数，供所属页面定位实现。 |
| `_write_lock_descriptor` | `_write_lock_descriptor` 是第 1009-1016 行的函数，供所属页面定位实现。 |
| `_process_start_identity` | `_process_start_identity` 是第 1019-1075 行的函数，供所属页面定位实现。 |
| `_new_output_lock_record` | `_new_output_lock_record` 是第 1078-1092 行的函数，供所属页面定位实现。 |
| `_parse_output_lock` | `_parse_output_lock` 是第 1095-1111 行的函数，供所属页面定位实现。 |
| `_lock_owner_state` | `_lock_owner_state` 是第 1114-1124 行的函数，供所属页面定位实现。 |
| `_legacy_lock_owner_state` | `_legacy_lock_owner_state` 是第 1127-1139 行的函数，供所属页面定位实现。 |
| `_same_lock_file` | `_same_lock_file` 是第 1142-1148 行的函数，供所属页面定位实现。 |
| `_release_output_lock` | `_release_output_lock` 是第 1151-1174 行的函数，供所属页面定位实现。 |
| `_output_lock` | `_output_lock` 是第 1178-1256 行的函数，供所属页面定位实现。 |
| `_append_state_event` | `_append_state_event` 是第 1259-1271 行的函数，供所属页面定位实现。 |
| `_save_state` | `_save_state` 是第 1274-1276 行的函数，供所属页面定位实现。 |
| `_load_state` | `_load_state` 是第 1279-1290 行的函数，供所属页面定位实现。 |
| `_new_state` | `_new_state` 是第 1293-1345 行的函数，供所属页面定位实现。 |
| `_current_digest` | `_current_digest` 是第 1348-1351 行的函数，供所属页面定位实现。 |
| `_recovery_matches` | `_recovery_matches` 是第 1354-1367 行的函数，供所属页面定位实现。 |
| `_write_project_evidence` | `_write_project_evidence` 是第 1370-1392 行的函数，供所属页面定位实现。 |
| `_journal_batch_result` | `_journal_batch_result` 是第 1395-1400 行的函数，供所属页面定位实现。 |
| `_summarize_state` | `_summarize_state` 是第 1403-1411 行的函数，供所属页面定位实现。 |
| `apply_batch_plan` | `apply_batch_plan` 是第 1414-1516 行的函数，供所属页面定位实现。 |
| `batch_status` | `batch_status` 是第 1519-1560 行的函数，供所属页面定位实现。 |
| `audit_batch_state` | `audit_batch_state` 是第 1563-1623 行的函数，供所属页面定位实现。 |
| `rollback_batch_state` | `rollback_batch_state` 是第 1626-1713 行的函数，供所属页面定位实现。 |

</details>
