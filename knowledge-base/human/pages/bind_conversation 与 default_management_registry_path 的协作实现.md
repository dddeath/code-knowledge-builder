# bind_conversation 与 default_management_registry_path 的协作实现

标签：#类型/代码

> `scripts/ckb_core/management_agent.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责管理 Agent 的会话绑定、执行队列、开发任务交接与合并审计状态。

## 什么时候需要修改

当 `scripts/ckb_core/management_agent.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/management_agent.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/management_agent.py:1:1)  `scripts/ckb_core/management_agent.py:1-1337`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[append 等测试场景]]。
- 实现时会用到 [[audit_gap_register 与 _root 的协作实现]]。
- 主要代码单元是 [[bind_conversation]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[initialize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[maintenance_check]]。
- 实现时会用到 [[maintenance_check 与 capability_matrix 的协作实现]]。
- 实现时会用到 [[retrieve_machine]]。

## 谁会来到这里

- [[append]] 会使用这里提供的行为。
- [[append 等测试场景]] 会使用这里提供的行为。
- [[bind_conversation]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[render_integration]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 40 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `default_management_registry_path` | `default_management_re...` 是第 51-53 行的函数，供所属页面定位实现。 |
| `_path_key` | `_path_key` 是第 56-58 行的函数，供所属页面定位实现。 |
| `_normalized_path` | `_normalized_path` 是第 61-62 行的函数，供所属页面定位实现。 |
| `_empty_registry` | `_empty_registry` 是第 65-71 行的函数，供所属页面定位实现。 |
| `_read_registry` | `_read_registry` 是第 74-85 行的函数，供所属页面定位实现。 |
| `_registry_lock` | `_registry_lock` 是第 89-113 行的函数，供所属页面定位实现。 |
| `_locked_registry` | `_locked_registry` 是第 117-127 行的函数，供所属页面定位实现。 |
| `_audit_event` | `_audit_event` 是第 130-140 行的函数，供所属页面定位实现。 |
| `_capability` | `_capability` 是第 143-144 行的函数，供所属页面定位实现。 |
| `harness_capabilities` | `harness_capabilities` 是第 147-161 行的函数，供所属页面定位实现。 |
| `binding_schema` | `binding_schema` 是第 164-217 行的函数，供所属页面定位实现。 |
| `canonical_binding_input` | `canonical_binding_input` 是第 220-248 行的函数，供所属页面定位实现。 |
| `_privacy_errors` | `_privacy_errors` 是第 251-262 行的函数，供所属页面定位实现。 |
| `audit_manager_registry` | `audit_manager_registry` 是第 265-352 行的函数，供所属页面定位实现。 |
| `_git` | `_git` 是第 355-362 行的函数，供所属页面定位实现。 |
| `_is_within` | `_is_within` 是第 365-368 行的函数，供所属页面定位实现。 |
| `_git_preflight` | `_git_preflight` 是第 371-414 行的函数，供所属页面定位实现。 |
| `_binding_identity` | `_binding_identity` 是第 417-418 行的函数，供所属页面定位实现。 |
| `_binding_project` | `_binding_project` 是第 421-422 行的函数，供所属页面定位实现。 |
| `_binding_id` | `_binding_id` 是第 425-432 行的函数，供所属页面定位实现。 |
| `_find_binding` | `_find_binding` 是第 553-559 行的函数，供所属页面定位实现。 |
| `_runtime_state` | `_runtime_state` 是第 562-602 行的函数，供所属页面定位实现。 |
| `binding_status` | `binding_status` 是第 605-625 行的函数，供所属页面定位实现。 |
| `unbind_conversation` | `unbind_conversation` 是第 628-669 行的函数，供所属页面定位实现。 |
| `_sqlite_integrity` | `_sqlite_integrity` 是第 672-683 行的函数，供所属页面定位实现。 |
| `_feedback_snapshot` | `_feedback_snapshot` 是第 686-704 行的函数，供所属页面定位实现。 |
| `_knowledge_snapshot` | `_knowledge_snapshot` 是第 707-743 行的函数，供所属页面定位实现。 |
| `_single_quote` | `_single_quote` 是第 746-747 行的函数，供所属页面定位实现。 |
| `_manager_commands` | `_manager_commands` 是第 750-767 行的函数，供所属页面定位实现。 |
| `_management_prompt` | `_management_prompt` 是第 770-843 行的函数，供所属页面定位实现。 |
| `audit_management_prompt` | `audit_management_prompt` 是第 846-883 行的函数，供所属页面定位实现。 |
| `management_context` | `management_context` 是第 886-932 行的函数，供所属页面定位实现。 |
| `_task_id` | `_task_id` 是第 935-936 行的函数，供所属页面定位实现。 |
| `_task_artifact_root` | `_task_artifact_root` 是第 939-940 行的函数，供所属页面定位实现。 |
| `_find_task` | `_find_task` 是第 943-944 行的函数，供所属页面定位实现。 |
| `_bounded_values` | `_bounded_values` 是第 947-957 行的函数，供所属页面定位实现。 |
| `_task_prompt` | `_task_prompt` 是第 960-1011 行的函数，供所属页面定位实现。 |
| `create_management_task` | `create_management_task` 是第 1014-1153 行的函数，供所属页面定位实现。 |
| `management_task_status` | `management_task_status` 是第 1156-1237 行的函数，供所属页面定位实现。 |
| `review_management_task` | `review_management_task` 是第 1240-1336 行的函数，供所属页面定位实现。 |

</details>
