# CodeKnowledgeBuilderTests

标签：#类型/代码

> `CodeKnowledgeBuilderTests` 汇集主构建流水线的端到端回归场景与断言。 它统一管理临时 Git 夹具，验证范围、审阅、投影、运行时和失败门。

## 什么时候需要修改

主流水线验收条件或测试夹具结构变化时，需要修改该测试类。

## 在代码中的位置

[打开源码：tests/test_ckb.py 第 170 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb.py:170:1)  `tests/test_ckb.py:170-1132`

## 相关代码

- 实现时会用到 [[CodeKnowledgeBuilderTests 等测试场景]]。
- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[retrieve]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[status 与 _load_state 的协作实现]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests 等测试场景]] 汇总了本页。
- [[LspClient.start]] 关联到这里的验证场景。
- [[LspClient.start 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[audit_migration]] 关联到这里的验证场景。
- [[audit_migration 与 _entity_key 的协作实现]] 关联到这里的验证场景。
- [[create_source_snapshot]] 关联到这里的验证场景。
- [[create_source_snapshot 与 git 的协作实现]] 关联到这里的验证场景。
- [[ensure_local_openers]] 关联到这里的验证场景。
- [[ensure_local_openers 与 default_openers 的协作实现]] 关联到这里的验证场景。
- [[execute]] 关联到这里的验证场景。
- [[load_page_config]] 关联到这里的验证场景。
- [[load_page_config 与 _merge_known 的协作实现]] 关联到这里的验证场景。
- [[module_name]] 关联到这里的验证场景。
- [[module_name 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[parse_file]] 关联到这里的验证场景。
- [[parse_file 与 _language 的协作实现]] 关联到这里的验证场景。
- [[prepare_vault]] 关联到这里的验证场景。
- [[prepare_vault 与 install_obsidian 的协作实现]] 关联到这里的验证场景。
- [[query_graph 与 _networkx_modules 的协作实现]] 关联到这里的验证场景。
- [[record_note]] 关联到这里的验证场景。
- [[record_note 与 page_tag 的协作实现]] 关联到这里的验证场景。
- [[render_integration 与 _looks_windows 的协作实现]] 关联到这里的验证场景。
- [[retrieve]] 关联到这里的验证场景。
- [[retrieve 与 _tokens 的协作实现]] 关联到这里的验证场景。
- [[retrieve_machine]] 关联到这里的验证场景。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[run]] 关联到这里的验证场景。
- [[run 与 CkbError 的协作实现]] 关联到这里的验证场景。
- [[source_files]] 关联到这里的验证场景。
- [[status]] 关联到这里的验证场景。
- [[status 与 _load_state 的协作实现]] 关联到这里的验证场景。
- [[sync_human_layer]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 20 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `CodeKnowledgeBuilderTests.setUp` | 该附属代码负责构造或执行可重复的回归验证场景，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.tearDown` | 该附属代码负责构造或执行可重复的回归验证场景，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_non_git_path_reminds_then_opt_in_creates_one_initial_commit` | 该附属代码负责固定仓库来源并规划扫描、页面与审阅批次，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_unborn_git_repo_requires_opt_in_and_existing_dirty_repo_is_not_committed` | 该附属代码负责范围、分段、审阅、格式、索引、C#、配置和完成门回归测试，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_fast_run_can_bootstrap_non_git_source_and_stops_for_review` | 该附属代码负责核对并登记逐实体 Agent 审阅结果，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_markdown_whole_repository_and_completion_gate` | 该测试验证Markdown 人类页面、双链和完成标记符合固定契约。 |
| `CodeKnowledgeBuilderTests.test_local_scope_has_one_hop_boundary` | 该附属代码负责解析 tracked source 范围、显式路径和边界实体，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_entry_scope_uses_fixed_snapshot_while_live_worktree_changes` | 该附属代码负责建立并验证与固定提交一致的源码快照，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_review_set_mismatch_fails` | 该附属代码负责核对并登记逐实体 Agent 审阅结果，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_runtime_plan_lite` | 该附属代码负责管理隔离离线运行时及其回滚，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_required_format_duplicate_entry_and_syntax_stage` | 该附属代码负责范围、分段、审阅、格式、索引、C#、配置和完成门回归测试，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_oversized_file_splits_on_declarations_without_duplicate_ids` | 该附属代码负责范围、分段、审阅、格式、索引、C#、配置和完成门回归测试，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_both_projection_parity_with_cli_contract_double` | 该附属代码负责范围、分段、审阅、格式、索引、C#、配置和完成门回归测试，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_logseq_only_projection_has_format_neutral_agent_index` | 该附属代码负责维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_english_only_agent_review_is_rejected` | 该附属代码负责核对并登记逐实体 Agent 审阅结果，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_navigation_page_quota_relation_budget_and_context_bundle` | 该附属代码负责范围、分段、审阅、格式、索引、C#、配置和完成门回归测试，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_page_configuration_controls_quotas_content_and_is_pinned` | 该附属代码负责范围、分段、审阅、格式、索引、C#、配置和完成门回归测试，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_csharp_project_selection_partial_types_and_generated_exclusions` | 该附属代码负责范围、分段、审阅、格式、索引、C#、配置和完成门回归测试，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_csharp_property_and_enum_land_in_class_or_file_aggregation` | 该附属代码负责范围、分段、审阅、格式、索引、C#、配置和完成门回归测试，并把结果交给所属页面中的主流程使用。 |
| `CodeKnowledgeBuilderTests.test_fallback_standard_derivation_and_stable_ids` | 该附属代码负责范围、分段、审阅、格式、索引、C#、配置和完成门回归测试，并把结果交给所属页面中的主流程使用。 |

</details>
