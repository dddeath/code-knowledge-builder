# audit_agent_protocol 与 _default_python 的协作实现

标签：#类型/代码

> `scripts/ckb_core/agent_protocol.py` 是 `scripts/ckb_core/agent_protocol.py` 中负责汇总并提供跨 Harness Agent 协议生成、安装、检查与维护入口的文件入口。 它按源码所示的参数、条件分支和数据结构完成汇总并提供跨 Harness Agent 协议生成、安装、检查与维护入口，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当跨 Harness Agent 协议生成、安装、检查与维护入口的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_protocol.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol.py:1:1)  `scripts/ckb_core/agent_protocol.py:1-507`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 主要代码单元是 [[audit_agent_protocol]]。
- 实现时会用到 [[audit_feedback 与 _contains_chinese 的协作实现]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[record_note 与 page_tag 的协作实现]]。
- 实现时会用到 [[retrieve]]。
- 实现时会用到 [[rollback]]。
- 实现时会用到 [[start_scope_extension 与 _error 的协作实现]]。

## 谁会来到这里

- [[audit_agent_protocol]] 会使用这里提供的行为。
- [[audit_global]] 会使用这里提供的行为。
- [[audit_global 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[run 等测试场景]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanPageTemplateValidationTests]]
- [[KeywordFallbackRetrievalWiringTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 21 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_default_python` | 返回默认 `python` 对应的数据与约束。 |
| `_default_ckb` | 返回默认 `ckb` 对应的数据与约束。 |
| `_single_quote` | 处理 `quote` 对应的数据与约束。 |
| `_command_examples` | 处理 `examples` 对应的数据与约束。 |
| `_protocol_text` | 处理 `text` 对应的数据与约束。 |
| `_adapter_texts` | 处理 `texts` 对应的数据与约束。 |
| `_managed_block` | 处理 `block` 对应的数据与约束。 |
| `_replace_managed_block` | 替换 `managed_block` 对应的数据与约束。 |
| `_instruction_roots` | 处理 `roots` 对应的数据与约束。 |
| `_write_exact_root` | 写入 `exact_root` 对应的数据与约束。 |
| `_update_markdown_ownership` | 更新 `markdown_ownership` 对应的数据与约束。 |
| `_hide_protocol_files` | 隐藏 `protocol_files` 对应的数据与约束。 |
| `_load_record` | 加载 `record` 对应的数据与约束。 |
| `_resolve_runtime` | 解析并确定 `runtime` 对应的数据与约束。 |
| `_workspace_root_allowed` | 判断 `workspace_root_allowed` 所表达的条件。 |
| `_write_workspace_root` | 写入 `workspace_root` 对应的数据与约束。 |
| `project_agent_protocol` | 投影 `agent_protocol` 对应的数据与约束。 |
| `install_agent_protocol` | 安装 `agent_protocol` 对应的数据与约束。 |
| `_expected_internal` | 处理 `internal` 对应的数据与约束。 |
| `_audit_note_storage` | 审计 `note_storage` 对应的数据与约束。 |
| `agent_protocol_status` | 汇总 `agent_protocol_status` 状态与计数。 |

</details>
