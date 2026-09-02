# CodeKnowledgeBuilderTests 等测试场景

标签：#类型/代码

> 文件 `tests/test_ckb.py`负责验证 CKB 核心构建、检索、投影、参考资料、运行时和 C++ 语法边界。 它属于项目主要公开合同的综合回归保护，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当任何核心命令、生成协议、运行时边界或跨模块行为变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：tests/test_ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb.py:1:1)  `tests/test_ckb.py:1-2467`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 主要代码单元是 [[CodeKnowledgeBuilderTests]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[doctor_report 与 _version_matches 的协作实现]]。
- 实现时会用到 [[parse_file]]。
- 实现时会用到 [[parser]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.register]] 关联到这里的验证场景。
- [[CanvasContractTests]] 关联到这里的验证场景。
- [[PdfReferenceExtractionTests 等测试场景]] 会使用这里提供的行为。
- [[RecordReplaceTests]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 关联到这里的验证场景。
- [[append 等测试场景]] 关联到这里的验证场景。
- [[assertions]] 关联到这里的验证场景。
- [[audit_agent_protocol]] 关联到这里的验证场景。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 关联到这里的验证场景。
- [[audit_feedback]] 关联到这里的验证场景。
- [[audit_feedback 与 _contains_chinese 的协作实现]] 关联到这里的验证场景。
- [[audit_gap_register 与 _root 的协作实现]] 关联到这里的验证场景。
- [[audit_migration]] 关联到这里的验证场景。
- [[audit_migration 与 _entity_key 的协作实现]] 关联到这里的验证场景。
- [[audit_obsidian]] 关联到这里的验证场景。
- [[audit_obsidian 与 prepare_vault 的协作实现]] 关联到这里的验证场景。
- [[audit_output_contract]] 关联到这里的验证场景。
- [[audit_output_contract 与 _default_ckb 的协作实现]] 关联到这里的验证场景。
- [[audit_work_record_index]] 关联到这里的验证场景。
- [[audit_work_record_index 与 _contains_chinese 的协作实现]] 关联到这里的验证场景。
- [[bind_conversation]] 关联到这里的验证场景。
- [[check_fact_freshness 与 _root 的协作实现]] 关联到这里的验证场景。
- [[contracts 的协作边界（623c049c）]] 关联到这里的验证场景。
- [[debug_value 等测试场景]] 关联到这里的验证场景。
- [[doctor_report 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[extract_pdf 与 PdfExtractionError 的协作实现]] 关联到这里的验证场景。
- [[finalize]] 关联到这里的验证场景。
- [[finalize 与 _replace_output_prefix 的协作实现]] 关联到这里的验证场景。
- [[ingest]] 关联到这里的验证场景。
- [[ingest_event 与 default_registry_path 的协作实现]] 关联到这里的验证场景。
- [[ingest_reference 与 _root 的协作实现]] 关联到这里的验证场景。
- [[keyword_provider_config 与 parser 的协作实现]] 关联到这里的验证场景。
- [[load_page_config 与 _merge_known 的协作实现]] 关联到这里的验证场景。
- [[module_name]] 关联到这里的验证场景。
- [[module_name 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[parse_file]] 关联到这里的验证场景。
- [[parse_file 与 _language 的协作实现]] 关联到这里的验证场景。
- [[parser]] 关联到这里的验证场景。
- [[preflight]] 关联到这里的验证场景。
- [[preflight 与 git 的协作实现]] 关联到这里的验证场景。
- [[query_graph 与 _networkx_modules 的协作实现]] 关联到这里的验证场景。
- [[record_note]] 关联到这里的验证场景。
- [[record_note 与 page_tag 的协作实现]] 关联到这里的验证场景。
- [[refresh]] 关联到这里的验证场景。
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]] 关联到这里的验证场景。
- [[retrieve]] 关联到这里的验证场景。
- [[retrieve 与 _tokens 的协作实现]] 关联到这里的验证场景。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[sample 等测试场景]] 关联到这里的验证场景。
- [[search_terms]] 关联到这里的验证场景。
- [[search_terms 与 _split_camel 的协作实现]] 关联到这里的验证场景。
- [[source_value]] 关联到这里的验证场景。
- [[source_value 等测试场景]] 关联到这里的验证场景。
- [[start_scope_extension 与 _error 的协作实现]] 关联到这里的验证场景。
- [[sync_human_layer]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[PdfReferenceExtractionTests 等测试场景]]
- [[RecordReplaceTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 17 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `invoke` | `invoke` 完成CKB 核心合同回归验证中的一个明确步骤。 |
| `write` | `write` 生成并写入CKB 核心合同回归验证所需的数据或状态。 |
| `git` | `git` 完成CKB 核心合同回归验证中的一个明确步骤。 |
| `make_repo` | `make_repo` 完成CKB 核心合同回归验证中的一个明确步骤。 |
| `review_all` | `review_all` 完成CKB 核心合同回归验证中的一个明确步骤。 |
| `CppParserAndSconsTests` | `setUp` 完成CKB 核心合同回归验证中的一个明确步骤。 |
| `CppParserAndSconsTests.setUp` | `setUp` 完成CKB 核心合同回归验证中的一个明确步骤。 |
| `CppParserAndSconsTests.tearDown` | `tearDown` 完成CKB 核心合同回归验证中的一个明确步骤。 |
| `CppParserAndSconsTests.parse_fixture` | `parse_fixture` 解析并归一化CKB 核心合同回归验证所需的数据或状态。 |
| `CppParserAndSconsTests.test_cpp_conditional_compilation_valid_and_incomplete` | 该测试验证“cpp conditional compilation v…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CppParserAndSconsTests.test_cpp_reference_direct_initialization_is_declaration_not_function` | 该测试验证“cpp reference direct initiali…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CppParserAndSconsTests.test_cpp_explicit_template_instantiation_has_no_pseudo_entities` | 该测试验证“cpp explicit template instant…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CppParserAndSconsTests.test_cpp_local_diagnostic_contract_marks_only_affected_ranges_and_blocks_broad_errors` | 该测试验证“cpp local diagnostic contract…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CppParserAndSconsTests.test_cpp_parser_dependency_and_root_unavailable_still_fail` | 该测试验证“cpp parser dependency and roo…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CppParserAndSconsTests.test_cpp_local_warning_reaches_status_machine_index_and_brief` | 该测试验证“cpp local warning reaches sta…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CppParserAndSconsTests.test_cpp_broad_syntax_error_still_blocks_syntax_stage` | 该测试验证“cpp broad syntax error still …”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |
| `CppParserAndSconsTests.test_scons_fallback_is_auditable_and_compile_database_stays_exact` | 该测试验证“scons fallback is auditable a…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。 |

</details>
