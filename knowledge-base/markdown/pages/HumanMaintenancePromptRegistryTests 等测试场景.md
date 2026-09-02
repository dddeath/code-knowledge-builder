# HumanMaintenancePromptRegistryTests 等测试场景

标签：#类型/代码

> `tests/test_human_maintenance_prompts.py` 页面绑定固定源码第 1-478 行，说明该文件如何承担人类维护 Prompt 注册、渲染和交付边界测试。 该文件负责人类维护 Prompt 注册、渲染和交付边界测试，并为相关命令、页面生成或测试提供源码入口。

## 什么时候需要修改

当 `tests/test_human_maintenance_prompts.py` 的公开输入、生成结果、状态边界或与其他模块的协作关系变化时，应更新本页。

## 在代码中的位置

[打开源码：tests/test_human_maintenance_prompts.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_human_maintenance_prompts.py:1:1)  `tests/test_human_maintenance_prompts.py:1-478`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 主要代码单元是 [[HumanMaintenancePromptRegistryTests]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[validate]]。
- 实现时会用到 [[validate_human_maintenance_invocation]]。
- 实现时会用到 [[validate_human_maintenance_invocation 与 ParameterSpec 的协作实现]]。

## 谁会来到这里

- [[audit_operation_journal 与 _root 的协作实现]] 关联到这里的验证场景。
- [[finalize 与 _replace_output_prefix 的协作实现]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。
- [[validate_human_maintenance_invocation]] 关联到这里的验证场景。
- [[validate_human_maintenance_invocation 与 ParameterSpec 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 29 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_fixture` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `_valid_maintain_summary` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `_template_review_parameters` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `_valid_template_audit_summary` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptValidationTests` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptValidationTests.test_validate_rejects_unknown_duplicate_and_missing_confirmation` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptValidationTests.test_validate_rejects_install_build_mixing_and_conflicting_scope` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptValidationTests.test_validate_rejects_accepted_feedback_without_applied_record` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptValidationTests.test_template_audit_and_rollback_require_explicit_human_review_fields` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptValidationTests.test_page_package_requires_confirmation_and_forbids_managed_projection_targets` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptValidationTests.test_page_init_rejects_old_contract_instead_of_silently_using_v3_headings` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptRenderTests` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptRenderTests.test_same_input_produces_identical_prompt_bytes` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptRenderTests.test_install_and_build_prompts_keep_responsibilities_separate` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptRenderTests.test_render_uses_only_active_operation_steps` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptRenderTests.test_invalid_render_raises_one_input_error` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptFixtureTests` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptFixtureTests.test_every_action_has_minimal_full_invalid_prompt_and_invalid_summary_fixtures` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptFixtureTests.test_readme_v4_install_and_explain_fixtures_keep_accepted_responsibility_split` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptFixtureTests.test_readme_v5_fixture_contains_only_agent_direction_and_direct_human_results` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenanceDeliveryAuditTests` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenanceDeliveryAuditTests.test_complete_summary_with_exact_command_inputs_output_and_exit_status_passes` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenanceDeliveryAuditTests.test_command_start_or_placeholder_is_not_completion` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenanceDeliveryAuditTests.test_summary_must_return_the_same_action_and_registry_hash` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenanceDeliveryAuditTests.test_template_approve_audit_requires_human_evidence_and_ready_rollback` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptCliTests` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptCliTests.run_cli` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptCliTests.test_list_show_render_and_validate_have_one_utf8_stdout_document` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |
| `HumanMaintenancePromptCliTests.test_audit_exit_status_is_zero_only_for_verified_completion` | 该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。 |

</details>
