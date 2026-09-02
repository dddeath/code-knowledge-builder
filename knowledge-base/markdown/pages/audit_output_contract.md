# audit_output_contract

标签：#类型/代码

> `audit_output_contract` 是 `scripts/ckb_core/output_contract.py` 第 111-143 行定义的函数，本页绑定该固定源码范围。 负责投影并校验面向 Agent 的输出契约。

## 什么时候需要修改

当 `audit_output_contract` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/output_contract.py 第 111 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/output_contract.py:111:1)  `scripts/ckb_core/output_contract.py:111-143`

## 相关代码

- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_output_contract 与 _default_ckb 的协作实现]]。
- 实现时会用到 [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]]。

## 谁会来到这里

- [[AgentProtocolBatchApplyTests]] 会使用这里提供的行为。
- [[audit_agent_protocol]] 会使用这里提供的行为。
- [[audit_obsidian]] 会使用这里提供的行为。
- [[audit_output_contract 与 _default_ckb 的协作实现]] 汇总了本页。
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[MigrationTest]]
- [[PageFanoutBenchmarkTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
