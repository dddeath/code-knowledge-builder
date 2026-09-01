# retrieve 与 _tokens 的协作实现

标签：#类型/代码

> `scripts/ckb_core/agent_index.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责构建兼容 Agent 索引，并按预算执行确定性检索与结果排序。

## 什么时候需要修改

当 `scripts/ckb_core/agent_index.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-555`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[initialize 与 _replace_output_prefix 的协作实现]]。
- 主要代码单元是 [[retrieve]]。
- 实现时会用到 [[search_terms 与 _split_camel 的协作实现]]。

## 谁会来到这里

- [[audit_gap_register 与 _root 的协作实现]] 会使用这里提供的行为。
- [[audit_references 与 _root 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[retrieve]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_tokens` | `_tokens` 是第 24-25 行的函数，供所属页面定位实现。 |
| `_note_documents` | `_note_documents` 是第 28-44 行的函数，供所属页面定位实现。 |
| `_projection` | `_projection` 是第 47-60 行的函数，供所属页面定位实现。 |
| `_page_documents` | `_page_documents` 是第 63-160 行的函数，供所属页面定位实现。 |
| `build_agent_index` | `build_agent_index` 是第 163-341 行的函数，供所属页面定位实现。 |
| `audit_agent_index` | `audit_agent_index` 是第 344-390 行的函数，供所属页面定位实现。 |
| `_agent_index_ready` | `_agent_index_ready` 是第 393-405 行的函数，供所属页面定位实现。 |
| `_fts_query` | `_fts_query` 是第 408-409 行的函数，供所属页面定位实现。 |
| `_next_pack_path` | `_next_pack_path` 是第 412-423 行的函数，供所属页面定位实现。 |

</details>
