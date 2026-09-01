# 项目关系导览

> 这份导览把经常一起工作的类和函数聚成职责群，帮助人先理解结构，再进入具体实现。

## 建议先看的代码

- **CkbError**：`CkbError` 是 `scripts/ckb_core/common.py` 中负责为 CKB 输入或状态错误提供固定进程退出码的类。
- **ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append**：`ManagementSchemaPersi...` 是 `tests/test_management_agent.py` 第 111-113 行定义的函数，本页绑定该固定源码范围。
- **main**：`main` 是 `scripts/ckb.py` 第 780-1393 行定义的函数，本页绑定该固定源码范围。
- **CodeKnowledgeBuilderTests**：`CodeKnowledgeBuilderT...` 是 `tests/test_ckb.py` 第 199-2232 行定义的类，本页绑定该固定源码范围。
- **command**：`command` 是 `tests/e2e_knowledge_batch_migration.py` 第 42-65 行定义的函数，本页绑定该固定源码范围。
- **_Transport.close**：`_Transport.close` 是 `scripts/ckb_core/session_stdio.py` 第 457-496 行定义的函数，本页绑定该固定源码范围。
- **execute**：`execute` 是 `tests/provider_integration.py` 第 19-24 行定义的函数，本页绑定该固定源码范围。
- **SessionStdioLifecycleTests**：`SessionStdioLifecycle...` 是 `tests/test_session_stdio.py` 第 77-536 行定义的类，本页绑定该固定源码范围。
- **initialize**：`initialize` 是 `scripts/ckb_core/pipeline.py` 第 676-922 行定义的函数，本页绑定该固定源码范围。
- **AgentProtocolBatchApplyTests**：`AgentProtocolBatchApp...` 是 `tests/test_agent_protocol_batch.py` 第 272-685 行定义的类，本页绑定该固定源码范围。
- **parser**：`parser` 是 `scripts/ckb.py` 第 270-743 行定义的函数，本页绑定该固定源码范围。
- **SourceLinkRenderer.uri**：`SourceLinkRenderer.uri` 将仓库内源码位置编码为编辑器可打开的 URI。

## 按职责群浏览

### main 相关职责

- **main**：`main` 是 `scripts/ckb.py` 第 780-1393 行定义的函数，本页绑定该固定源码范围。
- **_Transport.close**：`_Transport.close` 是 `scripts/ckb_core/session_stdio.py` 第 457-496 行定义的函数，本页绑定该固定源码范围。
- **execute**：`execute` 是 `tests/provider_integration.py` 第 19-24 行定义的函数，本页绑定该固定源码范围。
- **SourceLinkRenderer.uri**：`SourceLinkRenderer.uri` 将仓库内源码位置编码为编辑器可打开的 URI。
- **ingest_event**：`ingest_event` 是 `scripts/ckb_core/automation.py` 第 1394-1504 行定义的函数，本页绑定该固定源码范围。
- **AutomationTest.register**：`AutomationTest.register` 是 `tests/test_automation.py` 第 78-80 行定义的函数，本页绑定该固定源码范围。
- **Box**：`Box` 是 `tests/fixtures/cpp-parser-scons/scons-project/src/main.cpp` 第 2-2 行定义的类，本页绑定该固定源码范围。
- **AutomationTest**：`AutomationTest` 是第 48-885 行的类，供所属页面定位实现。

### ScopeExtensionTest 相关职责

- **ScopeExtensionTest**：`ScopeExtensionTest` 是 `tests/test_scope_extension.py` 第 63-418 行定义的类，本页绑定该固定源码范围。
- **start_scope_extension**：`start_scope_extension` 是 `scripts/ckb_core/scope_extension.py` 第 261-451 行定义的函数，本页绑定该固定源码范围。
- **create_knowledge_batch_plan**：`create_knowledge_batc...` 是 `scripts/ckb_core/knowledge_batch_migration.py` 第 888-956 行定义的函数，本页绑定该固定源码范围。
- **KnowledgeBatchWorkflowTests**：`KnowledgeBatchWorkflo...` 是第 127-701 行的类，供所属页面定位实现。
- **_tree_manifest**：`_tree_manifest` 是第 57-72 行的函数，供所属页面定位实现。
- **_inspect_knowledge_project**：`_inspect_knowledge_pr...` 是第 663-885 行的函数，供所属页面定位实现。
- **apply_knowledge_batch_plan**：`apply_knowledge_batch...` 是第 1506-1552 行的函数，供所属页面定位实现。
- **_knowledge_project_audit**：`_knowledge_project_audit` 是第 1292-1424 行的函数，供所属页面定位实现。

### AgentProtocolBatchApplyTests 相关职责

- **AgentProtocolBatchApplyTests**：`AgentProtocolBatchApp...` 是 `tests/test_agent_protocol_batch.py` 第 272-685 行定义的类，本页绑定该固定源码范围。
- **audit_agent_protocol**：`audit_agent_protocol` 是 `scripts/ckb_core/agent_protocol.py` 中负责核对各 Harness 指令文件、工作区绑定、反馈、工作记录与输出契约的函数。
- **create_batch_plan**：`create_batch_plan` 是 `scripts/ckb_core/agent_protocol_batch.py` 第 657-714 行定义的函数，本页绑定该固定源码范围。
- **run**：`run` 是 `tests/e2e_agent_protocol_batch.py` 第 147-305 行定义的函数，本页绑定该固定源码范围。
- **BatchProjectError**：`BatchProjectError` 是第 161-164 行的类，供所属页面定位实现。
- **apply_batch_plan**：`apply_batch_plan` 是第 1414-1516 行的函数，供所属页面定位实现。
- **create_protocol_fixture**：`create_protocol_fixture` 是第 47-118 行的函数，供所属页面定位实现。
- **_output_lock**：`_output_lock` 是第 1178-1256 行的函数，供所属页面定位实现。

### retrieve_machine 相关职责

- **retrieve_machine**：`retrieve_machine` 是 `scripts/ckb_core/machine_knowledge.py` 第 1600-1709 行定义的函数，本页绑定该固定源码范围。
- **run_keyword_provider**：`run_keyword_provider` 是 `scripts/ckb_core/keyword_fallback.py` 第 380-461 行定义的函数，本页绑定该固定源码范围。
- **KeywordFallbackRetrievalWiringTests**：`KeywordFallbackRetrie...` 是 `tests/test_keyword_fallback.py` 第 198-349 行定义的类，本页绑定该固定源码范围。
- **run_keyword_benchmark**：`run_keyword_benchmark` 是 `scripts/ckb_core/keyword_benchmark.py` 第 139-227 行定义的函数，本页绑定该固定源码范围。
- **keyword_provider_config**：`keyword_provider_config` 是 `scripts/ckb.py` 第 237-257 行定义的函数，本页绑定该固定源码范围。
- **load_page_config**：`load_page_config` 是源码中负责规范化并校验不可漂移的页面配置的命名代码单元。
- **KeywordFallbackAdapterTests.config**：`KeywordFallbackAdapte...` 是第 115-124 行的函数，供所属页面定位实现。
- **_retrieve_machine_deterministic**：`_retrieve_machine_det...` 是第 1077-1556 行的函数，供所属页面定位实现。

### SessionStdioLifecycleTests 相关职责

- **SessionStdioLifecycleTests**：`SessionStdioLifecycle...` 是 `tests/test_session_stdio.py` 第 77-536 行定义的类，本页绑定该固定源码范围。
- **main**：`main` 是 `tests/session_stdio_reactivation_probe.py` 第 16-112 行定义的函数，本页绑定该固定源码范围。
- **one_cycle**：`one_cycle` 是 `tests/session_stdio_stress.py` 第 22-45 行定义的函数，本页绑定该固定源码范围。
- **close_session**：`close_session` 是第 1330-1389 行的函数，供所属页面定位实现。
- **request_session**：`request_session` 是第 1139-1255 行的函数，供所属页面定位实现。
- **cleanup_sessions**：`cleanup_sessions` 是第 1392-1431 行的函数，供所属页面定位实现。
- **activate_session_stdio**：`activate_session_stdio` 是第 802-887 行的函数，供所属页面定位实现。
- **audit_sessions**：`audit_sessions` 是第 1434-1458 行的函数，供所属页面定位实现。

### retrieve 相关职责

- **retrieve**：`retrieve` 是 `scripts/ckb_core/agent_index.py` 第 426-554 行定义的函数，本页绑定该固定源码范围。
- **QueryTermsTests**：`QueryTermsTests` 是 `tests/test_query_terms.py` 第 25-107 行定义的类，本页绑定该固定源码范围。
- **search_terms**：`search_terms` 是 `scripts/ckb_core/query_terms.py` 第 65-69 行定义的函数，本页绑定该固定源码范围。
- **audit_gap_register**：`audit_gap_register` 是 `scripts/ckb_core/research_gaps.py` 第 233-272 行定义的函数，本页绑定该固定源码范围。
- **normalize**：`normalize` 是 `tests/benchmark_chinese_retrieval.py` 第 211-245 行定义的函数，本页绑定该固定源码范围。
- **build_machine_knowledge**：`build_machine_knowledge` 是第 354-613 行的函数，供所属页面定位实现。
- **audit_machine_knowledge**：`audit_machine_knowledge` 是第 637-718 行的函数，供所属页面定位实现。
- **create_gap**：`create_gap` 是第 123-149 行的函数，供所属页面定位实现。

### CodeKnowledgeBuilderTests 相关职责

- **CodeKnowledgeBuilderTests**：`CodeKnowledgeBuilderT...` 是 `tests/test_ckb.py` 第 199-2232 行定义的类，本页绑定该固定源码范围。
- **maintenance_check**：`maintenance_check` 是 `scripts/ckb_core/llm_wiki_capabilities.py` 第 408-458 行定义的函数，本页绑定该固定源码范围。
- **audit_operation_journal**：`audit_operation_journal` 是 `scripts/ckb_core/operation_journal.py` 第 383-452 行定义的函数，本页绑定该固定源码范围。
- **audit_output_contract**：`audit_output_contract` 是 `scripts/ckb_core/output_contract.py` 第 111-143 行定义的函数，本页绑定该固定源码范围。
- **register_obsidian_plugin**：`register_obsidian_plugin` 是 `scripts/ckb_core/obsidian_plugin.py` 中负责验证并登记独立 Obsidian Companion 包及其可部署载荷的函数。
- **audit_obsidian**：`audit_obsidian` 是 `scripts/ckb_core/obsidian.py` 中负责检查 Obsidian 配置、样式、所有权清单与页面投影约束的函数。
- **record_operation**：`record_operation` 是第 261-309 行的函数，供所属页面定位实现。
- **safe_rmtree**：处理 `rmtree` 对应的数据与约束。

### bind_conversation 相关职责

- **bind_conversation**：`bind_conversation` 是 `scripts/ckb_core/management_agent.py` 第 435-550 行定义的函数，本页绑定该固定源码范围。
- **ManagementBindingLifecycleTest**：`ManagementBindingLife...` 是第 128-470 行的类，供所属页面定位实现。
- **ManagementSchemaPersistenceTest**：`ManagementSchemaPersi...` 是第 49-125 行的类，供所属页面定位实现。
- **create_management_task**：`create_management_task` 是第 1014-1153 行的函数，供所属页面定位实现。
- **review_management_task**：`review_management_task` 是第 1240-1336 行的函数，供所属页面定位实现。
- **audit_manager_registry**：`audit_manager_registry` 是第 265-352 行的函数，供所属页面定位实现。
- **unbind_conversation**：`unbind_conversation` 是第 628-669 行的函数，供所属页面定位实现。
- **binding_status**：`binding_status` 是第 605-625 行的函数，供所属页面定位实现。

### CkbError 相关职责

- **CkbError**：`CkbError` 是 `scripts/ckb_core/common.py` 中负责为 CKB 输入或状态错误提供固定进程退出码的类。
- **audit_references**：`audit_references` 是 `scripts/ckb_core/reference_documents.py` 中负责核对资料原文、许可证、逐项引用、中文主张、镜像和机器索引的函数。
- **serve_stdio**：`serve_stdio` 是 `scripts/ckb_core/stdio_server.py` 第 202-391 行定义的函数，本页绑定该固定源码范围。
- **audit_feedback**：`audit_feedback` 是 `scripts/ckb_core/feedback.py` 中负责检查反馈锚点、状态、镜像、归档与落实记录的一致性的函数。
- **package_showcase**：`package_showcase` 是源码中负责构建可复现发行归档并复核成员集合的命名代码单元。
- **create_feedback**：创建 `feedback` 对应的数据与约束。
- **project_references**：投影 `references` 对应的数据与约束。
- **resolve_feedback**：解析并确定 `feedback` 对应的数据与约束。

### sha256_file 相关职责

- **sha256_file**：处理 `file` 对应的数据与约束。
- **refresh_human_navigation**：刷新 `human_navigation` 对应的数据与约束。
- **project_logseq**：投影 `logseq` 对应的数据与约束。
- **project_markdown**：投影 `markdown` 对应的数据与约束。
- **_audit_markdown**：审计 `markdown` 对应的数据与约束。
- **build_context**：构建 `context` 对应的数据与约束。
- **_normalized_edn_document**：处理 `edn_document` 对应的数据与约束。
- **_powershell_command.quote**：`_powershell_command.q...` 是第 45-46 行的函数，供所属页面定位实现。

### command 相关职责

- **command**：`command` 是 `tests/e2e_knowledge_batch_migration.py` 第 42-65 行定义的函数，本页绑定该固定源码范围。
- **render_integration**：`render_integration` 是 `scripts/ckb_core/automation_integrations.py` 第 432-574 行定义的函数，本页绑定该固定源码范围。
- **emit**：`emit` 是 `scripts/ckb.py` 第 749-752 行定义的函数，本页绑定该固定源码范围。
- **historical_output**：`historical_output` 是第 96-152 行的函数，供所属页面定位实现。
- **_opencode_v2_plugin**：`_opencode_v2_plugin` 是第 295-388 行的函数，供所属页面定位实现。
- **_codex_windows_bridge**：`_codex_windows_bridge` 是第 65-78 行的函数，供所属页面定位实现。
- **_commands**：`_commands` 是第 35-41 行的函数，供所属页面定位实现。
- **_cursor_hooks**：`_cursor_hooks` 是第 191-211 行的函数，供所属页面定位实现。

### utc_now 相关职责

- **utc_now**：处理 `now` 对应的数据与约束。
- **audit_global**：`audit_global` 是第 2891-3204 行的函数，供所属页面定位实现。
- **review_pack**：处理 `pack` 对应的数据与约束。
- **audit_chunk**：审计 `chunk` 对应的数据与约束。
- **AuditError**：处理 `auditerror` 对应的数据与约束。
- **build_chunk**：构建 `chunk` 对应的数据与约束。
- **write_marker**：写入 `marker` 对应的数据与约束。
- **review_chunk**：处理 `chunk` 对应的数据与约束。

### initialize 相关职责

- **initialize**：`initialize` 是 `scripts/ckb_core/pipeline.py` 第 676-922 行定义的函数，本页绑定该固定源码范围。
- **preflight**：`preflight` 是 `scripts/ckb_core/gitrepo.py` 第 194-217 行定义的函数，本页绑定该固定源码范围。
- **stable_id**：根据固定输入计算 `stable_id` 稳定标识。
- **_load_state**：加载 `state` 对应的数据与约束。
- **StaleSourceError**：处理 `stalesourceerror` 对应的数据与约束。
- **prepare_git_repository**：准备 `git_repository` 对应的数据与约束。
- **_relocate_completed_output**：处理 `completed_output` 对应的数据与约束。
- **assert_source_snapshot**：处理 `source_snapshot` 对应的数据与约束。

### audit_migration 相关职责

- **audit_migration**：`audit_migration` 是 `scripts/ckb_core/migration.py` 第 367-479 行定义的函数，本页绑定该固定源码范围。
- **MigrationTest**：`MigrationTest` 构造连续两个源码提交和迁移前后知识库。
- **migrate_output**：`migrate_output` 是第 253-364 行的函数，供所属页面定位实现。
- **relink_preserved_notes**：`relink_preserved_notes` 是第 487-581 行的函数，供所属页面定位实现。
- **_preserve_mutable_layers**：`_preserve_mutable_layers` 是第 114-181 行的函数，供所属页面定位实现。
- **_replace_review_packs**：`_replace_review_packs` 是第 199-250 行的函数，供所属页面定位实现。
- **MigrationTest.test_exact_blob_facts_and_agent_reviews_are_reused**：验证精确 blob 与中文审阅复用、可变层基线、目录提升后的路径重定位及篡改失败门。
- **_cold_build**：`_cold_build` 是第 1160-1232 行的函数，供所属页面定位实现。

### KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures.refresh 相关职责

- **KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures.refresh**：`KnowledgeBatchWorkflo...` 是 `tests/test_knowledge_batch_migration.py` 第 468-476 行定义的函数，本页绑定该固定源码范围。
- **finalize**：完成并封存 `finalize` 对应的数据与约束。
- **merge**：合并 `merge` 对应的数据与约束。
- **_control_records.depth**：`_control_records.depth` 是第 504-517 行的函数，供所属页面定位实现。
- **_logical_projection**：处理 `projection` 对应的数据与约束。
- **CodeKnowledgeBuilderTests.test_markdown_whole_repository_and_completion_gate**：`CodeKnowledgeBuilderT...` 是第 1145-1689 行的函数，供所属页面定位实现。
- **page_config_sha256**：该附属代码负责规范化并校验不可漂移的页面配置，并把结果交给所属页面中的主流程使用。
- **_operation_type**：`_operation_type` 是第 231-258 行的函数，供所属页面定位实现。

### parse_file 相关职责

- **parse_file**：`parse_file` 是 `scripts/ckb_core/parsers.py` 第 272-430 行定义的函数，本页绑定该固定源码范围。
- **deployment_plan**：`deployment_plan` 是 `scripts/ckb_core/runtime.py` 中负责根据锁定运行时清单生成所需组件、来源和部署动作的函数。
- **DependencyError**：处理 `dependencyerror` 对应的数据与约束。
- **deploy**：该附属代码负责管理隔离离线运行时及其回滚，并把结果交给所属页面中的主流程使用。
- **_byte_position**：`_byte_position` 是第 93-96 行的函数，供所属页面定位实现。
- **_node_text**：`_node_text` 是第 89-90 行的函数，供所属页面定位实现。
- **_parse_diagnostics**：`_parse_diagnostics` 是第 238-269 行的函数，供所属页面定位实现。
- **_find_name**：`_find_name` 是第 99-115 行的函数，供所属页面定位实现。

### query_graph 相关职责

- **query_graph**：`query_graph` 是源码中负责构造职责关系图并提供职责群或路径查询的命名代码单元。
- **project_graphify**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **_load_projected_graph**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **shortest_path**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **_community_records**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **_graphify_node**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **_networkx_modules**：该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。
- **_resolve_node**：该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。

### project_agent_protocol 相关职责

- **project_agent_protocol**：投影 `agent_protocol` 对应的数据与约束。
- **install_agent_protocol**：安装 `agent_protocol` 对应的数据与约束。
- **_command_examples**：处理 `examples` 对应的数据与约束。
- **_protocol_text**：处理 `text` 对应的数据与约束。
- **_adapter_texts**：处理 `texts` 对应的数据与约束。
- **_expected_internal**：处理 `internal` 对应的数据与约束。
- **_write_workspace_root**：写入 `workspace_root` 对应的数据与约束。
- **_load_record**：加载 `record` 对应的数据与约束。

### source_files 相关职责

- **source_files**：`source_files` 是 `scripts/package_release.py` 第 42-63 行定义的函数，本页绑定该固定源码范围。
- **PackageReleaseTests**：`PackageReleaseTests` 是 `tests/test_package_release.py` 第 23-72 行定义的类，本页绑定该固定源码范围。
- **build_core**：`build_core` 是第 122-185 行的函数，供所属页面定位实现。
- **_sections_for_entity**：`_sections_for_entity` 是第 161-179 行的函数，供所属页面定位实现。
- **build_plugin**：`build_plugin` 是第 213-270 行的函数，供所属页面定位实现。
- **PackageReleaseTests.test_core_packages_exclude_plugins_and_full_only_adds_runtime**：`PackageReleaseTests.t...` 是第 24-30 行的函数，供所属页面定位实现。
- **build**：`build` 是第 273-276 行的函数，供所属页面定位实现。
- **main**：`main` 是第 279-302 行的函数，供所属页面定位实现。

### run_benchmark 相关职责

- **run_benchmark**：`run_benchmark` 是第 285-386 行的函数，供所属页面定位实现。
- **build_manual_index**：`build_manual_index` 是第 111-154 行的函数，供所属页面定位实现。
- **copy_corpus**：`copy_corpus` 是第 74-99 行的函数，供所属页面定位实现。
- **main**：`main` 是第 547-564 行的函数，供所属页面定位实现。
- **invoke**：`invoke` 是第 248-261 行的函数，供所属页面定位实现。
- **manual_scan**：`manual_scan` 是第 157-208 行的函数，供所属页面定位实现。
- **result_signature**：`result_signature` 是第 264-271 行的函数，供所属页面定位实现。
- **summarize**：`summarize` 是第 389-499 行的函数，供所属页面定位实现。

### module_name 相关职责

- **module_name**：`module_name` 是源码中负责页面配额、实体归属、关系预算和上下文预算的确定性决策的命名代码单元。
- **build_navigation_plan**：该附属代码负责按固定排序计算页面、附录、归属和审阅预算，并把结果交给所属页面中的主流程使用。
- **_chunks**：处理 `chunks` 对应的数据与约束。
- **build_review_packs**：该附属代码负责按固定排序计算页面、附录、归属和审阅预算，并把结果交给所属页面中的主流程使用。
- **apply_navigation_plan**：该附属代码负责按固定排序计算页面、附录、归属和审阅预算，并把结果交给所属页面中的主流程使用。
- **_ancestors**：该附属代码负责页面配额、实体归属、关系预算和上下文预算的确定性决策，并把结果交给所属页面中的主流程使用。
- **_chunks.flush**：处理 `flush` 对应的数据与约束。
- **_chunks.units_for_file**：处理 `for_file` 对应的数据与约束。

### bind_reference 相关职责

- **bind_reference**：`bind_reference` 是 `tests/fixtures/cpp-parser-scons/reference-direct-init-valid.cpp` 第 3-6 行定义的函数，本页绑定该固定源码范围。
- **CppParserAndSconsTests**：`CppParserAndSconsTests` 是第 2235-2334 行的类，供所属页面定位实现。
- **CppParserAndSconsTests.parse_fixture**：`CppParserAndSconsTest...` 是第 2245-2252 行的函数，供所属页面定位实现。
- **CppParserAndSconsTests.test_cpp_conditional_compilation_valid_and_incomplete**：`CppParserAndSconsTest...` 是第 2254-2263 行的函数，供所属页面定位实现。
- **CppParserAndSconsTests.test_cpp_reference_direct_initialization_is_declaration_not_function**：`CppParserAndSconsTest...` 是第 2265-2273 行的函数，供所属页面定位实现。
- **CppParserAndSconsTests.test_cpp_explicit_template_instantiation_has_no_pseudo_entities**：`CppParserAndSconsTest...` 是第 2275-2292 行的函数，供所属页面定位实现。
- **debug_value**：`debug_value` 是第 2-4 行的函数，供所属页面定位实现。
- **CppParserAndSconsTests.setUp**：`CppParserAndSconsTest...` 是第 2238-2240 行的函数，供所属页面定位实现。

### doctor_report 相关职责

- **doctor_report**：`doctor_report` 是 `scripts/ckb_core/providers.py` 第 76-240 行定义的函数，本页绑定该固定源码范围。
- **collect_semantics**：`collect_semantics` 是第 489-618 行的函数，供所属页面定位实现。
- **_fallback_flags**：`_fallback_flags` 是第 433-460 行的函数，供所属页面定位实现。
- **_provider_spec**：`_provider_spec` 是第 371-430 行的函数，供所属页面定位实现。
- **resolve_executable**：`resolve_executable` 是第 57-73 行的函数，供所属页面定位实现。
- **CppParserAndSconsTests.test_scons_fallback_is_auditable_and_compile_database_stays_exact**：`CppParserAndSconsTest...` 是第 2294-2334 行的函数，供所属页面定位实现。
- **_provider_status**：`_provider_status` 是第 475-486 行的函数，供所属页面定位实现。
- **private_runtime_root**：`private_runtime_root` 是第 37-41 行的函数，供所属页面定位实现。

### record_note 相关职责

- **record_note**：`record_note` 是 `scripts/ckb_core/workspace_notes.py` 中负责校验中文正文与知识页回链，写入指定记录类型并更新镜像和索引的函数。
- **contains_chinese_narrative**：`contains_chinese_narr...` 是第 59-63 行的函数，供所属页面定位实现。
- **safe_title**：处理 `title` 对应的数据与约束。
- **_audit_note_storage**：审计 `note_storage` 对应的数据与约束。
- **audit_notes**：审计 `notes` 对应的数据与约束。
- **materialize_pending_notes**：物化 `pending_notes` 对应的数据与约束。
- **queue_pending_note**：处理 `pending_note` 对应的数据与约束。
- **_source_links_for_titles**：处理 `links_for_titles` 对应的数据与约束。

### parser 相关职责

- **parser**：`parser` 是 `scripts/ckb.py` 第 270-743 行定义的函数，本页绑定该固定源码范围。
- **main**：`main` 是 `tests/session_stdio_harness_probe.py` 第 16-30 行定义的函数，本页绑定该固定源码范围。
- **add_initial_arguments**：`add_initial_arguments` 是第 184-199 行的函数，供所属页面定位实现。
- **add_git_bootstrap_arguments**：`add_git_bootstrap_arg...` 是第 208-216 行的函数，供所属页面定位实现。
- **add_keyword_provider_arguments**：`add_keyword_provider_...` 是第 219-228 行的函数，供所属页面定位实现。
- **add_csharp_arguments**：`add_csharp_arguments` 是第 202-205 行的函数，供所属页面定位实现。
- **add_keyword_fallback_arguments**：`add_keyword_fallback_...` 是第 231-234 行的函数，供所属页面定位实现。

### audit_work_record_index 相关职责

- **audit_work_record_index**：`audit_work_record_index` 是 `scripts/ckb_core/work_record_index.py` 第 230-241 行定义的函数，本页绑定该固定源码范围。
- **refresh_work_record_index**：`refresh_work_record_i...` 是第 173-185 行的函数，供所属页面定位实现。
- **render_work_record_index**：渲染 `work_record_index` 对应的数据与约束。
- **audit_work_record_root**：审计 `work_record_root` 对应的数据与约束。
- **collect_work_records**：处理 `work_records` 对应的数据与约束。
- **CodeKnowledgeBuilderTests.test_work_record_index_covers_every_note_with_one_chinese_summary**：`CodeKnowledgeBuilderT...` 是第 1103-1143 行的函数，供所属页面定位实现。
- **_first_narrative**：处理 `narrative` 对应的数据与约束。
- **_plain_text**：处理 `text` 对应的数据与约束。

### resolve_checkout_git_dir 相关职责

- **resolve_checkout_git_dir**：`resolve_checkout_git_dir` 是 `tests/git_checkout.py` 第 20-32 行定义的函数，本页绑定该固定源码范围。
- **KnowledgeBatchVersionMatrixTests**：`KnowledgeBatchVersion...` 是第 25-124 行的类，供所属页面定位实现。
- **knowledge_version_matrix**：`knowledge_version_matrix` 是第 255-287 行的函数，供所属页面定位实现。
- **KnowledgeBatchVersionMatrixTests.test_git_common_dir_resolves_worktree_and_ordinary_clone**：`KnowledgeBatchVersion...` 是第 26-75 行的函数，供所属页面定位实现。
- **resolve_git_common_dir**：`resolve_git_common_dir` 是第 35-63 行的函数，供所属页面定位实现。
- **KnowledgeBatchVersionMatrixTests.test_matrix_uses_real_historical_releases**：`KnowledgeBatchVersion...` 是第 77-101 行的函数，供所属页面定位实现。
- **KnowledgeBatchVersionMatrixTests.test_reference_matrix_matches_runtime_matrix**：`KnowledgeBatchVersion...` 是第 103-109 行的函数，供所属页面定位实现。
- **_host_path**：`_host_path` 是第 9-17 行的函数，供所属页面定位实现。

### ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append 相关职责

- **ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append**：`ManagementSchemaPersi...` 是 `tests/test_management_agent.py` 第 111-113 行定义的函数，本页绑定该固定源码范围。
- **main**：`main` 解析补丁输出路径并生成从空目录到完整 Skill 的文本统一差异。
- **CodeKnowledgeBuilderTests.test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server**：`CodeKnowledgeBuilderT...` 是第 600-687 行的函数，供所属页面定位实现。
- **KeywordFallbackRetrievalWiringTests.test_stdio_exposes_the_same_nested_canonical_options**：`KeywordFallbackRetrie...` 是第 311-349 行的函数，供所属页面定位实现。
- **CodeKnowledgeBuilderTests.test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server.fake_record**：`CodeKnowledgeBuilderT...` 是第 619-621 行的函数，供所属页面定位实现。
- **build_review_packs.partition**：该附属代码负责按固定排序计算页面、附录、归属和审阅预算，并把结果交给所属页面中的主流程使用。
- **_logseq_count.visit**：处理 `visit` 对应的数据与约束。
- **CodeKnowledgeBuilderTests.test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server.fake_retrieve**：`CodeKnowledgeBuilderT...` 是第 607-617 行的函数，供所属页面定位实现。

### start_session 相关职责

- **start_session**：`start_session` 是源码中负责管理 Agent 会话、构建中记录和修改总结落页的命名代码单元。
- **finish_session**：该附属代码负责管理 Agent 会话、构建中记录和修改总结落页，并把结果交给所属页面中的主流程使用。
- **sync_workspace**：同步 `workspace` 对应的数据与约束。
- **_record_or_queue**：该附属代码负责Agent 任务会话、构建中笔记排队、修改总结和生命周期状态，并把结果交给所属页面中的主流程使用。
- **_new_session_id**：该附属代码负责管理 Agent 会话、构建中记录和修改总结落页，并把结果交给所属页面中的主流程使用。
- **_session_directory**：该附属代码负责管理 Agent 会话、构建中记录和修改总结落页，并把结果交给所属页面中的主流程使用。
- **sessions_status**：该附属代码负责管理 Agent 会话、构建中记录和修改总结落页，并把结果交给所属页面中的主流程使用。
- **_summary_heading_errors**：该附属代码负责Agent 任务会话、构建中笔记排队、修改总结和生命周期状态，并把结果交给所属页面中的主流程使用。

### LspClient 相关职责

- **LspClient**：`LspClient` 是第 258-368 行的类，供所属页面定位实现。
- **LspClient.send**：`LspClient.send` 是第 309-315 行的函数，供所属页面定位实现。
- **LspClient.notify**：`LspClient.notify` 是第 317-318 行的函数，供所属页面定位实现。
- **LspClient._read_stderr**：`LspClient._read_stderr` 是第 304-307 行的函数，供所属页面定位实现。
- **LspClient._read_stdout**：`LspClient._read_stdout` 是第 283-302 行的函数，供所属页面定位实现。
- **LspClient.start**：`LspClient.start` 是第 270-281 行的函数，供所属页面定位实现。
- **LspClient.request**：`LspClient.request` 是第 320-350 行的函数，供所属页面定位实现。
- **LspClient.__init__**：`LspClient.__init__` 是第 259-268 行的函数，供所属页面定位实现。

> 为保持阅读节奏，这里只展开最主要的职责群；图查询仍会使用完整关系。

## 围绕任务继续缩小范围

```powershell
& PYTHON scripts\ckb.py query --out OUTPUT "职责关键词" --budget 1500
& PYTHON scripts\ckb.py path --out OUTPUT "起点类或函数" "目标类或函数"
& PYTHON scripts\ckb.py explain --out OUTPUT "类名、函数名或职责关键词"
```

查询会先选择与问题最相关的代码，再沿真实关系扩展到预算允许的范围。
