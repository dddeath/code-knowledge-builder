# FactFreshnessStateMachineTest

标签：#类型/代码

> 代码单元 `setUp`负责验证 Git 驱动的事实新鲜度状态机、迁移计划、并发锁和协作记录。 它属于过期事实保护与自动同步触发的回归保护，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当Git 状态、迁移证据、锁所有权或协作查询变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：tests/test_git_fact_freshness.py 第 47 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_git_fact_freshness.py:47:1)  `tests/test_git_fact_freshness.py:47-337`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[check_fact_freshness]]。
- 实现时会用到 [[check_fact_freshness 与 _root 的协作实现]]。

## 谁会来到这里

- [[FactFreshnessStateMachineTest 等测试场景]] 汇总了本页。
- [[HumanMaintenancePromptRegistryTests]] 会使用这里提供的行为。
- [[PageFanoutBenchmarkTests]] 会使用这里提供的行为。
- [[check_fact_freshness 与 _root 的协作实现]] 关联到这里的验证场景。
- [[maintenance_check 与 capability_matrix 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[preflight]] 关联到这里的验证场景。
- [[preflight 与 git 的协作实现]] 关联到这里的验证场景。
- [[render_page_author 与 _error 的协作实现]] 会使用这里提供的行为。
- [[sample 等测试场景]] 关联到这里的验证场景。
- [[transaction 的协作边界]] 会使用这里提供的行为。
- [[validate_human_maintenance_invocation]] 会使用这里提供的行为。
- [[validate_human_maintenance_invocation 与 ParameterSpec 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[CanvasBenchmarkContractTests]]
- [[CanvasContractTests]]
- [[CanvasDeterminismTests]]
- [[CanvasGraphTests]]
- [[CanvasPathTests]]
- [[CanvasRollbackTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 20 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `FactFreshnessStateMachineTest.setUp` | `setUp` 完成源码事实新鲜度回归验证中的一个明确步骤。 |
| `FactFreshnessStateMachineTest.tearDown` | `tearDown` 完成源码事实新鲜度回归验证中的一个明确步骤。 |
| `FactFreshnessStateMachineTest._write_output_state` | `_write_output_state` 生成并写入源码事实新鲜度回归验证所需的数据或状态。 |
| `FactFreshnessStateMachineTest._commit` | `_commit` 完成源码事实新鲜度回归验证中的一个明确步骤。 |
| `FactFreshnessStateMachineTest.test_contract_declares_only_the_six_frozen_states` | 该测试验证“contract declares only the si…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_same_session_and_same_head_reuse_without_rebuilding` | 该测试验证“same session and same head re…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_new_commit_marks_stable_facts_stale_and_summarizes_range` | 该测试验证“new commit marks stable facts…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_dirty_worktree_creates_discardable_overlay_without_promoting_it` | 该测试验证“dirty worktree creates discar…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_dirty_tree_overlays_committed_drift_without_hiding_stable_state` | 该测试验证“dirty tree overlays committed…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_staging_requires_all_completion_evidence_before_ready` | 该测试验证“staging requires all completi…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_unavailable_preserves_last_confirmed_and_recovers_on_retry` | 该测试验证“unavailable preserves last co…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_stale_retrieval_pack_and_record_carry_a_deterministic_conclusion_guard` | 该测试验证“stale retrieval pack and reco…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_cli_status_returns_stale_exit_and_plan_never_creates_staging` | 该测试验证“cli status returns stale exit…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_dead_lock_is_recovered_and_concurrent_checks_serialize` | 该测试验证“dead lock is recovered and co…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_dead_lock_is_recovered_and_concurrent_checks_serialize.inspect` | `inspect` 完成源码事实新鲜度回归验证中的一个明确步骤。 |
| `FactFreshnessStateMachineTest.test_release_retries_windows_sharing_violation_and_leaves_no_lock` | 该测试验证“release retries windows shari…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_release_retries_windows_sharing_violation_and_leaves_no_lock.sharing_violation` | `sharing_violation` 完成源码事实新鲜度回归验证中的一个明确步骤。 |
| `FactFreshnessStateMachineTest.test_release_never_deletes_lock_replaced_by_another_owner` | 该测试验证“release never deletes lock re…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_release_timeout_is_bounded_diagnostic_and_preserves_owned_lock` | 该测试验证“release timeout is bounded di…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `FactFreshnessStateMachineTest.test_release_timeout_is_bounded_diagnostic_and_preserves_owned_lock.always_busy` | `always_busy` 完成源码事实新鲜度回归验证中的一个明确步骤。 |

</details>
