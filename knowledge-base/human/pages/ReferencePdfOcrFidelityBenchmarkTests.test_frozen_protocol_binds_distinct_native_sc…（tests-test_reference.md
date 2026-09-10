# ReferencePdfOcrFidelityBenchmarkTests.test_frozen_protocol_binds_distinct_native_sc…（tests/test_reference_pdf_ocr_fidelity_benchmark.py:1）

标签：#类型/代码

> 该文件验证原生、扫描和混合 OCR fixture 的冻结身份，以及归档测量中的文本覆盖、代码、表格和页定位指标与真实引擎证据。 它将分维度质量和故障诊断保留为独立断言，默认读取归档结果，只有显式开启环境开关才运行真实 OCR 重放，不向普通测试隐式增加识别调用。

## 什么时候需要修改

冻结输入、归档指标、引擎来源或真实重放开关变化时修改此文件，并区分归档核对与当前实际重跑。

## 在代码中的位置

[打开源码：tests/test_reference_pdf_ocr_fidelity_benchmark.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_reference_pdf_ocr_fidelity_benchmark.py:1:1)  `tests/test_reference_pdf_ocr_fidelity_benchmark.py:1-109`

## 相关代码

- 主要代码单元是 [[ReferencePdfOcrFidelityBenchmarkTests.test_frozen_protocol_binds_distinct_native_sc…（test_reference_pdf_ocr_fidelity_benchmark 测试）]]。

## 谁会来到这里

- 与 [[ReferencePdfOcrFidelityBenchmarkTests.test_frozen_protocol_binds_distinct_native_sc…（test_reference_pdf_ocr_fidelity_benchmark 测试）]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 6 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_sha256` | 计算 OCR 保真基准文件的 SHA-256，用于冻结协议和输入身份核对。 |
| `ReferencePdfOcrFidelityBenchmarkTests` | 核对冻结 OCR 夹具、分维度归档指标、真实识别来源和故障矩阵，真实重跑仅在显式环境开关启用。 |
| `ReferencePdfOcrFidelityBenchmarkTests.test_committed_measurement_reports_each_quality_dimension_separately` | 要求归档 OCR 结果分开报告文本、代码、表格和页定位，不使用单一总准确率掩盖代码行保真差异。 |
| `ReferencePdfOcrFidelityBenchmarkTests.test_committed_measurement_proves_real_ocr_content_and_reopened_provenance` | 检查归档测量中的真实 OCR 引擎版本、三类文档方法、原文复制与输出哈希，并保留中文识别内容。 |
| `ReferencePdfOcrFidelityBenchmarkTests.test_failure_matrix_covers_tool_timeout_empty_limit_and_corruption` | 核对归档 OCR 故障矩阵覆盖工具缺失、超时、空输出、页数预算和损坏 PDF 且诊断原因匹配。 |
| `ReferencePdfOcrFidelityBenchmarkTests.test_live_real_ocr_replay_meets_frozen_gates` | 在显式启用时重跑真实 OCR 基准，要求冻结合同、质量门与全部诊断均通过。 |

</details>
