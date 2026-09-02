# rollback

标签：#类型/代码

> `rollback` 位于 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py` 第 228-233 行，本页用固定源码范围说明它如何执行范围受控的恢复、撤销或清理。 `rollback` 负责在Canvas 原型命令编排和结果边界中执行范围受控的恢复、撤销或清理。

## 什么时候需要修改

当 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py` 中 `rollback` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：prototypes/ckb-canvas-skill/ckb_canvas/commands.py 第 228 行](vscode://file/E:/knowledge_builder/self-workspace/source/prototypes/ckb-canvas-skill/ckb_canvas/commands.py:228:1)  `prototypes/ckb-canvas-skill/ckb_canvas/commands.py:228-233`

## 相关代码

- 实现时会用到 [[contracts 的协作边界]]。
- 实现时会用到 [[transaction 的协作边界]]。

## 谁会来到这里

- [[AgentProtocolBatchApplyTests]] 会使用这里提供的行为。
- [[CanvasContractTests]] 会使用这里提供的行为。
- [[CanvasDeterminismTests]] 会使用这里提供的行为。
- [[CanvasRollbackTests]] 会使用这里提供的行为。
- [[HumanMaintenancePromptRegistryTests]] 会使用这里提供的行为。
- [[HumanMaintenancePromptRegistryTests 等测试场景]] 会使用这里提供的行为。
- [[HumanPageAuthoringPackageTests]] 会使用这里提供的行为。
- [[RecordReplaceTests]] 会使用这里提供的行为。
- [[TemplateProposalStoreTests]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[audit_operation_journal 与 _root 的协作实现]] 会使用这里提供的行为。
- [[audit_references 与 _root 的协作实现]] 会使用这里提供的行为。
- [[build_case]] 会使用这里提供的行为。
- [[build_case 等测试场景]] 会使用这里提供的行为。
- [[ckb_canvas 的协作边界]] 会使用这里提供的行为。
- [[command 等测试场景]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[deployment_plan]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[propose_template 与 _canonical_bytes 的协作实现]] 会使用这里提供的行为。
- [[refresh 等测试场景]] 会使用这里提供的行为。
- [[render_human_maintenance_prompt]] 会使用这里提供的行为。
- [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]] 会使用这里提供的行为。
- [[replace_note 与 RecordReplaceLockError 的协作实现]] 会使用这里提供的行为。
- [[rollback 与 RenderedBundle 的协作实现]] 汇总了本页。
- [[run]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[CanvasBenchmarkContractTests]]
- [[CanvasContractTests]]
- [[CanvasContractTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
