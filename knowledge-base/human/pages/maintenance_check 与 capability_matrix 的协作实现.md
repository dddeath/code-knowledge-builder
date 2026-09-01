# maintenance_check 与 capability_matrix 的协作实现

标签：#类型/代码

> `scripts/ckb_core/llm_wiki_capabilities.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责能力矩阵、紧凑 brief 与聚合 maintain 检查的生成和审计。

## 什么时候需要修改

当 `scripts/ckb_core/llm_wiki_capabilities.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/llm_wiki_capabilities.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/llm_wiki_capabilities.py:1:1)  `scripts/ckb_core/llm_wiki_capabilities.py:1-459`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[append]]。
- 主要代码单元是 [[maintenance_check]]。

## 谁会来到这里

- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[serve_stdio]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[ScopeExtensionTest]]
- [[append 等测试场景]]
- [[command 等测试场景]]
- [[refresh 等测试场景]]

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `capability_matrix` | `capability_matrix` 是第 275-286 行的函数，供所属页面定位实现。 |
| `render_capability_matrix_markdown` | `render_capability_mat...` 是第 289-343 行的函数，供所属页面定位实现。 |
| `write_capability_matrix` | `write_capability_matrix` 是第 346-355 行的函数，供所属页面定位实现。 |
| `compact_agent_brief` | `compact_agent_brief` 是第 358-405 行的函数，供所属页面定位实现。 |

</details>
