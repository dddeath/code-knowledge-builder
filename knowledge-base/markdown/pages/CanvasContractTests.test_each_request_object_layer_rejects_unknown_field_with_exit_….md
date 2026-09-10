# CanvasContractTests.test_each_request_object_layer_rejects_unknown_field_with_exit_…

标签：#类型/代码

> `tests/test_ckb_canvas_contracts.py` 页面绑定固定源码第 1-151 行，说明该文件在对应能力的可执行成功、失败和回归验证中的整体职责。 该文件负责对应能力的可执行成功、失败和回归验证，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `tests/test_ckb_canvas_contracts.py` 中 `tests/test_ckb_canvas_contracts.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_ckb_canvas_contracts.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_canvas_contracts.py:1:1)  `tests/test_ckb_canvas_contracts.py:1-151`

## 相关代码

- 主要代码单元是 [[CanvasContractTests.test_each_request_object_layer_rejects_unknown_field_with_exit_2]]。

## 谁会来到这里

- 与 [[CanvasContractTests.test_each_request_object_layer_rejects_unknown_field_with_exit_2]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `setUpModule` | `setUpModule` 在 `test_ckb_canvas_contracts.py` 中用于验证目标行为、失败分类和回归边界。 |
| `run_cli` | `run_cli` 在 `test_ckb_canvas_contracts.py` 中用于验证目标行为、失败分类和回归边界。 |
| `CanvasContractTests` | 验证 Canvas 请求和结果模式、未知字段拒绝、检索记录限制及阅读包精确回链，并检查标准验收请求结构。 |
| `CanvasContractTests.test_all_nine_schemas_parse_and_match_design` | `test_all_nine_schemas_parse_and_mat…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasContractTests.test_design_success_and_failure_fixtures_validate` | `test_design_success_and_failure_fix…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasContractTests._assert_record_rejected` | `_assert_record_rejected` 在 `test_ckb_canvas_contracts.py` 中用于验证目标行为、失败分类和回归边界。 |
| `CanvasContractTests.test_record_1_keyword_variant_and_unknown_candidate_rejected` | `test_record_1_keyword_variant_and_u…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasContractTests.test_pack_record_crosslink_is_exact` | `test_pack_record_crosslink_is_exact` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasContractTests.test_acceptance_runtime_request_is_valid` | `test_acceptance_runtime_request_is_…` 用于完成局部输入校验、转换或状态更新。 |

</details>
