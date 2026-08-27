# retrieve_machine 与 estimated_tokens 的协作实现

标签：#类型/代码

> 该文件实现完整 SQLite 机器知识库及纯确定性 Agent 检索。 它负责构建实体、关系、来源、中文章节和 FTS 索引，并以固定候选上限、批量读取、图传播和静态缓存生成低上下文阅读包。

## 什么时候需要修改

机器 Schema、检索召回规则、排序权重、缓存失效条件或阅读包预算策略变化时，需要修改该文件。

## 在代码中的位置

[打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`

## 相关代码

- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[retrieve]]。
- 主要代码单元是 [[retrieve_machine]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[source_files]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
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

<details><summary>查看本页收纳的 35 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `estimated_tokens` | 按 UTF-8 字节数估算阅读文本的上下文令牌占用。 |
| `contains_chinese_narrative` | 检查叙述字段是否达到最小中文字符数量。 |
| `_split_camel` | 把驼峰式代码标识符稳定拆成可检索词项。 |
| `search_terms` | 将问题规范化为英文标识符片段以及中文二元、三元检索词项。 |
| `explicit_anchors` | 从问题中提取具备代码标识符特征的精确查询锚点。 |
| `_fts_query` | 把高信息词项转义并组合为有界的 SQLite FTS 查询。 |
| `_human_projection` | 按固定优先级定位已完成的人类知识库投影。 |
| `_note_documents` | 读取分析、修改、踩坑、实验和会话 Markdown，转成机器文档记录。 |
| `_review_paths` | 建立实体到已通过 Agent 审阅文件的来源映射。 |
| `_source_texts` | 从固定源码快照读取图中涉及文件的完整文本。 |
| `_description` | 按实体分类拼接独立页三段说明或附录单句说明。 |
| `_human_map` | 读取实体所属人类页面以及页面元数据映射。 |
| `_sections_for_entity` | 把中文说明、来源核对和有界源码摘录拆成机器检索章节。 |
| `_create_schema` | 创建完整实体、关系、来源、文档、章节和 FTS 表的 SQLite Schema。 |
| `build_machine_knowledge` | 从已审阅事实图构建完整机器知识库及全文检索索引。 |
| `_markdown_sections` | 按 Markdown 标题切分人类笔记并保留无标题导言。 |
| `audit_machine_knowledge` | 核对机器库完整性、外键、实体覆盖、中文叙述与投影数量。 |
| `_adjacency` | 从关系表构建带权双向邻接表和实体度数。 |
| `_fast_graph_scores` | 从种子实体执行固定两跳传播并施加度数惩罚。 |
| `_deterministic_ppr` | 以固定轮次和重启率计算确定性的加权 PageRank 分数。 |
| `_next_pack_path` | 为下一份 Agent 阅读包分配稳定且不冲突的 Markdown 与 JSON 路径。 |
| `_sql_placeholders` | 根据参数数量生成 SQLite 参数占位符列表。 |
| `_utf8_prefix` | 在不截断 UTF-8 字符的前提下取得指定字节预算内的文本前缀。 |
| `_bulk_entity_context` | 用两次批量查询取得候选实体、源码范围、人类归属和章节内容。 |
| `_diverse_candidates` | 按得分稳定排序，并优先保留来自不同源码路径的候选实体。 |
| `_compact_entity_block` | 为每个入选实体生成保留来源链接且可按预算截断章节的紧凑区块。 |
| `_static_retrieval_key` | 用机器库大小、修改时间和源码打开器时间生成缓存失效键。 |
| `_static_retrieval_context` | 一次加载不可变实体元数据、章节、关系图和源码链接渲染器并缓存复用。 |
| `_openers` | 读取本地源码打开器配置，缺省时从知识库状态构造配置。 |
| `coverage` | 汇总机器知识库审计、逐实体审阅和中文说明覆盖率。 |
| `entity_lookup` | 按稳定 ID、名称或限定名查询实体及精确源码范围。 |
| `neighbor_lookup` | 从指定实体按深度和关系类型进行有界图邻居展开。 |
| `source_lookup` | 返回指定实体在固定源码中的精确范围及少量上下文。 |
| `change_documents` | 按类型和数量列出分析、修改、踩坑、实验或会话记录。 |
| `sync_workspace_changes` | 把工作树变更同步为机器层覆盖记录而不改动固定基线图。 |

</details>
