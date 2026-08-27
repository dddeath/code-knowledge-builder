# retrieve

标签：#类型/代码

> `retrieve` 是源码中负责维护旧版页面索引兼容接口并生成受预算约束的阅读包的命名代码单元。 它在所属模块内执行维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当维护旧版页面索引兼容接口并生成受预算约束的阅读包所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_index.py 第 440 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:440:1)  `scripts/ckb_core/agent_index.py:440-568`

## 相关代码

- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[module_name 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[retrieve 与 _tokens 的协作实现]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[parser]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 汇总了本页。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[start_session]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[MigrationTest]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]
