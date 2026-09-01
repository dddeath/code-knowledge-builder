# main（ckb 实现）

标签：#类型/代码

> `main` 是 `scripts/ckb.py` 第 780-1393 行定义的函数，本页绑定该固定源码范围。 负责注册 CKB 命令、校验参数，并把子命令分派到对应的知识库实现。

## 什么时候需要修改

当 `main` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 780 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:780:1)  `scripts/ckb.py:780-1393`

## 相关代码

- 实现时会用到 [[AutomationTest.register]]。
- 实现时会用到 [[CkbError]]。
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
- 实现时会用到 [[audit_references]]。
- 实现时会用到 [[audit_references 与 _root 的协作实现]]。
- 实现时会用到 [[bind_conversation 与 default_management_registry_path 的协作实现]]。
- 实现时会用到 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[initialize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[start_scope_extension 与 _error 的协作实现]]。

## 谁会来到这里

- [[keyword_provider_config 与 parser 的协作实现]] 汇总了本页。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
