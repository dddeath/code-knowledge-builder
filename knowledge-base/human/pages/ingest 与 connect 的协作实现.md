# ingest 与 connect 的协作实现

标签：#类型/代码

> 文件 `prototypes/ckb-tag-navigation/ckb_tag_navigation/store.py`负责以 SQLite 幂等保存 tag 事件，并为写入失败和回滚保留可恢复状态。 它属于机器 tag 实验的事务存储层，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当事件写入、事务、备份或回滚变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：prototypes/ckb-tag-navigation/ckb_tag_navigation/store.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/prototypes/ckb-tag-navigation/ckb_tag_navigation/store.py:1:1)  `prototypes/ckb-tag-navigation/ckb_tag_navigation/store.py:1-269`

## 相关代码

- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[assertions]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[contracts 的协作边界（743c915d）]]。
- 主要代码单元是 [[ingest]]。

## 谁会来到这里

- [[AutomationTest.register 等测试场景]] 会使用这里提供的行为。
- [[ChineseRetrievalEffectRetestFixtureTests]] 会使用这里提供的行为。
- [[DriftAndAvailabilityTests 等测试场景]] 会使用这里提供的行为。
- [[MigrationTest]] 会使用这里提供的行为。
- [[RecordReplaceTests 等测试场景]] 会使用这里提供的行为。
- [[ScopeExtensionTest]] 会使用这里提供的行为。
- [[SessionStdioLifecycleTests 等测试场景]] 会使用这里提供的行为。
- [[TagNavigationCanvasCompatibilityTests]] 会使用这里提供的行为。
- [[TagNavigationProjectionTests]] 会使用这里提供的行为。
- [[TagNavigationRollbackTests]] 会使用这里提供的行为。
- [[TagNavigationStateMachineTests]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[assertions 等测试场景]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[audit_gap_register]] 会使用这里提供的行为。
- [[audit_migration]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[benchmark 的协作边界（9fab5b96）]] 会使用这里提供的行为。
- [[build_case]] 会使用这里提供的行为。
- [[cli 的协作边界（prototypes）]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[doctor_report]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[ingest_reference 与 _root 的协作实现]] 会使用这里提供的行为。
- [[main（fake_logseq 测试）]] 会使用这里提供的行为。
- 可从 [[prototypes 职责导览]] 进入本页。
- [[replace_note 与 RecordReplaceLockError 的协作实现]] 会使用这里提供的行为。
- [[retrieve]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[run_failure_probe 等测试场景]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。
- [[state_machine 的协作边界]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register]]
- [[AutomationTest.register 等测试场景]]
- [[CanvasContractTests]]
- [[CanvasContractTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 8 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `connect` | `connect` 完成tag 事务与回滚所需的一个明确步骤。 |
| `initialize` | `initialize` 创建并初始化tag 事务与回滚所需的一个明确步骤。 |
| `read_assertion_jsonl` | `read_assertion_jsonl` 读取并判定tag 事务与回滚所需的一个明确步骤。 |
| `load_assertions` | `load_assertions` 读取并判定tag 事务与回滚所需的一个明确步骤。 |
| `integrity` | `integrity` 完成tag 事务与回滚所需的一个明确步骤。 |
| `replay_with_rollback` | `replay_with_rollback` 完成tag 事务与回滚所需的一个明确步骤。 |
| `_rollback_path_within` | `_rollback_path_within` 受控回滚tag 事务与回滚所需的一个明确步骤。 |
| `rollback` | `rollback` 受控回滚tag 事务与回滚所需的一个明确步骤。 |

</details>
