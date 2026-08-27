# run 与 CkbError 的协作实现

标签：#类型/代码

> 该文件集中实现错误类型、JSON 写入、子进程调用、路径约束和状态标记。 它是 Code Knowledge Builder 中承载错误类型、JSON 写入、子进程调用、路径约束和状态标记的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当错误类型、JSON 写入、子进程调用、路径约束和状态标记的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-158`

## 相关代码

- 主要代码单元是 [[run]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[LspClient.start 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[audit_migration]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[create_source_snapshot]] 会使用这里提供的行为。
- [[create_source_snapshot 与 git 的协作实现]] 会使用这里提供的行为。
- [[ensure_local_openers]] 会使用这里提供的行为。
- [[ensure_local_openers 与 default_openers 的协作实现]] 会使用这里提供的行为。
- [[ingest_event]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[load_page_config]] 会使用这里提供的行为。
- [[load_page_config 与 _merge_known 的协作实现]] 会使用这里提供的行为。
- [[module_name 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[package_showcase]] 会使用这里提供的行为。
- [[package_showcase 与 _parse_sample 的协作实现]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[parse_file 与 _language 的协作实现]] 会使用这里提供的行为。
- [[prepare_vault]] 会使用这里提供的行为。
- [[prepare_vault 与 install_obsidian 的协作实现]] 会使用这里提供的行为。
- [[query_graph]] 会使用这里提供的行为。
- [[query_graph 与 _networkx_modules 的协作实现]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[remove]] 会使用这里提供的行为。
- [[remove 与 skill_root 的协作实现]] 会使用这里提供的行为。
- [[render_integration]] 会使用这里提供的行为。
- [[retrieve]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[run]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[start_session]] 会使用这里提供的行为。
- [[start_session 与 _session_directory 的协作实现]] 会使用这里提供的行为。
- [[status 与 _load_state 的协作实现]] 会使用这里提供的行为。
- [[sync_human_layer]] 会使用这里提供的行为。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 17 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `CkbError` | 该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。 |
| `DependencyError` | 该附属代码负责检查依赖版本和本地运行条件，并把结果交给所属页面中的主流程使用。 |
| `ReviewRequired` | 该附属代码负责核对并登记逐实体 Agent 审阅结果，并把结果交给所属页面中的主流程使用。 |
| `AuditError` | 该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。 |
| `StaleSourceError` | 该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。 |
| `utc_now` | 该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。 |
| `stable_id` | 该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。 |
| `sha256_file` | 该附属代码负责计算机器交付物的完整性摘要，并把结果交给所属页面中的主流程使用。 |
| `json_load` | 该附属代码负责稳定读取或写入机器状态记录，并把结果交给所属页面中的主流程使用。 |
| `json_write` | 该附属代码负责稳定读取或写入机器状态记录，并把结果交给所属页面中的主流程使用。 |
| `command_version` | 该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。 |
| `clear_markers` | 该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。 |
| `write_marker` | 该附属代码负责稳定读取或写入机器状态记录，并把结果交给所属页面中的主流程使用。 |
| `safe_title` | 该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。 |
| `path_inside` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `safe_rmtree` | 该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。 |
| `temp_directory` | 该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。 |

</details>
