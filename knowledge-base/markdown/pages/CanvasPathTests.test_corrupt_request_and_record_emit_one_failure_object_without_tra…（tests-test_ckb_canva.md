# CanvasPathTests.test_corrupt_request_and_record_emit_one_failure_object_without_tra…（tests/test_ckb_canvas_paths.py:1）

标签：#类型/代码

> `tests/test_ckb_canvas_paths.py` 页面绑定固定源码第 1-155 行，说明该文件在对应能力的可执行成功、失败和回归验证中的整体职责。 该文件负责对应能力的可执行成功、失败和回归验证，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `tests/test_ckb_canvas_paths.py` 中 `tests/test_ckb_canvas_paths.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_ckb_canvas_paths.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_canvas_paths.py:1:1)  `tests/test_ckb_canvas_paths.py:1-155`

## 相关代码

- 主要代码单元是 [[CanvasPathTests.test_corrupt_request_and_record_emit_one_failure_object_without_tra…（test_ckb_canvas_paths 测试）]]。

## 谁会来到这里

- 与 [[CanvasPathTests.test_corrupt_request_and_record_emit_one_failure_object_without_tra…（test_ckb_canvas_paths 测试）]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 7 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `run_cli` | `run_cli` 在 `test_ckb_canvas_paths.py` 中用于验证目标行为、失败分类和回归边界。 |
| `CanvasPathTests` | 检验 Canvas 在中文路径、长路径、符号链接和损坏输入下的行为，并区分快照不符、证据漂移及已有目标保护。 |
| `CanvasPathTests.test_chinese_paths_generate_and_reopen` | `test_chinese_paths_generate_and_reo…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasPathTests.test_250_to_259_character_target_is_complete_or_stable_io_failure` | `test_250_to_259_character_target_is…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasPathTests.test_inside_link_is_allowed_and_outside_link_is_rejected` | `test_inside_link_is_allowed_and_out…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasPathTests.test_snapshot_and_evidence_drift_have_distinct_reasons` | `test_snapshot_and_evidence_drift_ha…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasPathTests.test_missing_target_and_existing_target_are_guarded` | `test_missing_target_and_existing_ta…` 用于完成局部输入校验、转换或状态更新。 |

</details>
