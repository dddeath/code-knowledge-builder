# graph 的协作边界

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **SourceSelection**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:32-36`。
- **canonical_json_bytes.normalize**：位于 `prototypes/ckb-canvas-skill/ckb_canvas/graph.py:59-66`。
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
- 实现时会用到 [[contracts 的协作边界（36093e4a）]]。
- 实现时会用到 [[freeze 的协作边界]]。
- 实现时会用到 [[source_files]]。

## 谁会来到这里

- [[CanvasGraphTests]] 会使用这里提供的行为。
- [[commands 的协作边界]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[propose_template 与 _canonical_bytes 的协作实现]] 会使用这里提供的行为。
- [[run_failure_probe 等测试场景]] 会使用这里提供的行为。
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]] 会使用这里提供的行为。
- [[search_terms 与 _split_camel 的协作实现]] 会使用这里提供的行为。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
