# transaction 的协作边界

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **ArtifactBaseline**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:40-60`。
- **ArtifactBaseline.manifest_states**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:46-60`。
- **_role_paths**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:82-87`。
- **capture_baseline**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:101-150`。
- **_write_temp**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:153-176`。
- **_parse_and_validate**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:179-185`。
- **stage_bundle**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:188-212`。
- **cleanup_staged**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:215-220`。
- **_write_backups**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:252-261`。
- **_verify_staged_role**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:280-304`。
- **promote_bundle**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:307-377`。
- **verify_promoted**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:380-411`。
- **rollback_from_manifest**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:421-556`。

## 相关代码

- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[contracts 的协作边界]]。
- 实现时会用到 [[freeze 的协作边界]]。
- 实现时会用到 [[graph 的协作边界]]。

## 谁会来到这里

- [[CanvasTransactionTests]] 会使用这里提供的行为。
- [[rollback]] 会使用这里提供的行为。
- [[rollback 与 RenderedBundle 的协作实现]] 会使用这里提供的行为。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
