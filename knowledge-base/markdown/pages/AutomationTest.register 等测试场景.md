# AutomationTest.register 等测试场景

标签：#类型/代码

> 文件 `tests/test_automation.py`负责验证多 Harness 事件归一化、会话激活、并发采集和受控投影。 它属于会话自动化生命周期的回归保护，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当自动化事件、会话状态、并发行为或人类投影规则变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：tests/test_automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:1:1)  `tests/test_automation.py:1-1001`

## 相关代码

- 主要代码单元是 [[AutomationTest.register]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 30 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `git` | `git` 完成会话自动化回归验证中的一个明确步骤。 |
| `AutomationTest` | `setUp` 完成会话自动化回归验证中的一个明确步骤。 |
| `AutomationTest.setUp` | `setUp` 完成会话自动化回归验证中的一个明确步骤。 |
| `AutomationTest.tearDown` | `tearDown` 完成会话自动化回归验证中的一个明确步骤。 |
| `AutomationTest.event` | `event` 完成会话自动化回归验证中的一个明确步骤。 |
| `AutomationTest.test_event_path_text_maps_wsl_mounts_for_windows_runtime` | 该测试验证“event path text maps wsl moun…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_windows_runtime_matches_wsl_cwd_to_registered_workspace` | 该测试验证“windows runtime matches wsl c…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_project_opt_in_and_hook_output` | 该测试验证“project opt in and hook output”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_registered_session_stays_idle_until_skill_is_explicitly_applied` | 该测试验证“registered session stays idle…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_agent_activation_command_uses_harness_session_and_workspace` | 该测试验证“agent activation command uses…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_skill_start_and_successful_git_commit_event_refresh_fact_state` | 该测试验证“skill start and successful gi…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_redaction_idempotency_change_capture_and_pending_review` | 该测试验证“redaction idempotency change …”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_claude_without_turn_ids_allows_repeated_prompt_after_completion` | 该测试验证“claude without turn ids allow…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_stop_detects_further_change_to_file_dirty_at_session_start` | 该测试验证“stop detects further change t…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_nested_untracked_project_bounds_git_status_and_uses_project_relative_paths` | 该测试验证“nested untracked project boun…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_workspace_root_maps_parent_task_to_nested_repository` | 该测试验证“workspace root maps parent ta…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_version_one_registry_is_read_compatibly` | 该测试验证“version one registry is read …”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_version_two_registry_upgrades_to_session_activation_contract` | 该测试验证“version two registry upgrades…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_opencode_and_generic_normalization` | 该测试验证“opencode and generic normaliz…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_gemini_copilot_and_cursor_normalization` | 该测试验证“gemini copilot and cursor nor…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_concurrent_hooks_are_serialized_without_event_loss` | 该测试验证“concurrent hooks are serializ…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_failed_spool_is_retained_and_retryable` | 该测试验证“failed spool is retained and …”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest._prepare_human_projection` | `_prepare_human_projection` 创建并初始化会话自动化回归验证所需的数据或状态。 |
| `AutomationTest.test_agent_review_promotes_one_chinese_human_note` | 该测试验证“agent review promotes one chi…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_render_all_harness_integrations` | 该测试验证“render all harness integratio…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_harness_retrieval_contract_separates_instruction_skill_activation_and_output_sources` | 该测试验证当前场景的实际结果、来源约束和失败边界。 |
| `AutomationTest.test_codex_windows_python_uses_wsl_launch_path_for_posix_command` | 该测试验证“codex windows python uses wsl…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_codex_windows_bridge_uses_cmd_and_forward_slash_launcher_path` | 该测试验证“codex windows bridge uses cmd…”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_automation_fts_finds_pending_machine_record` | 该测试验证“automation fts finds pending …”场景，保护会话自动化回归验证的预期结果与失败边界。 |
| `AutomationTest.test_machine_retrieval_and_changes_include_pending_automation` | 该测试验证“machine retrieval and changes…”场景，保护会话自动化回归验证的预期结果与失败边界。 |

</details>
