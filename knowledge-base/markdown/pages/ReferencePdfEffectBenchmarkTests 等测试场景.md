# ReferencePdfEffectBenchmarkTests 等测试场景

标签：#类型/代码

> 该文件核对历史原生 PDF 效果实验的冻结协议与归档复算，要求当前实现或解析器身份变化显式失败，同时不得覆盖已有历史结果。 它约束旧实验的适用范围，历史协议中的网页未实现和零真实 OCR 是当时条件而非当前能力判断；归档结果与当前重跑结论分开验证。

## 什么时候需要修改

历史基准复算、来源或解析器身份检查以及失败写入保护变化时修改此文件，保留冻结历史证据而不重标记成当前结果。

## 在代码中的位置

[打开源码：tests/test_reference_pdf_effect_benchmark.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_reference_pdf_effect_benchmark.py:1:1)  `tests/test_reference_pdf_effect_benchmark.py:1-97`

## 相关代码

- 主要代码单元是 [[ReferencePdfEffectBenchmarkTests]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。
