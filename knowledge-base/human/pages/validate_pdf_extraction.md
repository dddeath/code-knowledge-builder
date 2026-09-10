# validate_pdf_extraction

标签：#类型/代码

> 该函数重新打开 PDF 提取清单，核对参考身份、锁定解析器、页数顺序、页面路径和哈希、片段字符范围及非重叠约束，并对已记录的 OCR 输出检查精确路径和文件哈希。 它为参考审阅和总审计返回完整提取错误集合，同时区分旧记录缺少 OCR 输出证据与新证据漂移；要求就绪时仍有待处理页会失败，旧证据缺失只标记为历史不可用而不伪装为已验证。

## 什么时候需要修改

页面或 OCR 证据合同、片段来源与置信度字段、历史兼容策略、文件集合或待处理状态推导变化时修改此函数，并验证路径漂移、重叠片段、缺失 OCR 文件和就绪门。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_pdf.py 第 552 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_pdf.py:552:1)  `scripts/ckb_core/reference_pdf.py:552-762`

## 相关代码

- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[ingest_web_reference 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[validate_pdf_extraction 与 PdfExtractionError 的协作实现]] 汇总了本页。
