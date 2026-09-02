# finalize 与 _replace_output_prefix 的协作实现

标签：#类型/代码

> 文件 `scripts/ckb_core/pipeline.py`负责编排固定快照解析、Agent 审阅、页面投影、迁移、全局审计与最终生成。 它属于从源码事实到机器索引和人类页面的一致性主流程，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当构建阶段、迁移复用、页面预算、可读性、镜像或完成门变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3605`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[audit_obsidian]]。
- 实现时会用到 [[audit_work_record_index]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 主要代码单元是 [[finalize]]。
- 实现时会用到 [[ingest_reference 与 _root 的协作实现]]。
- 实现时会用到 [[load_page_config]]。
- 实现时会用到 [[load_page_config 与 _merge_known 的协作实现]]。
- 实现时会用到 [[parse_file]]。
- 实现时会用到 [[preflight]]。
- 实现时会用到 [[preflight 与 git 的协作实现]]。
- 实现时会用到 [[record_note 与 page_tag 的协作实现]]。
- 实现时会用到 [[refresh]]。
- 实现时会用到 [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[FactFreshnessStateMachineTest 等测试场景]] 会使用这里提供的行为。
- [[MigrationTest 等测试场景]] 会使用这里提供的行为。
- [[PdfReferenceExtractionTests 等测试场景]] 会使用这里提供的行为。
- [[RecordReplaceTests]] 会使用这里提供的行为。
- [[ScopeExtensionTest 等测试场景]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[append 等测试场景]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[audit_operation_journal 与 _root 的协作实现]] 会使用这里提供的行为。
- [[benchmark 的协作边界（cbc71645）]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[doctor_report 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[finalize]] 会使用这里提供的行为。
- [[ingest_reference 与 _root 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[run 等测试场景]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[start_scope_extension]] 会使用这里提供的行为。
- [[validate_human_maintenance_invocation 与 ParameterSpec 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CanvasBenchmarkContractTests]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[FactFreshnessStateMachineTest 等测试场景]]
- [[HumanMaintenancePromptRegistryTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 72 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_replace_output_prefix` | `_replace_output_prefix` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_relocate_completed_output` | `_relocate_completed_output` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_load_state` | `_load_state` 读取并判定知识库构建与投影主流程所需的数据或状态。 |
| `_module` | `_module` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_parse_entry` | `_parse_entry` 解析并归一化知识库构建与投影主流程所需的数据或状态。 |
| `_resolve_entries` | `_resolve_entries` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_expand_entries` | `_expand_entries` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_chunks` | `_chunks` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_chunks.flush` | `flush` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_chunks.units_for_file` | `units_for_file` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_write_review_pack_templates` | `_write_review_pack_templates` 生成并写入知识库构建与投影主流程所需的数据或状态。 |
| `_normalize_repo_selector` | `_normalize_repo_selector` 解析并归一化知识库构建与投影主流程所需的数据或状态。 |
| `_resolve_csharp_workspace` | `_resolve_csharp_workspace` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_prepare_csharp_restore` | `_prepare_csharp_restore` 创建并初始化知识库构建与投影主流程所需的数据或状态。 |
| `_prepare_csharp_fallback_workspace` | `_prepare_csharp_fallback_workspace` 创建并初始化知识库构建与投影主流程所需的数据或状态。 |
| `_rekey_reused_file_parse` | `_rekey_reused_file_parse` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_syntax_warning_summary` | `_syntax_warning_summary` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_semantic_warning_summary` | `_semantic_warning_summary` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `initialize` | `initialize` 创建并初始化知识库构建与投影主流程所需的数据或状态。 |
| `_selected_catalog` | `_selected_catalog` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_chunk` | `_chunk` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_review_pack` | `_review_pack` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_invalidate_after_build` | `_invalidate_after_build` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `build_chunk` | `build_chunk` 创建并初始化知识库构建与投影主流程所需的数据或状态。 |
| `_substantive_chinese` | `_substantive_chinese` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_single_chinese_sentence` | `_single_chinese_sentence` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_source_check` | `_source_check` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_partial_fragment_source_errors` | `_partial_fragment_source_errors` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `audit_chunk` | `audit_chunk` 校验知识库构建与投影主流程所需的数据或状态。 |
| `audit_chunk.gate` | `gate` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `review_chunk` | `review_chunk` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `review_pack` | `review_pack` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `merge` | `merge` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_repository_name` | `_repository_name` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_short_code_unit_name` | `_short_code_unit_name` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_source_role` | `_source_role` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_human_page_base_title` | `_human_page_base_title` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_assign_human_titles` | `_assign_human_titles` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_logical_projection` | `_logical_projection` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_logical_projection.new_page` | `new_page` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_logical_projection.relation_category` | `relation_category` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_source_manifest` | `_source_manifest` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_page_sections` | `_page_sections` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_overview_text` | `_overview_text` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_aggregate_overview` | `_aggregate_overview` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_canonical_page_context` | `_canonical_page_context` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_logical_context_budgets` | `_logical_context_budgets` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_relation_phrase` | `_relation_phrase` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_human_relation_sentences` | `_human_relation_sentences` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_normalized_edn_document` | `_normalized_edn_document` 解析并归一化知识库构建与投影主流程所需的数据或状态。 |
| `_render_markdown_page` | `_render_markdown_page` 生成并写入知识库构建与投影主流程所需的数据或状态。 |
| `_logseq_file_graph_config_bytes` | `_logseq_file_graph_config_bytes` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_install_logseq_file_graph_config` | `_install_logseq_file_graph_config` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_audit_logseq_file_graph_config` | `_audit_logseq_file_graph_config` 校验知识库构建与投影主流程所需的数据或状态。 |
| `_human_page_filenames` | `_human_page_filenames` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_index_document` | `_index_document` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_wiki_document` | `_wiki_document` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_readability_report` | `_readability_report` 读取并判定知识库构建与投影主流程所需的数据或状态。 |
| `project_markdown` | `project_markdown` 生成并写入知识库构建与投影主流程所需的数据或状态。 |
| `_preserved_human_bytes` | `_preserved_human_bytes` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `refresh_human_navigation` | `refresh_human_navigation` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_logseq` | `_logseq` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_logseq_count` | `_logseq_count` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_logseq_count.visit` | `visit` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `_logseq_count.contains_null_result` | `contains_null_result` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `project_logseq` | `project_logseq` 生成并写入知识库构建与投影主流程所需的数据或状态。 |
| `_audit_markdown` | `_audit_markdown` 校验知识库构建与投影主流程所需的数据或状态。 |
| `audit_global` | `audit_global` 校验知识库构建与投影主流程所需的数据或状态。 |
| `relink_sources` | `relink_sources` 完成知识库构建与投影主流程中的一个明确步骤。 |
| `build_context` | `build_context` 创建并初始化知识库构建与投影主流程所需的数据或状态。 |
| `status` | `status` 读取并判定知识库构建与投影主流程所需的数据或状态。 |
| `run_fast` | `run_fast` 完成知识库构建与投影主流程中的一个明确步骤。 |

</details>
