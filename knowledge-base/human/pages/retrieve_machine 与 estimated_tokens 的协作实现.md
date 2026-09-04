# retrieve_machine 与 estimated_tokens 的协作实现

标签：#类型/代码

> 文件 `scripts/ckb_core/machine_knowledge.py`负责构建双 SQLite 检索层，并组合 FTS5、图关系、工作记录和源码新鲜度生成检索包。 它属于Agent 先检索后窄读源码的核心机器入口，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当索引结构、词项、排序、预算、警告传播或检索输出合同变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1995`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[ScopeExtensionOfferTests.retrieval]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_feedback 与 _contains_chinese 的协作实现]]。
- 实现时会用到 [[audit_gap_register 与 _root 的协作实现]]。
- 实现时会用到 [[finalize]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[render_integration 与 harness_retrieval_contract 的协作实现]]。
- 主要代码单元是 [[retrieve_machine]]。
- 实现时会用到 [[run_keyword_provider]]。
- 实现时会用到 [[source_files]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[HumanPageAuthoringValidationFailureTests]] 会使用这里提供的行为。
- [[HumanPageTemplateRegistryTests 等测试场景]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests]] 会使用这里提供的行为。
- [[ScopeExtensionOfferTests.retrieval 等测试场景]] 会使用这里提供的行为。
- [[audit_gap_register 与 _root 的协作实现]] 会使用这里提供的行为。
- [[audit_operation_journal 与 _root 的协作实现]] 会使用这里提供的行为。
- [[doctor_report 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[ingest_reference]] 会使用这里提供的行为。
- [[ingest_reference 与 _root 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[parse_file 与 _language 的协作实现]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[replace_note 与 RecordReplaceLockError 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[run_benchmark]] 会使用这里提供的行为。
- [[run_benchmark 等测试场景]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[serve_stdio]] 会使用这里提供的行为。
- [[start_session]] 会使用这里提供的行为。
- [[start_session 与 _session_directory 的协作实现]] 会使用这里提供的行为。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AutomationTest.register 等测试场景]]
- [[ChineseRetrievalEffectRetestFixtureTests]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanPageAuthoringValidationFailureTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 44 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `estimated_tokens` | `estimated_tokens` 完成机器索引与检索包生成中的一个明确步骤。 |
| `contains_chinese_narrative` | `contains_chinese_narrative` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_fts_query` | `_fts_query` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_fts_query_values` | `_fts_query_values` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_human_projection` | `_human_projection` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_note_documents` | `_note_documents` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_review_paths` | `_review_paths` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_source_texts` | `_source_texts` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_description` | `_description` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_human_map` | `_human_map` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_sections_for_entity` | `_sections_for_entity` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_create_schema` | `_create_schema` 创建并初始化机器索引与检索包生成所需的数据或状态。 |
| `build_machine_knowledge` | `build_machine_knowledge` 创建并初始化机器索引与检索包生成所需的数据或状态。 |
| `_markdown_sections` | `_markdown_sections` 完成机器索引与检索包生成中的一个明确步骤。 |
| `audit_machine_knowledge` | `audit_machine_knowledge` 校验机器索引与检索包生成所需的数据或状态。 |
| `_adjacency` | `_adjacency` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_fast_graph_scores` | `_fast_graph_scores` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_deterministic_ppr` | `_deterministic_ppr` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_next_pack_path` | `_next_pack_path` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_indexed_warning_summary` | `_indexed_warning_summary` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_warning_pack_block` | `_warning_pack_block` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_sql_placeholders` | 该函数生成参数化 SQL 所需的占位符列表，并拒绝空输入。 |
| `_utf8_prefix` | `_utf8_prefix` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_bulk_entity_context` | `_bulk_entity_context` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_diverse_candidates` | `_diverse_candidates` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_compact_entity_block` | `_compact_entity_block` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_static_retrieval_key` | `_static_retrieval_key` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_static_retrieval_context` | `_static_retrieval_context` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_openers` | `_openers` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_matching_documents` | `_matching_documents` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_document_source_link` | `_document_source_link` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_document_block` | `_document_block` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_retrieve_machine_deterministic` | `_retrieve_machine_deterministic` 检索并组织机器索引与检索包生成所需的数据或状态。 |
| `_retrieve_machine_deterministic.add` | `add` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_retrieve_machine_deterministic.entity_column` | `entity_column` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_provider_record` | `_provider_record` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_attach_keyword_fallback` | `_attach_keyword_fallback` 完成机器索引与检索包生成中的一个明确步骤。 |
| `_retrieve_machine_without_freshness` | `_retrieve_machine_without_freshness` 检索并组织机器索引与检索包生成所需的数据或状态。 |
| `coverage` | `coverage` 检索并组织机器索引与检索包生成所需的数据或状态。 |
| `entity_lookup` | `entity_lookup` 完成机器索引与检索包生成中的一个明确步骤。 |
| `neighbor_lookup` | `neighbor_lookup` 完成机器索引与检索包生成中的一个明确步骤。 |
| `source_lookup` | `source_lookup` 完成机器索引与检索包生成中的一个明确步骤。 |
| `change_documents` | `change_documents` 完成机器索引与检索包生成中的一个明确步骤。 |
| `sync_workspace_changes` | `sync_workspace_changes` 完成机器索引与检索包生成中的一个明确步骤。 |

</details>
