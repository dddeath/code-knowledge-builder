# graph 的协作边界

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **SourceSelection**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:32-36`。
- **SelectedGraph**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:40-43`。
- **ValidationFacts**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:47-53`。
- **canonical_json_bytes**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:56-68`。
- **canonical_canvas_bytes**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:71-72`。
- **select_graph**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:88-238`。
- **_stable_id**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:241-243`。
- **layout_graph**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:246-300`。
- **layout_graph.edge**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:284-294`。
- **validate_canvas**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:345-418`。

## 相关代码

- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[contracts 的协作边界]]。
- 实现时会用到 [[freeze 的协作边界]]。
- 实现时会用到 [[source_files]]。

## 谁会来到这里

- [[CanvasBenchmarkContractTests]] 会使用这里提供的行为。
- [[CanvasDeterminismTests]] 会使用这里提供的行为。
- [[CanvasGraphTests]] 会使用这里提供的行为。
- [[benchmark 的协作边界]] 会使用这里提供的行为。
- [[main（benchmark_obsidian_canvas_navigation 测试）]] 会使用这里提供的行为。
- [[rollback 与 RenderedBundle 的协作实现]] 会使用这里提供的行为。
- [[transaction 的协作边界]] 会使用这里提供的行为。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
