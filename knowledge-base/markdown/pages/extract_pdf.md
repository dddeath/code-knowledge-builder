# extract_pdf

标签：#类型/代码

> 代码单元 `extract_pdf`负责按页提取 PDF 文本、代码和表格结构，评估质量并在需要时调用受限 OCR 适配器。 它属于PDF 来源可追溯、失败可诊断和页级审阅的实现层，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当PDF 限额、文本质量、页块分类、OCR 合同或页级证据规则变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_pdf.py 第 345 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_pdf.py:345:1)  `scripts/ckb_core/reference_pdf.py:345-522`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[extract_pdf 与 PdfExtractionError 的协作实现]]。
- 实现时会用到 [[parser]]。

## 谁会来到这里

- [[PdfReferenceExtractionTests]] 会使用这里提供的行为。
- [[extract_pdf 与 PdfExtractionError 的协作实现]] 汇总了本页。
- [[ingest_reference]] 会使用这里提供的行为。
- [[run_benchmark]] 会使用这里提供的行为。

## 相关测试

- [[PdfReferenceExtractionTests]]
- [[run_benchmark]]
