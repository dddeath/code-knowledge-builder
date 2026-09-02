# build_case 等测试场景

标签：#类型/代码

> `tests/fixtures/obsidian-canvas-agent-visualization/runtime_builder.py` 页面绑定固定源码第 1-371 行，说明该文件在Canvas 测试运行时 fixture 和固定来源环境中的整体职责。 该文件负责Canvas 测试运行时 fixture 和固定来源环境，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `tests/fixtures/obsidian-canvas-agent-visualization/runtime_builder.py` 中 `tests/fixtures/obsidian-canvas-agent-visualization/runtime_builder.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/fixtures/obsidian-canvas-agent-visualization/runtime_builder.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/fixtures/obsidian-canvas-agent-visualization/runtime_builder.py:1:1)  `tests/fixtures/obsidian-canvas-agent-visualization/runtime_builder.py:1-371`

## 相关代码

- 主要代码单元是 [[build_case]]。
- 实现时会用到 [[rollback]]。

## 谁会来到这里

- [[CanvasContractTests]] 会使用这里提供的行为。
- [[CanvasContractTests 等测试场景]] 会使用这里提供的行为。
- [[CanvasDeterminismTests]] 会使用这里提供的行为。
- [[CanvasGraphTests]] 会使用这里提供的行为。
- [[CanvasPathTests]] 会使用这里提供的行为。
- [[CanvasRollbackTests]] 会使用这里提供的行为。
- [[CanvasTransactionTests]] 会使用这里提供的行为。
- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[HumanPageAuthoringPackageTests 等测试场景]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 会使用这里提供的行为。
- [[MigrationTest]] 会使用这里提供的行为。
- [[PackageReleaseTests]] 会使用这里提供的行为。
- [[RecordReplaceTests]] 会使用这里提供的行为。
- [[TemplateProposalStoreTests]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[append 等测试场景]] 会使用这里提供的行为。
- [[audit_global]] 会使用这里提供的行为。
- [[benchmark 的协作边界]] 会使用这里提供的行为。
- [[build_case]] 会使用这里提供的行为。
- [[command 等测试场景]] 会使用这里提供的行为。
- [[create_batch_plan]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan]] 会使用这里提供的行为。
- [[freeze 的协作边界]] 会使用这里提供的行为。
- [[get_human_page_template 与 SectionContract 的协作实现]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[render_human_maintenance_prompt]] 会使用这里提供的行为。
- [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]] 会使用这里提供的行为。
- [[render_page_author]] 会使用这里提供的行为。
- [[render_page_author 与 _error 的协作实现]] 会使用这里提供的行为。
- [[replace_note]] 会使用这里提供的行为。
- [[rollback 与 RenderedBundle 的协作实现]] 会使用这里提供的行为。
- 可从 [[tests 职责导览]] 进入本页。
- [[transaction 的协作边界]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[CanvasBenchmarkContractTests]]
- [[CanvasContractTests]]
- [[CanvasContractTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 13 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `canonical` | `canonical` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `write_json` | `write_json` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `sha256` | `sha256` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `remove_tree` | `remove_tree` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `_link_directory` | `_link_directory` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `FixtureCase` | `FixtureCase` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `FixtureCase.validation` | `validation` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `FixtureCase.rollback_manifest` | `rollback_manifest` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `FixtureCase.request_value` | `request_value` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `FixtureCase.write_request` | `write_request` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `FixtureCase.cleanup` | `cleanup` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `_case_root` | `_case_root` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |
| `build_acceptance_runtime` | `build_acceptance_runtime` 在 `runtime_builder.py` 中用于验证目标行为、失败分类和回归边界。 |

</details>
