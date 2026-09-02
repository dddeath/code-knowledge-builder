# audit_migration

标签：#类型/代码

> `audit_migration` 是 `scripts/ckb_core/migration.py` 第 367-479 行定义的函数，本页绑定该固定源码范围。 负责把已审计知识库增量迁移到新快照，并保留可变层和复用证明。

## 什么时候需要修改

当 `audit_migration` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/migration.py 第 367 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:367:1)  `scripts/ckb_core/migration.py:367-479`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[execute]]。

## 谁会来到这里

- [[MigrationTest]] 会使用这里提供的行为。
- [[audit_global]] 会使用这里提供的行为。
- [[audit_global 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 汇总了本页。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanPageTemplateValidationTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[KeywordFallbackRetrievalWiringTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `audit_migration.check` | `audit_migration.check` 是第 373-374 行的函数，供所属页面定位实现。 |

</details>
