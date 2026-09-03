# retrieve_machine

标签：#类型/代码

> 代码单元 `retrieve_machine`负责构建双 SQLite 检索层，并组合 FTS5、图关系、工作记录和源码新鲜度生成检索包。 它属于Agent 先检索后窄读源码的核心机器入口，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当索引结构、词项、排序、预算、警告传播或检索输出合同变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/machine_knowledge.py 第 1827 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1827:1)  `scripts/ckb_core/machine_knowledge.py:1827-1849`

## 相关代码

- 实现时会用到 [[check_fact_freshness]]。
- 实现时会用到 [[check_fact_freshness 与 _root 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]。

## 谁会来到这里

- [[KeywordFallbackRetrievalWiringTests]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 会使用这里提供的行为。
- [[MigrationTest]] 会使用这里提供的行为。
- [[benchmark 的协作边界（9fab5b96）]] 会使用这里提供的行为。
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
