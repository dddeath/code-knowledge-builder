# AutomationTest.register 等测试场景

标签：#类型/代码

> `tests/test_automation.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责以可执行样例验证 `test_automation.py` 覆盖的成功行为、失败边界和回归约束。

## 什么时候需要修改

当 `tests/test_automation.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:1:1)  `tests/test_automation.py:1-890`

## 相关代码

- 主要代码单元是 [[AutomationTest.register]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[doctor_report 与 _version_matches 的协作实现]]。
- 实现时会用到 [[ingest_event]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[render_integration 与 _looks_windows 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.register]] 关联到这里的验证场景。
- [[CkbError]] 关联到这里的验证场景。
- [[CkbError 与 DependencyError 的协作实现]] 关联到这里的验证场景。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 关联到这里的验证场景。
- [[SourceLinkRenderer.uri]] 关联到这里的验证场景。
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]] 关联到这里的验证场景。
- [[_Transport.close]] 关联到这里的验证场景。
- [[_Transport.close 与 _StartGate 的协作实现]] 关联到这里的验证场景。
- [[append]] 关联到这里的验证场景。
- [[audit_feedback 与 _contains_chinese 的协作实现]] 关联到这里的验证场景。
- [[audit_gap_register 与 _root 的协作实现]] 关联到这里的验证场景。
- [[audit_global]] 关联到这里的验证场景。
- [[audit_global 与 _replace_output_prefix 的协作实现]] 关联到这里的验证场景。
- [[audit_migration]] 关联到这里的验证场景。
- [[audit_operation_journal 与 _root 的协作实现]] 关联到这里的验证场景。
- [[audit_references 与 _root 的协作实现]] 关联到这里的验证场景。
- [[audit_work_record_index]] 关联到这里的验证场景。
- [[audit_work_record_index 与 _contains_chinese 的协作实现]] 关联到这里的验证场景。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 关联到这里的验证场景。
- [[build_case 等测试场景]] 关联到这里的验证场景。
- [[ckb_canvas 的协作边界]] 关联到这里的验证场景。
- [[command]] 关联到这里的验证场景。
- [[contracts 的协作边界]] 关联到这里的验证场景。
- [[doctor_report 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[emit]] 关联到这里的验证场景。
- [[execute]] 关联到这里的验证场景。
- [[graph 的协作边界]] 关联到这里的验证场景。
- [[ingest_event]] 关联到这里的验证场景。
- [[ingest_event 与 default_registry_path 的协作实现]] 关联到这里的验证场景。
- [[module_name 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[record_note]] 关联到这里的验证场景。
- [[record_note 与 page_tag 的协作实现]] 关联到这里的验证场景。
- [[render_integration]] 关联到这里的验证场景。
- [[render_integration 与 _looks_windows 的协作实现]] 关联到这里的验证场景。
- [[retrieve]] 关联到这里的验证场景。
- [[retrieve 与 _tokens 的协作实现]] 关联到这里的验证场景。
- [[retrieve_machine]] 关联到这里的验证场景。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[rollback]] 关联到这里的验证场景。
- [[rollback 与 RenderedBundle 的协作实现]] 关联到这里的验证场景。
- [[run_keyword_provider]] 关联到这里的验证场景。
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]] 关联到这里的验证场景。
- [[search_terms]] 关联到这里的验证场景。
- [[search_terms 与 _split_camel 的协作实现]] 关联到这里的验证场景。
- [[start_scope_extension 与 _error 的协作实现]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。
- [[transaction 的协作边界]] 关联到这里的验证场景。
- [[validate]] 关联到这里的验证场景。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 28 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `git` | `git` 是第 42-45 行的函数，供所属页面定位实现。 |
| `AutomationTest` | `AutomationTest` 是第 48-885 行的类，供所属页面定位实现。 |
| `AutomationTest.setUp` | `AutomationTest.setUp` 是第 49-73 行的函数，供所属页面定位实现。 |
| `AutomationTest.tearDown` | `AutomationTest.tearDown` 是第 75-76 行的函数，供所属页面定位实现。 |
| `AutomationTest.event` | `AutomationTest.event` 是第 82-92 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_event_path_text_maps_wsl_mounts_for_windows_runtime` | `AutomationTest.test_e...` 是第 94-104 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_windows_runtime_matches_wsl_cwd_to_registered_workspace` | `AutomationTest.test_w...` 是第 107-117 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_project_opt_in_and_hook_output` | `AutomationTest.test_p...` 是第 119-127 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_registered_session_stays_idle_until_skill_is_explicitly_applied` | `AutomationTest.test_r...` 是第 129-178 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_agent_activation_command_uses_harness_session_and_workspace` | `AutomationTest.test_a...` 是第 180-197 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_redaction_idempotency_change_capture_and_pending_review` | `AutomationTest.test_r...` 是第 199-258 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_claude_without_turn_ids_allows_repeated_prompt_after_completion` | `AutomationTest.test_c...` 是第 260-270 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_stop_detects_further_change_to_file_dirty_at_session_start` | `AutomationTest.test_s...` 是第 272-289 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_nested_untracked_project_bounds_git_status_and_uses_project_relative_paths` | `AutomationTest.test_n...` 是第 291-354 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_workspace_root_maps_parent_task_to_nested_repository` | `AutomationTest.test_w...` 是第 356-422 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_version_one_registry_is_read_compatibly` | `AutomationTest.test_v...` 是第 424-449 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_version_two_registry_upgrades_to_session_activation_contract` | `AutomationTest.test_v...` 是第 451-490 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_opencode_and_generic_normalization` | `AutomationTest.test_o...` 是第 492-538 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_gemini_copilot_and_cursor_normalization` | `AutomationTest.test_g...` 是第 540-569 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_concurrent_hooks_are_serialized_without_event_loss` | `AutomationTest.test_c...` 是第 571-597 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_failed_spool_is_retained_and_retryable` | `AutomationTest.test_f...` 是第 599-607 行的函数，供所属页面定位实现。 |
| `AutomationTest._prepare_human_projection` | `AutomationTest._prepa...` 是第 609-630 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_agent_review_promotes_one_chinese_human_note` | `AutomationTest.test_a...` 是第 632-737 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_render_all_harness_integrations` | `AutomationTest.test_r...` 是第 739-797 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_codex_windows_python_uses_wsl_launch_path_for_posix_command` | `AutomationTest.test_c...` 是第 799-824 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_codex_windows_bridge_uses_cmd_and_forward_slash_launcher_path` | `AutomationTest.test_c...` 是第 826-833 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_automation_fts_finds_pending_machine_record` | `AutomationTest.test_a...` 是第 835-849 行的函数，供所属页面定位实现。 |
| `AutomationTest.test_machine_retrieval_and_changes_include_pending_automation` | `AutomationTest.test_m...` 是第 851-885 行的函数，供所属页面定位实现。 |

</details>
