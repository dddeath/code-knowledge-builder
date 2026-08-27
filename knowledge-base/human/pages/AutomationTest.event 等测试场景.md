# AutomationTest.event 等测试场景

标签：#类型/代码

> 该测试页覆盖项目登记、session Skill 激活、跨 Harness 规范化、并发、脱敏、路径过滤、待审阅与人类晋升。 它同时验证普通提及保持零写入、显式应用开启记录、其他 session 隔离、CLI 激活幂等以及 schema 1/2 升级。

## 什么时候需要修改

当自动化 Schema、激活协议、适配器事件或审计门变化时，需要同步扩展该测试。

## 在代码中的位置

[打开源码：tests/test_automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:1:1)  `tests/test_automation.py:1-801`

## 相关代码

- 主要代码单元是 [[AutomationTest.event]]。
- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[LspClient.start 与 _version_matches 的协作实现]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[ingest_event]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[AutomationTest.event]] 关联到这里的验证场景。
- [[LspClient.start]] 关联到这里的验证场景。
- [[LspClient.start 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]] 关联到这里的验证场景。
- [[audit_migration]] 关联到这里的验证场景。
- [[audit_migration 与 _entity_key 的协作实现]] 关联到这里的验证场景。
- [[create_source_snapshot]] 关联到这里的验证场景。
- [[create_source_snapshot 与 git 的协作实现]] 关联到这里的验证场景。
- [[ensure_local_openers]] 关联到这里的验证场景。
- [[ensure_local_openers 与 default_openers 的协作实现]] 关联到这里的验证场景。
- [[execute]] 关联到这里的验证场景。
- [[ingest_event]] 关联到这里的验证场景。
- [[ingest_event 与 default_registry_path 的协作实现]] 关联到这里的验证场景。
- [[load_page_config]] 关联到这里的验证场景。
- [[load_page_config 与 _merge_known 的协作实现]] 关联到这里的验证场景。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[module_name 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[parse_file]] 关联到这里的验证场景。
- [[parse_file 与 _language 的协作实现]] 关联到这里的验证场景。
- [[parser]] 会使用这里提供的行为。
- [[query_graph 与 _networkx_modules 的协作实现]] 关联到这里的验证场景。
- [[record_note]] 关联到这里的验证场景。
- [[record_note 与 page_tag 的协作实现]] 关联到这里的验证场景。
- [[render_integration]] 关联到这里的验证场景。
- [[render_integration 与 _looks_windows 的协作实现]] 关联到这里的验证场景。
- [[retrieve]] 关联到这里的验证场景。
- [[retrieve 与 _tokens 的协作实现]] 关联到这里的验证场景。
- [[retrieve_machine]] 关联到这里的验证场景。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[run]] 关联到这里的验证场景。
- [[run 与 CkbError 的协作实现]] 关联到这里的验证场景。
- [[status]] 关联到这里的验证场景。
- [[status 与 _load_state 的协作实现]] 关联到这里的验证场景。
- [[sync_human_layer]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。

## 相关测试

- [[MigrationTest]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 24 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `git` | 执行测试仓库 Git 命令并在失败时保留 stderr。 |
| `AutomationTest` | `AutomationTest` 汇集同一功能域的测试夹具、执行步骤和验收断言。 |
| `AutomationTest.setUp` | 建立带 Git 源码、知识输出和注册表的自动化测试夹具。 |
| `AutomationTest.tearDown` | 释放自动化测试创建的临时目录。 |
| `AutomationTest.register` | `AutomationTest.register` 根据固定源码完成所属自动化或测试流程中的局部处理。 |
| `AutomationTest.test_project_opt_in_and_hook_output` | 该测试验证对应功能的状态转换、输出和失败门符合固定契约。 |
| `AutomationTest.test_registered_session_stays_idle_until_skill_is_explicitly_applied` | 验证已登记 session 在普通提及时零写入，并在精确调用后只激活当前 session。 |
| `AutomationTest.test_agent_activation_command_uses_harness_session_and_workspace` | 验证 Agent 激活命令按 Harness session 与工作区匹配项目，且重复激活保持幂等。 |
| `AutomationTest.test_redaction_idempotency_change_capture_and_pending_review` | 该测试验证敏感字段脱敏、幂等写入和待审阅生成符合固定契约。 |
| `AutomationTest.test_claude_without_turn_ids_allows_repeated_prompt_after_completion` | 该测试验证对应功能的状态转换、输出和失败门符合固定契约。 |
| `AutomationTest.test_stop_detects_further_change_to_file_dirty_at_session_start` | 该测试验证对应功能的状态转换、输出和失败门符合固定契约。 |
| `AutomationTest.test_nested_untracked_project_bounds_git_status_and_uses_project_relative_paths` | 该测试验证Git 来源、初始化选择和工作树漂移门符合固定契约。 |
| `AutomationTest.test_workspace_root_maps_parent_task_to_nested_repository` | 该测试验证workspace 根到源码仓库的路由与路径过滤符合固定契约。 |
| `AutomationTest.test_version_one_registry_is_read_compatibly` | 该测试验证对应功能的状态转换、输出和失败门符合固定契约。 |
| `AutomationTest.test_version_two_registry_upgrades_to_session_activation_contract` | 验证 schema 2 注册表读取后立即遵守 session Skill 激活门，并可通过规范激活事件继续工作。 |
| `AutomationTest.test_opencode_and_generic_normalization` | 验证 OpenCode、generic 与 Claude Skill 事件可确定性规范化为统一事件和精确激活证据。 |
| `AutomationTest.test_gemini_copilot_and_cursor_normalization` | 该测试验证Gemini、Copilot 和 Cursor 的事件规范化符合固定契约。 |
| `AutomationTest.test_concurrent_hooks_are_serialized_without_event_loss` | 该测试验证并发 Hook 的串行导入与事件无损符合固定契约。 |
| `AutomationTest.test_failed_spool_is_retained_and_retryable` | 该测试验证失败 spool 的保留和显式重试符合固定契约。 |
| `AutomationTest._prepare_human_projection` | 建立自动化晋升测试所需的最小人类投影。 |
| `AutomationTest.test_agent_review_promotes_one_chinese_human_note` | 该测试验证Agent 审阅集合、中文说明和来源检查符合固定契约。 |
| `AutomationTest.test_render_all_harness_integrations` | 验证九种 Harness 适配包、激活清单字段、Claude Skill Hook 和 OpenCode V2 结构。 |
| `AutomationTest.test_automation_fts_finds_pending_machine_record` | 该测试验证自动化机器记录的 FTS 检索符合固定契约。 |
| `AutomationTest.test_machine_retrieval_and_changes_include_pending_automation` | 该测试验证对应功能的状态转换、输出和失败门符合固定契约。 |

</details>
