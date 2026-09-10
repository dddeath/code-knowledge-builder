# ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_dam…（tests/test_chinese_retrieval_fixture.py:1）

标签：#类型/代码

> 该测试文件固定中文检索协议、基线、回放结果和来源漂移行为。 它保证检索效果比较可重复，并验证复制索引在来源漂移失败时保持完整。

## 什么时候需要修改

调整中文词项、固定问题集、评价指标、回放数据或基准入口时需要修改。

## 在代码中的位置

[打开源码：tests/test_chinese_retrieval_fixture.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_chinese_retrieval_fixture.py:1:1)  `tests/test_chinese_retrieval_fixture.py:1-214`

## 相关代码

- 主要代码单元是 [[ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_dam…（test_chinese_retrieval_fixture 测试）]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 11 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ChineseRetrievalFixtureTests` | `ChineseRetrievalFixtureTests` 完成中文检索固定协议、基线、回放和来源漂移回归验证中的一个明确步骤。 |
| `ChineseRetrievalFixtureTests.test_frozen_protocol_shape` | `test_frozen_protocol_shape` 完成中文检索固定协议、基线、回放和来源漂移回归验证中的一个明确步骤。 |
| `ChineseRetrievalFixtureTests.test_baseline_records_all_mechanical_fragments` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |
| `ChineseRetrievalFixtureTests.test_baseline_corpus_and_recall_are_complete` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |
| `ChineseRetrievalEffectRetestFixtureTests` | 核对冻结三组中文检索协议、题目与回放证据边界，并用受控漂移测试要求报告失败但保留副本索引。 |
| `ChineseRetrievalEffectRetestFixtureTests.setUp` | `setUp` 完成中文检索固定协议、基线、回放和来源漂移回归验证中的一个明确步骤。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_three_arm_protocol_is_frozen_at_the_fixed_knowledge_base_commit` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_questions_have_fixed_relevance_labels_and_replay_responses` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_replay_is_declared_separately_from_real_provider_evidence` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_legacy_arm_preserves_the_exact_mechanical_fragments` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_rank_metrics_are_computed_from_document_order_and_fixed_grades` | 该测试验证中文检索固定协议、基线、回放或来源漂移中的一个明确行为。 |

</details>
