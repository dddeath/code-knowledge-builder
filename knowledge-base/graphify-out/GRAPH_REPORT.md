# 项目关系导览

> 这份导览把经常一起工作的类和函数聚成职责群，帮助人先理解结构，再进入具体实现。

## 建议先看的代码

- **CkbError**：`CkbError` 是 `scripts/ckb_core/common.py` 中负责为 CKB 输入或状态错误提供固定进程退出码的类。
- **ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append**：`ManagementSchemaPersi...` 是 `tests/test_management_agent.py` 第 111-113 行定义的函数，本页绑定该固定源码范围。
- **main**：`main` 位于 `scripts/ckb.py` 第 900-1637 行，本页用固定源码范围说明它如何编排命令入口、执行顺序和退出结果。
- **CodeKnowledgeBuilderTests**：`CodeKnowledgeBuilderT...` 是 `tests/test_ckb.py` 第 199-2232 行定义的类，本页绑定该固定源码范围。
- **rollback**：`rollback` 位于 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py` 第 228-233 行，本页用固定源码范围说明它如何执行范围受控的恢复、撤销或清理。
- **command**：`command` 是 `tests/e2e_knowledge_batch_migration.py` 第 42-65 行定义的函数，本页绑定该固定源码范围。
- **_Transport.close**：`_Transport.close` 是 `scripts/ckb_core/session_stdio.py` 第 457-496 行定义的函数，本页绑定该固定源码范围。
- **execute**：`execute` 是 `tests/provider_integration.py` 第 19-24 行定义的函数，本页绑定该固定源码范围。
- **parser**：`parser` 位于 `scripts/ckb.py` 第 303-853 行，本页用固定源码范围说明它如何解析、规范化并冻结调用输入。
- **SessionStdioLifecycleTests**：`SessionStdioLifecycle...` 是 `tests/test_session_stdio.py` 第 77-536 行定义的类，本页绑定该固定源码范围。
- **audit_global**：`audit_global` 位于 `scripts/ckb_core/pipeline.py` 第 2891-3204 行，本页用固定源码范围说明它如何校验输入、状态、证据或输出合同。
- **SourceLinkRenderer.uri**：`SourceLinkRenderer.uri` 将仓库内源码位置编码为编辑器可打开的 URI。

## 按职责群浏览

### rollback 相关职责

- **rollback**：`rollback` 位于 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py` 第 228-233 行，本页用固定源码范围说明它如何执行范围受控的恢复、撤销或清理。
- **build_case**：`build_case` 位于 `tests/fixtures/obsidian-canvas-agent-visualization/runtime_builder.py` 第 101-366 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **validate**：`validate` 位于 `references/design/obsidian-canvas-agent-visualization/verification/validate_design.py` 第 31-69 行，本页用固定源码范围说明它如何校验输入、状态、证据或输出合同。
- **CanvasContractTests**：`CanvasContractTests` 位于 `tests/test_ckb_canvas_contracts.py` 第 38-146 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **CanvasGraphTests**：`CanvasGraphTests` 位于 `tests/test_ckb_canvas_graph.py` 第 23-136 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **CanvasTransactionTests**：`CanvasTransactionTests` 位于 `tests/test_ckb_canvas_transaction.py` 第 24-111 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **CanvasBenchmarkContractTests**：`CanvasBenchmarkContractTests` 位于 `tests/test_ckb_canvas_benchmark_contract.py` 第 68-204 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **CanvasPathTests**：`CanvasPathTests` 位于 `tests/test_ckb_canvas_paths.py` 第 31-150 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。

### AgentProtocolBatchApplyTests 相关职责

- **AgentProtocolBatchApplyTests**：`AgentProtocolBatchApp...` 是 `tests/test_agent_protocol_batch.py` 第 272-685 行定义的类，本页绑定该固定源码范围。
- **audit_agent_protocol**：`audit_agent_protocol` 是 `scripts/ckb_core/agent_protocol.py` 中负责核对各 Harness 指令文件、工作区绑定、反馈、工作记录与输出契约的函数。
- **create_batch_plan**：`create_batch_plan` 是 `scripts/ckb_core/agent_protocol_batch.py` 第 657-714 行定义的函数，本页绑定该固定源码范围。
- **run**：`run` 是 `tests/e2e_agent_protocol_batch.py` 第 147-305 行定义的函数，本页绑定该固定源码范围。
- **BatchProjectError**：`BatchProjectError` 是第 161-164 行的类，供所属页面定位实现。
- **apply_batch_plan**：`apply_batch_plan` 是第 1414-1516 行的函数，供所属页面定位实现。
- **create_protocol_fixture**：`create_protocol_fixture` 是第 47-118 行的函数，供所属页面定位实现。
- **rollback_batch_state**：`rollback_batch_state` 是第 1626-1713 行的函数，供所属页面定位实现。

### render_page_author 相关职责

- **render_page_author**：`render_page_author` 位于 `scripts/ckb_core/human_page_authoring.py` 第 705-937 行，本页用固定源码范围说明它如何生成稳定排序的结构化表示或人类输出。
- **get_human_page_template**：`get_human_page_template` 位于 `scripts/ckb_core/human_page_templates.py` 第 598-616 行，本页用固定源码范围说明它如何读取、规范化并返回既有状态。
- **HumanPageTemplateValidationTests**：`HumanPageTemplateValidationTests` 位于 `tests/test_human_page_templates.py` 第 135-462 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **HumanPageAuthoringPackageTests**：`HumanPageAuthoringPackageTests` 位于 `tests/test_human_page_authoring.py` 第 416-504 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **validate_human_page**：`validate_human_page` 在 `human_page_templates.py` 中用于校验输入、状态、证据或输出合同。
- **HumanPageAuthoringValidationFailureTests**：`HumanPageAuthoringValidationFailure…` 用于完成局部输入校验、转换或状态更新。
- **HumanPageAuthoringRenderTests**：`HumanPageAuthoringRenderTests` 用于完成局部输入校验、转换或状态更新。
- **HumanPageTemplateRegistryTests**：`HumanPageTemplateRegistryTests` 用于完成局部输入校验、转换或状态更新。

### CodeKnowledgeBuilderTests 相关职责

- **CodeKnowledgeBuilderTests**：`CodeKnowledgeBuilderT...` 是 `tests/test_ckb.py` 第 199-2232 行定义的类，本页绑定该固定源码范围。
- **audit_feedback**：`audit_feedback` 是 `scripts/ckb_core/feedback.py` 中负责检查反馈锚点、状态、镜像、归档与落实记录的一致性的函数。
- **audit_gap_register**：`audit_gap_register` 是 `scripts/ckb_core/research_gaps.py` 第 233-272 行定义的函数，本页绑定该固定源码范围。
- **audit_output_contract**：`audit_output_contract` 是 `scripts/ckb_core/output_contract.py` 第 111-143 行定义的函数，本页绑定该固定源码范围。
- **register_obsidian_plugin**：`register_obsidian_plugin` 是 `scripts/ckb_core/obsidian_plugin.py` 中负责验证并登记独立 Obsidian Companion 包及其可部署载荷的函数。
- **audit_obsidian**：`audit_obsidian` 是 `scripts/ckb_core/obsidian.py` 中负责检查 Obsidian 配置、样式、所有权清单与页面投影约束的函数。
- **create_feedback**：创建 `feedback` 对应的数据与约束。
- **resolve_feedback**：解析并确定 `feedback` 对应的数据与约束。

### CkbError 相关职责

- **CkbError**：`CkbError` 是 `scripts/ckb_core/common.py` 中负责为 CKB 输入或状态错误提供固定进程退出码的类。
- **TemplateProposalStoreTests**：`TemplateProposalStoreTests` 位于 `tests/test_human_page_template_proposals.py` 第 38-348 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **propose_template**：`propose_template` 位于 `scripts/ckb_core/human_page_template_proposals.py` 第 988-1045 行，本页用固定源码范围说明它如何完成输出局部模板提议、人工审计、事件重放和回滚中的局部职责。
- **audit_references**：`audit_references` 是 `scripts/ckb_core/reference_documents.py` 中负责核对资料原文、许可证、逐项引用、中文主张、镜像和机器索引的函数。
- **stable_id**：根据固定输入计算 `stable_id` 稳定标识。
- **digest**：`digest` 在 `validate_design.py` 中用于生成稳定标识或字节校验值。
- **audit_template_proposal**：`audit_template_proposal` 用于完成局部输入校验、转换或状态更新。
- **normalize_template_proposal**：`normalize_template_proposal` 用于完成局部输入校验、转换或状态更新。

### SessionStdioLifecycleTests 相关职责

- **SessionStdioLifecycleTests**：`SessionStdioLifecycle...` 是 `tests/test_session_stdio.py` 第 77-536 行定义的类，本页绑定该固定源码范围。
- **main**：`main` 是 `tests/session_stdio_reactivation_probe.py` 第 16-112 行定义的函数，本页绑定该固定源码范围。
- **one_cycle**：`one_cycle` 是 `tests/session_stdio_stress.py` 第 22-45 行定义的函数，本页绑定该固定源码范围。
- **close_session**：`close_session` 是第 1330-1389 行的函数，供所属页面定位实现。
- **request_session**：`request_session` 是第 1139-1255 行的函数，供所属页面定位实现。
- **cleanup_sessions**：`cleanup_sessions` 是第 1392-1431 行的函数，供所属页面定位实现。
- **activate_session_stdio**：`activate_session_stdio` 是第 802-887 行的函数，供所属页面定位实现。
- **audit_sessions**：`audit_sessions` 是第 1434-1458 行的函数，供所属页面定位实现。

### record_note 相关职责

- **record_note**：`record_note` 位于 `scripts/ckb_core/workspace_notes.py` 第 138-210 行，本页用固定源码范围说明它如何完成该文件所属能力的输入、状态、输出和失败边界中的局部职责。
- **replace_note**：`replace_note` 位于 `scripts/ckb_core/record_replace.py` 第 930-991 行，本页用固定源码范围说明它如何完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。
- **start_session**：`start_session` 是源码中负责管理 Agent 会话、构建中记录和修改总结落页的命名代码单元。
- **audit_work_record_index**：`audit_work_record_index` 是 `scripts/ckb_core/work_record_index.py` 第 230-241 行定义的函数，本页绑定该固定源码范围。
- **_prepare_replacement**：`_prepare_replacement` 用于完成局部输入校验、转换或状态更新。
- **rollback_replacement**：`rollback_replacement` 在 `record_replace.py` 中用于执行范围受控的恢复、撤销或清理。
- **_promotion**：`_promotion` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。
- **_replace_lock**：`_replace_lock` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。

### ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append 相关职责

- **ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append**：`ManagementSchemaPersi...` 是 `tests/test_management_agent.py` 第 111-113 行定义的函数，本页绑定该固定源码范围。
- **query_graph**：`query_graph` 是源码中负责构造职责关系图并提供职责群或路径查询的命名代码单元。
- **_retrieve_machine_deterministic**：`_retrieve_machine_det...` 是第 1077-1556 行的函数，供所属页面定位实现。
- **build_machine_knowledge**：`build_machine_knowledge` 是第 354-613 行的函数，供所属页面定位实现。
- **_powershell_command.quote**：`_powershell_command.q...` 是第 45-46 行的函数，供所属页面定位实现。
- **project_graphify**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **CodeKnowledgeBuilderTests.test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server**：`CodeKnowledgeBuilderT...` 是第 600-687 行的函数，供所属页面定位实现。
- **audit_graphify**：该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。

### bind_conversation 相关职责

- **bind_conversation**：`bind_conversation` 位于 `scripts/ckb_core/management_agent.py` 第 453-568 行，本页用固定源码范围说明它如何完成管理对话绑定、任务派发和审阅上下文中的局部职责。
- **ManagementBindingLifecycleTest**：`ManagementBindingLife...` 是第 128-470 行的类，供所属页面定位实现。
- **ManagementSchemaPersistenceTest**：`ManagementSchemaPersi...` 是第 49-125 行的类，供所属页面定位实现。
- **create_management_task**：`create_management_task` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。
- **review_management_task**：`review_management_task` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。
- **unbind_conversation**：`unbind_conversation` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。
- **audit_manager_registry**：`audit_manager_registry` 在 `management_agent.py` 中用于校验输入、状态、证据或输出合同。
- **management_context**：`management_context` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。

### parse_file 相关职责

- **parse_file**：`parse_file` 是 `scripts/ckb_core/parsers.py` 第 272-430 行定义的函数，本页绑定该固定源码范围。
- **deployment_plan**：`deployment_plan` 是 `scripts/ckb_core/runtime.py` 中负责根据锁定运行时清单生成所需组件、来源和部署动作的函数。
- **bind_reference**：`bind_reference` 是 `tests/fixtures/cpp-parser-scons/reference-direct-init-valid.cpp` 第 3-6 行定义的函数，本页绑定该固定源码范围。
- **CppParserAndSconsTests**：`CppParserAndSconsTests` 是第 2235-2334 行的类，供所属页面定位实现。
- **LspClient**：`LspClient` 是第 258-368 行的类，供所属页面定位实现。
- **collect_semantics**：`collect_semantics` 是第 489-618 行的函数，供所属页面定位实现。
- **DependencyError**：处理 `dependencyerror` 对应的数据与约束。
- **_fallback_flags**：`_fallback_flags` 是第 433-460 行的函数，供所属页面定位实现。

### retrieve_machine 相关职责

- **retrieve_machine**：`retrieve_machine` 是 `scripts/ckb_core/machine_knowledge.py` 第 1600-1709 行定义的函数，本页绑定该固定源码范围。
- **run_keyword_provider**：`run_keyword_provider` 是 `scripts/ckb_core/keyword_fallback.py` 第 380-461 行定义的函数，本页绑定该固定源码范围。
- **KeywordFallbackRetrievalWiringTests**：`KeywordFallbackRetrie...` 是 `tests/test_keyword_fallback.py` 第 198-349 行定义的类，本页绑定该固定源码范围。
- **run_keyword_benchmark**：`run_keyword_benchmark` 是 `scripts/ckb_core/keyword_benchmark.py` 第 139-227 行定义的函数，本页绑定该固定源码范围。
- **keyword_provider_config**：`keyword_provider_config` 位于 `scripts/ckb.py` 第 270-290 行，本页用固定源码范围说明它如何完成CKB 主命令解析、分发和退出状态中的局部职责。
- **KeywordFallbackAdapterTests**：`KeywordFallbackAdapte...` 是第 106-195 行的类，供所属页面定位实现。
- **KeywordProviderConfig**：`KeywordProviderConfig` 是第 81-90 行的类，供所属页面定位实现。
- **KeywordFallbackSchemaTests**：`KeywordFallbackSchema...` 是第 61-103 行的类，供所属页面定位实现。

### QueryTermsTests 相关职责

- **QueryTermsTests**：`QueryTermsTests` 是 `tests/test_query_terms.py` 第 25-107 行定义的类，本页绑定该固定源码范围。
- **search_terms**：`search_terms` 是 `scripts/ckb_core/query_terms.py` 第 65-69 行定义的函数，本页绑定该固定源码范围。
- **build_manual_index**：`build_manual_index` 位于 `tests/benchmark_chinese_retrieval.py` 第 111-154 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **fts_query_terms**：`fts_query_terms` 是第 77-81 行的函数，供所属页面定位实现。
- **run_benchmark**：`run_benchmark` 是第 285-386 行的函数，供所属页面定位实现。
- **build_fts_query**：`build_fts_query` 是第 84-88 行的函数，供所属页面定位实现。
- **index_terms**：`index_terms` 是第 72-74 行的函数，供所属页面定位实现。
- **_ranked_terms**：`_ranked_terms` 是第 31-62 行的函数，供所属页面定位实现。

### LspClient.stop 相关职责

- **LspClient.stop**：`LspClient.stop` 是第 352-368 行的函数，供所属页面定位实现。
- **normalize_event**：`normalize_event` 是第 479-549 行的函数，供所属页面定位实现。
- **activate_skill_session**：`activate_skill_session` 是第 925-967 行的函数，供所属页面定位实现。
- **_process_event**：`_process_event` 是第 1215-1301 行的函数，供所属页面定位实现。
- **_create_pending_review**：`_create_pending_review` 是第 1139-1212 行的函数，供所属页面定位实现。
- **_record_skill_activation**：`_record_skill_activation` 是第 868-905 行的函数，供所属页面定位实现。
- **default_registry_path**：`default_registry_path` 是第 127-129 行的函数，供所属页面定位实现。
- **_canonical_type**：`_canonical_type` 是第 416-463 行的函数，供所属页面定位实现。

### parser 相关职责

- **parser**：`parser` 位于 `scripts/ckb.py` 第 303-853 行，本页用固定源码范围说明它如何解析、规范化并冻结调用输入。
- **package_showcase**：`package_showcase` 是源码中负责构建可复现发行归档并复核成员集合的命名代码单元。
- **main**：`main` 是 `tests/session_stdio_harness_probe.py` 第 16-30 行定义的函数，本页绑定该固定源码范围。
- **add_initial_arguments**：`add_initial_arguments` 在 `ckb.py` 中用于完成CKB 主命令解析、分发和退出状态中的局部职责。
- **sample**：`sample` 在 `sample.py` 中用于验证目标行为、失败分类和回归边界。
- **build_core**：`build_core` 是第 122-185 行的函数，供所属页面定位实现。
- **add_git_bootstrap_arguments**：`add_git_bootstrap_arguments` 在 `ckb.py` 中用于完成CKB 主命令解析、分发和退出状态中的局部职责。
- **add_keyword_provider_arguments**：`add_keyword_provider_arguments` 在 `ckb.py` 中用于完成CKB 主命令解析、分发和退出状态中的局部职责。

### load_page_config 相关职责

- **load_page_config**：`load_page_config` 是源码中负责规范化并校验不可漂移的页面配置的命名代码单元。
- **KeywordFallbackAdapterTests.config**：`KeywordFallbackAdapte...` 是第 115-124 行的函数，供所属页面定位实现。
- **project_logseq**：投影 `logseq` 对应的数据与约束。
- **SourceLinkRenderer**：复用已验证配置和路径缓存，为多个实体生成可点击的本地源码链接。
- **_audit_markdown**：审计 `markdown` 对应的数据与约束。
- **page_config_sha256**：该附属代码负责规范化并校验不可漂移的页面配置，并把结果交给所属页面中的主流程使用。
- **normalize_page_config**：该附属代码负责规范化并校验不可漂移的页面配置，并把结果交给所属页面中的主流程使用。
- **_logseq_count**：处理 `count` 对应的数据与约束。

### ScopeExtensionTest 相关职责

- **ScopeExtensionTest**：`ScopeExtensionTest` 是 `tests/test_scope_extension.py` 第 63-418 行定义的类，本页绑定该固定源码范围。
- **start_scope_extension**：`start_scope_extension` 是 `scripts/ckb_core/scope_extension.py` 第 261-451 行定义的函数，本页绑定该固定源码范围。
- **preflight**：`preflight` 是 `scripts/ckb_core/gitrepo.py` 第 194-217 行定义的函数，本页绑定该固定源码范围。
- **_tree_manifest**：`_tree_manifest` 是第 57-72 行的函数，供所属页面定位实现。
- **audit_scope_extension**：`audit_scope_extension` 是第 598-692 行的函数，供所属页面定位实现。
- **cutover_scope_extension**：`cutover_scope_extension` 是第 699-804 行的函数，供所属页面定位实现。
- **ScopeExtensionTest.add_preserved_layers**：`ScopeExtensionTest.ad...` 是第 93-192 行的函数，供所属页面定位实现。
- **rollback_scope_extension**：`rollback_scope_extension` 是第 821-908 行的函数，供所属页面定位实现。

### _inspect_knowledge_project 相关职责

- **_inspect_knowledge_project**：`_inspect_knowledge_pr...` 是第 663-885 行的函数，供所属页面定位实现。
- **_knowledge_project_audit**：`_knowledge_project_audit` 是第 1292-1424 行的函数，供所属页面定位实现。
- **_validate_recovery_topology**：`_validate_recovery_to...` 是第 593-634 行的函数，供所属页面定位实现。
- **_object**：`_object` 是第 205-208 行的函数，供所属页面定位实现。
- **_reject_unknown**：`_reject_unknown` 是第 199-202 行的函数，供所属页面定位实现。
- **_origin_health**：`_origin_health` 是第 397-491 行的函数，供所属页面定位实现。
- **_project_operation_id**：`_project_operation_id` 是第 576-586 行的函数，供所属页面定位实现。
- **_validate_structural_manifest**：`_validate_structural_...` 是第 327-373 行的函数，供所属页面定位实现。

### audit_global 相关职责

- **audit_global**：`audit_global` 位于 `scripts/ckb_core/pipeline.py` 第 2891-3204 行，本页用固定源码范围说明它如何校验输入、状态、证据或输出合同。
- **utc_now**：处理 `now` 对应的数据与约束。
- **audit_chunk**：审计 `chunk` 对应的数据与约束。
- **review_pack**：处理 `pack` 对应的数据与约束。
- **AuditError**：处理 `auditerror` 对应的数据与约束。
- **build_chunk**：构建 `chunk` 对应的数据与约束。
- **write_marker**：写入 `marker` 对应的数据与约束。
- **review_chunk**：处理 `chunk` 对应的数据与约束。

### _logical_projection 相关职责

- **_logical_projection**：处理 `projection` 对应的数据与约束。
- **refresh_human_navigation**：刷新 `human_navigation` 对应的数据与约束。
- **project_markdown**：投影 `markdown` 对应的数据与约束。
- **build_context**：构建 `context` 对应的数据与约束。
- **_normalized_edn_document**：处理 `edn_document` 对应的数据与约束。
- **_render_markdown_page**：渲染 `markdown_page` 对应的数据与约束。
- **_canonical_page_context**：处理 `page_context` 对应的数据与约束。
- **_logical_context_budgets**：处理 `context_budgets` 对应的数据与约束。

### audit_migration 相关职责

- **audit_migration**：`audit_migration` 是 `scripts/ckb_core/migration.py` 第 367-479 行定义的函数，本页绑定该固定源码范围。
- **MigrationTest**：`MigrationTest` 构造连续两个源码提交和迁移前后知识库。
- **sha256_file**：处理 `file` 对应的数据与约束。
- **migrate_output**：`migrate_output` 是第 253-364 行的函数，供所属页面定位实现。
- **relink_preserved_notes**：`relink_preserved_notes` 是第 487-581 行的函数，供所属页面定位实现。
- **_preserve_mutable_layers**：`_preserve_mutable_layers` 是第 114-181 行的函数，供所属页面定位实现。
- **_replace_review_packs**：`_replace_review_packs` 是第 199-250 行的函数，供所属页面定位实现。
- **MigrationTest.test_exact_blob_facts_and_agent_reviews_are_reused**：验证精确 blob 与中文审阅复用、可变层基线、目录提升后的路径重定位及篡改失败门。

### main 相关职责

- **main**：`main` 位于 `scripts/ckb.py` 第 900-1637 行，本页用固定源码范围说明它如何编排命令入口、执行顺序和退出结果。
- **_Transport.close**：`_Transport.close` 是 `scripts/ckb_core/session_stdio.py` 第 457-496 行定义的函数，本页绑定该固定源码范围。
- **execute**：`execute` 是 `tests/provider_integration.py` 第 19-24 行定义的函数，本页绑定该固定源码范围。
- **SourceLinkRenderer.uri**：`SourceLinkRenderer.uri` 将仓库内源码位置编码为编辑器可打开的 URI。
- **retrieve**：`retrieve` 是 `scripts/ckb_core/agent_index.py` 第 426-554 行定义的函数，本页绑定该固定源码范围。
- **serve_stdio**：`serve_stdio` 是 `scripts/ckb_core/stdio_server.py` 第 202-391 行定义的函数，本页绑定该固定源码范围。
- **doctor_report**：`doctor_report` 是 `scripts/ckb_core/providers.py` 第 76-240 行定义的函数，本页绑定该固定源码范围。
- **CodeKnowledgeBuilderTests.test_markdown_whole_repository_and_completion_gate**：`CodeKnowledgeBuilderT...` 是第 1145-1689 行的函数，供所属页面定位实现。

### ingest_event 相关职责

- **ingest_event**：`ingest_event` 是 `scripts/ckb_core/automation.py` 第 1394-1504 行定义的函数，本页绑定该固定源码范围。
- **AutomationTest.register**：`AutomationTest.register` 是 `tests/test_automation.py` 第 78-80 行定义的函数，本页绑定该固定源码范围。
- **AutomationTest**：`AutomationTest` 是第 48-885 行的类，供所属页面定位实现。
- **automation_status**：`automation_status` 是第 1507-1534 行的函数，供所属页面定位实现。
- **register_project**：`register_project` 是第 174-246 行的函数，供所属页面定位实现。
- **pending_automation_reviews**：`pending_automation_re...` 是第 1537-1559 行的函数，供所属页面定位实现。
- **AutomationTest.test_nested_untracked_project_bounds_git_status_and_uses_project_relative_paths**：`AutomationTest.test_n...` 是第 291-354 行的函数，供所属页面定位实现。
- **AutomationTest.test_redaction_idempotency_change_capture_and_pending_review**：`AutomationTest.test_r...` 是第 199-258 行的函数，供所属页面定位实现。

### command 相关职责

- **command**：`command` 是 `tests/e2e_knowledge_batch_migration.py` 第 42-65 行定义的函数，本页绑定该固定源码范围。
- **render_integration**：`render_integration` 是 `scripts/ckb_core/automation_integrations.py` 第 432-574 行定义的函数，本页绑定该固定源码范围。
- **emit**：`emit` 位于 `scripts/ckb.py` 第 859-862 行，本页用固定源码范围说明它如何生成稳定排序的结构化表示或人类输出。
- **_opencode_v2_plugin**：`_opencode_v2_plugin` 是第 295-388 行的函数，供所属页面定位实现。
- **_codex_windows_bridge**：`_codex_windows_bridge` 是第 65-78 行的函数，供所属页面定位实现。
- **_commands**：`_commands` 是第 35-41 行的函数，供所属页面定位实现。
- **_cursor_hooks**：`_cursor_hooks` 是第 191-211 行的函数，供所属页面定位实现。
- **_opencode_stable_plugin**：`_opencode_stable_plugin` 是第 214-292 行的函数，供所属页面定位实现。

### audit_human_maintenance_delivery 相关职责

- **audit_human_maintenance_delivery**：`audit_human_maintenance_delivery` 用于完成局部输入校验、转换或状态更新。
- **validate_human_maintenance_invocation**：`validate_human_maintenance_invocati…` 用于完成局部输入校验、转换或状态更新。
- **HumanMaintenancePromptValidationTests**：`HumanMaintenancePromptValidationTes…` 用于完成局部输入校验、转换或状态更新。
- **HumanMaintenanceDeliveryAuditTests**：`HumanMaintenanceDeliveryAuditTests` 用于完成局部输入校验、转换或状态更新。
- **human_maintenance_delivery_template**：`human_maintenance_delivery_template` 用于完成局部输入校验、转换或状态更新。
- **HumanMaintenancePromptCliTests**：`HumanMaintenancePromptCliTests` 用于完成局部输入校验、转换或状态更新。
- **_valid_maintain_summary**：`_valid_maintain_summary` 用于完成局部输入校验、转换或状态更新。
- **_knowledge_snapshot**：`_knowledge_snapshot` 在 `management_agent.py` 中用于完成管理对话绑定、任务派发和审阅上下文中的局部职责。

### ActionContract 相关职责

- **ActionContract**：`ActionContract` 用于完成局部输入校验、转换或状态更新。
- **_acceptance_template**：`_acceptance_template` 用于完成局部输入校验、转换或状态更新。
- **human_maintenance_action_document**：`human_maintenance_action_document` 用于完成局部输入校验、转换或状态更新。
- **render_step_command**：`render_step_command` 在 `human_maintenance_prompts.py` 中用于生成稳定排序的结构化表示或人类输出。
- **CommandStep**：`CommandStep` 在 `human_maintenance_prompts.py` 中用于编排命令入口、执行顺序和退出结果。
- **active_command_steps**：`active_command_steps` 在 `human_maintenance_prompts.py` 中用于编排命令入口、执行顺序和退出结果。
- **_effective_requirement_state**：`_effective_requirement_state` 用于完成局部输入校验、转换或状态更新。
- **_effective_rollback_mapping_and_command**：`_effective_rollback_mapping_and_com…` 用于完成局部输入校验、转换或状态更新。

### create_knowledge_batch_plan 相关职责

- **create_knowledge_batch_plan**：`create_knowledge_batc...` 是 `scripts/ckb_core/knowledge_batch_migration.py` 第 888-956 行定义的函数，本页绑定该固定源码范围。
- **KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures.refresh**：`KnowledgeBatchWorkflo...` 是 `tests/test_knowledge_batch_migration.py` 第 468-476 行定义的函数，本页绑定该固定源码范围。
- **KnowledgeBatchWorkflowTests**：`KnowledgeBatchWorkflo...` 是第 127-701 行的类，供所属页面定位实现。
- **apply_knowledge_batch_plan**：`apply_knowledge_batch...` 是第 1506-1552 行的函数，供所属页面定位实现。
- **KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures**：`KnowledgeBatchWorkflo...` 是第 457-575 行的函数，供所属页面定位实现。
- **KnowledgeBatchWorkflowTests.test_two_projects_isolate_partial_apply_cutover_and_subset_rollback**：`KnowledgeBatchWorkflo...` 是第 391-455 行的函数，供所属页面定位实现。
- **resume_knowledge_batch_state**：`resume_knowledge_batc...` 是第 1555-1561 行的函数，供所属页面定位实现。
- **KnowledgeBatchWorkflowTests._project_document**：`KnowledgeBatchWorkflo...` 是第 199-254 行的函数，供所属页面定位实现。

### RecordReplaceTests 相关职责

- **RecordReplaceTests**：`RecordReplaceTests` 位于 `tests/test_record_replace.py` 第 69-372 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **_owned_snapshot**：`_owned_snapshot` 在 `test_record_replace.py` 中用于验证目标行为、失败分类和回归边界。
- **RecordReplaceTests._replace**：`_replace` 在 `test_record_replace.py` 中用于验证目标行为、失败分类和回归边界。
- **make_repo**：`make_repo` 是第 95-168 行的函数，供所属页面定位实现。
- **RecordReplaceTests.setUpClass**：`setUpClass` 在 `test_record_replace.py` 中用于验证目标行为、失败分类和回归边界。
- **RecordReplaceTests.test_candidate_mirror_mismatch_blocks_promotion**：`test_candidate_mirror_mismatch_bloc…` 用于完成局部输入校验、转换或状态更新。
- **RecordReplaceTests.test_promotion_failure_restores_all_roles_and_leaves_no_sqlite_sidecars**：`test_promotion_failure_restores_all…` 用于完成局部输入校验、转换或状态更新。
- **RecordReplaceTests.test_replace_updates_every_role_and_rollback_is_exact_and_idempotent**：`test_replace_updates_every_role_and…` 用于完成局部输入校验、转换或状态更新。

### _cutover_one 相关职责

- **_cutover_one**：`_cutover_one` 是第 1721-1880 行的函数，供所属页面定位实现。
- **rollback_knowledge_batch_state**：`rollback_knowledge_ba...` 是第 2035-2075 行的函数，供所属页面定位实现。
- **_rollback_one**：`_rollback_one` 是第 1926-2032 行的函数，供所属页面定位实现。
- **cutover_knowledge_batch_state**：`cutover_knowledge_bat...` 是第 1883-1923 行的函数，供所属页面定位实现。
- **audit_knowledge_batch_state**：`audit_knowledge_batch...` 是第 1623-1679 行的函数，供所属页面定位实现。
- **_apply_one_project**：`_apply_one_project` 是第 1427-1503 行的函数，供所属页面定位实现。
- **_state_event**：`_state_event` 是第 1010-1029 行的函数，供所属页面定位实现。
- **knowledge_batch_status**：`knowledge_batch_status` 是第 1564-1620 行的函数，供所属页面定位实现。

### audit_operation_journal 相关职责

- **audit_operation_journal**：`audit_operation_journal` 位于 `scripts/ckb_core/operation_journal.py` 第 385-454 行，本页用固定源码范围说明它如何校验输入、状态、证据或输出合同。
- **record_operation**：`record_operation` 在 `operation_journal.py` 中用于完成该文件所属能力的输入、状态、输出和失败边界中的局部职责。
- **_operation_type**：`_operation_type` 在 `operation_journal.py` 中用于完成该文件所属能力的输入、状态、输出和失败边界中的局部职责。
- **record_cli_operation**：`record_cli_operation` 用于完成局部输入校验、转换或状态更新。
- **CodeKnowledgeBuilderTests.test_bounded_machine_operation_journal_is_private_deduplicated_and_audited**：`CodeKnowledgeBuilderT...` 是第 224-276 行的函数，供所属页面定位实现。
- **_read_shard**：`_read_shard` 在 `operation_journal.py` 中用于读取、规范化并返回既有状态。
- **_latest_summary**：`_latest_summary` 在 `operation_journal.py` 中用于完成该文件所属能力的输入、状态、输出和失败边界中的局部职责。
- **_state**：`_state` 在 `operation_journal.py` 中用于完成该文件所属能力的输入、状态、输出和失败边界中的局部职责。

### initialize 相关职责

- **initialize**：`initialize` 在 `pipeline.py` 中用于完成源码审阅 pack、提交、审计和生成流水线中的局部职责。
- **StaleSourceError**：处理 `stalesourceerror` 对应的数据与约束。
- **_load_state**：加载 `state` 对应的数据与约束。
- **prepare_git_repository**：准备 `git_repository` 对应的数据与约束。
- **_relocate_completed_output**：处理 `completed_output` 对应的数据与约束。
- **assert_source_snapshot**：处理 `source_snapshot` 对应的数据与约束。
- **_resolve_entries**：解析并确定 `entries` 对应的数据与约束。
- **create_source_snapshot**：创建 `source_snapshot` 对应的数据与约束。

> 为保持阅读节奏，这里只展开最主要的职责群；图查询仍会使用完整关系。

## 围绕任务继续缩小范围

```powershell
& PYTHON scripts\ckb.py query --out OUTPUT "职责关键词" --budget 1500
& PYTHON scripts\ckb.py path --out OUTPUT "起点类或函数" "目标类或函数"
& PYTHON scripts\ckb.py explain --out OUTPUT "类名、函数名或职责关键词"
```

查询会先选择与问题最相关的代码，再沿真实关系扩展到预算允许的范围。
