# run_failure_probe 等测试场景

标签：#类型/代码

> 文件 `tests/benchmark_chinese_retrieval.py`负责在固定语料上比较旧词项、当前词项和显式关键词回放慢路径。 它属于中文检索效果的三臂测量入口，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当问题集、词项算法、排序指标、缓存或延迟口径变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：tests/benchmark_chinese_retrieval.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/benchmark_chinese_retrieval.py:1:1)  `tests/benchmark_chinese_retrieval.py:1-652`

## 相关代码

- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[ScopeExtensionOfferTests.retrieval]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[graph 的协作边界]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[parser]]。
- 实现时会用到 [[retrieve_machine]]。
- 主要代码单元是 [[run_failure_probe]]。
- 实现时会用到 [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]。
- 实现时会用到 [[search_terms]]。
- 实现时会用到 [[search_terms 与 _split_camel 的协作实现]]。

## 谁会来到这里

- [[ChineseRetrievalEffectRetestFixtureTests]] 会使用这里提供的行为。
- [[run_failure_probe]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。

## 相关测试

- [[ChineseRetrievalEffectRetestFixtureTests]]
- [[run_failure_probe]]

## 内部细节

<details><summary>查看本页收纳的 23 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `json_load` | `json_load` 完成中文检索三臂基准所需的一个明确步骤。 |
| `json_write` | `json_write` 完成中文检索三臂基准所需的一个明确步骤。 |
| `sha256` | `sha256` 完成中文检索三臂基准所需的一个明确步骤。 |
| `percentile` | `percentile` 完成中文检索三臂基准所需的一个明确步骤。 |
| `_split_camel` | `_split_camel` 完成中文检索三臂基准所需的一个明确步骤。 |
| `legacy_search_terms` | `legacy_search_terms` 完成中文检索三臂基准所需的一个明确步骤。 |
| `legacy_build_fts_query` | `legacy_build_fts_query` 完成中文检索三臂基准所需的一个明确步骤。 |
| `legacy_term_binding` | `legacy_term_binding` 完成中文检索三臂基准所需的一个明确步骤。 |
| `fixture_environment` | `fixture_environment` 完成中文检索三臂基准所需的一个明确步骤。 |
| `marker_count` | `marker_count` 完成中文检索三臂基准所需的一个明确步骤。 |
| `_sqlite_backup` | `_sqlite_backup` 完成中文检索三臂基准所需的一个明确步骤。 |
| `copy_corpus` | `copy_corpus` 完成中文检索三臂基准所需的一个明确步骤。 |
| `validate_protocol` | `validate_protocol` 校验中文检索三臂基准所需的一个明确步骤。 |
| `replay_config` | `replay_config` 完成中文检索三臂基准所需的一个明确步骤。 |
| `unique_ranked_documents` | `unique_ranked_documents` 完成中文检索三臂基准所需的一个明确步骤。 |
| `quality_for_ranking` | `quality_for_ranking` 完成中文检索三臂基准所需的一个明确步骤。 |
| `result_signature` | `result_signature` 完成中文检索三臂基准所需的一个明确步骤。 |
| `invoke_arm` | `invoke_arm` 完成中文检索三臂基准所需的一个明确步骤。 |
| `run_row` | `run_row` 完成中文检索三臂基准所需的一个明确步骤。 |
| `aggregate_arm` | `aggregate_arm` 解析并归一化中文检索三臂基准所需的一个明确步骤。 |
| `comparison` | `comparison` 完成中文检索三臂基准所需的一个明确步骤。 |
| `run_benchmark` | `run_benchmark` 完成中文检索三臂基准所需的一个明确步骤。 |
| `main` | `main` 完成中文检索三臂基准所需的一个明确步骤。 |

</details>
