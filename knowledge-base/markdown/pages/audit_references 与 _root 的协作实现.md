# audit_references 与 _root 的协作实现

标签：#类型/代码

> `scripts/ckb_core/reference_documents.py` 是 `scripts/ckb_core/reference_documents.py` 中负责汇总并提供审阅文本资料的归档、逐项核对、投影、索引与回滚的文件入口。 它按源码所示的参数、条件分支和数据结构完成汇总并提供审阅文本资料的归档、逐项核对、投影、索引与回滚，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当审阅文本资料的归档、逐项核对、投影、索引与回滚的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_documents.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_documents.py:1:1)  `scripts/ckb_core/reference_documents.py:1-604`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_global 与 _replace_output_prefix 的协作实现]]。
- 主要代码单元是 [[audit_references]]。
- 实现时会用到 [[propose_template 与 _canonical_bytes 的协作实现]]。
- 实现时会用到 [[render_integration 与 _looks_windows 的协作实现]]。
- 实现时会用到 [[retrieve 与 _tokens 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[rollback]]。
- 实现时会用到 [[validate 与 canonical 的协作实现]]。

## 谁会来到这里

- [[audit_references]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[RecordReplaceTests]]
- [[ScopeExtensionTest]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 20 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_root` | 处理 `root` 对应的数据与约束。 |
| `_manifests` | 处理 `manifests` 对应的数据与约束。 |
| `_manifest` | 处理 `manifest` 对应的数据与约束。 |
| `_validate_output` | 验证 `output` 对应的数据与约束。 |
| `_validate_license` | 验证 `license` 对应的数据与约束。 |
| `_decode_source` | 处理 `source` 对应的数据与约束。 |
| `_set_marker` | 处理 `marker` 对应的数据与约束。 |
| `ingest_reference` | 接收并写入 `reference` 对应的数据与约束。 |
| `write_reference_review_template` | 写入 `reference_review_template` 对应的数据与约束。 |
| `_source_lines` | 处理 `lines` 对应的数据与约束。 |
| `_validate_review` | 验证 `review` 对应的数据与约束。 |
| `_source_uri` | 处理 `uri` 对应的数据与约束。 |
| `_render_reference_page` | 渲染 `reference_page` 对应的数据与约束。 |
| `_active_reviewed` | 处理 `reviewed` 对应的数据与约束。 |
| `project_references` | 投影 `references` 对应的数据与约束。 |
| `submit_reference_review` | 处理 `reference_review` 对应的数据与约束。 |
| `reference_machine_records` | 处理 `machine_records` 对应的数据与约束。 |
| `_reference_sections` | 处理 `sections` 对应的数据与约束。 |
| `list_references` | 列出 `references` 对应的数据与约束。 |
| `rollback_reference` | 回滚 `reference` 对应的数据与约束。 |

</details>
