# audit_migration 与 _entity_key 的协作实现

标签：#类型/代码

> `scripts/ckb_core/migration.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责把已审计知识库增量迁移到新快照，并保留可变层和复用证明。

## 什么时候需要修改

当 `scripts/ckb_core/migration.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-604`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 主要代码单元是 [[audit_migration]]。
- 实现时会用到 [[finalize]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[module_name 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[preflight 与 git 的协作实现]]。
- 实现时会用到 [[render_integration 与 harness_retrieval_contract 的协作实现]]。
- 实现时会用到 [[validate]]。

## 谁会来到这里

- [[MigrationTest]] 会使用这里提供的行为。
- [[audit_migration]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[finalize 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[start_scope_extension]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[MigrationTest]]
- [[PdfReferenceExtractionTests]]
- [[PdfReferenceExtractionTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 15 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_entity_key` | `_entity_key` 是第 24-34 行的函数，供所属页面定位实现。 |
| `_review_shape` | `_review_shape` 是第 37-38 行的函数，供所属页面定位实现。 |
| `_review_for_new_entity` | `_review_for_new_entity` 是第 41-62 行的函数，供所属页面定位实现。 |
| `_copy_file` | `_copy_file` 是第 65-74 行的函数，供所属页面定位实现。 |
| `_mutable_target` | `_mutable_target` 是第 77-84 行的函数，供所属页面定位实现。 |
| `_add_mutable_baseline` | `_add_mutable_baseline` 是第 87-104 行的函数，供所属页面定位实现。 |
| `_generated_paths` | `_generated_paths` 是第 107-111 行的函数，供所属页面定位实现。 |
| `_preserve_mutable_layers` | `_preserve_mutable_layers` 是第 114-181 行的函数，供所属页面定位实现。 |
| `_selected_entities` | `_selected_entities` 是第 184-196 行的函数，供所属页面定位实现。 |
| `_replace_review_packs` | `_replace_review_packs` 是第 199-250 行的函数，供所属页面定位实现。 |
| `migrate_output` | `migrate_output` 是第 253-364 行的函数，供所属页面定位实现。 |
| `_semantic_page_key` | `_semantic_page_key` 是第 482-484 行的函数，供所属页面定位实现。 |
| `relink_preserved_notes` | `relink_preserved_notes` 是第 487-581 行的函数，供所属页面定位实现。 |
| `relink_preserved_notes.replace_links` | `relink_preserved_note...` 是第 515-520 行的函数，供所属页面定位实现。 |
| `migration_status` | `migration_status` 是第 584-603 行的函数，供所属页面定位实现。 |

</details>
