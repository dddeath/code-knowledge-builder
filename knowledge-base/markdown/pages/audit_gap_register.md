# audit_gap_register

标签：#类型/代码

> `audit_gap_register` 是 `scripts/ckb_core/research_gaps.py` 第 233-272 行定义的函数，本页绑定该固定源码范围。 负责实现 `research_gaps.py` 中由固定源码定义的命令或知识库处理步骤。

## 什么时候需要修改

当 `audit_gap_register` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/research_gaps.py 第 233 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/research_gaps.py:233:1)  `scripts/ckb_core/research_gaps.py:233-272`

## 相关代码

- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_gap_register 与 _root 的协作实现]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。

## 谁会来到这里

- [[audit_gap_register 与 _root 的协作实现]] 汇总了本页。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[ScopeExtensionTest]]
- [[append 等测试场景]]
- [[command 等测试场景]]
- [[refresh 等测试场景]]
