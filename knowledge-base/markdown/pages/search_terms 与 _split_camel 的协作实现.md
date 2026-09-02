# search_terms 与 _split_camel 的协作实现

标签：#类型/代码

> `scripts/ckb_core/query_terms.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责从自然语言构造确定性中文及标识符检索词项。

## 什么时候需要修改

当 `scripts/ckb_core/query_terms.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/query_terms.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/query_terms.py:1:1)  `scripts/ckb_core/query_terms.py:1-106`

## 相关代码

- 主要代码单元是 [[search_terms]]。

## 谁会来到这里

- [[QueryTermsTests]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[search_terms]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanPageTemplateValidationTests]]
- [[KeywordFallbackRetrievalWiringTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 7 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_split_camel` | `_split_camel` 是第 23-28 行的函数，供所属页面定位实现。 |
| `_ranked_terms` | `_ranked_terms` 是第 31-62 行的函数，供所属页面定位实现。 |
| `_ranked_terms.add` | `_ranked_terms.add` 是第 35-37 行的函数，供所属页面定位实现。 |
| `index_terms` | `index_terms` 是第 72-74 行的函数，供所属页面定位实现。 |
| `fts_query_terms` | `fts_query_terms` 是第 77-81 行的函数，供所属页面定位实现。 |
| `build_fts_query` | `build_fts_query` 是第 84-88 行的函数，供所属页面定位实现。 |
| `explicit_anchors` | `explicit_anchors` 是第 91-105 行的函数，供所属页面定位实现。 |

</details>
