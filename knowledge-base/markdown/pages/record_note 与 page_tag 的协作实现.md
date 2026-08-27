# record_note 与 page_tag 的协作实现

标签：#类型/代码

> 该文件集中实现实时工作树覆盖层和分析、变更、踩坑、实验、会话笔记。 它是 Code Knowledge Builder 中承载实时工作树覆盖层和分析、变更、踩坑、实验、会话笔记的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当实时工作树覆盖层和分析、变更、踩坑、实验、会话笔记的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/workspace_notes.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/workspace_notes.py:1:1)  `scripts/ckb_core/workspace_notes.py:1-374`

## 相关代码

- 实现时会用到 [[ensure_local_openers]]。
- 实现时会用到 [[ensure_local_openers 与 default_openers 的协作实现]]。
- 主要代码单元是 [[record_note]]。
- 实现时会用到 [[retrieve 与 _tokens 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[start_session]] 会使用这里提供的行为。
- [[start_session 与 _session_directory 的协作实现]] 会使用这里提供的行为。
- [[status 与 _load_state 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 10 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `page_tag` | 该附属代码负责实时工作树覆盖层和分析、变更、踩坑、实验、会话笔记，并把结果交给所属页面中的主流程使用。 |
| `_markdown_root` | 该附属代码负责实时工作树覆盖层和分析、变更、踩坑、实验、会话笔记，并把结果交给所属页面中的主流程使用。 |
| `_resolve_page_titles` | 该附属代码负责实时工作树覆盖层和分析、变更、踩坑、实验、会话笔记，并把结果交给所属页面中的主流程使用。 |
| `_source_links_for_titles` | 该附属代码负责生成并核对可直接打开源码位置的 URI，并把结果交给所属页面中的主流程使用。 |
| `queue_pending_note` | 该附属代码负责管理 Agent 会话、构建中记录和修改总结落页，并把结果交给所属页面中的主流程使用。 |
| `selectors_for_changed_paths` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `materialize_pending_notes` | 该附属代码负责管理 Agent 会话、构建中记录和修改总结落页，并把结果交给所属页面中的主流程使用。 |
| `audit_notes` | 该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。 |
| `sync_workspace` | 该附属代码负责保存实时工作区变化和双链知识记录，并把结果交给所属页面中的主流程使用。 |
| `workspace_status` | 该附属代码负责保存实时工作区变化和双链知识记录，并把结果交给所属页面中的主流程使用。 |

</details>
