# HumanMaintenancePromptRegistryTests 等测试场景

标签：#类型/代码

> `tests/test_human_maintenance_prompts.py` 页面绑定固定源码第 1-423 行，说明该文件在稳定维护 Prompt 的 action 映射、渲染和交付审计中的整体职责。 该文件负责稳定维护 Prompt 的 action 映射、渲染和交付审计，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `tests/test_human_maintenance_prompts.py` 中 `tests/test_human_maintenance_prompts.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_human_maintenance_prompts.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_human_maintenance_prompts.py:1:1)  `tests/test_human_maintenance_prompts.py:1-423`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 主要代码单元是 [[HumanMaintenancePromptRegistryTests]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[render_human_maintenance_prompt]]。
- 实现时会用到 [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]]。
- 实现时会用到 [[rollback]]。
- 实现时会用到 [[validate]]。

## 谁会来到这里

- [[audit_global 与 _replace_output_prefix 的协作实现]] 关联到这里的验证场景。
- [[audit_operation_journal 与 _root 的协作实现]] 关联到这里的验证场景。
- [[render_human_maintenance_prompt]] 关联到这里的验证场景。
- [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 27 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_fixture` | `_fixture` 在 `test_human_maintenance_prompts.py` 中用于验证目标行为、失败分类和回归边界。 |
| `_valid_maintain_summary` | `_valid_maintain_summary` 用于完成局部输入校验、转换或状态更新。 |
| `_template_review_parameters` | `_template_review_parameters` 用于完成局部输入校验、转换或状态更新。 |
| `_valid_template_audit_summary` | `_valid_template_audit_summary` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptValidationTests` | `HumanMaintenancePromptValidationTes…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptValidationTests.test_validate_rejects_unknown_duplicate_and_missing_confirmation` | `test_validate_rejects_unknown_dupli…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptValidationTests.test_validate_rejects_install_build_mixing_and_conflicting_scope` | `test_validate_rejects_install_build…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptValidationTests.test_validate_rejects_accepted_feedback_without_applied_record` | `test_validate_rejects_accepted_feed…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptValidationTests.test_template_audit_and_rollback_require_explicit_human_review_fields` | `test_template_audit_and_rollback_re…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptValidationTests.test_page_package_requires_confirmation_and_forbids_managed_projection_targets` | `test_page_package_requires_confirma…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptRenderTests` | `HumanMaintenancePromptRenderTests` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptRenderTests.test_same_input_produces_identical_prompt_bytes` | `test_same_input_produces_identical_…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptRenderTests.test_install_and_build_prompts_keep_responsibilities_separate` | `test_install_and_build_prompts_keep…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptRenderTests.test_render_uses_only_active_operation_steps` | `test_render_uses_only_active_operat…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptRenderTests.test_invalid_render_raises_one_input_error` | `test_invalid_render_raises_one_inpu…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptFixtureTests` | `HumanMaintenancePromptFixtureTests` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptFixtureTests.test_every_action_has_minimal_full_invalid_prompt_and_invalid_summary_fixtures` | `test_every_action_has_minimal_full_…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptFixtureTests.test_readme_v4_install_and_explain_fixtures_keep_accepted_responsibility_split` | `test_readme_v4_install_and_explain_…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenanceDeliveryAuditTests` | `HumanMaintenanceDeliveryAuditTests` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenanceDeliveryAuditTests.test_complete_summary_with_exact_command_inputs_output_and_exit_status_passes` | `test_complete_summary_with_exact_co…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenanceDeliveryAuditTests.test_command_start_or_placeholder_is_not_completion` | `该测试用例` 在 `test_human_maintenance_prompts.py` 中用于验证目标行为、失败分类和回归边界。 |
| `HumanMaintenanceDeliveryAuditTests.test_summary_must_return_the_same_action_and_registry_hash` | `test_summary_must_return_the_same_a…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenanceDeliveryAuditTests.test_template_approve_audit_requires_human_evidence_and_ready_rollback` | `test_template_approve_audit_require…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptCliTests` | `HumanMaintenancePromptCliTests` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptCliTests.run_cli` | `run_cli` 在 `test_human_maintenance_prompts.py` 中用于验证目标行为、失败分类和回归边界。 |
| `HumanMaintenancePromptCliTests.test_list_show_render_and_validate_have_one_utf8_stdout_document` | `test_list_show_render_and_validate_…` 用于完成局部输入校验、转换或状态更新。 |
| `HumanMaintenancePromptCliTests.test_audit_exit_status_is_zero_only_for_verified_completion` | `test_audit_exit_status_is_zero_only…` 用于完成局部输入校验、转换或状态更新。 |

</details>
