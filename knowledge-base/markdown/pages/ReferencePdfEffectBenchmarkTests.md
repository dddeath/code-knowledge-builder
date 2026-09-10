# ReferencePdfEffectBenchmarkTests

标签：#类型/代码

> 该测试类检查冻结 PDF 协议、当前实现漂移和解析器漂移的结果，核对保存的报告可以独立复算，失败时原有结果文件保持不变。 它防止把历史原生 PDF 测量外推到网页与 OCR 综合能力，保留身份变化与数值指标相同也应失败的证据边界。

## 什么时候需要修改

报告检查字段、解析器身份或历史结果保护规则变化时修改此类，并分别核对旧报告和当前运行状态。

## 在代码中的位置

[打开源码：tests/test_reference_pdf_effect_benchmark.py 第 20 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_reference_pdf_effect_benchmark.py:20:1)  `tests/test_reference_pdf_effect_benchmark.py:20-92`

## 谁会来到这里

- [[ReferencePdfEffectBenchmarkTests 等测试场景]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 3 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ReferencePdfEffectBenchmarkTests.test_protocol_is_frozen_and_limits_claim_scope` | 核对历史原生 PDF 基准冻结解析器及零真实 OCR 等声明边界，并读取专门的版本漂移协议。 |
| `ReferencePdfEffectBenchmarkTests.test_committed_result_stays_frozen_and_current_source_drift_is_explicit` | 复算历史与当前报告，要求归档结果不变，而当前实现漂移显式失败且不扩展为 PDF 网页 OCR 综合效果。 |
| `ReferencePdfEffectBenchmarkTests.test_parser_version_drift_fails_without_overwriting_existing_results` | 使用漂移解析器协议调用基准命令，要求失败不覆盖已有原始结果和报告，并列出失败身份检查。 |

</details>
