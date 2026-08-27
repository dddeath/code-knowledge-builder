# MigrationTest

标签：#类型/代码

> `MigrationTest` 构造连续两个源码提交和迁移前后知识库。 它验证增量复用、delta 审阅、目录提升后的固定快照重定位、可变数据续写和基线防篡改。

## 什么时候需要修改

迁移计划、切换方式、审阅字段或可变层规则变化时，需要修改该测试类。

## 在代码中的位置

[打开源码：tests/test_migration.py 第 57 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:57:1)  `tests/test_migration.py:57-189`

## 相关代码

- 实现时会用到 [[AutomationTest.event]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[status 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.event]] 关联到这里的验证场景。
- [[AutomationTest.event 等测试场景]] 关联到这里的验证场景。
- [[LspClient.start]] 关联到这里的验证场景。
- [[LspClient.start 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[MigrationTest 等测试场景]] 汇总了本页。
- [[SourceLinkRenderer.uri]] 关联到这里的验证场景。
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]] 关联到这里的验证场景。
- [[add_git_bootstrap_arguments]] 关联到这里的验证场景。
- [[add_initial_arguments]] 关联到这里的验证场景。
- [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]] 关联到这里的验证场景。
- [[audit_migration]] 关联到这里的验证场景。
- [[audit_migration 与 _entity_key 的协作实现]] 关联到这里的验证场景。
- [[create_source_snapshot]] 关联到这里的验证场景。
- [[create_source_snapshot 与 git 的协作实现]] 关联到这里的验证场景。
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
- [[status 与 _replace_output_prefix 的协作实现]] 关联到这里的验证场景。
- [[sync_human_layer]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 3 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `MigrationTest.setUp` | 创建临时 Python 仓库、首个 Git 提交和确定性测试提供器。 |
| `MigrationTest.tearDown` | 恢复测试环境变量并清理临时迁移夹具。 |
| `MigrationTest.test_exact_blob_facts_and_agent_reviews_are_reused` | 验证精确 blob 与中文审阅复用、可变层基线、目录提升后的路径重定位及篡改失败门。 |

</details>
