# assertions 等测试场景

标签：#类型/代码

> 文件 `tests/test_ckb_tag_navigation_contracts.py`负责验证 tag assertion、策略、幂等写入和路径失败边界。 它属于tag 实验输入与事务合同的回归保护，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当Schema、路径、隐私或事务规则变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_contracts.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_contracts.py:1:1)  `tests/test_ckb_tag_navigation_contracts.py:1-212`

## 相关代码

- 主要代码单元是 [[assertions]]。
- 实现时会用到 [[contracts 的协作边界（743c915d）]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[sample 等测试场景]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `TagNavigationContractTests` | 该测试验证“five schemas are strict json …”场景，保护tag 合同测试的结果与失败边界。 |
| `TagNavigationContractTests.test_five_schemas_are_strict_json_objects` | 该测试验证“five schemas are strict json …”场景，保护tag 合同测试的结果与失败边界。 |
| `TagNavigationContractTests.test_assertion_schema_excludes_conversation_and_secret_fields` | 该测试验证“assertion schema excludes con…”场景，保护tag 合同测试的结果与失败边界。 |
| `TagNavigationContractTests.test_paths_tags_and_policy_are_bounded` | 该测试验证“paths tags and policy are bou…”场景，保护tag 合同测试的结果与失败边界。 |
| `TagNavigationContractTests.test_replay_deduplicates_identical_idempotency_key` | 该测试验证“replay deduplicates identical…”场景，保护tag 合同测试的结果与失败边界。 |
| `TagNavigationContractTests.test_idempotency_conflict_rolls_back_entire_new_database` | 该测试验证“idempotency conflict rolls ba…”场景，保护tag 合同测试的结果与失败边界。 |
| `TagNavigationContractTests.test_cli_rejects_output_outside_workspace` | 该测试验证“cli rejects output outside wo…”场景，保护tag 合同测试的结果与失败边界。 |
| `TagNavigationContractTests.test_cli_rejects_output_outside_workspace.digest` | `digest` 完成tag 合同测试所需的一个明确步骤。 |
| `TagNavigationContractTests.test_cli_rejects_output_outside_workspace.run_rollback` | `run_rollback` 完成tag 合同测试所需的一个明确步骤。 |

</details>
