# retrieve 与 _tokens 的协作实现

标签：#类型/代码

> 该文件集中实现旧版 SQLite 页面索引和检索接口兼容层。 它是 Code Knowledge Builder 中承载旧版 SQLite 页面索引和检索接口兼容层的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当旧版 SQLite 页面索引和检索接口兼容层的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`

## 相关代码

- 实现时会用到 [[ensure_local_openers]]。
- 实现时会用到 [[ensure_local_openers 与 default_openers 的协作实现]]。
- 实现时会用到 [[execute]]。
- 主要代码单元是 [[retrieve]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[status 与 _load_state 的协作实现]]。

## 谁会来到这里

- [[record_note]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[retrieve]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 10 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_tokens` | 该附属代码负责旧版 SQLite 页面索引和检索接口兼容层，并把结果交给所属页面中的主流程使用。 |
| `_terms` | 该附属代码负责维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把结果交给所属页面中的主流程使用。 |
| `_note_documents` | 该附属代码负责保存实时工作区变化和双链知识记录，并把结果交给所属页面中的主流程使用。 |
| `_projection` | 该附属代码负责旧版 SQLite 页面索引和检索接口兼容层，并把结果交给所属页面中的主流程使用。 |
| `_page_documents` | 该附属代码负责旧版 SQLite 页面索引和检索接口兼容层，并把结果交给所属页面中的主流程使用。 |
| `build_agent_index` | 该附属代码负责维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把结果交给所属页面中的主流程使用。 |
| `audit_agent_index` | 该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。 |
| `_agent_index_ready` | 该附属代码负责维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把结果交给所属页面中的主流程使用。 |
| `_fts_query` | 该附属代码负责维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把结果交给所属页面中的主流程使用。 |
| `_next_pack_path` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |

</details>
