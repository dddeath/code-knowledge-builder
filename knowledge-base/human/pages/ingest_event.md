# ingest_event

标签：#类型/代码

> 代码单元 `ingest_event`负责接收多 Harness 事件，维持会话级 Skill 激活状态，并把待审阅事实写入机器层。 它属于自动采集与受控人类投影之间的会话生命周期边界，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当事件格式、会话身份、激活规则、并发锁或审阅流程变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/automation.py 第 1411 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1411:1)  `scripts/ckb_core/automation.py:1411-1537`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[check_fact_freshness]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.register 等测试场景]] 会使用这里提供的行为。
- [[FactFreshnessStateMachineTest 等测试场景]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 会使用这里提供的行为。
- [[SessionStdioLifecycleTests]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 汇总了本页。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[FactFreshnessStateMachineTest 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests 等测试场景]]
- [[SessionStdioLifecycleTests]]
