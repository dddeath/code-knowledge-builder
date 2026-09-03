# ingest

标签：#类型/代码

> 代码单元 `ingest`负责以 SQLite 幂等保存 tag 事件，并为写入失败和回滚保留可恢复状态。 它属于机器 tag 实验的事务存储层，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当事件写入、事务、备份或回滚变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：prototypes/ckb-tag-navigation/ckb_tag_navigation/store.py 第 68 行](vscode://file/E:/knowledge_builder/self-workspace/source/prototypes/ckb-tag-navigation/ckb_tag_navigation/store.py:68:1)  `prototypes/ckb-tag-navigation/ckb_tag_navigation/store.py:68-104`

## 相关代码

- 实现时会用到 [[assertions]]。
- 实现时会用到 [[contracts 的协作边界（743c915d）]]。

## 谁会来到这里

- [[PdfReferenceExtractionTests]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[audit_operation_journal 与 _root 的协作实现]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[extract_pdf 与 PdfExtractionError 的协作实现]] 会使用这里提供的行为。
- [[ingest 与 connect 的协作实现]] 汇总了本页。
- [[ingest_reference]] 会使用这里提供的行为。
- [[ingest_reference 与 _root 的协作实现]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[web_input_adapter_contract]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[PdfReferenceExtractionTests]]
- [[PdfReferenceExtractionTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
