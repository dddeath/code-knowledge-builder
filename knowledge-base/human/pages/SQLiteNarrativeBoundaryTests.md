# SQLiteNarrativeBoundaryTests

标签：#类型/代码

> 组织 SQLite 叙述边界的两组单元测试。 以普通实现句子作为允许组，以完整性检查、数据库状态和 PRAGMA 语句作为机器证据组，逐例运行断言。

## 什么时候需要修改

需要扩充数据库证据语法或验证规则收窄后的误报边界时修改。

## 在代码中的位置

[打开源码：tests/test_sqlite_narrative_boundary.py 第 4 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_sqlite_narrative_boundary.py:4:1)  `tests/test_sqlite_narrative_boundary.py:4-19`

## 谁会来到这里

- [[SQLiteNarrativeBoundaryTests 等测试场景]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 2 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `SQLiteNarrativeBoundaryTests.test_implementation_descriptions_using_through_are_not_machine_results` | 断言包含“通过”的 SQLite 实现叙述不被判为数据库检查结果。 |
| `SQLiteNarrativeBoundaryTests.test_explicit_database_check_results_remain_machine_evidence` | 逐例断言显式数据库检查语句和通过状态仍命中机器证据规则。 |

</details>
