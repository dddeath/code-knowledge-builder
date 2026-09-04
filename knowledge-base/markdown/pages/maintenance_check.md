# maintenance_check

标签：#类型/代码

> 代码单元 `maintenance_check`负责维护外部 Wiki 能力的吸收状态，并给 Agent 生成紧凑能力说明。 它属于知识库能力边界与后续研究队列的机器可读入口，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当能力状态、证据链接、维护检查或紧凑说明格式变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/llm_wiki_capabilities.py 第 431 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/llm_wiki_capabilities.py:431:1)  `scripts/ckb_core/llm_wiki_capabilities.py:431-481`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_agent_protocol]]。
- 实现时会用到 [[audit_gap_register]]。
- 实现时会用到 [[audit_operation_journal]]。
- 实现时会用到 [[audit_work_record_index]]。
- 实现时会用到 [[ingest_reference 与 _root 的协作实现]]。
- 实现时会用到 [[maintenance_check 与 capability_matrix 的协作实现]]。
- 实现时会用到 [[retrieve 与 _tokens 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]。

## 谁会来到这里

- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check 与 capability_matrix 的协作实现]] 汇总了本页。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[ScopeExtensionTest]]
- [[append 等测试场景]]
- [[command 等测试场景]]
- [[refresh 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
