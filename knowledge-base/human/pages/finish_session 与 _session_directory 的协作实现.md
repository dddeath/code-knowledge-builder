# finish_session 与 _session_directory 的协作实现

标签：#类型/代码

> 该文件集中实现Agent 任务会话、构建中笔记排队、修改总结和生命周期状态。 它是 Code Knowledge Builder 中承载Agent 任务会话、构建中笔记排队、修改总结和生命周期状态的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当Agent 任务会话、构建中笔记排队、修改总结和生命周期状态的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[finish_session]]。
- 与 [[record_note]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note 与 page_tag 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[finish_session]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 6 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_session_directory` | 该附属代码负责管理 Agent 会话、构建中记录和修改总结落页，并把结果交给所属页面中的主流程使用。 |
| `_new_session_id` | 该附属代码负责管理 Agent 会话、构建中记录和修改总结落页，并把结果交给所属页面中的主流程使用。 |
| `_record_or_queue` | 该附属代码负责Agent 任务会话、构建中笔记排队、修改总结和生命周期状态，并把结果交给所属页面中的主流程使用。 |
| `start_session` | 校验任务问题和检索档位后同步工作树覆盖层，建立 active 会话与来源关联笔记；机器层未完成时明确记录等待并将笔记交统一队列入口。 |
| `_summary_heading_errors` | 该附属代码负责Agent 任务会话、构建中笔记排队、修改总结和生命周期状态，并把结果交给所属页面中的主流程使用。 |
| `sessions_status` | 该附属代码负责管理 Agent 会话、构建中记录和修改总结落页，并把结果交给所属页面中的主流程使用。 |

</details>
