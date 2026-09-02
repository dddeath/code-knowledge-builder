# run_failure_probe

标签：#类型/代码

> 代码单元 `run_failure_probe`负责在固定语料上比较旧词项、当前词项和显式关键词回放慢路径。 它属于中文检索三臂效果测量；实验代码不改变生产检索或稳定页面生成默认行为。

## 什么时候需要修改

当问题集、排序指标、缓存或检索臂发生变化时，应同步复查本页、固定实验协议及直接测试。

## 在代码中的位置

[打开源码：tests/benchmark_chinese_retrieval.py 第 476 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/benchmark_chinese_retrieval.py:476:1)  `tests/benchmark_chinese_retrieval.py:476-513`

## 相关代码

- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run_failure_probe 等测试场景]]。
- 实现时会用到 [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]。

## 谁会来到这里

- [[ChineseRetrievalEffectRetestFixtureTests]] 会使用这里提供的行为。
- [[run_failure_probe 等测试场景]] 汇总了本页。

## 相关测试

- [[ChineseRetrievalEffectRetestFixtureTests]]
- [[run_failure_probe 等测试场景]]
