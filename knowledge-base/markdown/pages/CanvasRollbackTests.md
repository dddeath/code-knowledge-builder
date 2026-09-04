# CanvasRollbackTests

标签：#类型/代码

> `CanvasRollbackTests` 位于 `tests/test_ckb_canvas_rollback.py` 第 18-75 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。 `CanvasRollbackTests` 负责在对应能力的可执行成功、失败和回归验证中验证目标行为、失败分类和回归边界。

## 什么时候需要修改

当 `tests/test_ckb_canvas_rollback.py` 中 `CanvasRollbackTests` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_ckb_canvas_rollback.py 第 18 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_canvas_rollback.py:18:1)  `tests/test_ckb_canvas_rollback.py:18-75`

## 相关代码

- 实现时会用到 [[build_case]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[commands 的协作边界]]。
- 实现时会用到 [[contracts 的协作边界（prototypes）]]。

## 谁会来到这里

- [[CanvasRollbackTests 等测试场景]] 汇总了本页。
- [[FactFreshnessStateMachineTest]] 关联到这里的验证场景。
- [[build_case]] 关联到这里的验证场景。
- [[check_fact_freshness]] 关联到这里的验证场景。
- [[commands 的协作边界]] 关联到这里的验证场景。
- [[freeze 的协作边界]] 关联到这里的验证场景。
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]] 关联到这里的验证场景。
- [[transaction 的协作边界]] 关联到这里的验证场景。
- [[validate]] 关联到这里的验证场景。
- [[validate 与 canonical 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `CanvasRollbackTests.test_absent_rollback_removes_all_three_generated_roles` | `test_absent_rollback_removes_all_th…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasRollbackTests.test_present_rollback_restores_three_roles_byte_identical` | `test_present_rollback_restores_thre…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasRollbackTests.test_rollback_drift_preserves_current_bytes_and_backup` | `test_rollback_drift_preserves_curre…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasRollbackTests.test_wrong_manifest_hash_changes_nothing` | `test_wrong_manifest_hash_changes_no…` 用于完成局部输入校验、转换或状态更新。 |

</details>
