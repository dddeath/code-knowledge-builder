# MigrationTest

标签：#类型/代码

> 代码单元 `setUp`负责验证固定 blob 迁移时复用事实并重键语法警告引用。 它属于增量知识库迁移不会保留旧提交标识的回归保护，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当实体标识、复用规则、警告关联或迁移版本变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：tests/test_migration.py 第 58 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:58:1)  `tests/test_migration.py:58-245`

## 相关代码

- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[ScopeExtensionOfferTests.retrieval]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[finalize]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。

## 谁会来到这里

- [[MigrationTest 等测试场景]] 汇总了本页。
- [[audit_agent_protocol]] 关联到这里的验证场景。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 关联到这里的验证场景。
- [[audit_feedback]] 关联到这里的验证场景。
- [[audit_gap_register 与 _root 的协作实现]] 关联到这里的验证场景。
- [[audit_migration]] 关联到这里的验证场景。
- [[audit_migration 与 _entity_key 的协作实现]] 关联到这里的验证场景。
- [[audit_obsidian]] 关联到这里的验证场景。
- [[audit_obsidian 与 prepare_vault 的协作实现]] 关联到这里的验证场景。
- [[audit_output_contract]] 关联到这里的验证场景。
- [[audit_output_contract 与 _default_ckb 的协作实现]] 关联到这里的验证场景。
- [[audit_work_record_index]] 关联到这里的验证场景。
- [[audit_work_record_index 与 _contains_chinese 的协作实现]] 关联到这里的验证场景。
- [[extract_pdf 与 PdfExtractionError 的协作实现]] 关联到这里的验证场景。
- [[load_page_config 与 _merge_known 的协作实现]] 关联到这里的验证场景。
- [[module_name]] 关联到这里的验证场景。
- [[module_name 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[preflight 与 git 的协作实现]] 关联到这里的验证场景。
- [[query_graph 与 _networkx_modules 的协作实现]] 关联到这里的验证场景。
- [[record_note]] 关联到这里的验证场景。
- [[record_note 与 page_tag 的协作实现]] 关联到这里的验证场景。
- [[refresh 等测试场景]] 关联到这里的验证场景。
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]] 关联到这里的验证场景。
- [[retrieve_machine]] 关联到这里的验证场景。
- [[run_keyword_provider]] 关联到这里的验证场景。
- [[sync_human_layer]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `MigrationTest.setUp` | `setUp` 完成固定快照迁移回归验证中的一个明确步骤。 |
| `MigrationTest.tearDown` | `tearDown` 完成固定快照迁移回归验证中的一个明确步骤。 |
| `MigrationTest.test_exact_blob_facts_and_agent_reviews_are_reused` | 该测试验证“exact blob facts and agent re…”场景，保护固定快照迁移回归验证的预期结果与失败边界。 |
| `MigrationTest.test_exact_blob_local_syntax_warning_reuse_rekeys_every_reference` | 该测试验证“exact blob local syntax warni…”场景，保护固定快照迁移回归验证的预期结果与失败边界。 |

</details>
