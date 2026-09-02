# extract_pdf 与 PdfExtractionError 的协作实现

标签：#类型/代码

> 文件 `scripts/ckb_core/reference_pdf.py`负责按页提取 PDF 文本、代码和表格结构，评估质量并在需要时调用受限 OCR 适配器。 它属于PDF 来源可追溯、失败可诊断和页级审阅的实现层，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当PDF 限额、文本质量、页块分类、OCR 合同或页级证据规则变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_pdf.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_pdf.py:1:1)  `scripts/ckb_core/reference_pdf.py:1-685`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[command]]。
- 主要代码单元是 [[extract_pdf]]。
- 实现时会用到 [[ingest]]。
- 实现时会用到 [[parser]]。

## 谁会来到这里

- [[PdfReferenceExtractionTests]] 会使用这里提供的行为。
- [[extract_pdf]] 会使用这里提供的行为。
- [[ingest_reference 与 _root 的协作实现]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanPageAuthoringValidationFailureTests]]
- [[HumanPageTemplateRegistryTests 等测试场景]]
- [[MigrationTest]]
- [[PageFanoutBenchmarkTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 16 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `PdfExtractionError` | `PdfExtractionError` 完成PDF 页级提取与校验中的一个明确步骤。 |
| `_load_pypdf` | `_load_pypdf` 读取并判定PDF 页级提取与校验所需的数据或状态。 |
| `_validate_positive_limit` | `_validate_positive_limit` 校验PDF 页级提取与校验所需的数据或状态。 |
| `validate_pdf_limits` | `validate_pdf_limits` 校验PDF 页级提取与校验所需的数据或状态。 |
| `validate_ocr_limits` | `validate_ocr_limits` 校验PDF 页级提取与校验所需的数据或状态。 |
| `_normalized_layout_text` | `_normalized_layout_text` 解析并归一化PDF 页级提取与校验所需的数据或状态。 |
| `_text_metrics` | `_text_metrics` 完成PDF 页级提取与校验中的一个明确步骤。 |
| `_usable_text` | `_usable_text` 完成PDF 页级提取与校验中的一个明确步骤。 |
| `_native_confidence` | `_native_confidence` 完成PDF 页级提取与校验中的一个明确步骤。 |
| `_classify_block` | `_classify_block` 解析并归一化PDF 页级提取与校验所需的数据或状态。 |
| `segment_page_text` | `segment_page_text` 解析并归一化PDF 页级提取与校验所需的数据或状态。 |
| `_resolve_ocr_adapter` | `_resolve_ocr_adapter` 完成PDF 页级提取与校验中的一个明确步骤。 |
| `_run_ocr_page` | `_run_ocr_page` 完成PDF 页级提取与校验中的一个明确步骤。 |
| `inspect_pdf` | `inspect_pdf` 完成PDF 页级提取与校验中的一个明确步骤。 |
| `validate_pdf_extraction` | `validate_pdf_extraction` 校验PDF 页级提取与校验所需的数据或状态。 |
| `pdf_fragment` | `pdf_fragment` 完成PDF 页级提取与校验中的一个明确步骤。 |

</details>
