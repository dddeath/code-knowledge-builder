# main 相关实现

标签：#类型/代码

> 该代码页汇总从空基线生成 Skill 文本统一补丁的实现。 它遍历可交付 UTF-8 文本文件，排除 `.git`、第三方 vendored 源码、运行时资产、缓存和二进制文件，再为每个文件生成新增补丁段。

## 什么时候需要修改

当源码目录结构、文本交付边界或补丁格式变化时，需要修改本页并检查输出中不含仓库元数据。

## 在代码中的位置

[打开源码：scripts/make_source_patch.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/make_source_patch.py:1:1)  `scripts/make_source_patch.py:1-47`

## 相关代码

- 主要代码单元是 [[main（make_source_patch 实现）]]。

## 谁会来到这里

- 可从 [[scripts 职责导览]] 进入本页。
