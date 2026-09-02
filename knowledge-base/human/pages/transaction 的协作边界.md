# transaction 的协作边界

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **_role_paths**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:82-87`。
- **capture_baseline**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:101-150`。
- **_write_temp**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:153-176`。
- **_parse_and_validate**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:179-185`。
- **stage_bundle**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:188-212`。
- **_verify_staged_role**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:280-304`。
- **promote_bundle**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:307-377`。
- **rollback_from_manifest**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:421-556`。

## 相关代码

- 实现时会用到 [[FactFreshnessStateMachineTest]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[contracts 的协作边界（2ef5688e）]]。
- 实现时会用到 [[freeze 的协作边界]]。

## 谁会来到这里

- [[CanvasTransactionTests]] 会使用这里提供的行为。
- [[commands 的协作边界]] 会使用这里提供的行为。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
