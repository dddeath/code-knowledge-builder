# PageFanoutBenchmarkTests

标签：#类型/代码

> 代码单元 `setUp`负责验证固定任务的盲化导航指标、负结果和现有投影合同兼容性。 它属于页面扩张效果实验的回归保护；实验代码不改变生产检索或稳定页面生成默认行为。

## 什么时候需要修改

当任务集、判定指标或推荐阈值变化时，应同步复查本页、固定实验协议及直接测试。

## 在代码中的位置

[打开源码：tests/test_ckb_page_fanout_benchmark.py 第 32 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_page_fanout_benchmark.py:32:1)  `tests/test_ckb_page_fanout_benchmark.py:32-193`

## 相关代码

- 实现时会用到 [[FactFreshnessStateMachineTest]]。
- 实现时会用到 [[benchmark 的协作边界（92b0cf7f）]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[contracts 的协作边界（prototypes）]]。
- 实现时会用到 [[generator 的协作边界]]。
- 实现时会用到 [[get_human_page_template]]。
- 实现时会用到 [[ingest_reference 与 _root 的协作实现]]。
- 实现时会用到 [[judge 的协作边界]]。

## 谁会来到这里

- [[PageFanoutBenchmarkTests 等测试场景]] 汇总了本页。
- [[audit_agent_protocol]] 关联到这里的验证场景。
- [[audit_feedback]] 关联到这里的验证场景。
- [[audit_obsidian]] 关联到这里的验证场景。
- [[audit_obsidian 与 prepare_vault 的协作实现]] 关联到这里的验证场景。
- [[audit_output_contract]] 关联到这里的验证场景。
- [[audit_output_contract 与 _default_ckb 的协作实现]] 关联到这里的验证场景。
- [[audit_work_record_index 与 _contains_chinese 的协作实现]] 关联到这里的验证场景。
- [[benchmark 的协作边界（92b0cf7f）]] 关联到这里的验证场景。
- [[contracts 的协作边界（prototypes）]] 关联到这里的验证场景。
- [[extract_pdf 与 PdfExtractionError 的协作实现]] 关联到这里的验证场景。
- [[generator 的协作边界]] 关联到这里的验证场景。
- [[get_human_page_template]] 关联到这里的验证场景。
- [[get_human_page_template 与 SectionContract 的协作实现]] 关联到这里的验证场景。
- [[judge 的协作边界]] 关联到这里的验证场景。
- [[module_name]] 关联到这里的验证场景。
- [[refresh]] 关联到这里的验证场景。
- [[sync_human_layer]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 10 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `PageFanoutBenchmarkTests.setUp` | `setUp` 完成页面扩张基准测试所需的一个明确步骤。 |
| `PageFanoutBenchmarkTests.tearDown` | `tearDown` 完成页面扩张基准测试所需的一个明确步骤。 |
| `PageFanoutBenchmarkTests._judge` | `_judge` 校验页面扩张基准测试所需的一个明确步骤。 |
| `PageFanoutBenchmarkTests._aggregate` | `_aggregate` 解析并归一化页面扩张基准测试所需的一个明确步骤。 |
| `PageFanoutBenchmarkTests.test_blinded_judge_recomputes_fixed_task_and_integrity_metrics` | 该测试验证“blinded judge recomputes fixed …”场景，保护页面扩张基准测试的结果与失败边界。 |
| `PageFanoutBenchmarkTests.test_aggregate_preserves_negative_result_and_uses_fixed_thresholds` | 该测试验证“aggregate preserves negative re…”场景，保护页面扩张基准测试的结果与失败边界。 |
| `PageFanoutBenchmarkTests.test_task_order_does_not_change_blinded_judge_output` | 该测试验证“task order does not change blin…”场景，保护页面扩张基准测试的结果与失败边界。 |
| `PageFanoutBenchmarkTests.test_orphan_and_broken_link_are_recomputed_from_markdown` | 该测试验证“orphan and broken link are reco…”场景，保护页面扩张基准测试的结果与失败边界。 |
| `PageFanoutBenchmarkTests.test_read_only_guard_rejects_any_snapshot_drift` | 该测试验证“read only guard rejects any sna…”场景，保护页面扩张基准测试的结果与失败边界。 |
| `PageFanoutBenchmarkTests.test_current_page_quota_v3_and_reference_projection_remain_compatible` | 该测试验证“current page quota v3 and refer…”场景，保护页面扩张基准测试的结果与失败边界。 |

</details>
