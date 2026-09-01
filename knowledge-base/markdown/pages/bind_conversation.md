# bind_conversation

标签：#类型/代码

> `bind_conversation` 是 `scripts/ckb_core/management_agent.py` 第 435-550 行定义的函数，本页绑定该固定源码范围。 负责管理 Agent 的会话绑定、执行队列、开发任务交接与合并审计状态。

## 什么时候需要修改

当 `bind_conversation` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/management_agent.py 第 435 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/management_agent.py:435:1)  `scripts/ckb_core/management_agent.py:435-550`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[append 等测试场景]]。
- 实现时会用到 [[bind_conversation 与 default_management_registry_path 的协作实现]]。
- 实现时会用到 [[preflight]]。

## 谁会来到这里

- [[append 等测试场景]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 汇总了本页。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[append 等测试场景]]
- [[command 等测试场景]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]
- [[main（session_stdio_harness_probe 测试）]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
