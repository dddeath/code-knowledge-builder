# ReferencePdfEffectBenchmarkTests

标签：#类型/代码

> `ReferencePdfEffectBenchmarkTests` 汇总同一能力的正例、负例和传输一致性测试。 它组织共享 fixture 和断言，验证实现满足冻结合同。

## 什么时候需要修改

当 `ReferencePdfEffectBenchmarkTests` 对应能力的验收矩阵变化时，应更新该测试类。

## 在代码中的位置

[打开源码：tests/test_reference_pdf_effect_benchmark.py 第 20 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_reference_pdf_effect_benchmark.py:20:1)  `tests/test_reference_pdf_effect_benchmark.py:20-82`

## 相关代码

- 实现时会用到 [[module_name]]。
- 实现时会用到 [[parser]]。

## 谁会来到这里

- [[AutomationTest.register]] 关联到这里的验证场景。
- [[ReferencePdfEffectBenchmarkTests 等测试场景]] 汇总了本页。
- [[append 等测试场景]] 关联到这里的验证场景。
- [[assertions]] 关联到这里的验证场景。
- [[bind_conversation]] 关联到这里的验证场景。
- [[keyword_provider_config 与 parser 的协作实现]] 关联到这里的验证场景。
- [[parser]] 关联到这里的验证场景。
- [[preflight]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 3 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ReferencePdfEffectBenchmarkTests.test_protocol_is_frozen_and_limits_claim_scope` | 该测试验证当前场景的实际结果、来源约束和失败边界。 |
| `ReferencePdfEffectBenchmarkTests.test_committed_result_replays_exactly` | 该测试验证当前场景的实际结果、来源约束和失败边界。 |
| `ReferencePdfEffectBenchmarkTests.test_parser_version_drift_fails_without_overwriting_existing_results` | 该测试验证当前场景的实际结果、来源约束和失败边界。 |

</details>
