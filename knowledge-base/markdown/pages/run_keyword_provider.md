# run_keyword_provider

标签：#类型/代码

> `run_keyword_provider` 是 `scripts/ckb_core/keyword_fallback.py` 第 380-461 行定义的函数，本页绑定该固定源码范围。 负责在确定性词项不足时执行受预算约束的 LLM 关键词备选慢路径。

## 什么时候需要修改

当 `run_keyword_provider` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/keyword_fallback.py 第 380 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/keyword_fallback.py:380:1)  `scripts/ckb_core/keyword_fallback.py:380-461`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]。

## 谁会来到这里

- [[KeywordFallbackRetrievalWiringTests]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]] 汇总了本页。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[KeywordFallbackRetrievalWiringTests 等测试场景]]
- [[append 等测试场景]]
- [[command 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
