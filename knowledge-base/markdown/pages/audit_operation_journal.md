# audit_operation_journal

标签：#类型/代码

> `audit_operation_journal` 位于 `scripts/ckb_core/operation_journal.py` 第 385-454 行，本页用固定源码范围说明它如何校验输入、状态、证据或输出合同。 `audit_operation_journal` 负责在该文件所属能力的输入、状态、输出和失败边界中校验输入、状态、证据或输出合同。

## 什么时候需要修改

当 `scripts/ckb_core/operation_journal.py` 中 `audit_operation_journal` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/operation_journal.py 第 385 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/operation_journal.py:385:1)  `scripts/ckb_core/operation_journal.py:385-454`

## 相关代码

- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_operation_journal 与 _root 的协作实现]]。

## 谁会来到这里

- [[audit_operation_journal 与 _root 的协作实现]] 汇总了本页。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[ScopeExtensionTest]]
- [[append 等测试场景]]
- [[command 等测试场景]]
- [[refresh 等测试场景]]
