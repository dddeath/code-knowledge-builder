# retrieve_machine 与 estimated_tokens 的协作实现

标签：#类型/代码

> `scripts/ckb_core/machine_knowledge.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责机器知识 SQLite 的构建、FTS5 检索、实体邻接和源码定位。

## 什么时候需要修改

当 `scripts/ckb_core/machine_knowledge.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1852`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_feedback 与 _contains_chinese 的协作实现]]。
- 实现时会用到 [[audit_gap_register 与 _root 的协作实现]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[initialize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[render_integration 与 _looks_windows 的协作实现]]。
- 主要代码单元是 [[retrieve_machine]]。
- 实现时会用到 [[search_terms]]。
- 实现时会用到 [[search_terms 与 _split_camel 的协作实现]]。
- 实现时会用到 [[source_files]]。

## 谁会来到这里

- [[KeywordFallbackRetrievalWiringTests]] 会使用这里提供的行为。
- [[audit_gap_register 与 _root 的协作实现]] 会使用这里提供的行为。
- [[audit_operation_journal 与 _root 的协作实现]] 会使用这里提供的行为。
- [[audit_references]] 会使用这里提供的行为。
- [[audit_references 与 _root 的协作实现]] 会使用这里提供的行为。
- [[doctor_report 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[serve_stdio]] 会使用这里提供的行为。
- [[start_session]] 会使用这里提供的行为。
- [[start_session 与 _session_directory 的协作实现]] 会使用这里提供的行为。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[KeywordFallbackRetrievalWiringTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 41 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `estimated_tokens` | `estimated_tokens` 是第 55-56 行的函数，供所属页面定位实现。 |
| `contains_chinese_narrative` | `contains_chinese_narr...` 是第 59-63 行的函数，供所属页面定位实现。 |
| `_fts_query` | `_fts_query` 是第 66-67 行的函数，供所属页面定位实现。 |
| `_fts_query_values` | `_fts_query_values` 是第 70-74 行的函数，供所属页面定位实现。 |
| `_human_projection` | `_human_projection` 是第 77-85 行的函数，供所属页面定位实现。 |
| `_note_documents` | `_note_documents` 是第 88-115 行的函数，供所属页面定位实现。 |
| `_review_paths` | `_review_paths` 是第 118-130 行的函数，供所属页面定位实现。 |
| `_source_texts` | `_source_texts` 是第 133-142 行的函数，供所属页面定位实现。 |
| `_description` | `_description` 是第 145-152 行的函数，供所属页面定位实现。 |
| `_human_map` | `_human_map` 是第 155-158 行的函数，供所属页面定位实现。 |
| `_sections_for_entity` | `_sections_for_entity` 是第 161-179 行的函数，供所属页面定位实现。 |
| `_create_schema` | `_create_schema` 是第 182-351 行的函数，供所属页面定位实现。 |
| `build_machine_knowledge` | `build_machine_knowledge` 是第 354-613 行的函数，供所属页面定位实现。 |
| `_markdown_sections` | `_markdown_sections` 是第 616-634 行的函数，供所属页面定位实现。 |
| `audit_machine_knowledge` | `audit_machine_knowledge` 是第 637-718 行的函数，供所属页面定位实现。 |
| `_adjacency` | `_adjacency` 是第 721-731 行的函数，供所属页面定位实现。 |
| `_fast_graph_scores` | `_fast_graph_scores` 是第 734-754 行的函数，供所属页面定位实现。 |
| `_deterministic_ppr` | `_deterministic_ppr` 是第 757-789 行的函数，供所属页面定位实现。 |
| `_next_pack_path` | `_next_pack_path` 是第 792-801 行的函数，供所属页面定位实现。 |
| `_sql_placeholders` | `该实体` 是第 804-808 行的函数，供所属页面定位实现。 |
| `_utf8_prefix` | `_utf8_prefix` 是第 811-820 行的函数，供所属页面定位实现。 |
| `_bulk_entity_context` | `_bulk_entity_context` 是第 823-846 行的函数，供所属页面定位实现。 |
| `_diverse_candidates` | `_diverse_candidates` 是第 849-872 行的函数，供所属页面定位实现。 |
| `_compact_entity_block` | `_compact_entity_block` 是第 875-931 行的函数，供所属页面定位实现。 |
| `_static_retrieval_key` | `_static_retrieval_key` 是第 934-946 行的函数，供所属页面定位实现。 |
| `_static_retrieval_context` | `_static_retrieval_con...` 是第 949-1003 行的函数，供所属页面定位实现。 |
| `_openers` | `_openers` 是第 1006-1018 行的函数，供所属页面定位实现。 |
| `_matching_documents` | `_matching_documents` 是第 1021-1044 行的函数，供所属页面定位实现。 |
| `_document_source_link` | `_document_source_link` 是第 1047-1058 行的函数，供所属页面定位实现。 |
| `_document_block` | `_document_block` 是第 1061-1074 行的函数，供所属页面定位实现。 |
| `_retrieve_machine_deterministic` | `_retrieve_machine_det...` 是第 1077-1556 行的函数，供所属页面定位实现。 |
| `_retrieve_machine_deterministic.add` | `_retrieve_machine_det...` 是第 1129-1132 行的函数，供所属页面定位实现。 |
| `_retrieve_machine_deterministic.entity_column` | `_retrieve_machine_det...` 是第 1203-1204 行的函数，供所属页面定位实现。 |
| `_provider_record` | `_provider_record` 是第 1559-1578 行的函数，供所属页面定位实现。 |
| `_attach_keyword_fallback` | `_attach_keyword_fallback` 是第 1581-1597 行的函数，供所属页面定位实现。 |
| `coverage` | `coverage` 是第 1712-1732 行的函数，供所属页面定位实现。 |
| `entity_lookup` | `entity_lookup` 是第 1735-1746 行的函数，供所属页面定位实现。 |
| `neighbor_lookup` | `neighbor_lookup` 是第 1749-1788 行的函数，供所属页面定位实现。 |
| `source_lookup` | `source_lookup` 是第 1791-1808 行的函数，供所属页面定位实现。 |
| `change_documents` | `change_documents` 是第 1811-1831 行的函数，供所属页面定位实现。 |
| `sync_workspace_changes` | `sync_workspace_changes` 是第 1834-1851 行的函数，供所属页面定位实现。 |

</details>
