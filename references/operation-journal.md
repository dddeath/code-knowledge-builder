# Bounded machine operation journal

CKB records completed CLI operations under `OUTPUT/workspace-meta/operations` without creating human pages. The journal exists to show which compile, query, record, audit, and maintenance actions completed and where their generated evidence can be reopened.

Each JSONL record has only seven fields: schema version, event ID, UTC time, operation type, bounded command token, result status, and up to eight paths relative to `OUTPUT`. Questions, selected text, conversation bodies, credentials, command arguments, stdout, stderr, and complete result objects are not accepted into this layer.

Daily shards are limited to 2,000 records and 1 MiB. The implementation removes the oldest record when either limit is exceeded, retains thirty UTC days, deduplicates equivalent same-day results, and writes `latest.json` as the deterministic index and compact summary. `state.json` preserves bounded-drop, expiration, and deduplication counters.

```powershell
& PYTHON scripts\ckb.py operations list --out OUTPUT --limit 50
& PYTHON scripts\ckb.py operations list --out OUTPUT --operation query --status passed
& PYTHON scripts\ckb.py operations audit --out OUTPUT
```

`maintain` includes the journal audit. Unexpected fields, absolute or escaping evidence paths, duplicate IDs, malformed JSONL, oversized shards, summary drift, or a generated `human/operations` page fail the gate. A knowledge base without an initialized journal remains valid and receives its first record after the next journaled CLI command.

## 管理绑定审计与 operation journal 的分层

`manager` 的 canonical registry 位于 `CKB_MANAGER_REGISTRY` 或显式 `--registry`，不写入知识库的 operation journal。这样可以在 conversation 解绑后保留项目管理身份、bound HEAD、任务派发和失败原因，同时避免把 opaque conversation ID、branch/worktree 路径或测试输出扩散到 `OUTPUT/workspace-meta/operations`。

管理注册表的 `audit_log` 只保存固定字段：event ID、binding ID、动作、结果、机器原因码和 UTC 时间；不保存 prompt、assistant 原文、secret、token 或 transcript path。任务交接 Prompt 与验证记录保存在注册表同目录的 `<registry-stem>-artifacts/`，注册表只保存绝对路径和 SHA-256；`manager audit` 重新打开并核对这些文件。

```powershell
& PYTHON scripts\ckb.py manager audit --registry MANAGER_REGISTRY
& PYTHON scripts\ckb.py manager status --conversation-id CONVERSATION_ID --harness HARNESS --registry MANAGER_REGISTRY
```

`manager audit` 证明 canonical 持久层、隐私字段、稳定 ID、生命周期状态和任务侧车一致；`manager status/context/task-status` 另行读取当前 Git 与知识库门。结构审计通过不覆盖 HEAD drift、dirty tree、测试失败或 maintain 失败。
