# web_input_adapter_contract

标签：#类型/代码

> 代码单元 `web_input_adapter_contract`负责定义本地文件与 Web 等参考输入适配器的最小协议。 它属于新增资料来源而不改变参考资料主流程的扩展边界，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当输入类型、适配器责任、准备结果或网络权限边界变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_inputs.py 第 44 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_inputs.py:44:1)  `scripts/ckb_core/reference_inputs.py:44-76`

## 相关代码

- 实现时会用到 [[ingest]]。

## 谁会来到这里

- [[web_input_adapter_contract 与 ReferenceInputRequest 的协作实现]] 汇总了本页。

## 相关测试

- [[PdfReferenceExtractionTests]]
