# doctor_report

标签：#类型/代码

> 代码单元 `doctor_report`负责启动并约束语言服务器，收集 Python、JavaScript、C/C++ 和 C# 的语义证据。 它属于精确语义与无编译数据库时有界近似之间的提供器层，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当运行时定位、LSP 协议、编译参数、诊断分级或进程释放变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/providers.py 第 76 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/providers.py:76:1)  `scripts/ckb_core/providers.py:76-240`

## 相关代码

- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[doctor_report 与 _version_matches 的协作实现]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[query_graph 与 _networkx_modules 的协作实现]]。

## 谁会来到这里

- [[doctor_report 与 _version_matches 的协作实现]] 汇总了本页。
