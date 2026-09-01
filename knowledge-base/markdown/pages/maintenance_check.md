# maintenance_check

标签：#类型/代码

> `maintenance_check` 是 `scripts/ckb_core/llm_wiki_capabilities.py` 第 408-458 行定义的函数，本页绑定该固定源码范围。 负责能力矩阵、紧凑 brief 与聚合 maintain 检查的生成和审计。

## 什么时候需要修改

当 `maintenance_check` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/llm_wiki_capabilities.py 第 408 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/llm_wiki_capabilities.py:408:1)  `scripts/ckb_core/llm_wiki_capabilities.py:408-458`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_agent_protocol]]。
- 实现时会用到 [[audit_gap_register]]。
- 实现时会用到 [[audit_operation_journal]]。
- 实现时会用到 [[audit_references]]。
- 实现时会用到 [[audit_work_record_index]]。
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
