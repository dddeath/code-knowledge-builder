# KeywordFallbackRetrievalWiringTests 等测试场景

标签：#类型/代码

> 文件 `tests/test_keyword_fallback.py`负责验证显式关键词慢路径的校验、缓存、失败回退和检索接线。 它属于LLM 关键词备选能力的回归保护，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当Provider 输入、触发、缓存或回退规则变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：tests/test_keyword_fallback.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_keyword_fallback.py:1:1)  `tests/test_keyword_fallback.py:1-469`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 主要代码单元是 [[KeywordFallbackRetrievalWiringTests]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[ingest_event]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run_keyword_benchmark]]。
- 实现时会用到 [[run_keyword_provider]]。
- 实现时会用到 [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.register 等测试场景]] 会使用这里提供的行为。
- [[ChineseRetrievalEffectRetestFixtureTests]] 会使用这里提供的行为。
- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[FactFreshnessStateMachineTest]] 会使用这里提供的行为。
- [[FactFreshnessStateMachineTest 等测试场景]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests]] 会使用这里提供的行为。
- [[MigrationTest]] 会使用这里提供的行为。
- [[SourceLinkRenderer.uri]] 会使用这里提供的行为。
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 关联到这里的验证场景。
- [[append 等测试场景]] 会使用这里提供的行为。
- [[audit_feedback 与 _contains_chinese 的协作实现]] 关联到这里的验证场景。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[audit_obsidian]] 会使用这里提供的行为。
- [[audit_obsidian 与 prepare_vault 的协作实现]] 会使用这里提供的行为。
- [[command 等测试场景]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[deploy 的协作边界]] 会使用这里提供的行为。
- [[doctor_report 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[finalize]] 关联到这里的验证场景。
- [[finalize 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[ingest_event]] 关联到这里的验证场景。
- [[keyword_provider_config]] 会使用这里提供的行为。
- [[keyword_provider_config 与 parser 的协作实现]] 会使用这里提供的行为。
- [[load_page_config]] 会使用这里提供的行为。
- [[load_page_config 与 _merge_known 的协作实现]] 会使用这里提供的行为。
- [[main 等测试场景（provider_integration 测试）]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[main（generate_large_fixture 测试）]] 会使用这里提供的行为。
- [[module_name 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[package_showcase]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[preflight 与 git 的协作实现]] 会使用这里提供的行为。
- [[refresh 等测试场景]] 会使用这里提供的行为。
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 关联到这里的验证场景。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[run 等测试场景]] 会使用这里提供的行为。
- [[run_failure_probe]] 会使用这里提供的行为。
- [[run_failure_probe 等测试场景]] 会使用这里提供的行为。
- [[run_keyword_benchmark]] 关联到这里的验证场景。
- [[run_keyword_benchmark 与 _text_list 的协作实现]] 关联到这里的验证场景。
- [[run_keyword_provider]] 关联到这里的验证场景。
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]] 会使用这里提供的行为。
- [[serve_stdio 与 _write_line 的协作实现]] 会使用这里提供的行为。
- [[start_scope_extension]] 会使用这里提供的行为。
- [[sync_human_layer]] 会使用这里提供的行为。
- 可从 [[tests 职责导览]] 进入本页。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[CanvasContractTests]]
- [[CanvasContractTests 等测试场景]]
- [[CanvasDeterminismTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 19 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `fixture_output` | `fixture_output` 完成关键词慢路径测试所需的一个明确步骤。 |
| `KeywordFallbackSchemaTests` | 该测试验证“canonical fixture output is b…”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackSchemaTests.test_canonical_fixture_output_is_bounded_and_normalized` | 该测试验证“canonical fixture output is b…”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackSchemaTests.test_invalid_json_is_rejected` | 该测试验证“invalid json is rejected”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackSchemaTests.test_oversized_duplicate_injected_and_invalid_candidates_are_rejected` | 该测试验证“oversized duplicate injected …”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackSchemaTests.test_canonical_failure_types_are_preserved_without_candidates` | 该测试验证“canonical failure types are p…”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackSchemaTests.test_chinese_retrieval_replay_is_keyed_by_the_canonical_input_hash` | 该测试验证“chinese retrieval replay is k…”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackAdapterTests` | `setUp` 完成关键词慢路径测试所需的一个明确步骤。 |
| `KeywordFallbackAdapterTests.setUp` | `setUp` 完成关键词慢路径测试所需的一个明确步骤。 |
| `KeywordFallbackAdapterTests.tearDown` | `tearDown` 完成关键词慢路径测试所需的一个明确步骤。 |
| `KeywordFallbackAdapterTests.config` | `config` 完成关键词慢路径测试所需的一个明确步骤。 |
| `KeywordFallbackAdapterTests.run_mode` | `run_mode` 完成关键词慢路径测试所需的一个明确步骤。 |
| `KeywordFallbackAdapterTests.test_command_adapter_caches_only_validated_output_under_identity_key` | 该测试验证“command adapter caches only v…”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackAdapterTests.test_invalid_json_output_and_process_failures_fall_back` | 该测试验证“invalid json output and proce…”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackAdapterTests.test_timeout_is_bounded_and_retried_at_most_once` | 该测试验证“timeout is bounded and retrie…”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackAdapterTests.test_missing_credentials_prevents_process_start` | 该测试验证“missing credentials prevents …”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackAdapterTests.test_cache_audit_rejects_secret_shaped_content` | 该测试验证“cache audit rejects secret sh…”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackBenchmarkTests` | 该测试验证“fixed benchmark compares qual…”场景，保护关键词慢路径测试的结果与失败边界。 |
| `KeywordFallbackBenchmarkTests.test_fixed_benchmark_compares_quality_latency_context_usage_and_restores_cache` | 该测试验证“fixed benchmark compares qual…”场景，保护关键词慢路径测试的结果与失败边界。 |

</details>
