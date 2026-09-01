# register_obsidian_plugin

标签：#类型/代码

> `register_obsidian_plugin` 是 `scripts/ckb_core/obsidian_plugin.py` 中负责验证并登记独立 Obsidian Companion 包及其可部署载荷的函数。 它按源码所示的参数、条件分支和数据结构完成验证并登记独立 Obsidian Companion 包及其可部署载荷，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当Obsidian Companion 包注册、部署、状态与移除的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/obsidian_plugin.py 第 88 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian_plugin.py:88:1)  `scripts/ckb_core/obsidian_plugin.py:88-111`

## 相关代码

- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]]。

## 谁会来到这里

- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]] 汇总了本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
