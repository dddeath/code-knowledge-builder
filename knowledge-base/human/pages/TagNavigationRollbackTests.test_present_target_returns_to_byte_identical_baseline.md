# TagNavigationRollbackTests.test_present_target_returns_to_byte_identical_baseline

标签：#类型/代码

> 该测试验证已有标签数据库回放后可恢复到逐字节相同的基线，并注入清单写入、恢复复制和恢复哈希故障。 它要求正常失败恢复清理残留，而恢复本身失败时保留数据库、备份和清单现场并返回明确的恢复失败，避免把未恢复状态误报成功。

## 什么时候需要修改

回放事务、回滚备份或恢复失败补偿规则变化时修改此测试，并分别核对成功恢复和保留现场两类行为。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_rollback.py 第 46 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_rollback.py:46:1)  `tests/test_ckb_tag_navigation_rollback.py:46-152`

## 谁会来到这里

- [[TagNavigationRollbackTests.test_present_target_returns_to_byte_identical_baseline 等…]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 5 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `TagNavigationRollbackTests.test_present_target_returns_to_byte_identical_baseline.fail_manifest_write` | `fail_manifest_write` 完成tag 回滚测试所需的一个明确步骤。 |
| `TagNavigationRollbackTests.test_present_target_returns_to_byte_identical_baseline.fail_manifest_before_restore_copy` | `fail_manifest_before_restore_copy` 完成tag 回滚测试所需的一个明确步骤。 |
| `TagNavigationRollbackTests.test_present_target_returns_to_byte_identical_baseline.fail_restore_copy` | `fail_restore_copy` 完成tag 回滚测试所需的一个明确步骤。 |
| `TagNavigationRollbackTests.test_present_target_returns_to_byte_identical_baseline.fail_manifest_before_restore_hash` | `fail_manifest_before_restore_hash` 完成tag 回滚测试所需的一个明确步骤。 |
| `TagNavigationRollbackTests.test_present_target_returns_to_byte_identical_baseline.fail_restore_hash` | `fail_restore_hash` 完成tag 回滚测试所需的一个明确步骤。 |

</details>
