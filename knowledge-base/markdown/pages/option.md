# option

标签：#类型/代码

> 该函数从模拟 Logseq 参数列表中读取指定选项后的值，选项缺失或没有后续参数时返回空值。 它为测试替身提供最小命令行取值行为，不解析复杂选项语法，也不验证值的含义。

## 什么时候需要修改

模拟命令的参数排列或缺省值约定变化时修改此函数，并检查缺少选项及末尾无值场景。

## 在代码中的位置

[打开源码：tests/fake_logseq.py 第 15 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/fake_logseq.py:15:1)  `tests/fake_logseq.py:15-19`

## 谁会来到这里

- [[option 等测试场景]] 汇总了本页。
