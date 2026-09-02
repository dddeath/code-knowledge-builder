# parser

标签：#类型/代码

> `parser` 位于 `scripts/ckb.py` 第 303-853 行，本页用固定源码范围说明它如何解析、规范化并冻结调用输入。 `parser` 负责在CKB 主命令解析、分发和退出状态中解析、规范化并冻结调用输入。

## 什么时候需要修改

当 `scripts/ckb.py` 中 `parser` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 303 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:303:1)  `scripts/ckb.py:303-853`

## 相关代码

- 实现时会用到 [[AutomationTest.register]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[append 等测试场景]]。
- 实现时会用到 [[audit_global 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[bind_conversation 与 default_management_registry_path 的协作实现]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[keyword_provider_config 与 parser 的协作实现]]。
- 实现时会用到 [[refresh]]。
- 实现时会用到 [[retrieve]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[rollback]]。
- 实现时会用到 [[sample 等测试场景]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[build 的协作边界]] 会使用这里提供的行为。
- [[build_manual_index 等测试场景]] 会使用这里提供的行为。
- [[command 等测试场景]] 会使用这里提供的行为。
- [[deploy 的协作边界]] 会使用这里提供的行为。
- [[execute 等测试场景]] 会使用这里提供的行为。
- [[get_human_page_template 与 SectionContract 的协作实现]] 会使用这里提供的行为。
- [[keyword_provider_config 与 parser 的协作实现]] 汇总了本页。
- [[main（benchmark_obsidian_canvas_navigation 测试）]] 会使用这里提供的行为。
- [[main（build_runtime_payload 实现）]] 会使用这里提供的行为。
- [[main（generate_large_fixture 测试）]] 会使用这里提供的行为。
- [[main（make_source_patch 实现）]] 会使用这里提供的行为。
- [[main（session_stdio_harness_probe 测试）]] 会使用这里提供的行为。
- [[main（session_stdio_reactivation_probe 测试）]] 会使用这里提供的行为。
- [[one_cycle 等测试场景]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[preflight 与 git 的协作实现]] 会使用这里提供的行为。
- [[run 等测试场景]] 会使用这里提供的行为。
- [[source_files 与 sha256 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[ScopeExtensionTest]]
- [[build_manual_index 等测试场景]]
- [[command 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
