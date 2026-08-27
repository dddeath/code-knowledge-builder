# prepare_vault 与 install_obsidian 的协作实现

标签：#类型/代码

> 该页面汇总 Obsidian vault 准备、最小配置安装、生成器所有权和审计实现。 它让生成页面可重建，同时保留用户 workspace、笔记和未知文件。

## 什么时候需要修改

Obsidian 目录、保留规则、CSS 或审计约束变化时，需要修改本文件。

## 在代码中的位置

[打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`

## 相关代码

- 主要代码单元是 [[prepare_vault]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[MigrationTest]]

## 内部细节

<details><summary>查看本页收纳的 3 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `install_obsidian` | 写入最小 Obsidian 配置、样式和默认图谱设置。 |
| `write_generated_ownership` | 该附属代码负责稳定读取或写入机器状态记录，并把结果交给所属页面中的主流程使用。 |
| `audit_obsidian` | 检查必要目录、配置、单标签和用户文件保留契约。 |

</details>
