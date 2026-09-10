# contract_errors 等测试场景

标签：#类型/代码

> 用现行人类入口合同检验 README，并保留历史夹具作为不可变对照。 校验三项任务入口、提示可复制性、锚点与操作边界，再通过删除和替换反例验证检查器；不把旧标题结构作为现行要求。

## 什么时候需要修改

用户确认 README 结构或提示边界变化时同步现行合同和测试，历史夹具保持原始内容。

## 在代码中的位置

[打开源码：tests/test_readme_human_entry.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_readme_human_entry.py:1:1)  `tests/test_readme_human_entry.py:1-99`

## 相关代码

- 主要代码单元是 [[contract_errors]]。

## 谁会来到这里

- 与 [[contract_errors]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `section` | 按指定二级标题提取正文，截取到下一二级标题或文末。 |
| `ReadmeHumanEntryTests` | 用现行文档合同验证任务入口和边界，并用反例及历史摘要防止合同混淆。 |
| `ReadmeHumanEntryTests.setUpClass` | 在测试类初始化时读取仓库 README 正文。 |
| `ReadmeHumanEntryTests.test_current_readme_has_direct_entries_prompts_boundaries_and_valid_anchors` | 断言 README 的直接入口、可复制提示、边界和内部锚点符合现行合同。 |
| `ReadmeHumanEntryTests.test_historical_v5_fixture_remains_unchanged_and_is_not_current_contract` | 校验历史夹具摘要不变，并断言其标题结构与现行合同明确不同。 |
| `ReadmeHumanEntryTests.test_deleted_entry_is_rejected` | 删除当前 Agent 入口行，断言合同检测到三项任务入口缺失。 |
| `ReadmeHumanEntryTests.test_broken_internal_link_is_rejected` | 把安装入口改成不存在的锚点，断言合同报告内部坏链。 |
| `ReadmeHumanEntryTests.test_restored_parameter_slots_are_rejected` | 在提示中重新加入项目和版本槽位，断言合同检测到填参内容。 |
| `ReadmeHumanEntryTests.test_missing_prompt_result_or_optional_boundary_is_rejected` | 分别破坏提示、完成结果、白板可选性和安装边界，断言对应诊断出现。 |

</details>
