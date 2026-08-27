# retrieve_machine

标签：#类型/代码

> `retrieve_machine` 根据问题生成来源绑定且受预算约束的 Agent 阅读包。 它组合精确锚点、中文与标识符词项、实体和章节 FTS、元数据加权、测试折扣、固定图传播、路径多样化及缓存上下文，稳定保留最相关源码目标。

## 什么时候需要修改

候选上限、召回字段、权重、测试意图、图算法、缓存策略或阅读包结构变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/ckb_core/machine_knowledge.py 第 942 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:942:1)  `scripts/ckb_core/machine_knowledge.py:942-1315`

## 相关代码

- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[retrieve]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[status 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.event 等测试场景]] 会使用这里提供的行为。
- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[LspClient.start 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[MigrationTest]] 会使用这里提供的行为。
- [[create_source_snapshot]] 会使用这里提供的行为。
- [[create_source_snapshot 与 git 的协作实现]] 会使用这里提供的行为。
- [[execute 等测试场景]] 会使用这里提供的行为。
- [[main（generate_large_fixture 测试）]] 会使用这里提供的行为。
- [[module_name 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[package_showcase]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[parse_file 与 _language 的协作实现]] 会使用这里提供的行为。
- [[query_graph]] 会使用这里提供的行为。
- [[query_graph 与 _networkx_modules 的协作实现]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- [[render_integration 与 _looks_windows 的协作实现]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 汇总了本页。
- [[start_session]] 会使用这里提供的行为。
- [[status 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 2 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `retrieve_machine.add` | 把一个实体的阶段分值、分解项和中文入选原因合并到查询状态。 |
| `retrieve_machine.entity_column` | 为兼容旧机器库选择现有列或提供空值别名。 |

</details>
