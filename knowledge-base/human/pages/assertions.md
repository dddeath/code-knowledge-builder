# assertions

标签：#类型/代码

> 代码单元 `assertions`负责验证 tag assertion、策略、幂等写入和路径失败边界。 它属于tag 实验输入与事务合同的回归保护，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当Schema、路径、隐私或事务规则变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_contracts.py 第 23 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_contracts.py:23:1)  `tests/test_ckb_tag_navigation_contracts.py:23-24`

## 谁会来到这里

- [[TagNavigationCanvasCompatibilityTests]] 会使用这里提供的行为。
- [[TagNavigationProjectionTests]] 会使用这里提供的行为。
- [[TagNavigationRollbackTests]] 会使用这里提供的行为。
- [[TagNavigationStateMachineTests]] 会使用这里提供的行为。
- [[assertions 等测试场景]] 汇总了本页。
- [[ingest]] 会使用这里提供的行为。
- [[ingest 与 connect 的协作实现]] 会使用这里提供的行为。
- [[state_machine 的协作边界]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[PdfReferenceExtractionTests]]
- [[PdfReferenceExtractionTests 等测试场景]]
- [[TagNavigationCanvasCompatibilityTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
