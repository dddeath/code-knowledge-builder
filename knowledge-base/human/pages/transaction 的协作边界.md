# transaction 的协作边界

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **stage_bundle**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:188-212`。
- **_write_backups**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:252-261`。
- **promote_bundle**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:307-377`。
- **rollback_from_manifest**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/transaction.py:421-556`。

## 相关代码

- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[contracts 的协作边界]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[freeze 的协作边界]] 存在待核验的词法关联；是否调用或依赖需查看源码。
