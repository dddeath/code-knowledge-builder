# SourceLinkRenderer.uri

标签：#类型/代码

> `SourceLinkRenderer.uri` 将仓库内源码位置编码为编辑器可打开的 URI。 它复用已校验绝对路径，并按 VS Code、Insiders、file 或自定义模板生成确定性链接。

## 什么时候需要修改

新增编辑器、调整 URI 编码或改变自定义模板字段时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/ckb_core/source_links.py 第 60 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:60:1)  `scripts/ckb_core/source_links.py:60-75`

## 相关代码

- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]。
- 实现时会用到 [[render_integration 与 _looks_windows 的协作实现]]。

## 谁会来到这里

- [[HumanPageAuthoringValidationFailureTests 等测试场景]] 会使用这里提供的行为。
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]] 汇总了本页。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[audit_migration]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[benchmark 的协作边界（9fab5b96）]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[build_case]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[doctor_report 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[freeze 的协作边界]] 会使用这里提供的行为。
- [[graph 的协作边界]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[ingest_reference 与 _root 的协作实现]] 会使用这里提供的行为。
- [[render_page_author 与 _error 的协作实现]] 会使用这里提供的行为。
- [[replace_note 与 RecordReplaceLockError 的协作实现]] 会使用这里提供的行为。
- [[retrieve]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[run_failure_probe 等测试场景]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[CanvasContractTests]]
- [[CanvasContractTests 等测试场景]]
- [[CanvasDeterminismTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
