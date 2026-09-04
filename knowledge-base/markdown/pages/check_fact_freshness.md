# check_fact_freshness

标签：#类型/代码

> 代码单元 `check_fact_freshness`负责比较知识库固定提交与 Git 当前状态，生成事实新鲜度状态、迁移计划和协作记录。 它属于阻止 Agent 把过期源码事实当作当前结论的前置保护层，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当Git 事件、状态机、锁释放、迁移完成证据或检索结论保护变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/freshness.py 第 569 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/freshness.py:569:1)  `scripts/ckb_core/freshness.py:569-685`

## 相关代码

- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[check_fact_freshness 与 _root 的协作实现]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。

## 谁会来到这里

- [[FactFreshnessStateMachineTest]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[check_fact_freshness 与 _root 的协作实现]] 汇总了本页。
- [[ingest_event]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[run_probe]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CanvasContractTests]]
- [[CanvasDeterminismTests]]
- [[CanvasGraphTests]]
- [[CanvasPathTests]]
- [[CanvasRollbackTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
