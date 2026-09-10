# slow_ocr_adapter 等测试场景

标签：#类型/代码

> 该适配器解析 OCR 命令参数后等待五秒，不写入识别结果。 它为上游超时和进程终止路径提供确定性的慢响应，不执行 PDF 渲染或文字识别。

## 什么时候需要修改

超时探针的时间预算或适配器参数合同变化时修改此脚本，并验证等待时长足以触发目标超时分支。

## 在代码中的位置

[打开源码：tests/fixtures/reference-pdf-ocr/adapters/slow_ocr_adapter.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/fixtures/reference-pdf-ocr/adapters/slow_ocr_adapter.py:1:1)  `tests/fixtures/reference-pdf-ocr/adapters/slow_ocr_adapter.py:1-13`

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。
