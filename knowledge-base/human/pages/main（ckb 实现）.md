# main（ckb 实现）

标签：#类型/代码

> `main` 位于 `scripts/ckb.py` 第 900-1637 行，本页用固定源码范围说明它如何编排命令入口、执行顺序和退出结果。 `main` 负责在CKB 主命令解析、分发和退出状态中编排命令入口、执行顺序和退出结果。

## 什么时候需要修改

当 `scripts/ckb.py` 中 `main` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 900 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:900:1)  `scripts/ckb.py:900-1637`

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
- 实现时会用到 [[audit_global]]。
- 实现时会用到 [[audit_global 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[audit_operation_journal]]。
- 实现时会用到 [[audit_operation_journal 与 _root 的协作实现]]。
- 实现时会用到 [[bind_conversation 与 default_management_registry_path 的协作实现]]。
- 实现时会用到 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[propose_template 与 _canonical_bytes 的协作实现]]。
- 实现时会用到 [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。

## 谁会来到这里

- [[keyword_provider_config 与 parser 的协作实现]] 汇总了本页。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
