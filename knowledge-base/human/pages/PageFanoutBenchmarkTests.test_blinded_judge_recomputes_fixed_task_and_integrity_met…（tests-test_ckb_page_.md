# PageFanoutBenchmarkTests.test_blinded_judge_recomputes_fixed_task_and_integrity_met…（tests/test_ckb_page_fanout_benchmark.py:1）

标签：#类型/代码

> 检验页面扩散实验的固定裁判、结果汇总、只读目录约束以及与参考页面配额的兼容性。 使用临时目录和固定语料对照两种投影；参考兼容测试调用真实投影函数，而不是依赖包装函数源码中的常量文字。

## 什么时候需要修改

需要调整实验合同、任务计分、负结果保留或参考投影兼容断言时修改。

## 在代码中的位置

[打开源码：tests/test_ckb_page_fanout_benchmark.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_page_fanout_benchmark.py:1:1)  `tests/test_ckb_page_fanout_benchmark.py:1-238`

## 相关代码

- 主要代码单元是 [[PageFanoutBenchmarkTests.test_blinded_judge_recomputes_fixed_task_and_integrity_met…（test_ckb_page_fanout_benchmark 测试）]]。

## 谁会来到这里

- 与 [[PageFanoutBenchmarkTests.test_blinded_judge_recomputes_fixed_task_and_integrity_met…（test_ckb_page_fanout_benchmark 测试）]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 10 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `PageFanoutBenchmarkTests` | 在隔离样例中验证页面扩散的任务指标、负结果、只读约束和实际参考投影。 |
| `PageFanoutBenchmarkTests.setUp` | 复制固定评测样例并生成扩散分支，建立带哨兵文件的只读对照目录。 |
| `PageFanoutBenchmarkTests.tearDown` | 清理当前评测用例的临时目录。 |
| `PageFanoutBenchmarkTests._judge` | 用固定裁判合同评判指定投影目录与来源目录。 |
| `PageFanoutBenchmarkTests._aggregate` | 保存两组判定及只读前后快照，再调用固定合同汇总评测。 |
| `PageFanoutBenchmarkTests.test_aggregate_preserves_negative_result_and_uses_fixed_thresholds` | 断言汇总保留扩散负结果，并按固定阈值推荐保守投影。 |
| `PageFanoutBenchmarkTests.test_task_order_does_not_change_blinded_judge_output` | 反转任务顺序后重算，断言规范化裁判输出字节不变。 |
| `PageFanoutBenchmarkTests.test_orphan_and_broken_link_are_recomputed_from_markdown` | 修改 Markdown 导航制造孤页和坏链，断言裁判从正文重新识别问题。 |
| `PageFanoutBenchmarkTests.test_read_only_guard_rejects_any_snapshot_drift` | 改变只读哨兵文件，断言聚合器以目录漂移原因中止评测。 |
| `PageFanoutBenchmarkTests.test_current_page_quota_v3_and_reference_projection_remain_compatible` | 调用实际参考投影验证单来源单页、非活跃资料排除及重复投影稳定性。 |

</details>
