# propose_template 与 _canonical_bytes 的协作实现

标签：#类型/代码

> `scripts/ckb_core/human_page_template_proposals.py` 页面绑定固定源码第 1-1452 行，说明该文件如何承担人类页面模板提议、人工审阅、版本化状态和回滚。 该文件负责人类页面模板提议、人工审阅、版本化状态和回滚，并为相关命令、页面生成或测试提供源码入口。

## 什么时候需要修改

当 `scripts/ckb_core/human_page_template_proposals.py` 的公开输入、生成结果、状态边界或与其他模块的协作关系变化时，应更新本页。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_page_template_proposals.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_page_template_proposals.py:1:1)  `scripts/ckb_core/human_page_template_proposals.py:1-1452`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[get_human_page_template 与 SectionContract 的协作实现]]。
- 实现时会用到 [[graph 的协作边界]]。
- 主要代码单元是 [[propose_template]]。
- 实现时会用到 [[validate]]。

## 谁会来到这里

- [[TemplateProposalStoreTests]] 会使用这里提供的行为。
- [[ingest_reference]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[propose_template]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[HumanPageAuthoringValidationFailureTests 等测试场景]]
- [[PdfReferenceExtractionTests]]
- [[TemplateProposalStoreTests]]

## 内部细节

<details><summary>查看本页收纳的 49 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_canonical_bytes` | `_canonical_bytes` 用于生成稳定序列化或内容摘要。 |
| `_sha256` | `_sha256` 用于生成稳定序列化或内容摘要。 |
| `_store_root` | `_store_root` 用于处理当前模块的结构化输入或状态。 |
| `_validated_output` | `_validated_output` 用于校验输入、状态、证据或输出合同。 |
| `_expect_object` | `_expect_object` 用于处理当前模块的结构化输入或状态。 |
| `_expect_fields` | `_expect_fields` 用于处理当前模块的结构化输入或状态。 |
| `_text` | `_text` 用于处理当前模块的结构化输入或状态。 |
| `_string_list` | `_string_list` 用于处理当前模块的结构化输入或状态。 |
| `_boolean` | `_boolean` 用于处理当前模块的结构化输入或状态。 |
| `_integer` | `_integer` 用于处理当前模块的结构化输入或状态。 |
| `_semantic_version` | `_semantic_version` 用于处理当前模块的结构化输入或状态。 |
| `_semantic_version_key` | `_semantic_version_key` 用于处理当前模块的结构化输入或状态。 |
| `_template_name` | `_template_name` 用于处理当前模块的结构化输入或状态。 |
| `_target_document` | `_target_document` 用于处理当前模块的结构化输入或状态。 |
| `_validate_target` | `_validate_target` 用于校验输入、状态、证据或输出合同。 |
| `_normalize_count_budget` | `_normalize_count_budget` 用于规范化输入字段并拒绝未知或越界值。 |
| `_normalize_section_length_budget` | `_normalize_section_length_budget` 用于规范化输入字段并拒绝未知或越界值。 |
| `_normalize_section_link_budget` | `_normalize_section_link_budget` 用于规范化输入字段并拒绝未知或越界值。 |
| `_normalize_fields` | `_normalize_fields` 用于规范化输入字段并拒绝未知或越界值。 |
| `_normalize_sections` | `_normalize_sections` 用于规范化输入字段并拒绝未知或越界值。 |
| `_normalize_examples` | `_normalize_examples` 用于规范化输入字段并拒绝未知或越界值。 |
| `normalize_template_proposal` | `normalize_template_proposal` 用于规范化输入字段并拒绝未知或越界值。 |
| `template_proposal_skeleton` | `template_proposal_skeleton` 用于处理当前模块的结构化输入或状态。 |
| `write_template_proposal_skeleton` | `write_template_proposal_skeleton` 用于生成范围受控且可重新打开的输出。 |
| `_store_schema_document` | `_store_schema_document` 用于处理当前模块的结构化输入或状态。 |
| `_validate_store_schema` | `_validate_store_schema` 用于校验输入、状态、证据或输出合同。 |
| `_prepare_store` | `_prepare_store` 用于处理当前模块的结构化输入或状态。 |
| `_initialize_store_locked` | `_initialize_store_locked` 用于创建受控候选状态而不越过后续确认边界。 |
| `_store_lock` | `_store_lock` 用于处理当前模块的结构化输入或状态。 |
| `_proposal_event_errors` | `_proposal_event_errors` 用于处理当前模块的结构化输入或状态。 |
| `_reviewer` | `_reviewer` 用于处理当前模块的结构化输入或状态。 |
| `_audit_event_errors` | `_audit_event_errors` 用于汇总并判断受控对象是否满足当前合同。 |
| `_rollback_event_errors` | `_rollback_event_errors` 用于执行范围受控的恢复或撤销。 |
| `_load_events` | `_load_events` 用于读取、定位并返回现有状态。 |
| `_builtin_items` | `_builtin_items` 用于处理当前模块的结构化输入或状态。 |
| `_item_sort_key` | `_item_sort_key` 用于处理当前模块的结构化输入或状态。 |
| `_index_from_events` | `_index_from_events` 用于处理当前模块的结构化输入或状态。 |
| `_operation_log_bytes` | `_operation_log_bytes` 用于生成稳定序列化或内容摘要。 |
| `_atomic_write_bytes` | `_atomic_write_bytes` 用于生成稳定序列化或内容摘要。 |
| `_rebuild_store` | `_rebuild_store` 用于处理当前模块的结构化输入或状态。 |
| `_load_verified_store` | `_load_verified_store` 用于读取、定位并返回现有状态。 |
| `_validate_local_version` | `_validate_local_version` 用于校验输入、状态、证据或输出合同。 |
| `validate_template_proposal` | `validate_template_proposal` 用于校验输入、状态、证据或输出合同。 |
| `list_templates` | `list_templates` 用于读取、定位并返回现有状态。 |
| `show_template` | `show_template` 用于读取、定位并返回现有状态。 |
| `_event_by_id` | `_event_by_id` 用于处理当前模块的结构化输入或状态。 |
| `_proposal_payload` | `_proposal_payload` 用于处理当前模块的结构化输入或状态。 |
| `audit_template_proposal` | `audit_template_proposal` 用于汇总并判断受控对象是否满足当前合同。 |
| `rollback_template_extension` | `rollback_template_extension` 用于执行范围受控的恢复或撤销。 |

</details>
