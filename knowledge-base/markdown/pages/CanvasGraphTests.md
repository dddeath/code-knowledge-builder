# CanvasGraphTests

标签：#类型/代码

> `CanvasGraphTests` 位于 `tests/test_ckb_canvas_graph.py` 第 23-136 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。 `CanvasGraphTests` 负责在对应能力的可执行成功、失败和回归验证中验证目标行为、失败分类和回归边界。

## 什么时候需要修改

当 `tests/test_ckb_canvas_graph.py` 中 `CanvasGraphTests` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_ckb_canvas_graph.py 第 23 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_canvas_graph.py:23:1)  `tests/test_ckb_canvas_graph.py:23-136`

## 相关代码

- 实现时会用到 [[build_case]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[commands 的协作边界]]。
- 实现时会用到 [[contracts 的协作边界（36093e4a）]]。
- 实现时会用到 [[freeze 的协作边界]]。
- 实现时会用到 [[graph 的协作边界]]。

## 谁会来到这里

- [[CanvasContractTests]] 关联到这里的验证场景。
- [[CanvasGraphTests 等测试场景]] 汇总了本页。
- [[FactFreshnessStateMachineTest]] 关联到这里的验证场景。
- [[build_case]] 关联到这里的验证场景。
- [[check_fact_freshness]] 关联到这里的验证场景。
- [[command]] 关联到这里的验证场景。
- [[commands 的协作边界]] 关联到这里的验证场景。
- [[freeze 的协作边界]] 关联到这里的验证场景。
- [[graph 的协作边界]] 关联到这里的验证场景。
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]] 关联到这里的验证场景。
- [[source_files]] 关联到这里的验证场景。
- [[transaction 的协作边界]] 关联到这里的验证场景。
- [[validate]] 关联到这里的验证场景。
- [[validate 与 canonical 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 6 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `CanvasGraphTests.test_maximal_selection_has_12_nodes_stable_order_and_fixed_coordinates` | `test_maximal_selection_has_12_nodes…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasGraphTests.test_duplicate_page_and_source_keep_first_record_ordinal` | `test_duplicate_page_and_source_keep…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasGraphTests.test_required_page_budget_is_not_silently_dropped` | `test_required_page_budget_is_not_si…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasGraphTests.test_dangling_edge_duplicate_id_and_machine_field_are_distinct_failures` | `test_dangling_edge_duplicate_id_and…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasGraphTests.test_collision_hook_never_adds_random_salt` | `test_collision_hook_never_adds_rand…` 用于完成局部输入校验、转换或状态更新。 |
| `CanvasGraphTests.test_invalid_source_range_is_rejected` | `test_invalid_source_range_is_reject…` 用于完成局部输入校验、转换或状态更新。 |

</details>
