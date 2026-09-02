# propose_template

标签：#类型/代码

> `propose_template` 位于 `scripts/ckb_core/human_page_template_proposals.py` 第 988-1045 行，本页用固定源码范围说明它如何完成输出局部模板提议、人工审计、事件重放和回滚中的局部职责。 `propose_template` 负责在输出局部模板提议、人工审计、事件重放和回滚中完成输出局部模板提议、人工审计、事件重放和回滚中的局部职责。

## 什么时候需要修改

当 `scripts/ckb_core/human_page_template_proposals.py` 中 `propose_template` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_page_template_proposals.py 第 988 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_page_template_proposals.py:988:1)  `scripts/ckb_core/human_page_template_proposals.py:988-1045`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[propose_template 与 _canonical_bytes 的协作实现]]。
- 实现时会用到 [[validate 与 canonical 的协作实现]]。

## 谁会来到这里

- [[TemplateProposalStoreTests]] 会使用这里提供的行为。
- [[propose_template 与 _canonical_bytes 的协作实现]] 汇总了本页。

## 相关测试

- [[HumanPageAuthoringPackageTests]]
- [[TemplateProposalStoreTests]]
