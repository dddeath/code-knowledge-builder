# ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_dam…（test_chinese_retrieval_fixture 测试）

标签：#类型/代码

> 该测试用替身生成固定语料副本，在首次模拟测量时故意修改源索引，要求基准报告源漂移失败但副本索引保持原字节。 它验证源语料漂移与测试副本损坏是两项独立检查，防止把源变化误记为副本索引变化；替身排名与固定耗时不作为真实检索性能证据。

## 什么时候需要修改

基准语料复制、前后哈希记录或失败报告字段变化时修改此测试，并保留源失败与副本通过的组合断言。

## 在代码中的位置

[打开源码：tests/test_chinese_retrieval_fixture.py 第 133 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_chinese_retrieval_fixture.py:133:1)  `tests/test_chinese_retrieval_fixture.py:133-209`

## 谁会来到这里

- [[ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_dam…（tests/test_chinese_retrieval_fixture.py:1）]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 2 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_damaging_copied_index.fake_copy` | `fake_copy` 完成中文检索固定协议、基线、回放和来源漂移回归验证中的一个明确步骤。 |
| `ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_damaging_copied_index.fake_row` | `fake_row` 完成中文检索固定协议、基线、回放和来源漂移回归验证中的一个明确步骤。 |

</details>
