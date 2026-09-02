# main（recompute 测试）

标签：#类型/代码

> 代码单元 `main`负责从逐次检索记录独立重算排序质量、延迟和确定性。 它属于中文检索指标复核；实验代码不改变生产检索或稳定页面生成默认行为。

## 什么时候需要修改

当逐题记录或聚合口径发生变化时，应同步复查本页、固定实验协议及直接测试。

## 在代码中的位置

[打开源码：tests/fixtures/chinese-retrieval-effects/recompute.py 第 105 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/fixtures/chinese-retrieval-effects/recompute.py:105:1)  `tests/fixtures/chinese-retrieval-effects/recompute.py:105-144`

## 相关代码

- 实现时会用到 [[parser]]。

## 谁会来到这里

- [[main 等测试场景（recompute 测试）]] 汇总了本页。
