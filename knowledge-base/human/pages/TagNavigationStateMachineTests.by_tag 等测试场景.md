# TagNavigationStateMachineTests.by_tag 等测试场景

标签：#类型/代码

> 文件 `tests/test_ckb_tag_navigation_state_machine.py`负责验证 candidate、confirmed、contested 和 deprecated 四态及原因码。 它属于tag 审计状态机的回归保护，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当投票、撤销、时效或提交漂移规则变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_state_machine.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_state_machine.py:1:1)  `tests/test_ckb_tag_navigation_state_machine.py:1-69`

## 相关代码

- 主要代码单元是 [[TagNavigationStateMachineTests.by_tag]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 7 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `TagNavigationStateMachineTests` | 核对标签四状态、独立投票去重、反对比例、来源漂移与撤回原因，并要求重复审计字节一致。 |
| `TagNavigationStateMachineTests.setUp` | `setUp` 完成tag 状态机测试所需的一个明确步骤。 |
| `TagNavigationStateMachineTests.tearDown` | `tearDown` 完成tag 状态机测试所需的一个明确步骤。 |
| `TagNavigationStateMachineTests.test_all_four_states_and_counts_are_frozen` | 该测试验证“all four states and counts ar…”场景，保护tag 状态机测试的结果与失败边界。 |
| `TagNavigationStateMachineTests.test_single_agent_revote_counts_once` | 该测试验证“single agent revote counts on…”场景，保护tag 状态机测试的结果与失败边界。 |
| `TagNavigationStateMachineTests.test_opposition_ratio_commit_drift_staleness_and_retraction_have_reason_codes` | 该测试验证“opposition ratio commit drift…”场景，保护tag 状态机测试的结果与失败边界。 |
| `TagNavigationStateMachineTests.test_repeated_audit_bytes_are_identical` | 该测试验证“repeated audit bytes are iden…”场景，保护tag 状态机测试的结果与失败边界。 |

</details>
