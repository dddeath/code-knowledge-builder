# benchmark 的协作边界（e30cfb0a）

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **EngineUnavailable**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:32-33`。
- **ModelUnavailable**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:36-37`。
- **_readonly_connection**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:80-81`。
- **_sqlite_backup**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:84-87`。
- **copy_corpus**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:90-120`。
- **validate_model_artifacts**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:123-159`。
- **engine_identity**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:162-175`。
- **validate_protocol**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:182-248`。
- **render_documents**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:251-278`。
- **documents_digest**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:281-283`。
- **network_guard**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:287-306`。
- **network_guard.blocked_connect**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:292-294`。
- **network_guard.blocked_create**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:296-298`。
- **_vector_ranking**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:348-375`。
- **_load_index**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:378-396`。
- **index_size_accounting**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:399-413`。
- **unique_sqlite_documents**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:507-525`。
- **_hybrid_ranking**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:595-643`。
- **_worker_rows**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:646-724`。
- **_worker_rows.invoke**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:667-699`。
- **_run_worker_process**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:770-841`。
- **_run_build_process**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:844-892`。
- **evaluate_resource_limits**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:984-998`。
- **run_benchmark**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:1001-1148`。
- **_write_unavailable**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:1151-1161`。
- **main**：位于 `prototypes/ckb-semantic-vector-benchmark/benchmark.py:1164-1209`。

## 相关代码

- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[retrieve_machine]]。

## 谁会来到这里

- [[DriftAndAvailabilityTests]] 会使用这里提供的行为。
- [[DriftAndAvailabilityTests 等测试场景]] 会使用这里提供的行为。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
