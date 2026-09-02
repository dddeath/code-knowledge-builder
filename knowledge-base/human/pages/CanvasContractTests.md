# CanvasContractTests

标签：#类型/代码

> `CanvasContractTests` 位于 `tests/test_ckb_canvas_contracts.py` 第 38-146 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。 `CanvasContractTests` 负责在对应能力的可执行成功、失败和回归验证中验证目标行为、失败分类和回归边界。

## 什么时候需要修改

当 `tests/test_ckb_canvas_contracts.py` 中 `CanvasContractTests` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_ckb_canvas_contracts.py 第 38 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_canvas_contracts.py:38:1)  `tests/test_ckb_canvas_contracts.py:38-146`

## 相关代码

- 实现时会用到 [[build_case]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[commands 的协作边界]]。
- 实现时会用到 [[contracts 的协作边界（2ef5688e）]]。
- 实现时会用到 [[source_files]]。
- 实现时会用到 [[validate]]。

## 谁会来到这里

- [[CanvasContractTests 等测试场景]] 汇总了本页。
- [[FactFreshnessStateMachineTest]] 关联到这里的验证场景。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 关联到这里的验证场景。
- [[SourceLinkRenderer.uri]] 关联到这里的验证场景。
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]] 关联到这里的验证场景。
- [[build_case]] 关联到这里的验证场景。
- [[build_case 等测试场景]] 关联到这里的验证场景。
- [[check_fact_freshness]] 关联到这里的验证场景。
- [[ckb_canvas 的协作边界]] 关联到这里的验证场景。
- [[command]] 关联到这里的验证场景。
- [[commands 的协作边界]] 关联到这里的验证场景。
- [[freeze 的协作边界]] 关联到这里的验证场景。
- [[graph 的协作边界]] 关联到这里的验证场景。
- [[ingest 与 connect 的协作实现]] 关联到这里的验证场景。
- [[render_integration 与 _looks_windows 的协作实现]] 关联到这里的验证场景。
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]] 关联到这里的验证场景。
- [[source_files]] 关联到这里的验证场景。
- [[transaction 的协作边界]] 关联到这里的验证场景。
- [[validate]] 关联到这里的验证场景。
- [[validate 与 canonical 的协作实现]] 关联到这里的验证场景。

## 相关测试

- [[CanvasGraphTests]]
- [[CanvasPathTests]]
- [[CanvasTransactionTests]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanMaintenancePromptRegistryTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 8 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `CanvasContractTests.test_all_nine_schemas_parse_and_match_design` | `test_all_nine_schemas_parse_and_mat…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasContractTests.test_design_success_and_failure_fixtures_validate` | `test_design_success_and_failure_fix…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasContractTests.test_each_request_object_layer_rejects_unknown_field_with_exit_2` | `test_each_request_object_layer_reje…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasContractTests.test_each_request_object_layer_rejects_unknown_field_with_exit_2.variants` | `variants` 在 `test_ckb_canvas_contracts.py` 中用于验证目标行为、失败分类和回归边界。 |
| `CanvasContractTests._assert_record_rejected` | `_assert_record_rejected` 在 `test_ckb_canvas_contracts.py` 中用于验证目标行为、失败分类和回归边界。 |
| `CanvasContractTests.test_record_1_keyword_variant_and_unknown_candidate_rejected` | `test_record_1_keyword_variant_and_u…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasContractTests.test_pack_record_crosslink_is_exact` | `test_pack_record_crosslink_is_exact` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasContractTests.test_acceptance_runtime_request_is_valid` | `test_acceptance_runtime_request_is_…` 用于完成局部输入校验、转换或状态更新。 |

</details>
