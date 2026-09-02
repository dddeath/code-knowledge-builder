# audit_global

标签：#类型/代码

> `audit_global` 位于 `scripts/ckb_core/pipeline.py` 第 2891-3204 行，本页用固定源码范围说明它如何校验输入、状态、证据或输出合同。 `audit_global` 负责在源码审阅 pack、提交、审计和生成流水线中校验输入、状态、证据或输出合同。

## 什么时候需要修改

当 `scripts/ckb_core/pipeline.py` 中 `audit_global` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/pipeline.py 第 2891 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:2891:1)  `scripts/ckb_core/pipeline.py:2891-3204`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_agent_protocol]]。
- 实现时会用到 [[audit_agent_protocol 与 _default_python 的协作实现]]。
- 实现时会用到 [[audit_global 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[audit_references]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[load_page_config 与 _merge_known 的协作实现]]。
- 实现时会用到 [[module_name 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[preflight 与 git 的协作实现]]。
- 实现时会用到 [[query_graph 与 _networkx_modules 的协作实现]]。
- 实现时会用到 [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[sync_human_layer]]。
- 实现时会用到 [[sync_human_layer 与 _source_manifest 的协作实现]]。

## 谁会来到这里

- [[audit_global 与 _replace_output_prefix 的协作实现]] 汇总了本页。
- [[main（ckb 实现）]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanPageTemplateValidationTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[KeywordFallbackRetrievalWiringTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
