# PageFanoutGeneratorTests.test_non_entailed_chinese_claim_stops_without_residue

标签：#类型/代码

> 该测试把候选中文主张替换为冻结原文没有的内容，要求生成器返回主张不受来源支撑的错误。 它检验中文文本存在不等于来源有效，失败后输出目录和回滚清单都不应产生。

## 什么时候需要修改

来源支撑判断或生成失败清理行为变化时修改此测试，并检查错误原因和无残留条件。

## 在代码中的位置

[打开源码：tests/test_ckb_page_fanout_generator.py 第 109 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_page_fanout_generator.py:109:1)  `tests/test_ckb_page_fanout_generator.py:109-117`

## 相关代码

- 与 [[PageFanoutGeneratorTests.test_non_entailed_chinese_claim_stops_without_residue 等测试场景]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[PageFanoutGeneratorTests.test_non_entailed_chinese_claim_stops_without_residue 等测试场景]] 汇总了本页。
