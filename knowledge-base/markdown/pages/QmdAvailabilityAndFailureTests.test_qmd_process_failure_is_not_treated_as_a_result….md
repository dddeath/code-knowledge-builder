# QmdAvailabilityAndFailureTests.test_qmd_process_failure_is_not_treated_as_a_result…

标签：#类型/代码

> 该文件验证 QMD 三组基准的冻结问题、统一裁判、运行时和模型身份，覆盖缺失与格式故障，并检查归档结果的复算和生产默认未改变。 它以固定记录和进程替身检验适配器合同，区分不可用、未测量、质量不劣、提升与退化；归档断言并不意味着当前轮次重新运行了真实向量实验。

## 什么时候需要修改

冻结协议、QMD 响应字段、公共截断与评分或归档报告合同变化时调整相应测试，保留故障不算有效结果的约束。

## 在代码中的位置

[打开源码：tests/test_ckb_qmd_three_arm_benchmark.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_qmd_three_arm_benchmark.py:1:1)  `tests/test_ckb_qmd_three_arm_benchmark.py:1-251`

## 相关代码

- 主要代码单元是 [[QmdAvailabilityAndFailureTests.test_qmd_process_failure_is_not_treated_as_a_result]]。

## 谁会来到这里

- 与 [[QmdAvailabilityAndFailureTests.test_qmd_process_failure_is_not_treated_as_a_result]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 15 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `load_module` | 从指定文件路径创建并执行模块加载对象，要求加载器存在，返回动态加载的测试模块。 |
| `FrozenQmdContractTests` | 核对 QMD 三组实验复用同一冻结语料、问题、预算和裁判，并绑定运行时、模型及适配器身份。 |
| `FrozenQmdContractTests.test_protocol_reuses_exact_corpus_questions_budget_and_judge` | 验证三组实验的冻结问题、统一截断顺序、资源上限、随机种子、候选深度和 GPU 配置合同。 |
| `FrozenQmdContractTests.test_qmd_runtime_lock_and_model_are_pinned` | 核对 QMD 包版本、提交、锁文件、模型大小及适配器哈希与冻结运行时清单一致。 |
| `QmdAvailabilityAndFailureTests` | 验证 QMD 缺失、进程失败和响应模式漂移被分类为无测量结果，而非可用于质量比较的检索响应。 |
| `QmdAvailabilityAndFailureTests.test_missing_qmd_package_is_structured_unavailable` | 模拟缺失 Node 与运行包，要求产生结构化不可用状态且效果声明为未测量。 |
| `QmdAvailabilityAndFailureTests.test_qmd_build_output_format_drift_is_rejected` | 注入构建响应模式漂移，要求 QMD 构建适配器报告封装格式错误。 |
| `QmdAvailabilityAndFailureTests.test_qmd_query_result_format_drift_is_rejected` | 构造缺少必需查询字段的 QMD 响应，要求字段合同校验拒绝该结果。 |
| `QmdAvailabilityAndFailureTests._identity` | 返回故障测试使用的固定 QMD 包、构建与 Node 身份字段。 |
| `CommonJudgeAndRecomputeTests` | 验证统一裁判先去重再按预算截断，并区分质量不劣、提升与退化及第三实验组复算。 |
| `CommonJudgeAndRecomputeTests.test_common_truncation_deduplicates_then_applies_budget_and_top_k` | 用重复来源与受限预算候选核对去重及截断顺序，检查所选来源和可见上下文用量。 |
| `CommonJudgeAndRecomputeTests.test_quality_claims_distinguish_non_inferiority_improvement_and_regression` | 使用相等、局部提高和局部下降的指标组合，检查质量声明分别为不劣、提升和退化。 |
| `CommonJudgeAndRecomputeTests.test_recompute_accepts_qmd_as_the_third_arm` | 以固定冷热排序记录验证复算器接纳 QMD 第三组并计算召回与确定性。 |
| `CommittedResultTests` | 核对归档 QMD 实验原始行数、冻结协议与复算结果，保留未改变生产默认及无测量失败样本的边界。 |
| `CommittedResultTests.test_committed_result_is_recomputable_and_keeps_production_default` | 检查归档三组实验及独立复算通过，比较提升与退化结论，并要求失败样本不产生效果测量主张。 |

</details>
