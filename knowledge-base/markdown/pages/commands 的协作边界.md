# commands 的协作边界

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **RenderedBundle**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py:34-42`。
- **_validation_manifest**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py:49-95`。
- **_rollback_manifest**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py:98-131`。
- **_render**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py:134-152`。
- **_bundle_bytes**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py:155-160`。
- **generate**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py:163-210`。
- **validate_only**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/commands.py:213-225`。

## 相关代码

- 实现时会用到 [[append]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[contracts 的协作边界（2ef5688e）]]。
- 实现时会用到 [[freeze 的协作边界]]。
- 实现时会用到 [[graph 的协作边界]]。
- 实现时会用到 [[transaction 的协作边界]]。

## 谁会来到这里

- [[CanvasContractTests]] 会使用这里提供的行为。
- [[CanvasDeterminismTests]] 会使用这里提供的行为。
- [[CanvasGraphTests]] 会使用这里提供的行为。
- [[CanvasPathTests]] 会使用这里提供的行为。
- [[CanvasRollbackTests]] 会使用这里提供的行为。
- [[CanvasTransactionTests]] 会使用这里提供的行为。
- [[ckb_canvas 的协作边界]] 会使用这里提供的行为。
- [[cli 的协作边界（prototypes）]] 会使用这里提供的行为。
- [[contracts 的协作边界（2ef5688e）]] 会使用这里提供的行为。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
