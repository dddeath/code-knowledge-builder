# package_showcase

标签：#类型/代码

> `package_showcase` 是源码中负责构建可复现发行归档并复核成员集合的命名代码单元。 它在所属模块内执行构建可复现发行归档并复核成员集合，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当构建可复现发行归档并复核成员集合所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/showcase.py 第 66 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/showcase.py:66:1)  `scripts/ckb_core/showcase.py:66-172`

## 相关代码

- 实现时会用到 [[package_showcase 与 _parse_sample 的协作实现]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[package_showcase 与 _parse_sample 的协作实现]] 汇总了本页。
