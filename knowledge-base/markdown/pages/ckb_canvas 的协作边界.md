# ckb_canvas 的协作边界

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **StrictParser.error**：位于 `prototypes/ckb-canvas-skill/scripts/ckb_canvas.py:24-25`。
- **_parser**：位于 `prototypes/ckb-canvas-skill/scripts/ckb_canvas.py:28-45`。
- **main**：位于 `prototypes/ckb-canvas-skill/scripts/ckb_canvas.py:53-100`。

## 相关代码

- 实现时会用到 [[benchmark 的协作边界（16d95d34）]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[commands 的协作边界]]。
- 实现时会用到 [[contracts 的协作边界（prototypes）]]。
- 实现时会用到 [[parser]]。
- 实现时会用到 [[validate]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[HumanMaintenancePromptRegistryTests 等测试场景]] 会使用这里提供的行为。
- [[HumanPageTemplateRegistryTests]] 会使用这里提供的行为。
- [[HumanPageTemplateRegistryTests 等测试场景]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 会使用这里提供的行为。
- [[ScopeExtensionOfferTests.retrieval 等测试场景]] 会使用这里提供的行为。
- [[_Transport.close]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[append 等测试场景]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[audit_feedback 与 _contains_chinese 的协作实现]] 会使用这里提供的行为。
- [[benchmark 的协作边界（e30cfb0a）]] 会使用这里提供的行为。
- [[bind_conversation]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[check_fact_freshness]] 会使用这里提供的行为。
- [[check_fact_freshness 与 _root 的协作实现]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[doctor_report 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[finalize 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[get_human_page_template 与 SectionContract 的协作实现]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[keyword_provider_config 与 parser 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check 与 capability_matrix 的协作实现]] 会使用这里提供的行为。
- [[main（build_runtime_payload 实现）]] 会使用这里提供的行为。
- [[parse_file 与 _language 的协作实现]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[propose_template 与 _canonical_bytes 的协作实现]] 会使用这里提供的行为。
- [[render_integration 与 harness_retrieval_contract 的协作实现]] 会使用这里提供的行为。
- [[render_page_author 与 _error 的协作实现]] 会使用这里提供的行为。
- [[replace_note]] 会使用这里提供的行为。
- [[run_benchmark 等测试场景]] 会使用这里提供的行为。
- [[run_keyword_benchmark]] 会使用这里提供的行为。
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]] 会使用这里提供的行为。
- [[serve_stdio]] 会使用这里提供的行为。
- [[validate_human_maintenance_invocation 与 ParameterSpec 的协作实现]] 会使用这里提供的行为。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
