# create_knowledge_batch_plan

标签：#类型/代码

> 读取并规范化批量迁移清单，为各项目生成只读预检结果、可执行策略和不可变计划摘要，可选择写到所有知识库目录之外。 先校验结构及恢复路径拓扑，再逐项目捕获分类失败并继续汇总；只有 ready 或 cold-build-required 计为可行动项目，据此返回 ready、partial 或 failed。计划同时记录版本矩阵、manifest digest 与 plan digest，未执行迁移或切换。

## 什么时候需要修改

调整清单归一化、允许根、恢复拓扑、项目预检或状态计数时，联动 _inspect_knowledge_project 和后续计划绑定校验；保持计划写入位置不落在任何 OUTPUT 或 staging 内。

## 在代码中的位置

[打开源码：scripts/ckb_core/knowledge_batch_migration.py 第 889 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_batch_migration.py:889:1)  `scripts/ckb_core/knowledge_batch_migration.py:889-957`

## 相关代码

- 与 [[BatchProjectError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 汇总了本页。
