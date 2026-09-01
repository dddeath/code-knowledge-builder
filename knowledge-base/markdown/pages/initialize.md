# initialize

标签：#类型/代码

> `initialize` 是 `scripts/ckb_core/pipeline.py` 第 676-922 行定义的函数，本页绑定该固定源码范围。 负责初始化、解析、Agent 审阅、全局审计和最终知识层投影。

## 什么时候需要修改

当 `initialize` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/pipeline.py 第 676 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:676:1)  `scripts/ckb_core/pipeline.py:676-922`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[initialize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[load_page_config]]。
- 实现时会用到 [[load_page_config 与 _merge_known 的协作实现]]。
- 实现时会用到 [[module_name 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[parse_file]]。
- 实现时会用到 [[parse_file 与 _language 的协作实现]]。
- 实现时会用到 [[preflight]]。
- 实现时会用到 [[preflight 与 git 的协作实现]]。

## 谁会来到这里

- [[MigrationTest]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[doctor_report 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[initialize 与 _replace_output_prefix 的协作实现]] 汇总了本页。
- [[keyword_provider_config 与 parser 的协作实现]] 会使用这里提供的行为。
- [[preflight 与 git 的协作实现]] 会使用这里提供的行为。
- [[run 等测试场景]] 会使用这里提供的行为。
- [[start_scope_extension]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[ScopeExtensionTest]]
- [[ScopeExtensionTest 等测试场景]]
- [[append 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
