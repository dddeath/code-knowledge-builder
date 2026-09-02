# propose_template 与 _canonical_bytes 的协作实现

标签：#类型/代码

> `scripts/ckb_core/human_page_template_proposals.py` 页面绑定固定源码第 1-1319 行，说明该文件在输出局部模板提议、人工审计、事件重放和回滚中的整体职责。 该文件负责输出局部模板提议、人工审计、事件重放和回滚，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `scripts/ckb_core/human_page_template_proposals.py` 中 `scripts/ckb_core/human_page_template_proposals.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_page_template_proposals.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_page_template_proposals.py:1:1)  `scripts/ckb_core/human_page_template_proposals.py:1-1319`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[get_human_page_template 与 SectionContract 的协作实现]]。
- 主要代码单元是 [[propose_template]]。
- 实现时会用到 [[rollback]]。
- 实现时会用到 [[validate]]。
- 实现时会用到 [[validate 与 canonical 的协作实现]]。

## 谁会来到这里

- [[TemplateProposalStoreTests]] 会使用这里提供的行为。
- [[audit_references 与 _root 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[propose_template]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[HumanPageAuthoringPackageTests]]
- [[TemplateProposalStoreTests]]

## 内部细节

<details><summary>查看本页收纳的 47 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_canonical_bytes` | `_canonical_bytes` 用于完成局部输入校验、转换或状态更新。 |
| `_sha256` | `_sha256` 在 `human_page_template_proposals.py` 中用于完成输出局部模板提议、人工审计、事件重放和回滚中的局部职责。 |
| `_store_root` | `_store_root` 用于完成局部输入校验、转换或状态更新。 |
| `_validated_output` | `_validated_output` 在 `human_page_template_proposals.py` 中用于校验输入、状态、证据或输出合同。 |
| `_expect_object` | `_expect_object` 在 `human_page_template_proposals.py` 中用于校验输入、状态、证据或输出合同。 |
| `_expect_fields` | `_expect_fields` 在 `human_page_template_proposals.py` 中用于校验输入、状态、证据或输出合同。 |
| `_text` | `_text` 在 `human_page_template_proposals.py` 中用于完成输出局部模板提议、人工审计、事件重放和回滚中的局部职责。 |
| `_string_list` | `_string_list` 在 `human_page_template_proposals.py` 中用于读取、规范化并返回既有状态。 |
| `_boolean` | `_boolean` 用于完成局部输入校验、转换或状态更新。 |
| `_integer` | `_integer` 用于完成局部输入校验、转换或状态更新。 |
| `_semantic_version` | `_semantic_version` 用于完成局部输入校验、转换或状态更新。 |
| `_semantic_version_key` | `_semantic_version_key` 用于完成局部输入校验、转换或状态更新。 |
| `_template_name` | `_template_name` 用于完成局部输入校验、转换或状态更新。 |
| `_target_document` | `_target_document` 在 `human_page_template_proposals.py` 中用于生成稳定排序的结构化表示或人类输出。 |
| `_validate_target` | `_validate_target` 在 `human_page_template_proposals.py` 中用于校验输入、状态、证据或输出合同。 |
| `_normalize_count_budget` | `_normalize_count_budget` 在 `human_page_template_proposals.py` 中用于读取、规范化并返回既有状态。 |
| `_normalize_fields` | `_normalize_fields` 在 `human_page_template_proposals.py` 中用于解析、规范化并冻结调用输入。 |
| `_normalize_sections` | `_normalize_sections` 在 `human_page_template_proposals.py` 中用于解析、规范化并冻结调用输入。 |
| `_normalize_examples` | `_normalize_examples` 在 `human_page_template_proposals.py` 中用于解析、规范化并冻结调用输入。 |
| `normalize_template_proposal` | `normalize_template_proposal` 用于完成局部输入校验、转换或状态更新。 |
| `template_proposal_skeleton` | `template_proposal_skeleton` 用于完成局部输入校验、转换或状态更新。 |
| `write_template_proposal_skeleton` | `write_template_proposal_skeleton` 用于完成局部输入校验、转换或状态更新。 |
| `_store_schema_document` | `_store_schema_document` 用于完成局部输入校验、转换或状态更新。 |
| `_validate_store_schema` | `_validate_store_schema` 用于完成局部输入校验、转换或状态更新。 |
| `_prepare_store` | `_prepare_store` 用于完成局部输入校验、转换或状态更新。 |
| `_initialize_store_locked` | `_initialize_store_locked` 用于完成局部输入校验、转换或状态更新。 |
| `_store_lock` | `_store_lock` 用于完成局部输入校验、转换或状态更新。 |
| `_proposal_event_errors` | `_proposal_event_errors` 用于完成局部输入校验、转换或状态更新。 |
| `_reviewer` | `_reviewer` 用于完成局部输入校验、转换或状态更新。 |
| `_audit_event_errors` | `_audit_event_errors` 在 `human_page_template_proposals.py` 中用于校验输入、状态、证据或输出合同。 |
| `_rollback_event_errors` | `_rollback_event_errors` 用于完成局部输入校验、转换或状态更新。 |
| `_load_events` | `_load_events` 在 `human_page_template_proposals.py` 中用于读取、规范化并返回既有状态。 |
| `_builtin_items` | `_builtin_items` 用于完成局部输入校验、转换或状态更新。 |
| `_item_sort_key` | `_item_sort_key` 用于完成局部输入校验、转换或状态更新。 |
| `_index_from_events` | `_index_from_events` 用于完成局部输入校验、转换或状态更新。 |
| `_operation_log_bytes` | `_operation_log_bytes` 用于完成局部输入校验、转换或状态更新。 |
| `_atomic_write_bytes` | `_atomic_write_bytes` 用于完成局部输入校验、转换或状态更新。 |
| `_rebuild_store` | `_rebuild_store` 用于完成局部输入校验、转换或状态更新。 |
| `_load_verified_store` | `_load_verified_store` 在 `human_page_template_proposals.py` 中用于读取、规范化并返回既有状态。 |
| `_validate_local_version` | `_validate_local_version` 用于完成局部输入校验、转换或状态更新。 |
| `validate_template_proposal` | `validate_template_proposal` 用于完成局部输入校验、转换或状态更新。 |
| `list_templates` | `list_templates` 在 `human_page_template_proposals.py` 中用于读取、规范化并返回既有状态。 |
| `show_template` | `show_template` 在 `human_page_template_proposals.py` 中用于读取、规范化并返回既有状态。 |
| `_event_by_id` | `_event_by_id` 用于完成局部输入校验、转换或状态更新。 |
| `_proposal_payload` | `_proposal_payload` 在 `human_page_template_proposals.py` 中用于读取、规范化并返回既有状态。 |
| `audit_template_proposal` | `audit_template_proposal` 用于完成局部输入校验、转换或状态更新。 |
| `rollback_template_extension` | `rollback_template_extension` 用于完成局部输入校验、转换或状态更新。 |

</details>
