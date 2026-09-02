# audit_feedback

标签：#类型/代码

> `audit_feedback` 是 `scripts/ckb_core/feedback.py` 中负责检查反馈锚点、状态、镜像、归档与落实记录的一致性的函数。 它按源码所示的参数、条件分支和数据结构完成检查反馈锚点、状态、镜像、归档与落实记录的一致性，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当定位式人工反馈的创建、重定位、审计与归档的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/feedback.py 第 437 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/feedback.py:437:1)  `scripts/ckb_core/feedback.py:437-545`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_feedback 与 _contains_chinese 的协作实现]]。

## 谁会来到这里

- [[audit_agent_protocol]] 会使用这里提供的行为。
- [[audit_feedback 与 _contains_chinese 的协作实现]] 汇总了本页。
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
