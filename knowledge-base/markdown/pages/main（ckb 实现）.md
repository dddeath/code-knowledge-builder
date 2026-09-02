# main（ckb 实现）

标签：#类型/代码

> 代码单元 `main`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。 它属于所有 Harness 调用 CKB 的统一公开入口，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当公开命令、参数合同、退出状态或子系统入口变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 966 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:966:1)  `scripts/ckb.py:966-1768`

## 相关代码

- 实现时会用到 [[AutomationTest.register]]。
- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[FactFreshnessStateMachineTest]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_agent_protocol]]。
- 实现时会用到 [[audit_feedback]]。
- 实现时会用到 [[audit_gap_register]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[audit_operation_journal]]。
- 实现时会用到 [[audit_operation_journal 与 _root 的协作实现]]。
- 实现时会用到 [[bind_conversation 与 default_management_registry_path 的协作实现]]。
- 实现时会用到 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[propose_template 与 _canonical_bytes 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[validate_human_maintenance_invocation 与 ParameterSpec 的协作实现]]。

## 谁会来到这里

- [[keyword_provider_config 与 parser 的协作实现]] 汇总了本页。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
