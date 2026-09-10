# aggregate 等测试场景

标签：#类型/代码

> 文件 `tests/fixtures/chinese-retrieval-effects/recompute.py`负责从逐次检索记录独立重算排序质量与延迟聚合。 它属于中文检索 benchmark 的独立复核层，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当逐题记录或聚合指标变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：tests/fixtures/chinese-retrieval-effects/recompute.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/fixtures/chinese-retrieval-effects/recompute.py:1:1)  `tests/fixtures/chinese-retrieval-effects/recompute.py:1-149`

## 相关代码

- 主要代码单元是 [[aggregate]]。

## 谁会来到这里

- 与 [[aggregate]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `load` | `load` 读取并判定中文检索指标重算所需的一个明确步骤。 |
| `percentile` | `percentile` 完成中文检索指标重算所需的一个明确步骤。 |
| `quality` | `quality` 完成中文检索指标重算所需的一个明确步骤。 |
| `main` | 从中文检索原始记录重新计算各实验组汇总，比较报告数值、记录数量和问题及实验组集合。 |

</details>
