# status

标签：#类型/代码

> `status` 根据分段和审阅包的当前状态计算下一项可执行动作。 它为 CLI 和 Agent 返回 `build-chunk`、`review-pack`、`finalize` 或 `complete`，避免重复解析已经通过的分段。

## 什么时候需要修改

当状态机字段、续建顺序或审阅包与分段的对应关系变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/ckb_core/pipeline.py 第 3174 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:3174:1)  `scripts/ckb_core/pipeline.py:3174-3184`

## 相关代码

- 实现时会用到 [[status 与 _load_state 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.event 等测试场景]] 会使用这里提供的行为。
- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[LspClient.start 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[MigrationTest]] 会使用这里提供的行为。
- [[MigrationTest 等测试场景]] 会使用这里提供的行为。
- [[audit_migration]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[create_source_snapshot]] 会使用这里提供的行为。
- [[create_source_snapshot 与 git 的协作实现]] 会使用这里提供的行为。
- [[execute 等测试场景]] 会使用这里提供的行为。
- [[ingest_event]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[load_page_config 与 _merge_known 的协作实现]] 会使用这里提供的行为。
- [[main 与 sha256 的协作实现]] 会使用这里提供的行为。
- [[main（build_runtime_payload 实现）]] 会使用这里提供的行为。
- [[main（fake_logseq 测试）]] 会使用这里提供的行为。
- [[module_name 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[package_showcase]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[prepare_vault 与 install_obsidian 的协作实现]] 会使用这里提供的行为。
- [[query_graph]] 会使用这里提供的行为。
- [[query_graph 与 _networkx_modules 的协作实现]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[remove]] 会使用这里提供的行为。
- [[remove 与 skill_root 的协作实现]] 会使用这里提供的行为。
- [[render_integration]] 会使用这里提供的行为。
- [[render_integration 与 _looks_windows 的协作实现]] 会使用这里提供的行为。
- [[retrieve]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[run 与 CkbError 的协作实现]] 会使用这里提供的行为。
- [[source_files 与 sha256 的协作实现]] 会使用这里提供的行为。
- [[start_session]] 会使用这里提供的行为。
- [[start_session 与 _session_directory 的协作实现]] 会使用这里提供的行为。
- [[status 与 _load_state 的协作实现]] 汇总了本页。
- [[sync_human_layer]] 会使用这里提供的行为。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
