# CkbError 与 DependencyError 的协作实现

标签：#类型/代码

> `scripts/ckb_core/common.py` 是 `scripts/ckb_core/common.py` 中负责汇总并提供路径、时间、JSON、哈希、进程与通用错误处理的文件入口。 它按源码所示的参数、条件分支和数据结构完成汇总并提供路径、时间、JSON、哈希、进程与通用错误处理，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当路径、时间、JSON、哈希、进程与通用错误处理的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-168`

## 相关代码

- 主要代码单元是 [[CkbError]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[contracts 的协作边界（2ef5688e）]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[ScopeExtensionTest]] 会使用这里提供的行为。
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[audit_feedback 与 _contains_chinese 的协作实现]] 会使用这里提供的行为。
- [[audit_gap_register 与 _root 的协作实现]] 会使用这里提供的行为。
- [[audit_migration]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[audit_obsidian 与 prepare_vault 的协作实现]] 会使用这里提供的行为。
- [[audit_operation_journal 与 _root 的协作实现]] 会使用这里提供的行为。
- [[bind_conversation]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[check_fact_freshness]] 会使用这里提供的行为。
- [[check_fact_freshness 与 _root 的协作实现]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[deployment_plan 与 skill_root 的协作实现]] 会使用这里提供的行为。
- [[doctor_report]] 会使用这里提供的行为。
- [[doctor_report 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[extract_pdf]] 会使用这里提供的行为。
- [[extract_pdf 与 PdfExtractionError 的协作实现]] 会使用这里提供的行为。
- [[finalize]] 会使用这里提供的行为。
- [[finalize 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[ingest_reference]] 会使用这里提供的行为。
- [[ingest_reference 与 _root 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- [[module_name 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[parse_file 与 _language 的协作实现]] 会使用这里提供的行为。
- [[preflight]] 会使用这里提供的行为。
- [[preflight 与 git 的协作实现]] 会使用这里提供的行为。
- [[propose_template]] 会使用这里提供的行为。
- [[propose_template 与 _canonical_bytes 的协作实现]] 会使用这里提供的行为。
- [[query_graph 与 _networkx_modules 的协作实现]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[register_obsidian_plugin]] 会使用这里提供的行为。
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]] 会使用这里提供的行为。
- [[replace_note]] 会使用这里提供的行为。
- [[replace_note 与 RecordReplaceLockError 的协作实现]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[start_scope_extension]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。
- [[start_session]] 会使用这里提供的行为。
- [[start_session 与 _session_directory 的协作实现]] 会使用这里提供的行为。
- [[sync_human_layer]] 会使用这里提供的行为。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register]]
- [[AutomationTest.register 等测试场景]]
- [[CanvasBenchmarkContractTests]]
- [[CanvasBenchmarkContractTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 18 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `DependencyError` | 处理 `dependencyerror` 对应的数据与约束。 |
| `ReviewRequired` | 处理 `reviewrequired` 对应的数据与约束。 |
| `AuditError` | 处理 `auditerror` 对应的数据与约束。 |
| `StaleSourceError` | 处理 `stalesourceerror` 对应的数据与约束。 |
| `utc_now` | 处理 `now` 对应的数据与约束。 |
| `stable_id` | 根据固定输入计算 `stable_id` 稳定标识。 |
| `sha256_file` | 处理 `file` 对应的数据与约束。 |
| `json_load` | 处理 `load` 对应的数据与约束。 |
| `json_write` | 处理 `write` 对应的数据与约束。 |
| `background_process_options` | 处理 `process_options` 对应的数据与约束。 |
| `run` | 执行 `run` 对应的数据与约束。 |
| `command_version` | 处理 `version` 对应的数据与约束。 |
| `clear_markers` | 处理 `markers` 对应的数据与约束。 |
| `write_marker` | 写入 `marker` 对应的数据与约束。 |
| `safe_title` | 处理 `title` 对应的数据与约束。 |
| `path_inside` | 生成 `inside` 对应的数据与约束。 |
| `safe_rmtree` | 处理 `rmtree` 对应的数据与约束。 |
| `temp_directory` | 处理 `directory` 对应的数据与约束。 |

</details>
