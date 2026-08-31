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

## LLM 关键词慢路径的日志边界

`retrieve`、`brief` 和 `keyword-benchmark` 仍只在本日志写入既有七个字段。问题正文、原始词项、模型候选、Provider 命令、环境变量、usage、stdout 和 stderr 不进入 operation journal。慢路径的原始/扩展词项、Provider 状态、token、费用和缓存命中只进入对应检索 record、benchmark 报告以及 `workspace-meta/keyword-fallback` 下的有界机器记录；`maintain` 独立审计这些记录的 schema 和隐私边界。
