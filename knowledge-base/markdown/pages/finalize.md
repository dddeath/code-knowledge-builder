# finalize

标签：#类型/代码

> 代码单元 `finalize`负责编排固定快照解析、Agent 审阅、页面投影、迁移、全局审计与最终生成。 它属于从源码事实到机器索引和人类页面的一致性主流程，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当构建阶段、迁移复用、页面预算、可读性、镜像或完成门变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/pipeline.py 第 3326 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:3326:1)  `scripts/ckb_core/pipeline.py:3326-3405`

## 相关代码

- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[MigrationTest]] 会使用这里提供的行为。
- [[PdfReferenceExtractionTests 等测试场景]] 会使用这里提供的行为。
- [[RecordReplaceTests]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[audit_operation_journal 与 _root 的协作实现]] 会使用这里提供的行为。
- [[command 等测试场景]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[finalize 与 _replace_output_prefix 的协作实现]] 汇总了本页。
- [[parser]] 会使用这里提供的行为。
- [[query_graph 与 _networkx_modules 的协作实现]] 会使用这里提供的行为。
- [[refresh 等测试场景]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[run 等测试场景]] 会使用这里提供的行为。
- [[serve_stdio]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。
- [[start_session]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[KeywordFallbackRetrievalWiringTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
