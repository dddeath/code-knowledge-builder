# bind_conversation

标签：#类型/代码

> 代码单元 `bind_conversation`负责把任意 Harness 对话绑定到源码仓库和知识库，并管理独立开发任务的创建与复查。 它属于跨 Harness 复现管理 Agent 行为的持久化控制面，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当绑定身份、隐私字段、仓库预检、任务交接或复查门变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/management_agent.py 第 454 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/management_agent.py:454:1)  `scripts/ckb_core/management_agent.py:454-569`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[append 等测试场景]]。
- 实现时会用到 [[bind_conversation 与 default_management_registry_path 的协作实现]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[preflight]]。

## 谁会来到这里

- [[append 等测试场景]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 汇总了本页。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[PdfReferenceExtractionTests]]
- [[PdfReferenceExtractionTests 等测试场景]]
- [[append 等测试场景]]
- [[command 等测试场景]]
- [[main（benchmark_obsidian_canvas_navigation 测试）]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
