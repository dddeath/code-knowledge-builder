# CanvasTransactionTests

标签：#类型/代码

> `CanvasTransactionTests` 位于 `tests/test_ckb_canvas_transaction.py` 第 24-111 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。 `CanvasTransactionTests` 负责在对应能力的可执行成功、失败和回归验证中验证目标行为、失败分类和回归边界。

## 什么时候需要修改

当 `tests/test_ckb_canvas_transaction.py` 中 `CanvasTransactionTests` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_ckb_canvas_transaction.py 第 24 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_canvas_transaction.py:24:1)  `tests/test_ckb_canvas_transaction.py:24-111`

## 相关代码

- 实现时会用到 [[build_case]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[commands 的协作边界]]。
- 实现时会用到 [[contracts 的协作边界（2ef5688e）]]。
- 实现时会用到 [[freeze 的协作边界]]。
- 实现时会用到 [[transaction 的协作边界]]。
- 实现时会用到 [[validate]]。

## 谁会来到这里

- [[CanvasContractTests]] 关联到这里的验证场景。
- [[CanvasTransactionTests 等测试场景]] 汇总了本页。
- [[check_fact_freshness 与 _root 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 7 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `CanvasTransactionTests.test_validate_stages_and_reopens_without_promotion` | `test_validate_stages_and_reopens_wi…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasTransactionTests.test_absent_generate_promotes_three_canonical_complete_roles` | `test_absent_generate_promotes_three…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasTransactionTests.test_promotion_detects_concurrent_canvas_and_preserves_external_bytes` | `test_promotion_detects_concurrent_c…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasTransactionTests.test_promotion_detects_concurrent_canvas_and_preserves_external_bytes.hook` | `hook` 在 `test_ckb_canvas_transaction.py` 中用于验证目标行为、失败分类和回归边界。 |
| `CanvasTransactionTests.test_write_fsync_and_promotion_faults_leave_complete_baseline` | `test_write_fsync_and_promotion_faul…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasTransactionTests.test_write_fsync_and_promotion_faults_leave_complete_baseline.hook` | `hook` 在 `test_ckb_canvas_transaction.py` 中用于验证目标行为、失败分类和回归边界。 |
| `CanvasTransactionTests.test_staged_canvas_corruption_is_rejected_before_target_changes` | `test_staged_canvas_corruption_is_re…` 用于完成局部输入校验、转换或状态更新。 |

</details>
