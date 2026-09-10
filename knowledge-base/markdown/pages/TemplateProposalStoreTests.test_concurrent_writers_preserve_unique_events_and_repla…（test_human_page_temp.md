# TemplateProposalStoreTests.test_concurrent_writers_preserve_unique_events_and_repla…（test_human_page_template_proposals 测试）

标签：#类型/代码

> 该测试并发提交八个不同模板提案，要求全部提交成功、序号唯一连续，事件日志与索引均记录八项。 它验证模板提案存储在多写入者场景下不丢事件且可重放，线程异常会回到主测试直接失败。

## 什么时候需要修改

提案锁、事件编号或索引生成方式变化时修改此测试，并同时检查事件行数和索引数量。

## 在代码中的位置

[打开源码：tests/test_human_page_template_proposals.py 第 164 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_human_page_template_proposals.py:164:1)  `tests/test_human_page_template_proposals.py:164-191`

## 相关代码

- 与 [[TemplateProposalStoreTests.test_concurrent_writers_preserve_unique_events_and_repla…（tests/test_human_page_template_proposals.py:1）]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[TemplateProposalStoreTests.test_concurrent_writers_preserve_unique_events_and_repla…（tests/test_human_page_template_proposals.py:1）]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `TemplateProposalStoreTests.test_concurrent_writers_preserve_unique_events_and_replayable_index.submit` | 该测试验证模板提议的校验、人工审阅、状态转换或回滚边界。 |

</details>
