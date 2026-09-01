# execute

标签：#类型/代码

> `execute` 是 `tests/provider_integration.py` 第 19-24 行定义的函数，本页绑定该固定源码范围。 该函数作为可执行验证入口，检查标识符 `execute` 所指的行为与失败边界。

## 什么时候需要修改

当被测行为、输入夹具、断言或失败条件变化时，应同步更新 `execute` 的说明。

## 在代码中的位置

[打开源码：tests/provider_integration.py 第 19 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/provider_integration.py:19:1)  `tests/provider_integration.py:19-24`

## 相关代码

- 实现时会用到 [[command]]。

## 谁会来到这里

- [[MigrationTest]] 会使用这里提供的行为。
- [[ScopeExtensionTest]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[audit_gap_register]] 会使用这里提供的行为。
- [[audit_migration]] 会使用这里提供的行为。
- [[audit_references]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[doctor_report]] 会使用这里提供的行为。
- [[execute 等测试场景]] 汇总了本页。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[initialize 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[main（fake_logseq 测试）]] 会使用这里提供的行为。
- [[normalize 等测试场景]] 会使用这里提供的行为。
- [[render_integration 与 _looks_windows 的协作实现]] 会使用这里提供的行为。
- [[retrieve]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
