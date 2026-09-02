# CodeKnowledgeBuilderTests

标签：#类型/代码

> 代码单元 `setUp`负责验证 CKB 核心构建、检索、投影、参考资料、运行时和 C++ 语法边界。 它属于项目主要公开合同的综合回归保护，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当任何核心命令、生成协议、运行时边界或跨模块行为变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：tests/test_ckb.py 第 199 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb.py:199:1)  `tests/test_ckb.py:199-2232`

## 相关代码

- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[audit_feedback 与 _contains_chinese 的协作实现]]。
- 实现时会用到 [[audit_gap_register 与 _root 的协作实现]]。
- 实现时会用到 [[audit_operation_journal 与 _root 的协作实现]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[finalize]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]]。
- 实现时会用到 [[retrieve]]。

## 谁会来到这里

- [[AutomationTest.register]] 关联到这里的验证场景。
- [[CanvasContractTests]] 关联到这里的验证场景。
- [[CodeKnowledgeBuilderTests 等测试场景]] 汇总了本页。
- [[assertions]] 关联到这里的验证场景。
- [[audit_agent_protocol]] 关联到这里的验证场景。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 关联到这里的验证场景。
- [[audit_feedback]] 关联到这里的验证场景。
- [[audit_feedback 与 _contains_chinese 的协作实现]] 关联到这里的验证场景。
- [[audit_gap_register]] 关联到这里的验证场景。
- [[audit_gap_register 与 _root 的协作实现]] 关联到这里的验证场景。
- [[audit_migration]] 关联到这里的验证场景。
- [[audit_migration 与 _entity_key 的协作实现]] 关联到这里的验证场景。
- [[audit_obsidian]] 关联到这里的验证场景。
- [[audit_obsidian 与 prepare_vault 的协作实现]] 关联到这里的验证场景。
- [[audit_operation_journal]] 关联到这里的验证场景。
- [[audit_operation_journal 与 _root 的协作实现]] 关联到这里的验证场景。
- [[audit_output_contract]] 关联到这里的验证场景。
- [[audit_output_contract 与 _default_ckb 的协作实现]] 关联到这里的验证场景。
- [[audit_work_record_index]] 关联到这里的验证场景。
- [[audit_work_record_index 与 _contains_chinese 的协作实现]] 关联到这里的验证场景。
- [[check_fact_freshness 与 _root 的协作实现]] 关联到这里的验证场景。
- [[contracts 的协作边界（623c049c）]] 关联到这里的验证场景。
- [[doctor_report 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[extract_pdf 与 PdfExtractionError 的协作实现]] 关联到这里的验证场景。
- [[finalize]] 关联到这里的验证场景。
- [[finalize 与 _replace_output_prefix 的协作实现]] 关联到这里的验证场景。
- [[ingest]] 关联到这里的验证场景。
- [[ingest_event 与 default_registry_path 的协作实现]] 关联到这里的验证场景。
- [[ingest_reference 与 _root 的协作实现]] 关联到这里的验证场景。
- [[load_page_config 与 _merge_known 的协作实现]] 关联到这里的验证场景。
- [[maintenance_check 与 capability_matrix 的协作实现]] 关联到这里的验证场景。
- [[module_name]] 关联到这里的验证场景。
- [[module_name 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[preflight 与 git 的协作实现]] 关联到这里的验证场景。
- [[query_graph 与 _networkx_modules 的协作实现]] 关联到这里的验证场景。
- [[record_note]] 关联到这里的验证场景。
- [[record_note 与 page_tag 的协作实现]] 关联到这里的验证场景。
- [[refresh]] 关联到这里的验证场景。
- [[register_obsidian_plugin]] 关联到这里的验证场景。
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]] 关联到这里的验证场景。
- [[retrieve]] 关联到这里的验证场景。
- [[retrieve 与 _tokens 的协作实现]] 关联到这里的验证场景。
- [[retrieve_machine]] 关联到这里的验证场景。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[run_keyword_provider]] 关联到这里的验证场景。
- [[sample 等测试场景]] 关联到这里的验证场景。
- [[search_terms]] 关联到这里的验证场景。
- [[search_terms 与 _split_camel 的协作实现]] 关联到这里的验证场景。
- [[serve_stdio]] 关联到这里的验证场景。
- [[serve_stdio 与 _write_line 的协作实现]] 关联到这里的验证场景。
- [[start_scope_extension 与 _error 的协作实现]] 关联到这里的验证场景。
- [[sync_human_layer]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 37 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `CodeKnowledgeBuilderTests.setUp` | `setUp` 完成CKB 核心合同回归验证中的一个明确步骤。 |
| `CodeKnowledgeBuilderTests.tearDown` | `tearDown` 完成CKB 核心合同回归验证中的一个明确步骤。 |
| `CodeKnowledgeBuilderTests.test_noninteractive_subprocesses_use_the_platform_background_flag` | 该测试验证“noninteractive subprocesses u…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_bounded_machine_operation_journal_is_private_deduplicated_and_audited` | 该测试验证“bounded machine operation jou…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_research_gap_register_is_machine_only_deduplicated_and_resolvable` | 该测试验证“research gap register is mach…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_llm_wiki_capability_matrix_has_closed_four_state_boundaries` | 该测试验证“llm wiki capability matrix ha…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_reviewed_text_reference_is_searchable_revisioned_and_reversible` | 该测试验证“reviewed text reference is se…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_empty_document_symbols_are_not_a_provider_failure` | 该测试验证“empty document symbols are no…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_python_attribute_accessors_stay_in_the_file_appendix` | 该测试验证“python attribute accessors st…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server` | 该测试验证“stdio retrieval protocol is j…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server.fake_retrieve` | `fake_retrieve` 完成CKB 核心合同回归验证中的一个明确步骤。 |
| `CodeKnowledgeBuilderTests.test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server.fake_record` | `fake_record` 完成CKB 核心合同回归验证中的一个明确步骤。 |
| `CodeKnowledgeBuilderTests.test_record_explanation_writes_utf8_machine_evidence_not_analysis_page` | 该测试验证“record explanation writes utf…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_obsidian_plugin_package_can_be_registered_deployed_and_removed` | 该测试验证“obsidian plugin package can b…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_obsidian_plugin_deploy_falls_back_when_vault_directory_is_locked` | 该测试验证“obsidian plugin deploy falls …”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_obsidian_output_contract_is_not_required_without_installed_plugin` | 该测试验证“obsidian output contract is n…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_non_git_path_reminds_then_opt_in_creates_one_initial_commit` | 该测试验证“non git path reminds then opt…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_unborn_git_repo_requires_opt_in_and_existing_dirty_repo_is_not_committed` | 该测试验证“unborn git repo requires opt …”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_fast_run_can_bootstrap_non_git_source_and_stops_for_review` | 该测试验证“fast run can bootstrap non gi…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_feedback_anchor_mirroring_audit_and_archive_are_deterministic` | 该测试验证“feedback anchor mirroring aud…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_work_record_index_covers_every_note_with_one_chinese_summary` | 该测试验证“work record index covers ever…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_markdown_whole_repository_and_completion_gate` | 该测试验证“markdown whole repository and…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_local_scope_has_one_hop_boundary` | 该测试验证“local scope has one hop bound…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_entry_scope_uses_fixed_snapshot_while_live_worktree_changes` | 该测试验证“entry scope uses fixed snapsh…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_review_set_mismatch_fails` | 该测试验证“review set mismatch fails”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_runtime_plan_lite` | 该测试验证“runtime plan lite”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_obsidian_companion_distribution_reuses_pinned_claudian` | 该测试验证“obsidian companion distributi…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_required_format_duplicate_entry_and_syntax_stage` | 该测试验证“required format duplicate ent…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_oversized_file_splits_on_declarations_without_duplicate_ids` | 该测试验证“oversized file splits on decl…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_both_projection_parity_with_cli_contract_double` | 该测试验证“both projection parity with c…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_logseq_only_projection_has_format_neutral_agent_index` | 该测试验证“logseq only projection has fo…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_english_only_agent_review_is_rejected` | 该测试验证“english only agent review is …”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_navigation_page_quota_relation_budget_and_context_bundle` | 该测试验证“navigation page quota relatio…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_page_configuration_controls_quotas_content_and_is_pinned` | 该测试验证“page configuration controls q…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_csharp_project_selection_partial_types_and_generated_exclusions` | 该测试验证“csharp project selection part…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_csharp_property_and_enum_land_in_class_or_file_aggregation` | 该测试验证“csharp property and enum land…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CodeKnowledgeBuilderTests.test_fallback_standard_derivation_and_stable_ids` | 该测试验证“fallback standard derivation …”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |

</details>
