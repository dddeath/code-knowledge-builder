# ascii_pdf

标签：#类型/代码

> 代码单元 `ascii_pdf`负责生成可重复的 PDF 测试样例，覆盖文本、中文、空白和加密文档。 它属于PDF 吸收行为的离线固定输入集合，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当PDF 结构、编码样例或失败场景需求变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：tests/pdf_fixture_factory.py 第 38 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/pdf_fixture_factory.py:38:1)  `tests/pdf_fixture_factory.py:38-63`

## 相关代码

- 实现时会用到 [[append]]。
- 实现时会用到 [[ascii_pdf 等测试场景]]。

## 谁会来到这里

- [[PdfReferenceExtractionTests]] 会使用这里提供的行为。
- [[PdfReferenceExtractionTests 等测试场景]] 会使用这里提供的行为。
- [[ascii_pdf 等测试场景]] 汇总了本页。
- [[run_benchmark]] 会使用这里提供的行为。

## 相关测试

- [[PdfReferenceExtractionTests]]
- [[PdfReferenceExtractionTests 等测试场景]]
- [[ascii_pdf 等测试场景]]
- [[run_benchmark]]
