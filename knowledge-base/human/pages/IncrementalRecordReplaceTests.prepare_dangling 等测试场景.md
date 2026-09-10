# IncrementalRecordReplaceTests.prepare_dangling 等测试场景

标签：#类型/代码

> 验证历史坏链存在时的单篇记录替换、全库维护状态和严格失败保护。 在真实临时知识库中复用受管记录与索引夹具，覆盖逐篇修复、目标与其他笔记错误、候选字节漂移、索引故障及回滚补偿。

## 什么时候需要修改

改变单篇修复诊断边界或事务角色行为时调整对应正反例，测试通过不直接代表稳定知识库已同步。

## 在代码中的位置

[打开源码：tests/test_record_replace_incremental.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_record_replace_incremental.py:1:1)  `tests/test_record_replace_incremental.py:1-126`

## 相关代码

- 主要代码单元是 [[IncrementalRecordReplaceTests.prepare_dangling]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `IncrementalRecordReplaceTests` | 在真实小库中验证逐篇坏链修复、未处理诊断披露和严格失败补偿。 |
| `IncrementalRecordReplaceTests.assert_target_unchanged` | 比较当前目标文件、元数据及索引逻辑状态与测试基线。 |
| `IncrementalRecordReplaceTests.test_two_dangling_notes_can_be_repaired_one_at_a_time_without_claiming_maintenance` | 验证两篇记录依次修复，第一篇后维护仍报错，全部修好后维护通过。 |
| `IncrementalRecordReplaceTests.test_target_retained_or_new_dangling_link_is_rejected_before_writes` | 分别提交保留原坏链和新增坏链的目标正文，断言拒绝且目标角色不变。 |
| `IncrementalRecordReplaceTests.test_other_error_type_and_other_mirror_damage_remain_blocking` | 破坏其他笔记标签或单侧镜像，断言替换仍失败且目标保持基线。 |
| `IncrementalRecordReplaceTests.test_changed_other_candidate_is_not_waived_even_with_same_diagnostic` | 修改其他候选笔记正文或坏链数量，断言即使原诊断相同也拒绝替换。 |
| `IncrementalRecordReplaceTests.test_changed_other_candidate_is_not_waived_even_with_same_diagnostic.changed` | 保留真实候选复制流程，再向另一笔记双镜像追加当前故障反例内容。 |
| `IncrementalRecordReplaceTests.test_target_mirror_and_promotion_failures_remain_strict_with_pending_diagnostics` | 注入目标镜像或索引写入故障，断言存在基线诊断时仍严格失败并恢复。 |
| `IncrementalRecordReplaceTests.test_rollback_does_not_restore_a_dangling_target_and_compensates_exactly` | 验证回滚恢复坏链会被拒绝，且补偿精确保持已修复的目标角色。 |

</details>
