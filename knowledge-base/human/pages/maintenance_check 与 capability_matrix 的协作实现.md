# maintenance_check 与 capability_matrix 的协作实现

标签：#类型/代码

> 文件 `scripts/ckb_core/llm_wiki_capabilities.py`负责维护外部 Wiki 能力的吸收状态，并给 Agent 生成紧凑能力说明。 它属于知识库能力边界与后续研究队列的机器可读入口，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当能力状态、证据链接、维护检查或紧凑说明格式变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/llm_wiki_capabilities.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/llm_wiki_capabilities.py:1:1)  `scripts/ckb_core/llm_wiki_capabilities.py:1-482`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[FactFreshnessStateMachineTest]]。
- 实现时会用到 [[ScopeExtensionOfferTests.retrieval]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 主要代码单元是 [[maintenance_check]]。

## 谁会来到这里

- [[ScopeExtensionOfferTests.retrieval 等测试场景]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[serve_stdio]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[ScopeExtensionOfferTests.retrieval 等测试场景]]
- [[ScopeExtensionTest]]
- [[append 等测试场景]]
- [[command 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `capability_matrix` | `capability_matrix` 完成Wiki 能力状态维护中的一个明确步骤。 |
| `render_capability_matrix_markdown` | `render_capability_matrix_markdown` 生成并写入Wiki 能力状态维护所需的数据或状态。 |
| `write_capability_matrix` | `write_capability_matrix` 生成并写入Wiki 能力状态维护所需的数据或状态。 |
| `compact_agent_brief` | `compact_agent_brief` 将完整检索结果压缩为首轮 Agent 可见 JSON，并保留扩库确认建议及其有界诊断。 |

</details>
