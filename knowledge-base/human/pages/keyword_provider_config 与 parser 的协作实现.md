# keyword_provider_config 与 parser 的协作实现

标签：#类型/代码

> `scripts/ckb.py` 页面绑定固定源码第 1-1649 行，说明该文件在CKB 主命令解析、分发和退出状态中的整体职责。 该文件负责CKB 主命令解析、分发和退出状态，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `scripts/ckb.py` 中 `scripts/ckb.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:1:1)  `scripts/ckb.py:1-1649`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_global 与 _replace_output_prefix 的协作实现]]。
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
- [[MigrationTest]]
- [[ScopeExtensionTest]]
- [[build_manual_index 等测试场景]]
- [[command 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `add_initial_arguments` | `add_initial_arguments` 在 `ckb.py` 中用于完成CKB 主命令解析、分发和退出状态中的局部职责。 |
| `add_csharp_arguments` | `add_csharp_arguments` 在 `ckb.py` 中用于完成CKB 主命令解析、分发和退出状态中的局部职责。 |
| `add_git_bootstrap_arguments` | `add_git_bootstrap_arguments` 在 `ckb.py` 中用于完成CKB 主命令解析、分发和退出状态中的局部职责。 |
| `add_keyword_provider_arguments` | `add_keyword_provider_arguments` 在 `ckb.py` 中用于完成CKB 主命令解析、分发和退出状态中的局部职责。 |
| `add_keyword_fallback_arguments` | `add_keyword_fallback_arguments` 在 `ckb.py` 中用于完成CKB 主命令解析、分发和退出状态中的局部职责。 |
| `keyword_fallback_options` | `keyword_fallback_options` 在 `ckb.py` 中用于完成CKB 主命令解析、分发和退出状态中的局部职责。 |
| `emit_prompt_json` | `emit_prompt_json` 在 `ckb.py` 中用于生成稳定排序的结构化表示或人类输出。 |
| `emit_prompt_text` | `emit_prompt_text` 在 `ckb.py` 中用于生成稳定排序的结构化表示或人类输出。 |
| `_session_query` | `_session_query` 在 `ckb.py` 中用于完成CKB 主命令解析、分发和退出状态中的局部职责。 |

</details>
