# retrieve_machine 与 estimated_tokens 的协作实现

标签：#类型/代码

> 该页面汇总完整机器知识 SQLite、FTS、图传播和预算化检索实现。 它保存全部源码事实与审阅证据，并用纯确定性排序生成 Agent 阅读包。

## 什么时候需要修改

数据库 schema、索引字段、检索评分、预算或自动化文档接入方式变化时，需要修改本文件。

## 在代码中的位置

[打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1151`

## 相关代码

- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 主要代码单元是 [[retrieve_machine]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[source_files]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[start_session]] 会使用这里提供的行为。
- [[start_session 与 _session_directory 的协作实现]] 会使用这里提供的行为。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 28 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `estimated_tokens` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `contains_chinese_narrative` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `_split_camel` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `search_terms` | 该附属代码负责维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把结果交给所属页面中的主流程使用。 |
| `explicit_anchors` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `_fts_query` | 该附属代码负责维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把结果交给所属页面中的主流程使用。 |
| `_human_projection` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `_note_documents` | 该附属代码负责保存实时工作区变化和双链知识记录，并把结果交给所属页面中的主流程使用。 |
| `_review_paths` | 该附属代码负责核对并登记逐实体 Agent 审阅结果，并把结果交给所属页面中的主流程使用。 |
| `_source_texts` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `_description` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `_human_map` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `_sections_for_entity` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `_create_schema` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `build_machine_knowledge` | 该附属代码负责构建完整机器库并执行分节全文检索和确定性图扩展，并把结果交给所属页面中的主流程使用。 |
| `_markdown_sections` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `audit_machine_knowledge` | 该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。 |
| `_adjacency` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `_fast_graph_scores` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `_deterministic_ppr` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `_next_pack_path` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `_openers` | 该附属代码负责生成并核对可直接打开源码位置的 URI，并把结果交给所属页面中的主流程使用。 |
| `coverage` | 该附属代码负责构建完整机器库并执行分节全文检索和确定性图扩展，并把结果交给所属页面中的主流程使用。 |
| `entity_lookup` | 该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。 |
| `neighbor_lookup` | 该附属代码负责构建完整机器库并执行分节全文检索和确定性图扩展，并把结果交给所属页面中的主流程使用。 |
| `source_lookup` | 该附属代码负责构建完整机器库并执行分节全文检索和确定性图扩展，并把结果交给所属页面中的主流程使用。 |
| `change_documents` | 查询分析、修改、踩坑、实验、会话和自动化记录。 |
| `sync_workspace_changes` | 该附属代码负责保存实时工作区变化和双链知识记录，并把结果交给所属页面中的主流程使用。 |

</details>
