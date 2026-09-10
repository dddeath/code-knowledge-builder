# RealVaultStudyTests.setUp

标签：#类型/代码

> 该初始化方法创建临时源库和独立实验工作区，计算源身份并生成冻结协议，再设置支持票、独立来源、反对比例和标签数策略。 它为每个真实库标签研究测试提供一致且隔离的输入，避免不同测试共享修改状态。

## 什么时候需要修改

测试源结构、冻结身份或标签确认阈值变化时修改此方法，并检查每次测试都从新目录开始。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_real_vault.py 第 32 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_real_vault.py:32:1)  `tests/test_ckb_tag_navigation_real_vault.py:32-49`

## 相关代码

- 与 [[RealVaultStudyTests.setUp 等测试场景]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[RealVaultStudyTests.setUp 等测试场景]] 汇总了本页。
