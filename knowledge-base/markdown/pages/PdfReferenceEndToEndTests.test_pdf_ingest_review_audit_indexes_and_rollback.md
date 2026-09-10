# PdfReferenceEndToEndTests.test_pdf_ingest_review_audit_indexes_and_rollback

标签：#类型/代码

> 该测试先验证待 OCR 页拒绝审阅以及幂等重导入需先回滚，再导入原生 PDF 并提交精确页片段主张，核对人类页、双索引和维护结果。 它把 PDF 页级来源贯通到参考检索层，检查错误页码被拒绝、旧 OCR 证据缺失保留兼容标记，并证明定向回滚只删除该 PDF 资料而不改源码实体或无关参考。

## 什么时候需要修改

待处理页重导入、审阅定位、OCR 历史兼容或定向回滚变化时修改此测试，并同时核对引用范围与回滚后的索引数量。

## 在代码中的位置

[打开源码：tests/test_reference_pdf.py 第 441 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_reference_pdf.py:441:1)  `tests/test_reference_pdf.py:441-711`

## 相关代码

- 与 [[PdfReferenceEndToEndTests.test_pdf_ingest_review_audit_indexes_and_rollback 等测试场景]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[PdfReferenceEndToEndTests.test_pdf_ingest_review_audit_indexes_and_rollback 等测试场景]] 汇总了本页。
