# freeze 的协作边界

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **FrozenInputs**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/freeze.py:104-126`。
- **_sqlite_meta**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/freeze.py:285-295`。
- **load_and_freeze_request**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/freeze.py:331-480`。
- **recheck_frozen_inputs**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/freeze.py:483-511`。

## 相关代码

- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[contracts 的协作边界（prototypes）]]。
- 实现时会用到 [[source_files]]。

## 谁会来到这里

- [[CanvasGraphTests]] 会使用这里提供的行为。
- [[CanvasTransactionTests]] 会使用这里提供的行为。
- [[commands 的协作边界]] 会使用这里提供的行为。
- [[graph 的协作边界]] 会使用这里提供的行为。
- [[transaction 的协作边界]] 会使用这里提供的行为。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
