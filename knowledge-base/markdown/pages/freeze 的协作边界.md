# freeze 的协作边界

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **FrozenInputs**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/freeze.py:104-126`。
- **_expect_hash**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/freeze.py:204-218`。
- **load_and_freeze_request**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/freeze.py:331-480`。
- **recheck_frozen_inputs**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/freeze.py:483-511`。
- **validate_source_range**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/freeze.py:514-530`。

## 相关代码

- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[contracts 的协作边界]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ensure_local_openers 与 SourceLinkRenderer 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[graph 的协作边界]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[transaction 的协作边界]] 存在待核验的词法关联；是否调用或依赖需查看源码。
