# validate

标签：#类型/代码

> `validate` 位于 `references/design/obsidian-canvas-agent-visualization/verification/validate_design.py` 第 31-69 行，本页用固定源码范围说明它如何校验输入、状态、证据或输出合同。 `validate` 负责在Canvas 设计 schema、fixture、链接和 benchmark 合同验证中校验输入、状态、证据或输出合同。

## 什么时候需要修改

当 `references/design/obsidian-canvas-agent-visualization/verification/validate_design.py` 中 `validate` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：references/design/obsidian-canvas-agent-visualization/verification/validate_design.py 第 31 行](vscode://file/E:/knowledge_builder/self-workspace/source/references/design/obsidian-canvas-agent-visualization/verification/validate_design.py:31:1)  `references/design/obsidian-canvas-agent-visualization/verification/validate_design.py:31-69`

## 相关代码

- 实现时会用到 [[CanvasContractTests]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[validate 与 canonical 的协作实现]]。

## 谁会来到这里

- [[CanvasContractTests]] 会使用这里提供的行为。
- [[CanvasPathTests]] 会使用这里提供的行为。
- [[CanvasTransactionTests]] 会使用这里提供的行为。
- [[HumanMaintenancePromptRegistryTests]] 会使用这里提供的行为。
- [[HumanMaintenancePromptRegistryTests 等测试场景]] 会使用这里提供的行为。
- [[HumanPageAuthoringPackageTests]] 会使用这里提供的行为。
- [[TemplateProposalStoreTests]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[ckb_canvas 的协作边界]] 会使用这里提供的行为。
- [[get_human_page_template 与 SectionContract 的协作实现]] 会使用这里提供的行为。
- [[main（fake_logseq 测试）]] 会使用这里提供的行为。
- [[propose_template 与 _canonical_bytes 的协作实现]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]] 会使用这里提供的行为。
- [[render_page_author]] 会使用这里提供的行为。
- [[render_page_author 与 _error 的协作实现]] 会使用这里提供的行为。
- [[rollback 与 RenderedBundle 的协作实现]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。
- [[validate 与 canonical 的协作实现]] 汇总了本页。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CanvasContractTests]]
- [[CanvasDeterminismTests]]
- [[CanvasGraphTests]]
- [[CanvasPathTests]]
- [[CanvasRollbackTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
