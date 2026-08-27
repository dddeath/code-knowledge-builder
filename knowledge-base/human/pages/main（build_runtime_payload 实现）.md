# main（build_runtime_payload 实现）

标签：#类型/代码

> `main` 是源码中负责接收命令参数并把请求路由到对应实现的命名代码单元。 它在所属模块内执行接收命令参数并把请求路由到对应实现，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当接收命令参数并把请求路由到对应实现所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/build_runtime_payload.py 第 101 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/build_runtime_payload.py:101:1)  `scripts/build_runtime_payload.py:101-112`

## 相关代码

- 实现时会用到 [[parser]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[main 与 sha256 的协作实现]] 汇总了本页。
