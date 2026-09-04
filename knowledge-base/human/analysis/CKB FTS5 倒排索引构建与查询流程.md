# CKB FTS5 倒排索引构建与查询流程

标签：#类型/分析

## 这套索引产生什么结果

CKB 把固定 Git 快照中的代码实体、中文审阅字段、人类知识页章节、工作记录、reference、research gap 和完整源码分别写入 SQLite。查询先从确定性词项、精确代码锚点和 FTS5 全文命中取得候选，再叠加固定元数据权重与图关系，最后生成有预算的 Agent pack。整个过程运行在本地，不依赖 embedding、向量数据库或网络模型。

这里的“倒排索引”主要由 SQLite FTS5 虚拟表实现。CKB 声明需要检索的列并向虚拟表逐行写入内容；分词、词项到行号的倒排表以及内部 shadow table 由 FTS5 维护。CKB 另外保留普通 `terms` 表，用于可解释的确定性词项权重，它不是 FTS5 的内部倒排表。

## 三个 FTS5 索引

`_create_schema` 创建三个使用 `tokenize='trigram'` 的 FTS5 虚拟表：

1. `entity_fts`：索引 `name`、`qualified_name`、`meaning_zh`、`role_zh`、`change_when_zh`、`description_zh` 和 `source_path`；`entity_id` 使用 `UNINDEXED`，只承担命中后回到实体表的关联键。
2. `section_fts`：索引知识文档章节的 `heading`、`content` 和 `source_path`；`section_id`、`document_id` 使用 `UNINDEXED`。代码实体说明、正式工作记录、reference 和 research gap 都先成为 `documents/sections`，再进入该全文索引。
3. `source_fts`：按源码路径索引固定快照的完整源码文本；`source_path` 使用 `UNINDEXED`，`content` 进入全文索引。该层只在 `precise` 检索中参与候选生成，避免默认快速路径扫描过宽。

`trigram` 按连续三字符片段建立词法索引，适合代码标识符、路径和连续中文的确定性子串召回。它不是中文语义分词，因此会产生不自然的中文片段；中文词项改进已经作为独立开发任务处理，在固定问题集通过前不替换当前默认路径。

## 构建和更新流程

`build_machine_knowledge` 先读取 `graph.json`、人类投影、源码文本和审阅来源，然后在 `machine/knowledge.sqlite.tmp` 上创建完整 Schema。写入顺序包括：

1. `files` 与 `source_fts`；
2. `entities`、来源范围、审阅、human owner 与 `entity_fts`；
3. 实体说明和源码摘录形成的 `documents/sections/section_fts`；
4. 关系、provider、诊断、community 和边界；
5. analysis、change、pitfall、experiment、session 等正式记录及其章节；
6. reference 资料、研究缺口和工作区覆盖状态。

实体写入时，CKB 还用 `search_terms` 为限定名、名称、路径和中文说明生成普通 `terms(term, entity_id, weight)` 记录：限定名、名称、路径和说明分别使用固定权重。`terms_term` 普通 B-tree 索引负责快速取得这些可解释词项候选。

全部写入完成后先提交事务，再执行 `PRAGMA integrity_check` 和 `PRAGMA foreign_key_check`。两项通过后关闭连接，并用临时数据库原子替换 `machine/knowledge.sqlite`。因此构建中断不会把半写入数据库当成正式机器知识库；正式库也不依赖手工修改 FTS shadow table。

通过 `record` 增加工作记录、通过 reference 或 gap 命令修改资料层时，CKB 会重新生成受影响的机器索引。源码实体、关系或来源提交变化时，应走 reindex、migrate 或对应构建流程，而不是直接写 SQLite。

## 查询词项和 BM25 排序

`_fts_query` 调用 `search_terms(question)`，保留长度至少为 3 的前 16 个词项，将每项转义为双引号短语，再用 `OR` 连接成 FTS5 `MATCH` 表达式。查询仍会并行使用精确代码锚点、普通 `terms` 表和元数据匹配，所以 FTS5 命中只是候选来源之一。

`entity_fts` 使用固定 BM25 列权重，名称和限定名高于中文职责字段与路径；`section_fts` 让标题权重大于章节正文和来源路径。`fast` 档位读取有限的实体和章节命中，`precise` 提高候选上限并额外查询 `source_fts`。BM25 分值被转换成正向候选分，随后再合并确定性词项、元数据、关系传播、度数惩罚和页面预算。

当前实现不是“把问题交给 FTS5 后直接返回行”。最终返回对象仍带实体 ID、来源路径、源码范围、命中原因、分项得分、人类知识页和相关工作记录，完整候选保存在 JSON record，首轮 `brief` 只暴露预算化 Agent pack 与后续窄读取入口。

## 当前边界和维护规则

- FTS5 是纯词法索引，不直接理解同义词、意图或代码行为；中文词项、精确标识符和图关系共同补充它。
- `source_fts` 只使用固定快照源码，工作区变化由独立 overlay 表示，基线事实保持固定。
- FTS5 行数应分别与实体数、章节数和源码文件数一致；维护审计同时检查双 SQLite 完整性、记录数量和人类镜像。
- `entity_fts_data`、`section_fts_data`、`source_fts_data` 等 shadow table 由 SQLite 管理，它们的物理行数不等于业务文档数；业务一致性应比较虚拟表行数与实体、章节、文件表。
- 调试顺序仍是 `brief fast`、Agent pack、`entity/neighbors/source/changes`，再读取检索返回的精确源码范围；宽范围文本搜索只作为已确认缺口的补充。

## 相关知识页

- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[finalize 与 _replace_output_prefix 的协作实现]]
- [[sync_human_layer 与 _source_manifest 的协作实现]]
- [[maintenance_check 与 capability_matrix 的协作实现]]
- [[render_integration 与 harness_retrieval_contract 的协作实现]]
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]]
- [[ingest_reference 与 _root 的协作实现]]
- [[audit_agent_protocol 与 _default_python 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1715`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3482`
- [打开源码：scripts/ckb_core/knowledge_layers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:1:1)  `scripts/ckb_core/knowledge_layers.py:1-262`
- [打开源码：scripts/ckb_core/llm_wiki_capabilities.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/llm_wiki_capabilities.py:1:1)  `scripts/ckb_core/llm_wiki_capabilities.py:1-453`
- [打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-536`
- [打开源码：scripts/ckb_core/obsidian_plugin.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian_plugin.py:1:1)  `scripts/ckb_core/obsidian_plugin.py:1-262`
- [打开源码：scripts/ckb_core/reference_documents.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_documents.py:1:1)  `scripts/ckb_core/reference_documents.py:1-604`
- [打开源码：scripts/ckb_core/agent_protocol.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol.py:1:1)  `scripts/ckb_core/agent_protocol.py:1-507`
