# parser

标签：#类型/代码

> 代码单元 `parser`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。 它属于所有 Harness 调用 CKB 的统一公开入口，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当公开命令、参数合同、退出状态或子系统入口变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 323 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:323:1)  `scripts/ckb.py:323-919`

## 相关代码

- 实现时会用到 [[AutomationTest.register]]。
- 实现时会用到 [[FactFreshnessStateMachineTest]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[append 等测试场景]]。
- 实现时会用到 [[bind_conversation 与 default_management_registry_path 的协作实现]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[finalize]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[graph 的协作边界]]。
- 实现时会用到 [[ingest]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[keyword_provider_config 与 parser 的协作实现]]。
- 实现时会用到 [[refresh]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[build 的协作边界]] 会使用这里提供的行为。
- [[ckb_canvas 的协作边界]] 会使用这里提供的行为。
- [[cli 的协作边界（prototypes）]] 会使用这里提供的行为。
- [[command 等测试场景]] 会使用这里提供的行为。
- [[deploy 的协作边界]] 会使用这里提供的行为。
- [[extract_pdf]] 会使用这里提供的行为。
- [[extract_pdf 与 PdfExtractionError 的协作实现]] 会使用这里提供的行为。
- [[get_human_page_template 与 SectionContract 的协作实现]] 会使用这里提供的行为。
- [[keyword_provider_config 与 parser 的协作实现]] 汇总了本页。
- [[main（benchmark_obsidian_canvas_navigation 测试）]] 会使用这里提供的行为。
- [[main（build_runtime_payload 实现）]] 会使用这里提供的行为。
- [[main（generate_large_fixture 测试）]] 会使用这里提供的行为。
- [[main（make_source_patch 实现）]] 会使用这里提供的行为。
- [[main（provider_integration 测试）]] 会使用这里提供的行为。
- [[main（recompute 测试）]] 会使用这里提供的行为。
- [[main（session_stdio_harness_probe 测试）]] 会使用这里提供的行为。
- [[main（session_stdio_reactivation_probe 测试）]] 会使用这里提供的行为。
- [[one_cycle 等测试场景]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[parse_file 与 _language 的协作实现]] 会使用这里提供的行为。
- [[preflight 与 git 的协作实现]] 会使用这里提供的行为。
- [[recompute 的协作边界]] 会使用这里提供的行为。
- [[run 等测试场景]] 会使用这里提供的行为。
- [[run_failure_probe 等测试场景]] 会使用这里提供的行为。
- [[source_files 与 sha256 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[PdfReferenceExtractionTests]]
- [[PdfReferenceExtractionTests 等测试场景]]
- [[command 等测试场景]]
- [[main（benchmark_obsidian_canvas_navigation 测试）]]
- [[main（generate_large_fixture 测试）]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
