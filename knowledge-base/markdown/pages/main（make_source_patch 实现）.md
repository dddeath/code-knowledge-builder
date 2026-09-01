# main（make_source_patch 实现）

标签：#类型/代码

> `main` 解析补丁输出路径并生成从空目录到完整 Skill 的文本统一差异。 它确定性过滤 `.git`、第三方 vendored 源码与二进制资产，按路径排序拼接新增文件补丁并以 UTF-8/LF 写入。

## 什么时候需要修改

当排除集合、编码策略、排序规则或统一差异格式变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/make_source_patch.py 第 19 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/make_source_patch.py:19:1)  `scripts/make_source_patch.py:19-42`

## 相关代码

- 实现时会用到 [[append]]。
- 实现时会用到 [[parser]]。

## 谁会来到这里

- [[main 相关实现]] 汇总了本页。
