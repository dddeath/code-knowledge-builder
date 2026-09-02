# start_session

标签：#类型/代码

> `start_session` 是源码中负责管理 Agent 会话、构建中记录和修改总结落页的命名代码单元。 它在所属模块内执行管理 Agent 会话、构建中记录和修改总结落页，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当管理 Agent 会话、构建中记录和修改总结落页所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_maintenance.py 第 70 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:70:1)  `scripts/ckb_core/agent_maintenance.py:70-142`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[finalize]]。
- 实现时会用到 [[record_note 与 page_tag 的协作实现]]。
- 实现时会用到 [[retrieve]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[start_session 与 _session_directory 的协作实现]]。

## 谁会来到这里

- [[start_session 与 _session_directory 的协作实现]] 汇总了本页。
