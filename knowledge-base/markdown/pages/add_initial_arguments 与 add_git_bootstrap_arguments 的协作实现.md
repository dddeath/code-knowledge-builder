# add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现

标签：#类型/代码

> 该代码页汇总 Code Knowledge Builder 的命令行入口、参数路由和退出状态。 它把构建、迁移、检索、工作区记录与自动化命令连接到确定性核心，并新增会话级 `automation activate` 路由。

## 什么时候需要修改

当命令、参数、退出码、会话激活入口或子命令调度变化时，需要修改本页并重跑 CLI 与 Hook canary。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:1:1)  `scripts/ckb.py:1-495`

## 相关代码

- 主要代码单元是 [[add_git_bootstrap_arguments]]。
- 主要代码单元是 [[add_initial_arguments]]。
- 主要代码单元是 [[main（ckb 实现）]]。
- 主要代码单元是 [[parser]]。

## 谁会来到这里

- [[add_initial_arguments]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[render_integration 与 _looks_windows 的协作实现]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[MigrationTest]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]

## 内部细节

<details><summary>查看本页收纳的 2 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `add_csharp_arguments` | 该附属代码负责计算机器交付物的完整性摘要，并把结果交给所属页面中的主流程使用。 |
| `emit` | 该附属代码负责命令行参数、子命令路由、统一退出码和顶层异常边界，并把结果交给所属页面中的主流程使用。 |

</details>
