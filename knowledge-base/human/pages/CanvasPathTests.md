# CanvasPathTests

标签：#类型/代码

> `CanvasPathTests` 位于 `tests/test_ckb_canvas_paths.py` 第 31-150 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。 `CanvasPathTests` 负责在对应能力的可执行成功、失败和回归验证中验证目标行为、失败分类和回归边界。

## 什么时候需要修改

当 `tests/test_ckb_canvas_paths.py` 中 `CanvasPathTests` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_ckb_canvas_paths.py 第 31 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_canvas_paths.py:31:1)  `tests/test_ckb_canvas_paths.py:31-150`

## 相关代码

- 实现时会用到 [[build_case]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[commands 的协作边界]]。
- 实现时会用到 [[contracts 的协作边界（2ef5688e）]]。
- 实现时会用到 [[validate]]。

## 谁会来到这里

- [[CanvasContractTests]] 关联到这里的验证场景。
- [[CanvasPathTests 等测试场景]] 汇总了本页。
- [[FactFreshnessStateMachineTest]] 关联到这里的验证场景。
- [[build_case]] 关联到这里的验证场景。
- [[check_fact_freshness]] 关联到这里的验证场景。
- [[commands 的协作边界]] 关联到这里的验证场景。
- [[freeze 的协作边界]] 关联到这里的验证场景。
- [[graph 的协作边界]] 关联到这里的验证场景。
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]] 关联到这里的验证场景。
- [[source_files]] 关联到这里的验证场景。
- [[transaction 的协作边界]] 关联到这里的验证场景。
- [[validate]] 关联到这里的验证场景。
- [[validate 与 canonical 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 6 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `CanvasPathTests.test_chinese_paths_generate_and_reopen` | `test_chinese_paths_generate_and_reo…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasPathTests.test_250_to_259_character_target_is_complete_or_stable_io_failure` | `test_250_to_259_character_target_is…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasPathTests.test_inside_link_is_allowed_and_outside_link_is_rejected` | `test_inside_link_is_allowed_and_out…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasPathTests.test_corrupt_request_and_record_emit_one_failure_object_without_traceback` | `test_corrupt_request_and_record_emi…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasPathTests.test_snapshot_and_evidence_drift_have_distinct_reasons` | `test_snapshot_and_evidence_drift_ha…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasPathTests.test_missing_target_and_existing_target_are_guarded` | `test_missing_target_and_existing_ta…` 用于完成局部输入校验、转换或状态更新。 |

</details>
