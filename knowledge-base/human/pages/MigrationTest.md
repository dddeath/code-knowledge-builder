# MigrationTest

标签：#类型/代码

> `MigrationTest` 是增量迁移的端到端回归测试夹具。 它在临时 Git 仓库中生成旧版与新版源码，完成两套知识库构建，并验证合法追加仍通过、不可变基线变化会失败。

## 什么时候需要修改

当迁移流程增加新阶段、保存新型用户数据或调整完成门时，需要扩展该测试类。

## 在代码中的位置

[打开源码：tests/test_migration.py 第 57 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:57:1)  `tests/test_migration.py:57-176`

## 相关代码

- 实现时会用到 [[AutomationTest.event]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[status 与 _load_state 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.event]] 关联到这里的验证场景。
- [[AutomationTest.event 等测试场景]] 关联到这里的验证场景。
- [[LspClient.start]] 关联到这里的验证场景。
- [[LspClient.start 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[MigrationTest 等测试场景]] 汇总了本页。
- [[add_git_bootstrap_arguments]] 关联到这里的验证场景。
- [[add_initial_arguments]] 关联到这里的验证场景。
- [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]] 关联到这里的验证场景。
- [[audit_migration]] 关联到这里的验证场景。
- [[audit_migration 与 _entity_key 的协作实现]] 关联到这里的验证场景。
- [[create_source_snapshot]] 关联到这里的验证场景。
- [[create_source_snapshot 与 git 的协作实现]] 关联到这里的验证场景。
- [[ensure_local_openers]] 关联到这里的验证场景。
- [[execute]] 关联到这里的验证场景。
- [[ingest_event 与 default_registry_path 的协作实现]] 关联到这里的验证场景。
- [[load_page_config]] 关联到这里的验证场景。
- [[load_page_config 与 _merge_known 的协作实现]] 关联到这里的验证场景。
- [[module_name]] 关联到这里的验证场景。
- [[module_name 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[parse_file]] 关联到这里的验证场景。
- [[parse_file 与 _language 的协作实现]] 关联到这里的验证场景。
- [[parser]] 关联到这里的验证场景。
- [[prepare_vault]] 关联到这里的验证场景。
- [[prepare_vault 与 install_obsidian 的协作实现]] 关联到这里的验证场景。
- [[query_graph 与 _networkx_modules 的协作实现]] 关联到这里的验证场景。
- [[record_note]] 关联到这里的验证场景。
- [[record_note 与 page_tag 的协作实现]] 关联到这里的验证场景。
- [[remove]] 关联到这里的验证场景。
- [[remove 与 skill_root 的协作实现]] 关联到这里的验证场景。
- [[render_integration 与 _looks_windows 的协作实现]] 关联到这里的验证场景。
- [[retrieve]] 关联到这里的验证场景。
- [[retrieve 与 _tokens 的协作实现]] 关联到这里的验证场景。
- [[retrieve_machine]] 关联到这里的验证场景。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[run]] 关联到这里的验证场景。
- [[run 与 CkbError 的协作实现]] 关联到这里的验证场景。
- [[status]] 关联到这里的验证场景。
- [[status 与 _load_state 的协作实现]] 关联到这里的验证场景。
- [[sync_human_layer]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 3 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `MigrationTest.setUp` | 创建临时 Python 仓库、首个 Git 提交和确定性测试提供器。 |
| `MigrationTest.tearDown` | 恢复测试环境变量并清理临时迁移夹具。 |
| `MigrationTest.test_exact_blob_facts_and_agent_reviews_are_reused` | 端到端验证精确复用、差量审阅、基线保留、合法 Hook 写入、篡改失败和 Wiki 重链接。 |

</details>
