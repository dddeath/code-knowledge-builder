# run_benchmark（benchmark_chinese_retrieval 测试）

标签：#类型/代码

> 该函数在冻结语料副本上轮换运行旧式确定性、当前确定性和固定回放关键词回退三组冷热检索，汇总排序质量、缓存与启动计数，并注入限流验证原始排序保持。 它编排中文检索可复现实验，运行前后核对源语料和副本索引哈希并输出逐次原始记录及汇总；固定回放组明确不代表真实模型效果，真实提供器调用次数保持为零。

## 什么时候需要修改

冻结协议、各组轮换与缓存规则、质量汇总、故障探针或源语料保护检查变化时修改此函数，并核对行数、排序稳定性和原始索引未变。

## 在代码中的位置

[打开源码：tests/benchmark_chinese_retrieval.py 第 516 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/benchmark_chinese_retrieval.py:516:1)  `tests/benchmark_chinese_retrieval.py:516-636`

## 相关代码

- 与 [[run_benchmark 等测试场景（benchmark_chinese_retrieval 测试）]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[run_benchmark 等测试场景（benchmark_chinese_retrieval 测试）]] 汇总了本页。
