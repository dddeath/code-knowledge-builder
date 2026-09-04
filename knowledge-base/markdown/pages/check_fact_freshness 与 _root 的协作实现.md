# check_fact_freshness 与 _root 的协作实现

标签：#类型/代码

> 文件 `scripts/ckb_core/freshness.py`负责比较知识库固定提交与 Git 当前状态，生成事实新鲜度状态、迁移计划和协作记录。 它属于阻止 Agent 把过期源码事实当作当前结论的前置保护层，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当Git 事件、状态机、锁释放、迁移完成证据或检索结论保护变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/freshness.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/freshness.py:1:1)  `scripts/ckb_core/freshness.py:1-1037`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[ScopeExtensionOfferTests.retrieval]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 主要代码单元是 [[check_fact_freshness]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[preflight]]。
- 实现时会用到 [[sample 等测试场景]]。

## 谁会来到这里

- [[FactFreshnessStateMachineTest]] 会使用这里提供的行为。
- [[FactFreshnessStateMachineTest 等测试场景]] 会使用这里提供的行为。
- [[check_fact_freshness]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CanvasTransactionTests]]
- [[ChineseRetrievalEffectRetestFixtureTests]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[FactFreshnessStateMachineTest]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 33 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_root` | `_root` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_pid_alive` | `_pid_alive` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_read_lock` | `_read_lock` 读取并判定Git 源码事实新鲜度所需的数据或状态。 |
| `_lock_file_identity` | `_lock_file_identity` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_release_owned_state_lock` | `_release_owned_state_lock` 受控释放或回滚Git 源码事实新鲜度所需的数据或状态。 |
| `_state_lock` | `_state_lock` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_bounded_text` | `_bounded_text` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_repository_binding` | `_repository_binding` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_git` | `_git` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_status_records` | `_status_records` 读取并判定Git 源码事实新鲜度所需的数据或状态。 |
| `_repository_snapshot` | `_repository_snapshot` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_change_summary` | `_change_summary` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_iso_after` | `_iso_after` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_prune_overlays` | `_prune_overlays` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_write_overlay` | `_write_overlay` 生成并写入Git 源码事实新鲜度所需的数据或状态。 |
| `_migration_evidence` | `_migration_evidence` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_next_action` | `_next_action` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_event_record` | `_event_record` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_write_events` | `_write_events` 生成并写入Git 源码事实新鲜度所需的数据或状态。 |
| `_last_confirmed` | `_last_confirmed` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_unavailable_result` | `_unavailable_result` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `create_migration_plan` | `create_migration_plan` 创建并初始化Git 源码事实新鲜度所需的数据或状态。 |
| `discard_overlay` | `discard_overlay` 受控释放或回滚Git 源码事实新鲜度所需的数据或状态。 |
| `_command_strings` | `_command_strings` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `classify_git_trigger` | `classify_git_trigger` 解析并归一化Git 源码事实新鲜度所需的数据或状态。 |
| `_collaboration_path` | `_collaboration_path` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `_read_collaboration` | `_read_collaboration` 读取并判定Git 源码事实新鲜度所需的数据或状态。 |
| `_write_collaboration` | `_write_collaboration` 生成并写入Git 源码事实新鲜度所需的数据或状态。 |
| `_relative_paths` | `_relative_paths` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `record_collaboration` | `record_collaboration` 登记并持久化Git 源码事实新鲜度所需的数据或状态。 |
| `_feature_terms` | `_feature_terms` 完成Git 源码事实新鲜度中的一个明确步骤。 |
| `query_collaboration_records` | `query_collaboration_records` 读取并判定Git 源码事实新鲜度所需的数据或状态。 |
| `attach_freshness_to_retrieval` | `attach_freshness_to_retrieval` 完成Git 源码事实新鲜度中的一个明确步骤。 |

</details>
