# CkbError

标签：#类型/代码

> `CkbError` 是 `scripts/ckb_core/common.py` 中负责为 CKB 输入或状态错误提供固定进程退出码的类。 它按源码所示的参数、条件分支和数据结构完成为 CKB 输入或状态错误提供固定进程退出码，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当路径、时间、JSON、哈希、进程与通用错误处理的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/common.py 第 24 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:24:1)  `scripts/ckb_core/common.py:24-25`

## 谁会来到这里

- [[BatchProjectError]] 会使用这里提供的行为。
- 与 [[BatchProjectError 与 ProtocolRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[CkbError 与 DependencyError 的协作实现]] 汇总了本页。
- 与 [[HumanPageTemplateContract 与 SectionContract 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[KeywordFallbackOptions 与 KeywordProviderConfig 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_agent_protocol 与 _default_python 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_feedback]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_feedback 与 _contains_chinese 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_obsidian]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_work_record_index 与 _contains_chinese 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index 与 _tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[check_fact_freshness 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[close_session 与 _StartGate 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_gap]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_gap 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_knowledge_batch_plan]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[deploy]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[deploy 与 skill_root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[deploy_obsidian_plugin_to_vault]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[deploy_obsidian_plugin_to_vault 与 default_obsidian_plugin_registry 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[doctor_report 与 _version_matches 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ensure_local_openers 与 SourceLinkRenderer 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[finish_session]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[finish_session 与 _session_directory 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ingest_web_reference]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ingest_web_reference 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[init_page_author 与 _error 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[maintenance_check]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[maintenance_check 与 capability_matrix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[migrate_output]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[migrate_output 与 _entity_key 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[normalize_page_config]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[normalize_page_config 与 _merge_known 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[package_showcase]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[package_showcase 与 _parse_sample 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[parse_file]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[preflight 与 git 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[project_graphify 与 _networkx_modules 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[propose_template]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[propose_template 与 _canonical_bytes 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note 与 page_tag 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_operation]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_operation 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[render_human_maintenance_prompt]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[render_integration]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[render_integration 与 harness_retrieval_contract 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_automation]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_automation 与 default_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_management_task]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_management_task 与 default_management_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[rollback_replacement]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[rollback_replacement 与 RecordReplaceLockError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[run_keyword_benchmark 与 _text_list 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[serve_stdio]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[serve_stdio 与 _write_line 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[start_scope_extension]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[start_scope_extension 与 _error 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[sync_human_layer]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[sync_human_layer 与 _source_manifest 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[validate_pdf_extraction 与 PdfExtractionError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[validate_web_extraction]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[validate_web_extraction 与 WebSnapshotError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
