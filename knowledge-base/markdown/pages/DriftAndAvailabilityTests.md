# DriftAndAvailabilityTests

标签：#类型/代码

> 代码单元 `test_model_identity_drift_is_rejected`负责验证三臂协议、真实模型身份、索引、指标、资源门和失败证据。 它属于语义向量实验的回归保护；实验代码不改变生产检索或稳定页面生成默认行为。

## 什么时候需要修改

当模型清单、索引、质量指标或资源限制变化时，应同步复查本页、固定实验协议及直接测试。

## 在代码中的位置

[打开源码：tests/test_ckb_semantic_vector_benchmark.py 第 76 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_semantic_vector_benchmark.py:76:1)  `tests/test_ckb_semantic_vector_benchmark.py:76-189`

## 相关代码

- 实现时会用到 [[benchmark 的协作边界（9fab5b96）]]。

## 谁会来到这里

- [[DriftAndAvailabilityTests 等测试场景]] 汇总了本页。
- [[benchmark 的协作边界（9fab5b96）]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `DriftAndAvailabilityTests.test_model_identity_drift_is_rejected` | 该测试验证“model identity drift is rejected”场景，保护语义向量实验测试的结果与失败边界。 |
| `DriftAndAvailabilityTests.test_missing_engine_has_structured_unavailable_evidence` | 该测试验证“missing engine has structured u…”场景，保护语义向量实验测试的结果与失败边界。 |
| `DriftAndAvailabilityTests.test_index_digest_drift_is_rejected` | 该测试验证“index digest drift is rejected”场景，保护语义向量实验测试的结果与失败边界。 |
| `DriftAndAvailabilityTests.test_index_size_is_reported_after_final_manifest_serialization` | 该测试验证“index size is reported after fi…”场景，保护语义向量实验测试的结果与失败边界。 |

</details>
