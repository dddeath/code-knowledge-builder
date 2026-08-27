# module_name

标签：#类型/代码

> `module_name` 是源码中负责页面配额、实体归属、关系预算和上下文预算的确定性决策的命名代码单元。 它在所属模块内执行页面配额、实体归属、关系预算和上下文预算的确定性决策，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当页面配额、实体归属、关系预算和上下文预算的确定性决策所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/navigation.py 第 37 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/navigation.py:37:1)  `scripts/ckb_core/navigation.py:37-39`

## 谁会来到这里

- [[module_name 与 estimated_tokens 的协作实现]] 汇总了本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[MigrationTest]]
