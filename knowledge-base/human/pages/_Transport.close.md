# _Transport.close

标签：#类型/代码

> `_Transport.close` 是 `scripts/ckb_core/session_stdio.py` 第 457-496 行定义的函数，本页绑定该固定源码范围。 负责会话级 stdio 服务的首次激活、租约续用、关闭与资源释放。

## 什么时候需要修改

当 `close` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/session_stdio.py 第 457 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/session_stdio.py:457:1)  `scripts/ckb_core/session_stdio.py:457-496`

## 相关代码

- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[contracts 的协作边界]]。

## 谁会来到这里

- [[AutomationTest.register 等测试场景]] 会使用这里提供的行为。
- [[MigrationTest]] 会使用这里提供的行为。
- [[RecordReplaceTests 等测试场景]] 会使用这里提供的行为。
- [[ScopeExtensionTest]] 会使用这里提供的行为。
- [[SessionStdioLifecycleTests]] 会使用这里提供的行为。
- [[SessionStdioLifecycleTests 等测试场景]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 汇总了本页。
- [[append 等测试场景]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[audit_global 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[audit_migration]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[audit_operation_journal 与 _root 的协作实现]] 会使用这里提供的行为。
- [[audit_references]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[build_case]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[doctor_report]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[main（session_stdio_reactivation_probe 测试）]] 会使用这里提供的行为。
- [[one_cycle]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[replace_note 与 RecordReplaceLockError 的协作实现]] 会使用这里提供的行为。
- [[retrieve]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。
- [[transaction 的协作边界]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register]]
- [[AutomationTest.register 等测试场景]]
- [[CanvasBenchmarkContractTests]]
- [[CanvasBenchmarkContractTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
