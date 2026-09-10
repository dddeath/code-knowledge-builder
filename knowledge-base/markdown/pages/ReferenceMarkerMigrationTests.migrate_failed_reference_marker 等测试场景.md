# ReferenceMarkerMigrationTests.migrate_failed_reference_marker 等测试场景

标签：#类型/代码

> 验证参考状态标记在迁移保留层中的历史基线与当前生命周期边界。 用真实参考资料审阅和原文漂移产生状态转换，覆盖旧计划兼容、再次终结、基线篡改及原文和其他文件缺失，并保留当前参考失败的完成门。

## 什么时候需要修改

修改精确状态标记集合、旧计划兼容或保留层缺失规则时调整对应测试。

## 在代码中的位置

[打开源码：tests/test_reference_marker_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_reference_marker_migration.py:1:1)  `tests/test_reference_marker_migration.py:1-141`

## 相关代码

- 主要代码单元是 [[ReferenceMarkerMigrationTests.migrate_failed_reference_marker]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 6 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ReferenceMarkerMigrationTests` | 验证参考状态标记的历史基线与真实状态转换，覆盖旧计划及资料缺失保护。 |
| `ReferenceMarkerMigrationTests.test_successful_reference_rebuild_retires_failed_marker_but_keeps_baseline_and_legacy_plan` | 验证重建清除失败标记且基线不变，旧计划仍可审计，基线篡改或缺失则失败。 |
| `ReferenceMarkerMigrationTests.test_missing_raw_manifest_review_and_non_marker_paths_still_block` | 逐项删除原文、清单、审阅与非标记文件，断言迁移仍报告真实文件缺失。 |
| `ReferenceMarkerMigrationTests.test_current_reference_failures_are_not_hidden_by_marker_retirement` | 再次制造原文漂移，断言参考审计与完成入口仍阻止错误资料。 |
| `ReferenceMarkerMigrationTests.test_complete_and_pending_markers_follow_real_reference_state_transitions` | 通过实际资料导入和审阅切换完成与待审标记，验证旧标记消失不冻结迁移。 |
| `ReferenceMarkerMigrationTests.test_complete_and_pending_markers_follow_real_reference_state_transitions.capture` | 为真实生成的当前状态标记保存基线，并追加旧分类的迁移记录用于兼容测试。 |

</details>
