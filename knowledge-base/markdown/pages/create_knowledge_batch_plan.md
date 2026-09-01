# create_knowledge_batch_plan

标签：#类型/代码

> `create_knowledge_batc...` 是 `scripts/ckb_core/knowledge_batch_migration.py` 第 888-956 行定义的函数，本页绑定该固定源码范围。 负责完整知识库批量迁移的计划、隔离构建、审计、切换和精确回滚。

## 什么时候需要修改

当 `create_knowledge_batch_plan` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/knowledge_batch_migration.py 第 888 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_batch_migration.py:888:1)  `scripts/ckb_core/knowledge_batch_migration.py:888-956`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[create_batch_plan 与 ProtocolRelease 的协作实现]]。
- 实现时会用到 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]]。

## 谁会来到这里

- [[command 等测试场景]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 汇总了本页。
- [[refresh 等测试场景]] 会使用这里提供的行为。

## 相关测试

- [[command 等测试场景]]
- [[refresh 等测试场景]]
