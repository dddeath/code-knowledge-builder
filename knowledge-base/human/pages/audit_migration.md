# audit_migration

标签：#类型/代码

> `audit_migration` 对增量迁移计划、复用集合、可变层基线、审阅状态和目标图来源执行确定性复核。 它区分不可变的迁移基线与可继续写入的工作副本，验证 Markdown/JSON 可读性和 SQLite 完整性，并在全部门通过后提升迁移状态。

## 什么时候需要修改

当迁移计划 Schema、允许的可变文件类型、完整性规则或完成状态语义变化时，需要修改该函数并增加失败注入测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/migration.py 第 353 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:353:1)  `scripts/ckb_core/migration.py:353-460`

## 相关代码

- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[MigrationTest]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 汇总了本页。
- [[create_source_snapshot 与 git 的协作实现]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[main（generate_large_fixture 测试）]] 会使用这里提供的行为。
- [[run]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `audit_migration.check` | 把单项迁移门的名称、真假结果和证据追加到审计清单。 |

</details>
