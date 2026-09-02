# audit_references

标签：#类型/代码

> `audit_references` 是 `scripts/ckb_core/reference_documents.py` 中负责核对资料原文、许可证、逐项引用、中文主张、镜像和机器索引的函数。 它按源码所示的参数、条件分支和数据结构完成核对资料原文、许可证、逐项引用、中文主张、镜像和机器索引，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当审阅文本资料的归档、逐项核对、投影、索引与回滚的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_documents.py 第 470 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_documents.py:470:1)  `scripts/ckb_core/reference_documents.py:470-558`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_references 与 _root 的协作实现]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。

## 谁会来到这里

- [[audit_global]] 会使用这里提供的行为。
- [[audit_references 与 _root 的协作实现]] 汇总了本页。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanPageTemplateValidationTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[MigrationTest]]
- [[RecordReplaceTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
