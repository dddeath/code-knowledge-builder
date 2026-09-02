# MigrationTest

标签：#类型/代码

> `MigrationTest` 构造连续两个源码提交和迁移前后知识库。 它验证增量复用、delta 审阅、目录提升后的固定快照重定位、可变数据续写和基线防篡改。

## 什么时候需要修改

迁移计划、切换方式、审阅字段或可变层规则变化时，需要修改该测试类。

## 在代码中的位置

[打开源码：tests/test_migration.py 第 57 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:57:1)  `tests/test_migration.py:57-189`

## 相关代码

- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[audit_global 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[execute]]。

## 谁会来到这里

- [[AutomationTest.register]] 关联到这里的验证场景。
- [[MigrationTest 等测试场景]] 汇总了本页。
- [[append 等测试场景]] 关联到这里的验证场景。
- [[audit_agent_protocol]] 关联到这里的验证场景。
- [[audit_feedback]] 关联到这里的验证场景。
- [[audit_gap_register 与 _root 的协作实现]] 关联到这里的验证场景。
- [[audit_migration 与 _entity_key 的协作实现]] 关联到这里的验证场景。
- [[audit_obsidian]] 关联到这里的验证场景。
- [[audit_obsidian 与 prepare_vault 的协作实现]] 关联到这里的验证场景。
- [[audit_output_contract]] 关联到这里的验证场景。
- [[audit_output_contract 与 _default_ckb 的协作实现]] 关联到这里的验证场景。
- [[audit_references]] 关联到这里的验证场景。
- [[audit_references 与 _root 的协作实现]] 关联到这里的验证场景。
- [[audit_work_record_index]] 关联到这里的验证场景。
- [[audit_work_record_index 与 _contains_chinese 的协作实现]] 关联到这里的验证场景。
- [[doctor_report 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[keyword_provider_config 与 parser 的协作实现]] 关联到这里的验证场景。
- [[load_page_config]] 关联到这里的验证场景。
- [[load_page_config 与 _merge_known 的协作实现]] 关联到这里的验证场景。
- [[module_name]] 关联到这里的验证场景。
- [[parse_file]] 关联到这里的验证场景。
- [[parse_file 与 _language 的协作实现]] 关联到这里的验证场景。
- [[parser]] 关联到这里的验证场景。
- [[preflight]] 关联到这里的验证场景。
- [[preflight 与 git 的协作实现]] 关联到这里的验证场景。
- [[query_graph 与 _networkx_modules 的协作实现]] 关联到这里的验证场景。
- [[record_note]] 关联到这里的验证场景。
- [[refresh]] 关联到这里的验证场景。
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]] 关联到这里的验证场景。
- [[sample 等测试场景]] 关联到这里的验证场景。
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
