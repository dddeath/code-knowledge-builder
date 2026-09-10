# propose_template

标签：#类型/代码

> `propose_template` 位于 `scripts/ckb_core/human_page_template_proposals.py` 第 1121-1178 行，用于把通过校验的模板扩展写入待人工审阅状态，不直接激活模板。 `propose_template` 在人类页面模板提议、人工审阅、版本化状态和回滚中负责把通过校验的模板扩展写入待人工审阅状态，不直接激活模板。

## 什么时候需要修改

当 `propose_template` 的输入、输出、状态转换或失败边界变化时，应更新对应说明和测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_page_template_proposals.py 第 1121 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_page_template_proposals.py:1121:1)  `scripts/ckb_core/human_page_template_proposals.py:1121-1178`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[propose_template 与 _canonical_bytes 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[propose_template 与 _canonical_bytes 的协作实现]] 汇总了本页。
