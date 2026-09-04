# ChineseRetrievalEffectRetestFixtureTests

标签：#类型/代码

> 该测试类核对三臂中文检索实验的协议、指标重算和来源漂移保护。 它区分确定性词项、旧实现和 LLM 回放结果，避免把回放数据当作真实调用。

## 什么时候需要修改

调整检索实验分组、固定指标、来源清单或回放证据时需要修改。

## 在代码中的位置

[打开源码：tests/test_chinese_retrieval_fixture.py 第 50 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_chinese_retrieval_fixture.py:50:1)  `tests/test_chinese_retrieval_fixture.py:50-209`

## 相关代码

- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[ScopeExtensionOfferTests.retrieval]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[run_failure_probe]]。
- 实现时会用到 [[run_failure_probe 等测试场景]]。
- 实现时会用到 [[search_terms]]。

## 谁会来到这里

- [[ChineseRetrievalEffectRetestFixtureTests 等测试场景]] 汇总了本页。
- [[check_fact_freshness 与 _root 的协作实现]] 关联到这里的验证场景。
- [[finalize 与 _replace_output_prefix 的协作实现]] 关联到这里的验证场景。
- [[refresh 等测试场景]] 关联到这里的验证场景。
- [[retrieve_machine]] 关联到这里的验证场景。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[run_failure_probe]] 关联到这里的验证场景。
- [[run_failure_probe 等测试场景]] 关联到这里的验证场景。
- [[run_keyword_provider]] 关联到这里的验证场景。
- [[search_terms]] 关联到这里的验证场景。
- [[search_terms 与 _split_camel 的协作实现]] 关联到这里的验证场景。
- [[start_scope_extension 与 _error 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ChineseRetrievalEffectRetestFixtureTests.setUp` | `setUp` 完成中文检索固定协议、基线、回放和来源漂移回归验证中的一个明确步骤。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_three_arm_protocol_is_frozen_at_the_fixed_knowledge_base_commit` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_questions_have_fixed_relevance_labels_and_replay_responses` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_replay_is_declared_separately_from_real_provider_evidence` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_legacy_arm_preserves_the_exact_mechanical_fragments` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_rank_metrics_are_computed_from_document_order_and_fixed_grades` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_damaging_copied_index` | 验证检索基准发现来源漂移时停止测量且不改坏复制的索引。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_damaging_copied_index.fake_copy` | `fake_copy` 完成中文检索固定协议、基线、回放和来源漂移回归验证中的一个明确步骤。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_damaging_copied_index.fake_row` | `fake_row` 完成中文检索固定协议、基线、回放和来源漂移回归验证中的一个明确步骤。 |

</details>
