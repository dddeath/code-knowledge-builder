# record_note

标签：#类型/代码

> `record_note` 是源码中负责保存实时工作区变化和双链知识记录的命名代码单元。 它在所属模块内执行保存实时工作区变化和双链知识记录，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当保存实时工作区变化和双链知识记录所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/workspace_notes.py 第 106 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/workspace_notes.py:106:1)  `scripts/ckb_core/workspace_notes.py:106-183`

## 相关代码

- 实现时会用到 [[ensure_local_openers 与 default_openers 的协作实现]]。
- 实现时会用到 [[record_note 与 page_tag 的协作实现]]。
- 实现时会用到 [[retrieve 与 _tokens 的协作实现]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[sync_human_layer 与 _source_manifest 的协作实现]]。

## 谁会来到这里

- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 汇总了本页。
- [[start_session 与 _session_directory 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[MigrationTest]]
