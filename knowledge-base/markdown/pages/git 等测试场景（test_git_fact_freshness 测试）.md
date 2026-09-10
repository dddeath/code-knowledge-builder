# git 等测试场景（test_git_fact_freshness 测试）

标签：#类型/代码

> 文件 `tests/test_git_fact_freshness.py`负责验证 Git 驱动的事实新鲜度状态机、迁移计划、并发锁和协作记录。 它属于过期事实保护与自动同步触发的回归保护，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当Git 状态、迁移证据、锁所有权或协作查询变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：tests/test_git_fact_freshness.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_git_fact_freshness.py:1:1)  `tests/test_git_fact_freshness.py:1-527`

## 相关代码

- 主要代码单元是 [[git（test_git_fact_freshness 测试）]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 31 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `FactFreshnessStateMachineTest` | 覆盖 Git 事实六状态、脏树临时层、迁移就绪门、检索结论限制及锁并发恢复，确保不静默改写稳定事实。 |
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
| `GitTriggerAndCollaborationTest` | `setUp` 完成源码事实新鲜度回归验证中的一个明确步骤。 |
| `GitTriggerAndCollaborationTest.setUp` | `setUp` 完成源码事实新鲜度回归验证中的一个明确步骤。 |
| `GitTriggerAndCollaborationTest.tearDown` | `tearDown` 完成源码事实新鲜度回归验证中的一个明确步骤。 |
| `GitTriggerAndCollaborationTest.test_git_tool_commands_classify_only_the_four_required_event_families` | 该测试验证“git tool commands classify on…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `GitTriggerAndCollaborationTest.test_branch_commit_task_queries_and_duplicate_candidates_keep_evidence_boundary` | 该测试验证“branch commit task queries an…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `RealGitEventSequenceTest` | `setUp` 完成源码事实新鲜度回归验证中的一个明确步骤。 |
| `RealGitEventSequenceTest.setUp` | `setUp` 完成源码事实新鲜度回归验证中的一个明确步骤。 |
| `RealGitEventSequenceTest.tearDown` | `tearDown` 完成源码事实新鲜度回归验证中的一个明确步骤。 |
| `RealGitEventSequenceTest.test_commit_branch_switch_merge_and_pull_each_drive_a_real_check` | 该测试验证“commit branch switch merge an…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。 |
| `RealGitEventSequenceTest.test_commit_branch_switch_merge_and_pull_each_drive_a_real_check.git_event` | `git_event` 完成源码事实新鲜度回归验证中的一个明确步骤。 |

</details>
