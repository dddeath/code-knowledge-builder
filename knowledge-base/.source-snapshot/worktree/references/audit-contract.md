# Audit contract

## Parse-batch gates

1. **scope**: the entity set exactly matches the parse-batch plan and every exclusion has a recorded reason.
2. **syntax**: every included file parses and each named declaration has one machine entity.
3. **classification**: every entity exactly matches the deterministic navigation plan as `page`, `appendix`, or `boundary`; every appendix has one planned source page.
4. **semantics**: providers succeed, every independent key entity has definition evidence, and emitted internal relationships resolve.
5. **source**: commit and blob objects exist and every primary range, C# partial fragment, and name matches the fixed Git blob.
6. **descriptions**: every page has reviewed Simplified-Chinese meaning, responsibility, modification trigger, and evidence; every appendix has one useful reviewed Simplified-Chinese sentence and evidence. English proper nouns and code identifiers may remain, but an English-only sentence or paragraph fails this gate.
7. **links**: endpoints exist and cross-batch relations remain explicit until merge.

Machine parse batches and Agent review packs are independent state objects. Page-review packs and appendix-review packs have separate file, item, and deterministic token limits. A parse batch passes only after all of its review packs and all seven gates pass.

## Navigation hard gates

- Deterministic scripts are the only authority for classification, ownership, rank, order, quotas, relation aggregation, and context limits.
- Page quotas come only from the pinned `page-config.json`. Defaults are one key page per ordinary file, four per core file, one per adjacent file, and four core plus three adjacent pages per entry cluster. Overlaps are globally deduplicated.
- Boundary entities are grouped by source path in the human projection while remaining separate machine facts.
- Per source page, visible relation groups are bounded by the pinned configuration; defaults are 20 direct, 10 aggregate, 8 test, and 8 boundary. Every hidden group has a count and every original relation remains in `graph.json`.
- The Graphify node and link ID sets exactly equal the CKB fact graph; endpoints, relation type, commit/blob/range fields, provider evidence, and source paths match. Confidence is one deterministic Graphify tier, and signed communities cover every node exactly once.
- `graphify-out/GRAPH_REPORT.md`, `graph.json`, `communities.json`, and `projection.json` exist with matching hashes and machine-side provenance/count contracts. The human report exposes no commits, confidence tiers, degree, classification, community ID, or cohesion.
- Markdown links have existing targets and visible backlinks are exactly symmetric.
- Every human page has exactly one deterministic type tag. Every source-bearing page has one valid local editor URI and its readable relative path/range. Human pages and workspace notes contain no hash-like identifiers.
- The detached source snapshot still resolves to the pinned commit/tree and has no tracked changes. The user's live HEAD and worktree may advance after snapshot creation without changing the baseline result.
- The Obsidian vault contains the minimal generated configuration and all five preserved note directories. Generator ownership never includes Obsidian workspace layout or unknown user files.
- `facts/graph.json` is byte-identical to the root graph; source and review manifests have exact entity/pack sets and matching counts.
- `machine/knowledge.sqlite` passes SQLite integrity and foreign-key checks; all file/entity/range/relation/review/human-ownership counts match the fact graph; every required narrative field contains Chinese content; fixed source is stored once per file; deterministic retrieval stays within budget and returns source-bound entities.
- `human/` and `markdown/` have byte parity for generated pages and Agent notes. Human readability, Chinese narrative, double-link, source-link, Obsidian, quota and ownership audits all pass.
- `agent-index.sqlite` passes SQLite integrity and foreign-key checks as a compatibility index; page/note counts and the recorded source projection format match, and the schema contains no hash field.
- Every Logseq CLI operation stops the DB worker scoped to its isolated output root and graph. The cleanup record must show every stop succeeded, so repeated `finalize` does not depend on an unlocked file race.
- Human titles are prefix-free and unique; standalone pages map only to classes/functions; all other pages are class/function aggregations. Visible Markdown/Logseq content has no frontmatter, stable IDs, commit hashes, blobs, classification/provider properties, raw relation labels, or machine counts.
- `WIKI.md` contains the Chinese reading order, page contract, modification workflow, deterministic machine retrieval, Graphify task narrowing, and Logseq instructions. `readability-audit.json` must report zero non-Chinese narrative fields as well as all existing readability metrics; the separate `human-readable-pages` gate prevents completion on any failure.
- Markdown outputs contain `logseq/config.edn` at both selectable roots, `OUTPUT` and `OUTPUT/markdown`, byte-identical to the pinned upstream template, with matching paths, SHA-256, commit, and source URL in `projection.json`.
- Appendix rows contain only symbol and one useful sentence. They expose no stable entity ID, type, source range, or direct relation count.
- Context and review-pack limits come only from the pinned configuration. Defaults use `ceil(UTF-8 bytes / 3)`: full module at most 80,000, task subgraph at most 20,000, total budget 100,000 with 20,000 reserved for the Agent.

## Global gates

- Parse-batch entity sets form an exact, non-overlapping union of the selected catalog.
- Every review pack and parse-batch audit is `passed`.
- The canonical `page-config.json`, its state/graph/projection hashes, navigation limits, relation limits, context records, and rendered section contract all match.
- Cross-batch links resolve and one-hop boundaries match `scope.json`.
- C# partial fragments resolve to one logical entity and every fragment remains source-authentic.
- Logseq validation and SQLite export succeed when requested.
- Markdown and Logseq projections have identical page ownership, visible relation, source, EDN, and count contracts in `both` mode.
- The fixed snapshot commit/tree, Git blobs, source ranges, C# fallback/restore worktree, and private restore evidence remain authentic. The live worktree is represented separately by workspace metadata.
- Every queued Agent session/note that predates the human projection is materialized exactly once. Changed sessions contain the required Chinese `修改内容`、`修改原因` and `验证结果` sections and link to deterministic query results or changed-path owner pages.
- `.complete`, `.machine.complete`, and `.human.complete` are written together only by `finalize`; rebuilding or auditing withdraws the full completion set first.
- An incremental output additionally passes `migration/audit.json`: the origin was globally audited, exact-blob reuse sets match, every reused parse carries re-key evidence, mutable user/Agent files retain immutable preservation baselines while live copies remain readable, every migrated/delta review pack passed, and the target graph contains only target-commit entity provenance. Migration never exempts an output from an ordinary current-version gate.

`bounded-approximate` may pass only when the relevant provider returns document symbols for every included file, every key entity has semantic evidence, fatal diagnostics are zero, and unresolved internal targets are zero. Only `finalize` may create the three completion markers.

## Automation gates

Automation health is audited separately from the fixed-source completion set:

- every written event belongs to an enabled repository/Harness registration and its `cwd` is inside that repository;
- a registered session without an exact `code-knowledge-builder` activation produces zero event, turn and spool writes;
- prompt, native Skill event and `automation activate` routes produce one idempotent activation scoped to Harness, session and repository;
- spool pending/processed/failed transitions are atomic, retry is explicit, and `automation.sqlite` integrity is `ok`;
- replaying the same stable event produces one event, one turn update and at most one pending review;
- concurrent events preserve every unique event and never duplicate the same changed path/review ownership;
- default and custom redaction remove sensitive values before spool persistence;
- changed paths are repository-relative and exclude knowledge output paths outside or inside the repository;
- each completed turn creates exactly one machine `pending-agent-review` record;
- pending records are visible to deterministic FTS and `changes`, but have no human file;
- promotion requires a Chinese body, Chinese evidence note, exact changed-path source-check set, resolved links and the ordinary note audit;
- Hook outputs never claim source-graph completion and never change Harness permissions or continuation decisions.

An automation failure leaves the fixed snapshot completion markers unchanged while `automation status` reports the failed/pending state. A reviewed automation note is ordinary mutable knowledge layered over that fixed baseline.
