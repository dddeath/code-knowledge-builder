# audit_agent_protocol

标签：#类型/代码

> `audit_agent_protocol` 是 `scripts/ckb_core/agent_protocol.py` 中负责核对各 Harness 指令文件、工作区绑定、反馈、工作记录与输出契约的函数。 它按源码所示的参数、条件分支和数据结构完成核对各 Harness 指令文件、工作区绑定、反馈、工作记录与输出契约，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当跨 Harness Agent 协议生成、安装、检查与维护入口的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_protocol.py 第 420 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol.py:420:1)  `scripts/ckb_core/agent_protocol.py:420-496`

## 相关代码

- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_agent_protocol 与 _default_python 的协作实现]]。
- 实现时会用到 [[audit_feedback]]。
- 实现时会用到 [[audit_output_contract]]。
- 实现时会用到 [[audit_work_record_index]]。

## 谁会来到这里

- [[AgentProtocolBatchApplyTests]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 汇总了本页。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[serve_stdio 与 _write_line 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[MigrationTest]]
- [[PageFanoutBenchmarkTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
