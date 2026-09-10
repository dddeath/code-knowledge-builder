# migrate_output

标签：#类型/代码

> 从完成且全局审计通过的旧库创建增量输出，并返回迁移计划、复用统计和下一审阅包。 预检创作包与必需证据，沿用范围和页面配置初始化固定快照；只复用文件内容、声明范围与审阅形状一致的已审实体，其余进入增量审阅。

## 什么时候需要修改

需要修改迁移启动条件、范围继承、保留层或复用拆包规则时修改；计划生成和审阅就绪不代表已切换或发布。

## 在代码中的位置

[打开源码：scripts/ckb_core/migration.py 第 482 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:482:1)  `scripts/ckb_core/migration.py:482-595`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[migrate_output 与 _entity_key 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[migrate_output 与 _entity_key 的协作实现]] 汇总了本页。
