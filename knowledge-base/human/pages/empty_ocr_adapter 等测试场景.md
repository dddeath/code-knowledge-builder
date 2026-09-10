# empty_ocr_adapter 等测试场景

标签：#类型/代码

> 该适配器接受 OCR 页面参数，写出状态为已提取且置信分值很高、但文本为空的协议响应，并记录零检测数。 它专门验证主流程不会只凭成功状态或高分接受空 OCR 文本，输出内容是故障 fixture 而非实际识别结果。

## 什么时候需要修改

OCR 输出模式或空文本质量门变化时修改此脚本，并确认主流程将页面保持为待处理。

## 在代码中的位置

[打开源码：tests/fixtures/reference-pdf-ocr/adapters/empty_ocr_adapter.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/fixtures/reference-pdf-ocr/adapters/empty_ocr_adapter.py:1:1)  `tests/fixtures/reference-pdf-ocr/adapters/empty_ocr_adapter.py:1-24`

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。
