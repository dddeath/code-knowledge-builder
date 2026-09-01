# query_graph 与 _networkx_modules 的协作实现

标签：#类型/代码

> 该文件集中实现Graphify 兼容图、确定性职责群、路径查询和关系报告。 它是 Code Knowledge Builder 中承载Graphify 兼容图、确定性职责群、路径查询和关系报告的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当Graphify 兼容图、确定性职责群、路径查询和关系报告的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/graphify_core.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/graphify_core.py:1:1)  `scripts/ckb_core/graphify_core.py:1-676`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[initialize 与 _replace_output_prefix 的协作实现]]。
- 主要代码单元是 [[query_graph]]。

## 谁会来到这里

- [[doctor_report]] 会使用这里提供的行为。
- [[query_graph]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[MigrationTest]]
- [[ScopeExtensionTest]]
- [[command 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 21 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_networkx_modules` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |
| `_canonical_json_sha256` | 该附属代码负责稳定读取或写入机器状态记录，并把结果交给所属页面中的主流程使用。 |
| `_source_location` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |
| `_node_label` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |
| `_description` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |
| `_confidence` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |
| `_graphify_node` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `_graphify_link` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `_build_networkx` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |
| `_community_records` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `_report` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |
| `project_graphify` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `audit_graphify` | 该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。 |
| `_load_projected_graph` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `_terms` | 该附属代码负责维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把结果交给所属页面中的主流程使用。 |
| `_seed_scores` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |
| `_adjacency` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |
| `_query_size` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |
| `_resolve_node` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |
| `shortest_path` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `explain_node` | 该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。 |

</details>
