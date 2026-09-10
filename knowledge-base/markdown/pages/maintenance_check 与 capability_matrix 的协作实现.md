# maintenance_check 与 capability_matrix 的协作实现

标签：#类型/代码

> 提供能力边界矩阵、紧凑检索阅读入口和聚合维护结果。 复用既有检索与审计模块；文档说明参考资料输入命令与效果实验的区别，维护结果保留事实时效和历史页面覆盖边界。

## 什么时候需要修改

需要调整能力文档、首轮检索上下文或维护子审计及其结果汇总时修改。

## 在代码中的位置

[打开源码：scripts/ckb_core/llm_wiki_capabilities.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/llm_wiki_capabilities.py:1:1)  `scripts/ckb_core/llm_wiki_capabilities.py:1-528`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[maintenance_check]]。

## 谁会来到这里

- 与 [[maintenance_check]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_management_task 与 default_management_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。
- 与 [[serve_stdio]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `capability_matrix` | 按固定状态统计能力条目，返回带版本、边界说明和独立条目副本的矩阵。 |
| `render_capability_matrix_markdown` | 生成能力矩阵文档，区分已实现的参考输入命令、可选 OCR 与隔离效果实验。 |
| `write_capability_matrix` | 向不存在的目标写入 Markdown 或 JSON 能力矩阵，已有文件则报错。 |
| `compact_agent_brief` | 压缩检索结果为阅读入口、反馈和时效提示，完整候选留在检索记录。 |

</details>
