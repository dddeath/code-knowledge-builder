# get_human_page_template

标签：#类型/代码

> `get_human_page_template` 位于 `scripts/ckb_core/human_page_templates.py` 第 598-616 行，本页用固定源码范围说明它如何读取、规范化并返回既有状态。 `get_human_page_template` 负责在人类页面类型合同、预算和确定性验证中读取、规范化并返回既有状态。

## 什么时候需要修改

当 `scripts/ckb_core/human_page_templates.py` 中 `get_human_page_template` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_page_templates.py 第 598 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_page_templates.py:598:1)  `scripts/ckb_core/human_page_templates.py:598-616`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[get_human_page_template 与 SectionContract 的协作实现]]。

## 谁会来到这里

- [[HumanPageAuthoringPackageTests 等测试场景]] 会使用这里提供的行为。
- [[HumanPageTemplateValidationTests]] 会使用这里提供的行为。
- [[HumanPageTemplateValidationTests 等测试场景]] 会使用这里提供的行为。
- [[get_human_page_template 与 SectionContract 的协作实现]] 汇总了本页。
- [[render_page_author 与 _error 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[HumanPageAuthoringPackageTests]]
- [[HumanPageAuthoringPackageTests 等测试场景]]
- [[HumanPageTemplateValidationTests]]
- [[HumanPageTemplateValidationTests 等测试场景]]
- [[TemplateProposalStoreTests]]
