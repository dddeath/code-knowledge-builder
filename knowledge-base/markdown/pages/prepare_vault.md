# prepare_vault

标签：#类型/代码

> `prepare_vault` 清理上一轮生成器拥有的文件，并建立页面与五类笔记目录。 它以所有权清单控制重建范围，避免覆盖用户页面和 Obsidian 工作区状态。

## 什么时候需要修改

生成器所有权、保留目录或 vault 初始化规则变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/ckb_core/obsidian.py 第 23 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:23:1)  `scripts/ckb_core/obsidian.py:23-43`

## 相关代码

- 实现时会用到 [[run 与 CkbError 的协作实现]]。

## 谁会来到这里

- [[prepare_vault 与 install_obsidian 的协作实现]] 汇总了本页。
- [[status 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[MigrationTest]]
