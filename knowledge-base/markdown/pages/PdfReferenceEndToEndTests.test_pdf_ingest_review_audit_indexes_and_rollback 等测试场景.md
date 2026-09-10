# PdfReferenceEndToEndTests.test_pdf_ingest_review_audit_indexes_and_rollback 等测试场景

标签：#类型/代码

> 该文件用原生、中文和空白 PDF 及受控 OCR 适配器验证逐页文本、代码表格布局、字符范围和来源哈希，覆盖质量不足、预算、取消、损坏与加密失败。 它同时通过完整参考导入审阅和回滚流程核对双镜像、索引与页码链接，区分提取就绪和主张已审阅，确保参考文档不会增加源码实体。

## 什么时候需要修改

PDF 解析器、布局分片、OCR 输出与预算、页定位或参考审阅索引规则变化时修改对应测试，并保留失败状态及无关资料不受回滚影响的断言。

## 在代码中的位置

[打开源码：tests/test_reference_pdf.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_reference_pdf.py:1:1)  `tests/test_reference_pdf.py:1-716`

## 相关代码

- 主要代码单元是 [[PdfReferenceEndToEndTests.test_pdf_ingest_review_audit_indexes_and_rollback]]。

## 谁会来到这里

- 与 [[PdfReferenceEndToEndTests.test_pdf_ingest_review_audit_indexes_and_rollback]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 16 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_commands` | 把 PDF 夹具绘制位置与文本参数组成列表，供测试页面生成函数使用。 |
| `PdfReferenceExtractionTests` | 验证原生 PDF 布局、中文、页片段和 OCR 证据，覆盖扫描待处理、预算取消及损坏加密与路径限制。 |
| `PdfReferenceExtractionTests.setUp` | 为 PDF 提取测试创建独立临时目录。 |
| `PdfReferenceExtractionTests.tearDown` | 清理当前 PDF 提取测试拥有的临时目录。 |
| `PdfReferenceExtractionTests.test_native_layout_preserves_page_code_and_table_boundaries` | 生成两页原生 PDF，核对代码缩进、表格间距、页序和片段字符范围，并检查受管路径审计约束。 |
| `PdfReferenceExtractionTests.test_page_audit_detects_manifest_page_empty_and_path_drift` | 篡改提取清单字节、页码顺序或页面路径，要求分别发现哈希、序列和越界错误。 |
| `PdfReferenceExtractionTests.test_native_chinese_page_round_trips_unicode` | 生成原生中文 PDF 并提取，要求页面标题与中文正文在 UTF-8 文本中完整保留。 |
| `PdfReferenceExtractionTests.test_wrapped_table_continuation_remains_a_table_fragment` | 核对换行表格续行仍归为表格且带推断警告，同时避免把对齐代码误判成表格。 |
| `PdfReferenceExtractionTests.test_ocr_output_hash_and_runtime_metadata_are_audited` | 核对 OCR 引擎元数据和输出哈希，区分旧记录缺失证据与实际文件漂移，后者必须审计失败。 |
| `PdfReferenceExtractionTests.test_scanned_mixed_and_bounded_ocr_states_are_explicit` | 覆盖扫描与混合页、OCR 缺失、输入页数预算、预先和运行中取消及超时，要求保留明确页面状态。 |
| `PdfReferenceExtractionTests.test_corrupt_encrypted_size_page_and_source_root_limits` | 要求损坏、加密、字节超限、页数超限和来源根越界 PDF 被拒绝。 |
| `PdfReferenceExtractionTests.test_web_adapter_boundary_requires_explicit_fetch_and_agent_review` | 核对网页适配器明确区分静态无网络与显式获取，提取输出仍需导入和 Agent 审阅。 |
| `PdfReferenceEndToEndTests` | 贯通 PDF 待提取、OCR 重导入、页片段审阅、双索引和定向回滚，要求不改变代码实体及无关参考。 |
| `PdfReferenceEndToEndTests.setUp` | 创建临时目录和多语言仓库，为 PDF 参考端到端测试准备源对象。 |
| `PdfReferenceEndToEndTests.tearDown` | 清理 PDF 参考端到端测试的临时目录。 |
| `PdfReferenceEndToEndTests._completed_output` | 依次初始化、审阅、合并并完成测试知识库，每步检查退出状态后返回输出路径。 |

</details>
