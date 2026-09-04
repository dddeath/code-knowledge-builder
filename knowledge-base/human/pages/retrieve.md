# retrieve

标签：#类型/代码

> `retrieve` 是 `scripts/ckb_core/agent_index.py` 第 426-554 行定义的函数，本页绑定该固定源码范围。 负责构建兼容 Agent 索引，并按预算执行确定性检索与结果排序。

## 什么时候需要修改

当 `retrieve` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_index.py 第 426 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:426:1)  `scripts/ckb_core/agent_index.py:426-554`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[ScopeExtensionOfferTests.retrieval]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[module_name 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[retrieve 与 _tokens 的协作实现]]。
- 实现时会用到 [[search_terms]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[QueryTermsTests]] 会使用这里提供的行为。
- [[ScopeExtensionOfferTests.retrieval 等测试场景]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[audit_operation_journal 与 _root 的协作实现]] 会使用这里提供的行为。
- [[build 的协作边界]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[deploy 的协作边界]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 汇总了本页。
- [[serve_stdio]] 会使用这里提供的行为。
- [[start_session]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
