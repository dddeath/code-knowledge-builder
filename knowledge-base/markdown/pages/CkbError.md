# CkbError

标签：#类型/代码

> `CkbError` 是 `scripts/ckb_core/common.py` 中负责为 CKB 输入或状态错误提供固定进程退出码的类。 它按源码所示的参数、条件分支和数据结构完成为 CKB 输入或状态错误提供固定进程退出码，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当路径、时间、JSON、哈希、进程与通用错误处理的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/common.py 第 24 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:24:1)  `scripts/ckb_core/common.py:24-25`

## 相关代码

- 实现时会用到 [[contracts 的协作边界（2ef5688e）]]。

## 谁会来到这里

- [[AgentProtocolBatchApplyTests 等测试场景]] 会使用这里提供的行为。
- [[CkbError 与 DependencyError 的协作实现]] 汇总了本页。
- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[FactFreshnessStateMachineTest]] 会使用这里提供的行为。
- [[HumanMaintenancePromptRegistryTests 等测试场景]] 会使用这里提供的行为。
- [[HumanPageTemplateRegistryTests]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 会使用这里提供的行为。
- [[PdfReferenceExtractionTests]] 会使用这里提供的行为。
- [[RecordReplaceTests]] 会使用这里提供的行为。
- [[ScopeExtensionTest]] 会使用这里提供的行为。
- [[SessionStdioLifecycleTests]] 会使用这里提供的行为。
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]] 会使用这里提供的行为。
- [[TemplateProposalStoreTests]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[append 等测试场景]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[audit_feedback]] 会使用这里提供的行为。
- [[audit_feedback 与 _contains_chinese 的协作实现]] 会使用这里提供的行为。
- [[audit_gap_register 与 _root 的协作实现]] 会使用这里提供的行为。
- [[audit_migration]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[audit_obsidian]] 会使用这里提供的行为。
- [[audit_operation_journal 与 _root 的协作实现]] 会使用这里提供的行为。
- [[audit_work_record_index 与 _contains_chinese 的协作实现]] 会使用这里提供的行为。
- [[bind_conversation]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[check_fact_freshness 与 _root 的协作实现]] 会使用这里提供的行为。
- [[create_batch_plan]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[deployment_plan 与 skill_root 的协作实现]] 会使用这里提供的行为。
- [[doctor_report 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[extract_pdf]] 会使用这里提供的行为。
- [[extract_pdf 与 PdfExtractionError 的协作实现]] 会使用这里提供的行为。
- [[finalize 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[get_human_page_template]] 会使用这里提供的行为。
- [[get_human_page_template 与 SectionContract 的协作实现]] 会使用这里提供的行为。
- [[ingest_event]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[ingest_reference]] 会使用这里提供的行为。
- [[ingest_reference 与 _root 的协作实现]] 会使用这里提供的行为。
- [[keyword_provider_config]] 会使用这里提供的行为。
- [[keyword_provider_config 与 parser 的协作实现]] 会使用这里提供的行为。
- [[load_page_config]] 会使用这里提供的行为。
- [[load_page_config 与 _merge_known 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- [[maintenance_check 与 capability_matrix 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[package_showcase]] 会使用这里提供的行为。
- [[package_showcase 与 _parse_sample 的协作实现]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[preflight 与 git 的协作实现]] 会使用这里提供的行为。
- [[propose_template]] 会使用这里提供的行为。
- [[propose_template 与 _canonical_bytes 的协作实现]] 会使用这里提供的行为。
- [[query_graph]] 会使用这里提供的行为。
- [[query_graph 与 _networkx_modules 的协作实现]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[refresh 等测试场景]] 会使用这里提供的行为。
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]] 会使用这里提供的行为。
- [[render_integration]] 会使用这里提供的行为。
- [[render_page_author 与 _error 的协作实现]] 会使用这里提供的行为。
- [[replace_note]] 会使用这里提供的行为。
- [[replace_note 与 RecordReplaceLockError 的协作实现]] 会使用这里提供的行为。
- [[retrieve]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[run_keyword_benchmark 与 _text_list 的协作实现]] 会使用这里提供的行为。
- [[run_keyword_provider]] 会使用这里提供的行为。
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]] 会使用这里提供的行为。
- [[serve_stdio]] 会使用这里提供的行为。
- [[serve_stdio 与 _write_line 的协作实现]] 会使用这里提供的行为。
- [[start_scope_extension]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。
- [[start_session]] 会使用这里提供的行为。
- [[start_session 与 _session_directory 的协作实现]] 会使用这里提供的行为。
- [[sync_human_layer]] 会使用这里提供的行为。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 会使用这里提供的行为。
- [[validate_human_maintenance_invocation 与 ParameterSpec 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register]]
- [[AutomationTest.register 等测试场景]]
- [[CanvasBenchmarkContractTests]]
- [[CanvasBenchmarkContractTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
