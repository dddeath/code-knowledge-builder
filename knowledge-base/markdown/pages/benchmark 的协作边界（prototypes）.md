# benchmark 的协作边界（prototypes）

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **validate_run**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/benchmark.py:51-111`。
- **load_run**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/benchmark.py:114-117`。
- **judge_session**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/benchmark.py:147-247`。
- **run_session**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/benchmark.py:250-266`。
- **summarize**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/benchmark.py:305-455`。
- **summarize_to_path**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/benchmark.py:473-493`。

## 相关代码

- 实现时会用到 [[append]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[contracts 的协作边界（36093e4a）]]。
- 实现时会用到 [[doctor_report 与 _version_matches 的协作实现]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[CanvasBenchmarkContractTests]] 会使用这里提供的行为。
- [[ckb_canvas 的协作边界]] 会使用这里提供的行为。
- [[main（benchmark_obsidian_canvas_navigation 测试）]] 会使用这里提供的行为。
