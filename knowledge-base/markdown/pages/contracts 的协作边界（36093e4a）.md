# contracts 的协作边界（36093e4a）

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **validate_instance**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/contracts.py:165-168`。
- **CanvasFailure**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/contracts.py:225-264`。
- **CanvasFailure.exit_code**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/contracts.py:239-240`。

## 相关代码

- 实现时会用到 [[commands 的协作边界]]。

## 谁会来到这里

- [[CanvasBenchmarkContractTests]] 会使用这里提供的行为。
- [[CanvasContractTests]] 会使用这里提供的行为。
- [[CanvasGraphTests]] 会使用这里提供的行为。
- [[CanvasPathTests]] 会使用这里提供的行为。
- [[CanvasRollbackTests]] 会使用这里提供的行为。
- [[CanvasTransactionTests]] 会使用这里提供的行为。
- [[CkbError]] 会使用这里提供的行为。
- [[CkbError 与 DependencyError 的协作实现]] 会使用这里提供的行为。
- [[SessionStdioLifecycleTests]] 会使用这里提供的行为。
- [[TagNavigationCanvasCompatibilityTests]] 会使用这里提供的行为。
- [[_Transport.close]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[benchmark 的协作边界（prototypes）]] 会使用这里提供的行为。
- [[ckb_canvas 的协作边界]] 会使用这里提供的行为。
- [[commands 的协作边界]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[freeze 的协作边界]] 会使用这里提供的行为。
- [[graph 的协作边界]] 会使用这里提供的行为。
- [[serve_stdio]] 会使用这里提供的行为。
- [[transaction 的协作边界]] 会使用这里提供的行为。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
