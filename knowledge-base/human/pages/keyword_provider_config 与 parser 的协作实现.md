# keyword_provider_config 与 parser 的协作实现

标签：#类型/代码

> 文件 `scripts/ckb.py`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。 它属于所有 Harness 调用 CKB 的统一公开入口，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当公开命令、参数合同、退出状态或子系统入口变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:1:1)  `scripts/ckb.py:1-1780`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 主要代码单元是 [[emit]]。
- 主要代码单元是 [[keyword_provider_config]]。
- 主要代码单元是 [[main（ckb 实现）]]。
- 主要代码单元是 [[parser]]。
- 实现时会用到 [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]。
- 实现时会用到 [[start_scope_extension 与 _error 的协作实现]]。

## 谁会来到这里

- [[parser]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[PdfReferenceExtractionTests]]
- [[PdfReferenceExtractionTests 等测试场景]]
- [[ReferencePdfEffectBenchmarkTests]]
- [[command 等测试场景]]
- [[main（benchmark_obsidian_canvas_navigation 测试）]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `add_initial_arguments` | `add_initial_arguments` 完成CKB 公开命令分派中的一个明确步骤。 |
| `add_csharp_arguments` | `add_csharp_arguments` 完成CKB 公开命令分派中的一个明确步骤。 |
| `add_git_bootstrap_arguments` | `add_git_bootstrap_arguments` 完成CKB 公开命令分派中的一个明确步骤。 |
| `add_keyword_provider_arguments` | `add_keyword_provider_arguments` 完成CKB 公开命令分派中的一个明确步骤。 |
| `add_keyword_fallback_arguments` | `add_keyword_fallback_arguments` 完成CKB 公开命令分派中的一个明确步骤。 |
| `keyword_fallback_options` | `keyword_fallback_options` 完成CKB 公开命令分派中的一个明确步骤。 |
| `emit_prompt_json` | `emit_prompt_json` 生成并写入CKB 公开命令分派所需的数据或状态。 |
| `emit_prompt_text` | `emit_prompt_text` 生成并写入CKB 公开命令分派所需的数据或状态。 |
| `_session_query` | `_session_query` 完成CKB 公开命令分派中的一个明确步骤。 |

</details>
