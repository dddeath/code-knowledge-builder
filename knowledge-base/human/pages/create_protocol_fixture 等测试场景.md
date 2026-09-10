# create_protocol_fixture 等测试场景

标签：#类型/代码

> `tests/test_agent_protocol_batch.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责以可执行样例验证 `test_agent_protocol_batch.py` 覆盖的成功行为、失败边界和回归约束。

## 什么时候需要修改

当 `tests/test_agent_protocol_batch.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_agent_protocol_batch.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_agent_protocol_batch.py:1:1)  `tests/test_agent_protocol_batch.py:1-690`

## 相关代码

- 主要代码单元是 [[create_protocol_fixture]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 26 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `tree_digest` | `tree_digest` 是第 38-44 行的函数，供所属页面定位实现。 |
| `install_fake_plugin` | `install_fake_plugin` 是第 121-126 行的函数，供所属页面定位实现。 |
| `outside_managed_bytes` | `outside_managed_bytes` 是第 129-132 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchMatrixTests` | `AgentProtocolBatchMat...` 是第 135-158 行的类，供所属页面定位实现。 |
| `AgentProtocolBatchMatrixTests.test_frozen_historical_fixtures_match_matrix` | `AgentProtocolBatchMat...` 是第 136-151 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchMatrixTests.test_unknown_and_backward_paths_are_rejected` | `AgentProtocolBatchMat...` 是第 153-158 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchPlanTests` | `AgentProtocolBatchPla...` 是第 161-269 行的类，供所属页面定位实现。 |
| `AgentProtocolBatchPlanTests.test_plan_is_byte_stable_and_does_not_write_target` | `AgentProtocolBatchPla...` 是第 162-178 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchPlanTests.test_manifest_and_project_failures_have_stable_categories` | `AgentProtocolBatchPla...` 是第 180-202 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchPlanTests.test_required_failure_fixtures_are_classified_without_guessing` | `AgentProtocolBatchPla...` 是第 204-253 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchPlanTests.test_duplicate_and_nested_outputs_fail_manifest_preflight` | `AgentProtocolBatchPla...` 是第 255-269 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests` | 通过夹具与故障注入覆盖协议批量升级的幂等、漂移、用户字节保留、部分失败、锁身份、续跑和定向回滚。 |
| `AgentProtocolBatchApplyTests.test_current_version_fixture_is_audited_and_idempotently_skipped` | `AgentProtocolBatchApp...` 是第 273-284 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_apply_rejects_plan_target_drift_before_transaction` | `AgentProtocolBatchApp...` 是第 286-300 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_apply_updates_protocol_contract_and_preserves_user_bytes` | `AgentProtocolBatchApp...` 是第 302-349 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_partial_failure_restores_failed_project_and_audits_each_result` | `AgentProtocolBatchApp...` 是第 351-391 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_partial_failure_restores_failed_project_and_audits_each_result.selective_audit` | `AgentProtocolBatchApp...` 是第 371-372 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_interrupted_apply_restores_baseline_then_resumes` | `AgentProtocolBatchApp...` 是第 393-423 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_interrupted_apply_restores_baseline_then_resumes.interrupt_after_first_write` | `AgentProtocolBatchApp...` 是第 402-408 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_existing_output_lock_reports_concurrent_failure_without_writes` | `AgentProtocolBatchApp...` 是第 425-438 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_live_cross_process_owner_is_not_stolen_after_stale_threshold` | `AgentProtocolBatchApp...` 是第 440-489 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_dead_cross_process_owner_is_recovered_only_after_stale_threshold` | `AgentProtocolBatchApp...` 是第 491-531 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_corrupt_pid_reused_unverifiable_and_release_drift_are_classified` | `AgentProtocolBatchApp...` 是第 533-607 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_single_project_rollback_restores_bytes_modes_and_source_version` | `AgentProtocolBatchApp...` 是第 609-638 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_subset_rollback_keeps_unselected_success_applied` | `AgentProtocolBatchApp...` 是第 640-667 行的函数，供所属页面定位实现。 |
| `AgentProtocolBatchApplyTests.test_rollback_refuses_post_batch_user_drift` | `AgentProtocolBatchApp...` 是第 669-685 行的函数，供所属页面定位实现。 |

</details>
