# QmdAvailabilityAndFailureTests.test_qmd_process_failure_is_not_treated_as_a_result

标签：#类型/代码

> 该测试运行会以状态七退出的 QMD 构建替身，要求外层抛出进程执行失败而不是返回检索结果。 它验证外部进程失败与低质量但有效的检索输出分开记录，防止失败样本进入质量统计。

## 什么时候需要修改

QMD 构建命令或错误包装方式变化时修改此测试，并保留退出码进入结构化失败的断言。

## 在代码中的位置

[打开源码：tests/test_ckb_qmd_three_arm_benchmark.py 第 97 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_qmd_three_arm_benchmark.py:97:1)  `tests/test_ckb_qmd_three_arm_benchmark.py:97-112`

## 相关代码

- 与 [[QmdAvailabilityAndFailureTests.test_qmd_process_failure_is_not_treated_as_a_result…]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[QmdAvailabilityAndFailureTests.test_qmd_process_failure_is_not_treated_as_a_result…]] 汇总了本页。
