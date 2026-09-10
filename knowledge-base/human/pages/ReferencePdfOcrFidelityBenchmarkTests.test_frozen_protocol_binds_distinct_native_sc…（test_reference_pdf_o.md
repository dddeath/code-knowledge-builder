# ReferencePdfOcrFidelityBenchmarkTests.test_frozen_protocol_binds_distinct_native_sc…（test_reference_pdf_ocr_fidelity_benchmark 测试）

标签：#类型/代码

> 该测试核对冻结协议与标准答案哈希，要求三类 PDF 具有不同的原生文本页模式，并验证各文件哈希、页眉页脚噪声和四个质量维度。 它确保 OCR 基准输入类型真实分离，避免用同一种可提取文本的 PDF 冒充扫描与混合对照。

## 什么时候需要修改

测试文档或标准答案变化时同步冻结此处期望，并重新核对原生、扫描和混合页模式。

## 在代码中的位置

[打开源码：tests/test_reference_pdf_ocr_fidelity_benchmark.py 第 23 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_reference_pdf_ocr_fidelity_benchmark.py:23:1)  `tests/test_reference_pdf_ocr_fidelity_benchmark.py:23-39`

## 相关代码

- 与 [[ReferencePdfOcrFidelityBenchmarkTests.test_frozen_protocol_binds_distinct_native_sc…（tests/test_reference_pdf_ocr_fidelity_benchmark.py:1）]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[ReferencePdfOcrFidelityBenchmarkTests.test_frozen_protocol_binds_distinct_native_sc…（tests/test_reference_pdf_ocr_fidelity_benchmark.py:1）]] 汇总了本页。
