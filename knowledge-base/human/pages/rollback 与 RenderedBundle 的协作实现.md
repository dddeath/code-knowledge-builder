# rollback 与 RenderedBundle 的协作实现

标签：#类型/代码

> `prototypes/ckb-canvas-skill/ckb_canvas/commands.py` 页面绑定固定源码第 1-234 行，说明该文件在Canvas 原型命令编排和结果边界中的整体职责。 该文件负责Canvas 原型命令编排和结果边界，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py` 中 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：prototypes/ckb-canvas-skill/ckb_canvas/commands.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/prototypes/ckb-canvas-skill/ckb_canvas/commands.py:1:1)  `prototypes/ckb-canvas-skill/ckb_canvas/commands.py:1-234`

## 相关代码

- 实现时会用到 [[append]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[contracts 的协作边界]]。
- 实现时会用到 [[freeze 的协作边界]]。
- 实现时会用到 [[graph 的协作边界]]。
- 主要代码单元是 [[rollback]]。
- 实现时会用到 [[transaction 的协作边界]]。
- 实现时会用到 [[validate]]。

## 谁会来到这里

- [[CanvasContractTests]] 会使用这里提供的行为。
- [[CanvasDeterminismTests]] 会使用这里提供的行为。
- [[CanvasGraphTests]] 会使用这里提供的行为。
- [[CanvasPathTests]] 会使用这里提供的行为。
- [[CanvasRollbackTests]] 会使用这里提供的行为。
- [[CanvasTransactionTests]] 会使用这里提供的行为。
- [[ckb_canvas 的协作边界]] 会使用这里提供的行为。
- [[contracts 的协作边界]] 会使用这里提供的行为。
- 可从 [[prototypes 职责导览]] 进入本页。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[CanvasBenchmarkContractTests]]
- [[CanvasContractTests]]
- [[CanvasDeterminismTests]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 8 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `RenderedBundle` | `RenderedBundle` 在 `commands.py` 中用于生成稳定排序的结构化表示或人类输出。 |
| `_sha` | `_sha` 在 `commands.py` 中用于完成Canvas 原型命令编排和结果边界中的局部职责。 |
| `_validation_manifest` | `_validation_manifest` 在 `commands.py` 中用于完成Canvas 原型命令编排和结果边界中的局部职责。 |
| `_rollback_manifest` | `_rollback_manifest` 在 `commands.py` 中用于执行范围受控的恢复、撤销或清理。 |
| `_render` | `_render` 在 `commands.py` 中用于生成稳定排序的结构化表示或人类输出。 |
| `_bundle_bytes` | `_bundle_bytes` 在 `commands.py` 中用于完成Canvas 原型命令编排和结果边界中的局部职责。 |
| `generate` | `generate` 在 `commands.py` 中用于完成Canvas 原型命令编排和结果边界中的局部职责。 |
| `validate_only` | `validate_only` 在 `commands.py` 中用于校验输入、状态、证据或输出合同。 |

</details>
