# run_benchmark

标签：#类型/代码

> `run_benchmark` 在冻结协议下比较旧基线与当前原生 PDF 能力，并测量页码、中文、代码缩进、表格和失败诊断。 它绑定源码 blob 与实际 pypdf 运行时身份，明确把 Web 和真实 OCR 留在未覆盖范围。

## 什么时候需要修改

当 PDF 解析器、fixture、指标或运行时身份门变化时，应更新本函数并重新生成原始结果和报告。

## 在代码中的位置

[打开源码：tests/benchmark_reference_pdf_effect.py 第 150 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/benchmark_reference_pdf_effect.py:150:1)  `tests/benchmark_reference_pdf_effect.py:150-324`

## 相关代码

- 实现时会用到 [[append 等测试场景]]。
- 实现时会用到 [[ascii_pdf]]。
- 实现时会用到 [[ascii_pdf 等测试场景]]。
- 实现时会用到 [[extract_pdf]]。
- 实现时会用到 [[extract_pdf 与 PdfExtractionError 的协作实现]]。
- 实现时会用到 [[parser]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run_benchmark 等测试场景]]。
- 实现时会用到 [[web_input_adapter_contract]]。

## 谁会来到这里

- [[ascii_pdf]] 关联到这里的验证场景。
- [[ascii_pdf 等测试场景]] 关联到这里的验证场景。
- [[extract_pdf]] 关联到这里的验证场景。
- [[run_benchmark 等测试场景]] 汇总了本页。
- [[web_input_adapter_contract]] 关联到这里的验证场景。
