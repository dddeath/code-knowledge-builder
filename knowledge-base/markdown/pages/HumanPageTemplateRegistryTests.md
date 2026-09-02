# HumanPageTemplateRegistryTests

标签：#类型/代码

> `HumanPageTemplateRegistryTests` 位于 `tests/test_human_page_templates.py` 第 63-174 行，用于覆盖 14 类 V3 页面合同、书面标题和稳定注册表。 `HumanPageTemplateRegistryTests` 在V3 页面标题、章节预算、链接和披露边界测试中负责覆盖 14 类 V3 页面合同、书面标题和稳定注册表。

## 什么时候需要修改

当 `HumanPageTemplateRegistryTests` 的输入、输出、状态转换或失败边界变化时，应更新对应说明和测试。

## 在代码中的位置

[打开源码：tests/test_human_page_templates.py 第 63 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_human_page_templates.py:63:1)  `tests/test_human_page_templates.py:63-174`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[HumanPageTemplateRegistryTests 等测试场景]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[get_human_page_template]]。
- 实现时会用到 [[get_human_page_template 与 SectionContract 的协作实现]]。

## 谁会来到这里

- [[HumanPageTemplateRegistryTests 等测试场景]] 汇总了本页。
- [[get_human_page_template]] 关联到这里的验证场景。
- [[get_human_page_template 与 SectionContract 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 6 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `HumanPageTemplateRegistryTests.test_registry_has_one_v3_contract_for_every_human_page_type` | 该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。 |
| `HumanPageTemplateRegistryTests.test_registry_serialization_and_hash_are_byte_stable` | 该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。 |
| `HumanPageTemplateRegistryTests.test_query_returns_an_immutable_contract` | 该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。 |
| `HumanPageTemplateRegistryTests.test_confirmed_v3_headings_are_exact` | 该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。 |
| `HumanPageTemplateRegistryTests.test_old_1_0_0_is_rejected_with_explicit_migration_rule` | 该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。 |
| `HumanPageTemplateRegistryTests.test_unknown_query_and_validator_type_fail_with_machine_readable_reasons` | 该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。 |

</details>
