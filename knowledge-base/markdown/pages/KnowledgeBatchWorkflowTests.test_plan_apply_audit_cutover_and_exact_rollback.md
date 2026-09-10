# KnowledgeBatchWorkflowTests.test_plan_apply_audit_cutover_and_exact_rollback

标签：#类型/代码

> 该测试用含工作记录、参考、缺口和用户笔记的基线贯通计划、应用、审计与切换，再执行第二次切换并按父链逆序回滚。 它同时核对目录树精确恢复和移动后固定快照的 Git 反向注册与锁标记，防止只有内容恢复但工作树管理信息失效。

## 什么时候需要修改

切换链、备份恢复位置、可变层保留或工作树重注册变化时修改此测试，并保留两次切换后的逐级树摘要断言。

## 在代码中的位置

[打开源码：tests/test_knowledge_batch_migration.py 第 271 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_knowledge_batch_migration.py:271:1)  `tests/test_knowledge_batch_migration.py:271-342`

## 相关代码

- 与 [[KnowledgeBatchWorkflowTests.test_plan_apply_audit_cutover_and_exact_rollback 等测试场景]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[KnowledgeBatchWorkflowTests.test_plan_apply_audit_cutover_and_exact_rollback 等测试场景]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `KnowledgeBatchWorkflowTests.test_plan_apply_audit_cutover_and_exact_rollback.assert_registration` | 复读固定快照的 Git 管理目录，核对工作树反向注册指向当前路径且仍持有锁定标记。 |

</details>
