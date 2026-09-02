# ReadmeHumanEntryTests

标签：#类型/代码

> 代码单元 `setUpClass`负责验证 README 只保留三个人类入口、稳定 Prompt 和直接结果。 它属于人类入门导航的回归保护，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当README 入口、职责拆分或验收说明变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：tests/test_readme_human_entry.py 第 20 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_readme_human_entry.py:20:1)  `tests/test_readme_human_entry.py:20-73`

## 谁会来到这里

- [[ReadmeHumanEntryTests 等测试场景]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 6 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ReadmeHumanEntryTests.setUpClass` | `setUpClass` 完成README 人类入口测试所需的一个明确步骤。 |
| `ReadmeHumanEntryTests.test_first_screen_contains_only_three_human_tasks_and_direct_results` | 该测试验证“first screen contains only th…”场景，保护README 人类入口测试的结果与失败边界。 |
| `ReadmeHumanEntryTests.test_required_headings_are_exact_and_ordered` | 该测试验证“required headings are exact a…”场景，保护README 人类入口测试的结果与失败边界。 |
| `ReadmeHumanEntryTests.test_each_task_card_reuses_the_accepted_direct_result_and_prompt` | 该测试验证“each task card reuses the acc…”场景，保护README 人类入口测试的结果与失败边界。 |
| `ReadmeHumanEntryTests.test_install_and_explain_prompts_keep_separate_responsibilities` | 该测试验证“install and explain prompts k…”场景，保护README 人类入口测试的结果与失败边界。 |
| `ReadmeHumanEntryTests.test_follow_up_navigation_separates_existing_reading_from_maintenance` | 该测试验证“follow up navigation separate…”场景，保护README 人类入口测试的结果与失败边界。 |

</details>
