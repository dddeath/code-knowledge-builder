# ingest_reference

标签：#类型/代码

> 代码单元 `ingest_reference`负责管理参考资料的吸收、审阅、投影、索引、失败重试与回滚。 它属于外部资料进入独立参考层的受控生命周期入口，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当资料格式、来源定位、审阅合同、状态迁移或回滚规则变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_documents.py 第 156 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_documents.py:156:1)  `scripts/ckb_core/reference_documents.py:156-390`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[extract_pdf]]。
- 实现时会用到 [[ingest]]。
- 实现时会用到 [[ingest_reference 与 _root 的协作实现]]。
- 实现时会用到 [[propose_template 与 _canonical_bytes 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。

## 谁会来到这里

- [[PdfReferenceExtractionTests]] 会使用这里提供的行为。
- [[ingest_reference 与 _root 的协作实现]] 汇总了本页。

## 相关测试

- [[PdfReferenceExtractionTests]]
