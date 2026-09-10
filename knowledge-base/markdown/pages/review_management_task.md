# review_management_task

标签：#类型/代码

> 复验已派发开发任务的声明测试与提交状态，生成管理侧验证记录。 核对测试退出状态、开发树是否变化及集成基线，满足条件后记录实现状态；它不执行源码合并，也不证明声明测试覆盖了全部需求。

## 什么时候需要修改

调整任务验收命令、基线检查、结果记录或重复复验条件时修改。

## 在代码中的位置

[打开源码：scripts/ckb_core/management_agent.py 第 1294 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/management_agent.py:1294:1)  `scripts/ckb_core/management_agent.py:1294-1398`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_management_task 与 default_management_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[review_management_task 与 default_management_registry_path 的协作实现]] 汇总了本页。
