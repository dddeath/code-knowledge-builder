# ingest_reference 与 _root 的协作实现

标签：#类型/代码

> 文件 `scripts/ckb_core/reference_documents.py`负责管理参考资料的吸收、审阅、投影、索引、失败重试与回滚。 它属于外部资料进入独立参考层的受控生命周期入口，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当资料格式、来源定位、审阅合同、状态迁移或回滚规则变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_documents.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_documents.py:1:1)  `scripts/ckb_core/reference_documents.py:1-903`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[extract_pdf 与 PdfExtractionError 的协作实现]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[ingest]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 主要代码单元是 [[ingest_reference]]。
- 实现时会用到 [[render_integration 与 harness_retrieval_contract 的协作实现]]。
- 实现时会用到 [[retrieve 与 _tokens 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。

## 谁会来到这里

- [[PageFanoutBenchmarkTests]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[finalize 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[ingest_reference]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanPageAuthoringValidationFailureTests]]
- [[HumanPageTemplateRegistryTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 24 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_root` | `_root` 完成参考资料生命周期中的一个明确步骤。 |
| `_manifests` | `_manifests` 完成参考资料生命周期中的一个明确步骤。 |
| `_manifest` | `_manifest` 完成参考资料生命周期中的一个明确步骤。 |
| `_validate_output` | `_validate_output` 校验参考资料生命周期所需的数据或状态。 |
| `_validate_license` | `_validate_license` 校验参考资料生命周期所需的数据或状态。 |
| `_decode_source` | `_decode_source` 完成参考资料生命周期中的一个明确步骤。 |
| `_managed_path` | `_managed_path` 完成参考资料生命周期中的一个明确步骤。 |
| `_set_marker` | `_set_marker` 完成参考资料生命周期中的一个明确步骤。 |
| `_pending_pdf_next_steps` | `_pending_pdf_next_steps` 完成参考资料生命周期中的一个明确步骤。 |
| `write_reference_review_template` | `write_reference_review_template` 生成并写入参考资料生命周期所需的数据或状态。 |
| `_source_lines` | `_source_lines` 完成参考资料生命周期中的一个明确步骤。 |
| `_validate_pdf_claims` | `_validate_pdf_claims` 校验参考资料生命周期所需的数据或状态。 |
| `_validate_review` | `_validate_review` 校验参考资料生命周期所需的数据或状态。 |
| `_source_uri` | `_source_uri` 完成参考资料生命周期中的一个明确步骤。 |
| `_pdf_source_uri` | `_pdf_source_uri` 完成参考资料生命周期中的一个明确步骤。 |
| `_render_reference_page` | `_render_reference_page` 生成并写入参考资料生命周期所需的数据或状态。 |
| `_active_reviewed` | `_active_reviewed` 完成参考资料生命周期中的一个明确步骤。 |
| `project_references` | `project_references` 生成并写入参考资料生命周期所需的数据或状态。 |
| `submit_reference_review` | `submit_reference_review` 完成参考资料生命周期中的一个明确步骤。 |
| `reference_machine_records` | `reference_machine_records` 完成参考资料生命周期中的一个明确步骤。 |
| `_reference_sections` | `_reference_sections` 完成参考资料生命周期中的一个明确步骤。 |
| `audit_references` | `audit_references` 校验参考资料生命周期所需的数据或状态。 |
| `list_references` | `list_references` 完成参考资料生命周期中的一个明确步骤。 |
| `rollback_reference` | `rollback_reference` 受控释放或回滚参考资料生命周期所需的数据或状态。 |

</details>
