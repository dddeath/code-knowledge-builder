# retrieve_machine

标签：#类型/代码

> `retrieve_machine` 执行机器知识检索，附加 Git 新鲜度，并对问题中的唯一显式源码 selector 评估是否需要给出扩库确认建议。 它保持既有排序和预算，把范围外确认作为检索后的证据判断，而不是第二套检索引擎。

## 什么时候需要修改

当检索结果、新鲜度合同、scope offer 接线或关键词慢路径变化时，应更新本函数并复查 CLI 与 stdio 一致性。

## 在代码中的位置

[打开源码：scripts/ckb_core/machine_knowledge.py 第 1827 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1827:1)  `scripts/ckb_core/machine_knowledge.py:1827-1852`

## 相关代码

- 实现时会用到 [[check_fact_freshness]]。
- 实现时会用到 [[check_fact_freshness 与 _root 的协作实现]]。
- 实现时会用到 [[refresh 等测试场景]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]。
- 实现时会用到 [[start_scope_extension 与 _error 的协作实现]]。

## 谁会来到这里

- [[KeywordFallbackRetrievalWiringTests]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 会使用这里提供的行为。
- [[benchmark 的协作边界（e30cfb0a）]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[command 等测试场景]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 汇总了本页。
- [[run_failure_probe]] 会使用这里提供的行为。
- [[run_failure_probe 等测试场景]] 会使用这里提供的行为。
- [[run_keyword_benchmark 与 _text_list 的协作实现]] 会使用这里提供的行为。
- [[serve_stdio]] 会使用这里提供的行为。
- [[start_session]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[ChineseRetrievalEffectRetestFixtureTests]]
- [[CodeKnowledgeBuilderTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[KeywordFallbackRetrievalWiringTests 等测试场景]]
- [[MigrationTest]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
