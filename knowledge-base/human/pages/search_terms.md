# search_terms

标签：#类型/代码

> `search_terms` 是 `scripts/ckb_core/query_terms.py` 第 65-69 行定义的函数，本页绑定该固定源码范围。 负责从自然语言构造确定性中文及标识符检索词项。

## 什么时候需要修改

当 `search_terms` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/query_terms.py 第 65 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/query_terms.py:65:1)  `scripts/ckb_core/query_terms.py:65-69`

## 相关代码

- 实现时会用到 [[search_terms 与 _split_camel 的协作实现]]。

## 谁会来到这里

- [[QueryTermsTests]] 会使用这里提供的行为。
- [[normalize 等测试场景]] 会使用这里提供的行为。
- [[retrieve]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[search_terms 与 _split_camel 的协作实现]] 汇总了本页。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
