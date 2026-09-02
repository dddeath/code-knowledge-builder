# validate 与 canonical 的协作实现

标签：#类型/代码

> `references/design/obsidian-canvas-agent-visualization/verification/validate_design.py` 页面绑定固定源码第 1-181 行，说明该文件在Canvas 设计 schema、fixture、链接和 benchmark 合同验证中的整体职责。 该文件负责Canvas 设计 schema、fixture、链接和 benchmark 合同验证，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `references/design/obsidian-canvas-agent-visualization/verification/validate_design.py` 中 `references/design/obsidian-canvas-agent-visualization/verification/validate_design.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：references/design/obsidian-canvas-agent-visualization/verification/validate_design.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/references/design/obsidian-canvas-agent-visualization/verification/validate_design.py:1:1)  `references/design/obsidian-canvas-agent-visualization/verification/validate_design.py:1-181`

## 相关代码

- 实现时会用到 [[append]]。
- 主要代码单元是 [[validate]]。

## 谁会来到这里

- [[AgentProtocolBatchApplyTests 等测试场景]] 会使用这里提供的行为。
- [[CkbError 与 DependencyError 的协作实现]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[audit_references 与 _root 的协作实现]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[doctor_report 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[main 与 sha256 的协作实现]] 会使用这里提供的行为。
- [[propose_template]] 会使用这里提供的行为。
- [[propose_template 与 _canonical_bytes 的协作实现]] 会使用这里提供的行为。
- 可从 [[references 职责导览]] 进入本页。
- [[render_page_author 与 _error 的协作实现]] 会使用这里提供的行为。
- [[run]] 会使用这里提供的行为。
- [[source_files]] 会使用这里提供的行为。
- [[source_files 与 sha256 的协作实现]] 会使用这里提供的行为。
- [[validate]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[CanvasBenchmarkContractTests]]
- [[CanvasContractTests]]
- [[CanvasContractTests 等测试场景]]
- [[CanvasDeterminismTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 8 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `canonical` | `canonical` 用于完成局部输入校验、转换或状态更新。 |
| `digest` | `digest` 在 `validate_design.py` 中用于生成稳定标识或字节校验值。 |
| `is_type` | `is_type` 用于完成局部输入校验、转换或状态更新。 |
| `load` | `load` 在 `validate_design.py` 中用于读取、规范化并返回既有状态。 |
| `assert_valid` | `assert_valid` 在 `validate_design.py` 中用于校验输入、状态、证据或输出合同。 |
| `slug` | `slug` 用于完成局部输入校验、转换或状态更新。 |
| `walk` | `walk` 用于完成局部输入校验、转换或状态更新。 |
| `add` | `add` 用于完成局部输入校验、转换或状态更新。 |

</details>
