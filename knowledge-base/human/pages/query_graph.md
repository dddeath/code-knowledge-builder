# query_graph

标签：#类型/代码

> `query_graph` 是源码中负责构造职责关系图并提供职责群或路径查询的命名代码单元。 它在所属模块内执行构造职责关系图并提供职责群或路径查询，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当构造职责关系图并提供职责群或路径查询所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/graphify_core.py 第 526 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/graphify_core.py:526:1)  `scripts/ckb_core/graphify_core.py:526-583`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[query_graph 与 _networkx_modules 的协作实现]]。
- 实现时会用到 [[source_files]]。
- 实现时会用到 [[start_scope_extension 与 _error 的协作实现]]。

## 谁会来到这里

- [[query_graph 与 _networkx_modules 的协作实现]] 汇总了本页。
