# aggregate

标签：#类型/代码

> 该函数仅从保存的原始运行记录重算指定实验组的每题冷启动检索质量、首包用量、冷热延迟分位数和排序确定性，再汇总提供器启动次数。 它是冻结中文检索实验的独立复算入口，不调用检索器或提供器；质量用各题冷启动排序计量，确定性比较同题全部运行签名。

## 什么时候需要修改

原始记录字段、排名评分、分位数或题级汇总规则变化时修改此函数，并检查复算结果与原始记录可追溯。

## 在代码中的位置

[打开源码：tests/fixtures/chinese-retrieval-effects/recompute.py 第 64 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/fixtures/chinese-retrieval-effects/recompute.py:64:1)  `tests/fixtures/chinese-retrieval-effects/recompute.py:64-102`

## 相关代码

- 与 [[aggregate 等测试场景]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[aggregate 等测试场景]] 汇总了本页。
