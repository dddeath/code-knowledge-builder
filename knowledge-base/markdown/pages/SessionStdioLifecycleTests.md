# SessionStdioLifecycleTests

标签：#类型/代码

> `SessionStdioLifecycle...` 是 `tests/test_session_stdio.py` 第 77-536 行定义的类，本页绑定该固定源码范围。 该类作为可执行验证入口，检查标识符 `SessionStdioLifecycleTests` 所指的行为与失败边界。

## 什么时候需要修改

当被测行为、输入夹具、断言或失败条件变化时，应同步更新 `SessionStdioLifecycleTests` 的说明。

## 在代码中的位置

[打开源码：tests/test_session_stdio.py 第 77 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_session_stdio.py:77:1)  `tests/test_session_stdio.py:77-536`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[SessionStdioLifecycleTests 等测试场景]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[contracts 的协作边界（36093e4a）]]。
- 实现时会用到 [[doctor_report 与 _version_matches 的协作实现]]。
- 实现时会用到 [[ingest_event]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。

## 谁会来到这里

- [[SessionStdioLifecycleTests 等测试场景]] 汇总了本页。
- [[ingest_event]] 关联到这里的验证场景。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 28 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `SessionStdioLifecycleTests.setUp` | `SessionStdioLifecycle...` 是第 78-93 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.tearDown` | `SessionStdioLifecycle...` 是第 95-107 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.event` | `SessionStdioLifecycle...` 是第 109-116 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_session_start_and_plain_prompt_do_not_start_stdio` | `SessionStdioLifecycle...` 是第 118-129 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_exact_skill_activation_reuses_pid_across_turn_stop_and_session_end_reaps` | `SessionStdioLifecycle...` 是第 131-184 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_sixteen_concurrent_first_requests_singleflight_and_isolation` | `SessionStdioLifecycle...` 是第 186-240 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_sixteen_concurrent_first_requests_singleflight_and_isolation.request` | `SessionStdioLifecycle...` 是第 207-214 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_parent_death_reaps_and_explicit_close_is_idempotent` | `SessionStdioLifecycle...` 是第 242-269 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_start_failure_is_bounded_cli_fallback_not_resident` | `SessionStdioLifecycle...` 是第 271-284 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_same_external_id_immediate_reactivation_uses_new_generation` | `SessionStdioLifecycle...` 是第 286-324 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_compact_lease_temporary_supports_long_windows_root` | `SessionStdioLifecycle...` 是第 326-362 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_over_budget_windows_root_returns_explicit_fallback` | `SessionStdioLifecycle...` 是第 365-381 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_server_crash_restarts_once_then_falls_back_to_per_command_cli` | `SessionStdioLifecycle...` 是第 383-421 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_supervisor_crash_stale_lease_is_cleaned_before_reactivation` | `SessionStdioLifecycle...` 是第 423-454 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_protocol_version_mismatch_fails_handshake_with_bounded_reason` | `SessionStdioLifecycle...` 是第 456-497 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_protocol_version_mismatch_fails_handshake_with_bounded_reason.FakeProcess` | `SessionStdioLifecycle...` 是第 457-477 行的类，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_protocol_version_mismatch_fails_handshake_with_bounded_reason.FakeProcess.__init__` | `SessionStdioLifecycle...` 是第 461-464 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_protocol_version_mismatch_fails_handshake_with_bounded_reason.FakeProcess.poll` | `SessionStdioLifecycle...` 是第 466-467 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_protocol_version_mismatch_fails_handshake_with_bounded_reason.FakeProcess.wait` | `SessionStdioLifecycle...` 是第 469-471 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_protocol_version_mismatch_fails_handshake_with_bounded_reason.FakeProcess.terminate` | `SessionStdioLifecycle...` 是第 473-474 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_protocol_version_mismatch_fails_handshake_with_bounded_reason.FakeProcess.kill` | `SessionStdioLifecycle...` 是第 476-477 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_close_timeout_escalates_to_terminate_then_kill_and_waits` | `SessionStdioLifecycle...` 是第 499-536 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_close_timeout_escalates_to_terminate_then_kill_and_waits.TimeoutProcess` | `SessionStdioLifecycle...` 是第 500-526 行的类，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_close_timeout_escalates_to_terminate_then_kill_and_waits.TimeoutProcess.__init__` | `SessionStdioLifecycle...` 是第 504-510 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_close_timeout_escalates_to_terminate_then_kill_and_waits.TimeoutProcess.poll` | `SessionStdioLifecycle...` 是第 512-513 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_close_timeout_escalates_to_terminate_then_kill_and_waits.TimeoutProcess.wait` | `SessionStdioLifecycle...` 是第 515-520 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_close_timeout_escalates_to_terminate_then_kill_and_waits.TimeoutProcess.terminate` | `SessionStdioLifecycle...` 是第 522-523 行的函数，供所属页面定位实现。 |
| `SessionStdioLifecycleTests.test_close_timeout_escalates_to_terminate_then_kill_and_waits.TimeoutProcess.kill` | `SessionStdioLifecycle...` 是第 525-526 行的函数，供所属页面定位实现。 |

</details>
