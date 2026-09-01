# Graphify construction core

## Pinned source

- Upstream: `https://github.com/Graphify-Labs/graphify`
- Branch observed at acquisition: `v8`
- Commit: `b2cd36267456c166788c95be6e68574064a92a42`
- Package version: `0.9.48`
- License: Apache-2.0 with upstream NOTICE and retained historical MIT text.

The unmodified upstream `graphify/cluster.py` and vendored NetworkX 3.5 are in
`scripts/_vendor/`. Their source and license records are part of both lite and
full packages.

## Stage mapping

Graphify separates `detect -> extract -> build -> cluster -> report -> export`.
CKB maps its resumable state machine onto those boundaries:

| Graphify stage | CKB stage | Hard evidence retained |
| --- | --- | --- |
| detect | `init` scope/catalog/chunk plan | fixed commit, tree, blob IDs, explicit includes/excludes |
| extract | `build-chunk syntax/semantics` | Tree-sitter ranges, LSP commands, diagnostics, provider targets |
| build | `merge` | exact entity and link sets after every Agent review pack passes |
| cluster | global audit projection | deterministic Graphify Leiden/Louvain fallback with seed 42 and stable reindexing |
| report | global audit projection | bounded Chinese responsibility groups and class/function entry points; machine provenance remains in JSON |
| export | `graphify-out`, Markdown, Logseq DB | one canonical fact graph with audited parity gates |

Graphify's graph is a projection, not a second fact extractor. This prevents a
community or fuzzy label from overwriting CKB's stable IDs, Git blobs, exact
ranges, local-scope boundary facts, or Agent-reviewed descriptions.

## Confidence mapping

- `EXTRACTED` with score `1.0`: direct AST, language-server, or structural
  provider evidence.
- `INFERRED` with score `0.85`: deterministic lexical-candidate resolution.
- `AMBIGUOUS` with score `0.55`: the provider or relation explicitly marks an
  uncertain target.

Agent prose does not choose these values. Every projected relation preserves its
CKB link ID, provider, evidence object, source file, endpoints, and cross-chunk
flag. A missing provider/source or invalid endpoint fails the global gate.

## Query-first navigation

After completion, prefer:

```powershell
& PYTHON scripts\ckb.py query --out OUTPUT "问题" --budget 1500
& PYTHON scripts\ckb.py query --out OUTPUT "精确调用链" --dfs --budget 1500
& PYTHON scripts\ckb.py path --out OUTPUT "起点" "终点"
& PYTHON scripts\ckb.py explain --out OUTPUT "类名、函数名或职责关键词"
```

`query` uses deterministic label, qualified-name, path, reviewed-description,
and CJK-bigram scoring. It then runs bounded BFS or DFS over the local node-link
graph and records the result under `OUTPUT/graphify-out/queries/`. The budget is
`ceil(UTF-8 JSON bytes / 3)`. Query results point back to source paths and lines;
they do not authorize skipping source verification before a change.

## Completion rule

Every node and link in CKB `graph.json` must appear exactly once in Graphify
`graph.json`; every node must occur in exactly one signed community; projection
hashes, counts, confidence labels, upstream commit, and repository commit must
match in machine JSON. The human `GRAPH_REPORT.md` must not expose either
commit, confidence tiers, degrees, classifications, community IDs, or cohesion.
It groups reviewed classes/functions by responsibility. `finalize` writes
`.complete` only after this gate, human readability, and the requested format
gates pass.
