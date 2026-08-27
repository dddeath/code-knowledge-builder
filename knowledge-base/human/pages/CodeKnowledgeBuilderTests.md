# CodeKnowledgeBuilderTests

标签：#类型/代码

> `CodeKnowledgeBuilderTests` 汇集 code-knowledge-builder 的端到端验收场景。 它统一管理临时 Git 夹具，验证初始化、范围、审阅、投影、运行时、C#、检索缓存和失败门。

## 什么时候需要修改

构建流水线验收条件、测试夹具结构或新增回归风险时，需要修改该测试类。

## 在代码中的位置

[打开源码：tests/test_ckb.py 第 171 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb.py:171:1)  `tests/test_ckb.py:171-1147`

## 相关代码

- 实现时会用到 [[CodeKnowledgeBuilderTests 等测试场景]]。
- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[status 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests 等测试场景]] 汇总了本页。
- [[LspClient.start]] 关联到这里的验证场景。
- [[LspClient.start 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[SourceLinkRenderer.uri]] 关联到这里的验证场景。
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]] 关联到这里的验证场景。
- [[audit_migration]] 关联到这里的验证场景。
- [[audit_migration 与 _entity_key 的协作实现]] 关联到这里的验证场景。
- [[create_source_snapshot]] 关联到这里的验证场景。
- [[create_source_snapshot 与 git 的协作实现]] 关联到这里的验证场景。
- [[execute]] 关联到这里的验证场景。
- [[ingest_event 与 default_registry_path 的协作实现]] 关联到这里的验证场景。
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
- [[status 与 _replace_output_prefix 的协作实现]] 关联到这里的验证场景。
- [[sync_human_layer]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 20 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `CodeKnowledgeBuilderTests.setUp` | 为每个用例创建隔离临时目录和已提交的多语言仓库。 |
| `CodeKnowledgeBuilderTests.tearDown` | 在用例结束后清理隔离测试目录。 |
| `CodeKnowledgeBuilderTests.test_non_git_path_reminds_then_opt_in_creates_one_initial_commit` | 验证非 Git 目录先提示，再仅在显式选择后创建一次初始提交。 |
| `CodeKnowledgeBuilderTests.test_unborn_git_repo_requires_opt_in_and_existing_dirty_repo_is_not_committed` | 验证无提交仓库需要显式初始化，且已有脏仓库不会被自动提交。 |
| `CodeKnowledgeBuilderTests.test_fast_run_can_bootstrap_non_git_source_and_stops_for_review` | 验证快速入口可初始化非 Git 源码，并在首个 Agent 审阅门停止。 |
| `CodeKnowledgeBuilderTests.test_markdown_whole_repository_and_completion_gate` | 端到端验证 Markdown 构建、机器检索、缓存命中、源码链接与三项完成门。 |
| `CodeKnowledgeBuilderTests.test_local_scope_has_one_hop_boundary` | 验证局部路径扫描会为范围外关系生成一跳边界。 |
| `CodeKnowledgeBuilderTests.test_entry_scope_uses_fixed_snapshot_while_live_worktree_changes` | 验证入口扫描使用固定快照且允许后续工作树修改独立记录。 |
| `CodeKnowledgeBuilderTests.test_review_set_mismatch_fails` | 验证审阅实体集合与计划不一致时审计门失败。 |
| `CodeKnowledgeBuilderTests.test_runtime_plan_lite` | 验证 lite 运行时计划准确报告待部署依赖而不直接部署。 |
| `CodeKnowledgeBuilderTests.test_required_format_duplicate_entry_and_syntax_stage` | 验证必填格式、重名入口候选和单阶段语法构建契约。 |
| `CodeKnowledgeBuilderTests.test_oversized_file_splits_on_declarations_without_duplicate_ids` | 验证超大文件按声明边界分段且实体 ID 不重复。 |
| `CodeKnowledgeBuilderTests.test_both_projection_parity_with_cli_contract_double` | 验证 Markdown 与 Logseq DB 双投影具有同一逻辑页面和关系集合。 |
| `CodeKnowledgeBuilderTests.test_logseq_only_projection_has_format_neutral_agent_index` | 验证仅 Logseq DB 模式仍生成与格式无关的 Agent 索引。 |
| `CodeKnowledgeBuilderTests.test_english_only_agent_review_is_rejected` | 验证只有英文的 Agent 说明不能通过中文叙述门。 |
| `CodeKnowledgeBuilderTests.test_navigation_page_quota_relation_budget_and_context_bundle` | 验证页面配额、关系预算和上下文包均由确定性配置约束。 |
| `CodeKnowledgeBuilderTests.test_page_configuration_controls_quotas_content_and_is_pinned` | 验证页面内容与数量配置会被规范化、固定并影响最终投影。 |
| `CodeKnowledgeBuilderTests.test_csharp_project_selection_partial_types_and_generated_exclusions` | 验证 C# 项目选择、partial 类型合并和生成目录排除。 |
| `CodeKnowledgeBuilderTests.test_csharp_property_and_enum_land_in_class_or_file_aggregation` | 验证 C# 属性和枚举归入类页或文件聚合附录。 |
| `CodeKnowledgeBuilderTests.test_fallback_standard_derivation_and_stable_ids` | 验证 C/C++ fallback 标准推导与稳定实体 ID。 |

</details>
