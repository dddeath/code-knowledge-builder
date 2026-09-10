# normalize_page_config

标签：#类型/代码

> 该函数把用户提交的局部页面配置与默认配置合并，检查模式版本、已知字段、章节集合、标题、概览字段和附录展示模式，并规范化页面与关系数量限制。 它是页面配置进入构建前的统一校验入口，同时约束任务、模块、总上下文和 Agent 预留预算之间的大小关系，防止审阅包预算超出可用上下文。

## 什么时候需要修改

页面配额、章节或标题字段、上下文预算范围及审阅包上限变化时修改此函数，并检查局部配置合并后的规范化结果及预算交叉约束。

## 在代码中的位置

[打开源码：scripts/ckb_core/page_config.py 第 144 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/page_config.py:144:1)  `scripts/ckb_core/page_config.py:144-206`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[normalize_page_config 与 _merge_known 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_global]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[normalize_page_config 与 _merge_known 的协作实现]] 汇总了本页。
