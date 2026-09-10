# TagNavigationRollbackTests.test_present_target_returns_to_byte_identical_baseline 等…

标签：#类型/代码

> 文件 `tests/test_ckb_tag_navigation_rollback.py`负责验证 tag 数据库回滚、漂移保护和恢复失败证据保留。 它属于tag 实验可恢复性的回归保护，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当备份、manifest、原子替换或恢复错误变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_rollback.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_rollback.py:1:1)  `tests/test_ckb_tag_navigation_rollback.py:1-169`

## 相关代码

- 主要代码单元是 [[TagNavigationRollbackTests.test_present_target_returns_to_byte_identical_baseline]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `TagNavigationRollbackTests` | 验证标签数据库从不存在或已有基线回滚的精确恢复，注入恢复故障时保留证据，并阻断外部漂移后的回滚。 |
| `TagNavigationRollbackTests.test_absent_target_returns_to_absent` | 该测试验证“absent target returns to abse…”场景，保护tag 回滚测试的结果与失败边界。 |
| `TagNavigationRollbackTests.test_absent_target_returns_to_absent.fail_manifest_write` | `fail_manifest_write` 完成tag 回滚测试所需的一个明确步骤。 |
| `TagNavigationRollbackTests.test_drift_blocks_rollback_and_preserves_current_bytes` | 该测试验证“drift blocks rollback and pre…”场景，保护tag 回滚测试的结果与失败边界。 |

</details>
