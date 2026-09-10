# CanvasBenchmarkContractTests.test_judge_owns_page_source_and_range_verdict 等测试场景

标签：#类型/代码

> `tests/test_ckb_canvas_benchmark_contract.py` 页面绑定固定源码第 1-209 行，说明该文件在对应能力的可执行成功、失败和回归验证中的整体职责。 该文件负责对应能力的可执行成功、失败和回归验证，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `tests/test_ckb_canvas_benchmark_contract.py` 中 `tests/test_ckb_canvas_benchmark_contract.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_ckb_canvas_benchmark_contract.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_canvas_benchmark_contract.py:1:1)  `tests/test_ckb_canvas_benchmark_contract.py:1-209`

## 相关代码

- 主要代码单元是 [[CanvasBenchmarkContractTests.test_judge_owns_page_source_and_range_verdict]]。

## 谁会来到这里

- 与 [[CanvasBenchmarkContractTests.test_judge_owns_page_source_and_range_verdict]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 8 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_capture` | `_capture` 在 `test_ckb_canvas_benchmark_contract.py` 中用于验证目标行为、失败分类和回归边界。 |
| `CanvasBenchmarkContractTests` | 验证 Canvas 冻结任务分配、证据一致性、未冻结环境停机及独立会话汇总门，构造测量仅作为合同测试。 |
| `CanvasBenchmarkContractTests.test_frozen_run_has_12_tasks_four_assignments_and_equal_evidence` | `test_frozen_run_has_12_tasks_four_a…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasBenchmarkContractTests.test_design_session_and_summary_examples_are_schema_valid_only` | `test_design_session_and_summary_exa…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasBenchmarkContractTests.test_unfilled_obsidian_version_stops_session` | `test_unfilled_obsidian_version_stop…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasBenchmarkContractTests.test_summary_passes_only_with_four_independent_sessions_and_all_seven_gates` | `test_summary_passes_only_with_four_…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasBenchmarkContractTests.test_runner_rejects_evidence_drift` | `test_runner_rejects_evidence_drift` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasBenchmarkContractTests.test_benchmark_cli_stdout_is_one_schema_object` | `test_benchmark_cli_stdout_is_one_sc…` 用于完成局部输入校验、转换或状态更新。 |

</details>
