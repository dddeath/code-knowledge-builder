# Research gaps and missing-source register

Research gaps are pending claims, not reviewed facts. CKB stores them under `OUTPUT/workspace-meta/gaps`, indexes them in `machine/knowledge.sqlite`, and exposes one aggregate “研究缺口与待补来源” section in `RECORDS.md`. It never creates one Markdown page per gap.

Create a gap only when an existing retrieval record, feedback record, reviewed reference, or other durable file inside `OUTPUT` shows insufficient evidence, conflicting sources, or an explicitly deferred feedback item. The summary must be one bounded Simplified-Chinese statement. Evidence accepts one to twelve existing paths inside `OUTPUT`; raw prompts, conversation bodies, external absolute paths, and unverified claims are rejected.

```powershell
& PYTHON scripts\ckb.py gaps create --out OUTPUT `
  --kind insufficient-evidence --summary SUMMARY.md --evidence machine/agent-packs/PACK.json
& PYTHON scripts\ckb.py gaps list --out OUTPUT --status open
& PYTHON scripts\ckb.py gaps resolve --out OUTPUT `
  --gap GAP_ID --resolution RESOLUTION.md --evidence human/changes/VERIFIED.md
& PYTHON scripts\ckb.py gaps audit --out OUTPUT
```

The three kinds are `insufficient-evidence`, `conflicting-sources`, and `deferred-feedback`. New records are `open`, except deferred feedback starts as `deferred`; only `resolve` produces `resolved`. Resolution requires a Chinese closure statement and at least one existing closure-evidence path.

The audit checks the fixed schema, stable ID, evidence containment, status fields, deterministic index, SQLite count, `RECORDS.md` mirror, and the zero-page quota. `maintain` includes this audit. Retrieval labels matching gap documents as “待验证研究缺口”, so Agents can find missing evidence without treating it as source-grounded truth.
