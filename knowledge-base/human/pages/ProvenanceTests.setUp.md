# ProvenanceTests.setUp

标签：#类型/代码

> 该初始化方法创建临时小型 Git 仓库并提交固定的双倍计算函数，登记临时目录自动清理，并设置旧新输出位置。 它为来源保留测试提供真实 Git 对象与可移动的固定快照基础，而不是以文件名或虚构提交代替版本身份。

## 什么时候需要修改

来源测试的仓库最小内容、Git 身份或输出目录结构变化时修改此方法，并保持每项测试隔离。

## 在代码中的位置

[打开源码：tests/test_recruitment_migration_provenance.py 第 33 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_recruitment_migration_provenance.py:33:1)  `tests/test_recruitment_migration_provenance.py:33-45`

## 相关代码

- 与 [[ProvenanceTests.setUp 等测试场景]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[ProvenanceTests.setUp 等测试场景]] 汇总了本页。
