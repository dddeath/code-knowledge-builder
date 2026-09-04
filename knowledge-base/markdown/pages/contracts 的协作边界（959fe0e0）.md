# contracts 的协作边界（959fe0e0）

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **TagNavigationError**：位于 `prototypes/ckb-tag-navigation/ckb_tag_navigation/contracts.py:25-29`。
- **canonical_json_text**：位于 `prototypes/ckb-tag-navigation/ckb_tag_navigation/contracts.py:36-37`。
- **validate_assertion**：位于 `prototypes/ckb-tag-navigation/ckb_tag_navigation/contracts.py:145-194`。
- **validate_policy**：位于 `prototypes/ckb-tag-navigation/ckb_tag_navigation/contracts.py:197-226`。

## 谁会来到这里

- [[TagNavigationBenchmarkTests]] 会使用这里提供的行为。
- [[TagNavigationRollbackTests]] 会使用这里提供的行为。
- [[assertions 等测试场景]] 会使用这里提供的行为。
- [[benchmark 的协作边界（prototypes）]] 会使用这里提供的行为。
- [[cli 的协作边界（99938c49）]] 会使用这里提供的行为。
- [[ingest]] 会使用这里提供的行为。
- [[ingest 与 connect 的协作实现]] 会使用这里提供的行为。
- [[projection 的协作边界]] 会使用这里提供的行为。
- [[state_machine 的协作边界]] 会使用这里提供的行为。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
