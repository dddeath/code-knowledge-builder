# audit_operation_journal

标签：#类型/代码

> `audit_operation_journal` 是 `scripts/ckb_core/operation_journal.py` 第 383-452 行定义的函数，本页绑定该固定源码范围。 负责追加和审计有界、机器可读的操作日志。

## 什么时候需要修改

当 `audit_operation_journal` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/operation_journal.py 第 383 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/operation_journal.py:383:1)  `scripts/ckb_core/operation_journal.py:383-452`

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
