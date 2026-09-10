# HumanPageTemplateContract

标签：#类型/代码

> 保存一种人类页面的不可变完整合同，包括读者任务、章节、预算、证据和适用边界。 作为注册表、序列化和页面验证之间共享的类型化数据结构，组合章节与首屏等子合同。

## 什么时候需要修改

需要增减页面级合同字段或改变生成器与校验器共享的数据形状时修改，并同步序列化与消费入口。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_page_templates.py 第 94 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_page_templates.py:94:1)  `scripts/ckb_core/human_page_templates.py:94-107`

## 相关代码

- 与 [[HumanPageTemplateContract 与 SectionContract 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[HumanPageTemplateContract 与 SectionContract 的协作实现]] 汇总了本页。
- [[init_page_author 与 _error 的协作实现]] 会使用这里提供的行为。
