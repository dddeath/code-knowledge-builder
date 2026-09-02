# create_batch_plan

标签：#类型/代码

> `create_batch_plan` 是 `scripts/ckb_core/agent_protocol_batch.py` 第 657-714 行定义的函数，本页绑定该固定源码范围。 负责批量升级 Agent Protocol，包括计划、锁、备份、审计、切换和回滚。

## 什么时候需要修改

当 `create_batch_plan` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_protocol_batch.py 第 657 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol_batch.py:657:1)  `scripts/ckb_core/agent_protocol_batch.py:657-714`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[create_batch_plan 与 ProtocolRelease 的协作实现]]。

## 谁会来到这里

- [[AgentProtocolBatchApplyTests]] 会使用这里提供的行为。
- [[AgentProtocolBatchApplyTests 等测试场景]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 汇总了本页。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
