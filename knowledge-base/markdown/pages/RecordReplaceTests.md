# RecordReplaceTests

标签：#类型/代码

> `RecordReplaceTests` 位于 `tests/test_record_replace.py` 第 69-372 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。 `RecordReplaceTests` 负责在工作记录正文替换、候选验证、原子 promotion 和回滚中验证目标行为、失败分类和回归边界。

## 什么时候需要修改

当 `tests/test_record_replace.py` 中 `RecordReplaceTests` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_record_replace.py 第 69 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_record_replace.py:69:1)  `tests/test_record_replace.py:69-372`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CodeKnowledgeBuilderTests 等测试场景]]。
- 实现时会用到 [[RecordReplaceTests 等测试场景]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[finalize]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[replace_note]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests 等测试场景]] 关联到这里的验证场景。
- [[RecordReplaceTests 等测试场景]] 汇总了本页。
- [[audit_obsidian]] 关联到这里的验证场景。
- [[audit_obsidian 与 prepare_vault 的协作实现]] 关联到这里的验证场景。
- [[audit_operation_journal 与 _root 的协作实现]] 关联到这里的验证场景。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 关联到这里的验证场景。
- [[module_name]] 关联到这里的验证场景。
- [[record_note]] 关联到这里的验证场景。
- [[replace_note]] 关联到这里的验证场景。
- [[replace_note 与 RecordReplaceLockError 的协作实现]] 关联到这里的验证场景。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 12 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `RecordReplaceTests.setUpClass` | `setUpClass` 在 `test_record_replace.py` 中用于验证目标行为、失败分类和回归边界。 |
| `RecordReplaceTests.tearDownClass` | `tearDownClass` 在 `test_record_replace.py` 中用于验证目标行为、失败分类和回归边界。 |
| `RecordReplaceTests.setUp` | `setUp` 在 `test_record_replace.py` 中用于验证目标行为、失败分类和回归边界。 |
| `RecordReplaceTests.tearDown` | `tearDown` 在 `test_record_replace.py` 中用于验证目标行为、失败分类和回归边界。 |
| `RecordReplaceTests._replace` | `_replace` 在 `test_record_replace.py` 中用于验证目标行为、失败分类和回归边界。 |
| `RecordReplaceTests.test_replace_updates_every_role_and_rollback_is_exact_and_idempotent` | `test_replace_updates_every_role_and…` 用于完成局部输入校验、转换或状态更新。 |
| `RecordReplaceTests.test_exact_target_kind_and_cli_mode_failures_do_not_change_owned_roles` | `test_exact_target_kind_and_cli_mode…` 用于完成局部输入校验、转换或状态更新。 |
| `RecordReplaceTests.test_body_and_explicit_evidence_validation_failures_are_stable` | `test_body_and_explicit_evidence_val…` 用于完成局部输入校验、转换或状态更新。 |
| `RecordReplaceTests.test_promotion_failure_restores_all_roles_and_leaves_no_sqlite_sidecars` | `test_promotion_failure_restores_all…` 用于完成局部输入校验、转换或状态更新。 |
| `RecordReplaceTests.test_candidate_mirror_mismatch_blocks_promotion` | `test_candidate_mirror_mismatch_bloc…` 用于完成局部输入校验、转换或状态更新。 |
| `RecordReplaceTests.test_rollback_detects_external_drift` | `test_rollback_detects_external_drift` 用于完成局部输入校验、转换或状态更新。 |
| `RecordReplaceTests.test_explicit_evidence_replaces_old_links_and_create_append_remain_compatible` | `test_explicit_evidence_replaces_old…` 用于完成局部输入校验、转换或状态更新。 |

</details>
