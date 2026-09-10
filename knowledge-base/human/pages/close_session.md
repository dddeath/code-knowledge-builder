# close_session

标签：#类型/代码

> 该函数按 Harness、会话摘要和输出身份匹配租约，为匹配会话写入关闭控制请求并等待服务及监督进程退出；超时后强制终止记录中的进程并调用限定会话清理。 它提供显式会话关闭入口，区分已经关闭、正常关闭和强制清理，并返回匹配数量。强制分支返回的是清理动作结果标签，不额外保证末次进程存活复查已经完成。

## 什么时候需要修改

租约匹配、关闭控制字段、等待超时或强制终止清理策略变化时修改此函数，并检查只命中指定输出会话及无匹配时的返回状态。

## 在代码中的位置

[打开源码：scripts/ckb_core/session_stdio.py 第 1330 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/session_stdio.py:1330:1)  `scripts/ckb_core/session_stdio.py:1330-1389`

## 相关代码

- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[close_session 与 _StartGate 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[close_session 与 _StartGate 的协作实现]] 汇总了本页。
- 与 [[review_automation 与 default_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_management_task 与 default_management_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
