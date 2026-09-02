# audit_work_record_index

标签：#类型/代码

> `audit_work_record_index` 是 `scripts/ckb_core/work_record_index.py` 第 230-241 行定义的函数，本页绑定该固定源码范围。 负责实现 `work_record_index.py` 中由固定源码定义的命令或知识库处理步骤。

## 什么时候需要修改

当 `audit_work_record_index` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/work_record_index.py 第 230 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/work_record_index.py:230:1)  `scripts/ckb_core/work_record_index.py:230-241`

## 相关代码

- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_work_record_index 与 _contains_chinese 的协作实现]]。

## 谁会来到这里

- [[audit_agent_protocol]] 会使用这里提供的行为。
- [[audit_work_record_index 与 _contains_chinese 的协作实现]] 汇总了本页。
- [[finalize 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- [[replace_note 与 RecordReplaceLockError 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[MigrationTest]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
