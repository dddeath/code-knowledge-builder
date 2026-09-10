# generate

标签：#类型/代码

> 该函数依次生成原生、纯扫描和混合 PDF，删除临时页面图像后核对各页文本模式，再把文档哈希、标准页面内容和质量维度写入标准答案清单并复读。 它是三类 OCR fixture 的生成编排入口，清单把内容与具体文件绑定，供后续独立基准核对输入一致性，而不直接评价 OCR 精度。

## 什么时候需要修改

生成文件集合、渲染步骤、临时图像清理或清单字段变化时修改此函数，并验证文档类型与最终清单实际字节。

## 在代码中的位置

[打开源码：tests/generate_reference_pdf_ocr_fixtures.py 第 224 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/generate_reference_pdf_ocr_fixtures.py:224:1)  `tests/generate_reference_pdf_ocr_fixtures.py:224-260`

## 相关代码

- 与 [[generate 等测试场景]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[generate 等测试场景]] 汇总了本页。
