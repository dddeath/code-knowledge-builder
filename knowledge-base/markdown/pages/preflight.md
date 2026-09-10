# preflight

标签：#类型/代码

> 确认可用 Git 仓库并拒绝任何已跟踪或未跟踪的工作树改动，返回规范化仓库根、HEAD 提交、tree 及初始化记录。 先通过 prepare_git_repository 处理已有仓库或显式首次初始化，再执行包含未跟踪文件的 porcelain 状态检查；脏工作树抛出 StaleSourceError，不生成可用基线描述。

## 什么时候需要修改

修改 Git 首次初始化、干净状态定义或仓库根定位时，联动 prepare_git_repository 与使用返回 commit/tree 的快照创建和来源一致性检查。

## 在代码中的位置

[打开源码：scripts/ckb_core/gitrepo.py 第 194 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:194:1)  `scripts/ckb_core/gitrepo.py:194-217`

## 相关代码

- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[preflight 与 git 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[preflight 与 git 的协作实现]] 汇总了本页。
- 与 [[start_scope_extension]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[start_scope_extension 与 _error 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
