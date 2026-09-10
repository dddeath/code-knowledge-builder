# fixture_output 等测试场景

标签：#类型/代码

> 该文件验证关键词回退协议、命令适配器、缓存、检索接线和基准报告，覆盖无效候选、超时、凭据缺失、条件触发及失败保留原结果。 它以确定性提供器夹具和函数替身检查受控扩展仍由确定性检索选择，热缓存不计新用量，默认不启动模型；固定基准的增益断言仅验证评分逻辑。

## 什么时候需要修改

候选校验、身份缓存、重试与触发条件、标准输入输出选项或基准恢复规则变化时修改此文件，并保留默认路径和失败回退行为。

## 在代码中的位置

[打开源码：tests/test_keyword_fallback.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_keyword_fallback.py:1:1)  `tests/test_keyword_fallback.py:1-471`

## 相关代码

- 主要代码单元是 [[fixture_output]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 27 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `KeywordFallbackSchemaTests` | 验证关键词提供器响应的规范身份、候选限制和失败类型，并核对中文冻结回放按输入哈希定位。 |
| `KeywordFallbackSchemaTests.test_canonical_fixture_output_is_bounded_and_normalized` | 校验规范提供器夹具响应，核对关键词、源码锚点和构造用量经验证后保留。 |
| `KeywordFallbackSchemaTests.test_invalid_json_is_rejected` | 向解析函数提供无效 JSON 夹具输出，要求抛出明确格式错误。 |
| `KeywordFallbackSchemaTests.test_oversized_duplicate_injected_and_invalid_candidates_are_rejected` | 逐项注入超量、重复、提示注入、非法字符、空候选和请求错配，要求响应校验分别拒绝。 |
| `KeywordFallbackSchemaTests.test_canonical_failure_types_are_preserved_without_candidates` | 核对限流与凭据缺失响应保留标准失败类型，并且失败响应不携带候选关键词。 |
| `KeywordFallbackSchemaTests.test_chinese_retrieval_replay_is_keyed_by_the_canonical_input_hash` | 按冻结问题调用回放提供器，要求输入哈希映射到预期锚点和用量，启动次数等于问题数。 |
| `KeywordFallbackAdapterTests` | 覆盖命令适配器的身份缓存、无效输出、受限重试、凭据前置检查及敏感形状缓存审计。 |
| `KeywordFallbackAdapterTests.setUp` | 为每个关键词适配器测试创建独立临时输出目录。 |
| `KeywordFallbackAdapterTests.tearDown` | 清理关键词适配器测试的临时目录。 |
| `KeywordFallbackAdapterTests.config` | 基于固定夹具身份构造可配置超时、重试和必需环境变量的提供器配置。 |
| `KeywordFallbackAdapterTests.run_mode` | 临时切换故障模式并以禁用缓存运行提供器，返回实际适配器结果。 |
| `KeywordFallbackAdapterTests.test_command_adapter_caches_only_validated_output_under_identity_key` | 要求只缓存已验证输出，热命中不启动进程或计新用量，缓存不包含原问题且审计通过。 |
| `KeywordFallbackAdapterTests.test_invalid_json_output_and_process_failures_fall_back` | 对格式、空候选、注入、进程失败和限流逐项核对失败类型与重试次数，失败候选必须为空。 |
| `KeywordFallbackAdapterTests.test_timeout_is_bounded_and_retried_at_most_once` | 使用短超时夹具验证最多重试一次，并要求总延迟保持有界。 |
| `KeywordFallbackAdapterTests.test_missing_credentials_prevents_process_start` | 清空必需凭据并监视启动函数，要求零次尝试且完全不创建提供器进程。 |
| `KeywordFallbackAdapterTests.test_cache_audit_rejects_secret_shaped_content` | 篡改缓存关键词为凭据形状文本，要求缓存审计失败并给出对应原因。 |
| `KeywordFallbackRetrievalWiringTests` | 验证关键词回退在默认、允许、强制及失败场景的检索接线，保证扩展后仍由确定性选择并通过标准输入输出传递选项。 |
| `KeywordFallbackRetrievalWiringTests.setUp` | 创建带最小机器索引占位的临时输出，并配置非强制且不使用缓存的关键词回退选项。 |
| `KeywordFallbackRetrievalWiringTests.tearDown` | 清理关键词检索接线测试的临时目录。 |
| `KeywordFallbackRetrievalWiringTests.test_default_result_adds_unavailable_freshness_without_starting_provider` | 模拟无有效新鲜度绑定的默认检索，要求添加不可用状态但不修改基线对象或启动提供器。 |
| `KeywordFallbackRetrievalWiringTests.test_allow_mode_does_not_start_provider_after_passed_result` | 在确定性检索已通过时使用允许模式，要求提供器不启动并保存已跳过的回退记录。 |
| `KeywordFallbackRetrievalWiringTests.test_needs_source_read_uses_validated_terms_then_deterministic_selection` | 模拟证据不足后提供器给出有效词项，核对规范化扩展再次进入确定性检索并可审计。 |
| `KeywordFallbackRetrievalWiringTests.test_provider_failure_returns_original_result_with_structured_reason` | 模拟提供器超时，要求保留原检索状态并附结构化失败原因。 |
| `KeywordFallbackRetrievalWiringTests.test_stdio_exposes_the_same_nested_canonical_options` | 通过标准输入输出请求传递嵌套回退配置，核对强制模式与禁用缓存选项被准确解析。 |
| `KeywordFallbackRetrievalWiringTests.test_stdio_exposes_the_same_nested_canonical_options.fake_retrieve` | 捕获模拟检索的关键词回退配置并返回固定阅读包和记录路径，供协议选项断言。 |
| `KeywordFallbackBenchmarkTests` | 用固定冷、热结果验证关键词基准质量、上下文和用量汇总，同时要求恢复运行前缓存原字节。 |
| `KeywordFallbackBenchmarkTests.test_fixed_benchmark_compares_quality_latency_context_usage_and_restores_cache` | 模拟基线未命中与冷、热命中结果，核对质量变化、热缓存零新用量及基准结束后缓存精确恢复。 |

</details>
