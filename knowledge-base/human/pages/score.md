# score

标签：#类型/代码

> 该函数把扫描 PDF 页面与两页标准答案比较，计算文本目标覆盖，并调用代码和表格评分；通过标记唯一落在预期页验证来源定位，同时核对混合文档提取方法序列。 它把输入提取记录转成可复算质量指标，不运行 OCR，也不自行决定冻结门是否通过；代码、表格、页定位和文本覆盖保持独立指标。

## 什么时候需要修改

标准答案结构、文本匹配规范化、来源页标记或混合方法期望变化时修改此函数，并使用保留的页面文本复算对应指标。

## 在代码中的位置

[打开源码：tests/benchmark_reference_pdf_ocr_fidelity.py 第 414 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/benchmark_reference_pdf_ocr_fidelity.py:414:1)  `tests/benchmark_reference_pdf_ocr_fidelity.py:414-455`

## 相关代码

- 与 [[score 等测试场景]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[qmd_adapter 的协作边界]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[score 等测试场景]] 汇总了本页。
