# git（test_migration 测试）

标签：#类型/代码

> 该函数执行指定迁移测试仓库的 Git 子命令，失败时抛出捕获的标准错误，成功返回修剪后的标准输出。 它为迁移测试构造提交和读取身份提供简短入口，使用子进程默认文本编码而不是显式指定 UTF-8。

## 什么时候需要修改

迁移测试的命令或编码要求变化时修改此函数，并核对非 ASCII 输出与失败诊断。

## 在代码中的位置

[打开源码：tests/test_migration.py 第 21 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:21:1)  `tests/test_migration.py:21-30`

## 谁会来到这里

- [[git 等测试场景（test_migration 测试）]] 汇总了本页。
