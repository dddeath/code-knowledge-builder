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
