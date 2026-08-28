---
name: code-knowledge-builder
description: Build and maintain separate machine and human code knowledge bases from a fixed Git snapshot, with deterministic SQLite retrieval, conservative Chinese Markdown/Obsidian pages, persistent cross-Harness Agent instructions, Agent review, local scopes, optional Logseq DB, and opt-in conversation/change synchronization. Use for locating or maintaining change-relevant files, types, functions, source ranges, analyses, modifications, and durable Agent-session evidence in C/C++, C#, standard JavaScript, and Python repositories; not for one-file explanation or ordinary text search.
metadata:
  version: "5.1.4"
---

# Code Knowledge Builder

## 简体中文描述硬契约

知识库中的**所有叙述内容必须使用简体中文**。这条规则适用于实体的含义、职责、修改时机、来源核验说明、附录句子、首页、Wiki、关系叙述、Agent 阅读包、分析、修改原因、踩坑、实验和会话总结。英文只保留在专有名词、API、类型、类、函数、变量、命令、路径以及确有必要的技术术语中；不得提交整句或整段纯英文说明。Agent 必须把来源中的英文解释改写为中文叙述，同时原样保留源码标识符。

逐实体审阅、全局审计、人类层审计和机器层审计都会确定性检查该契约。任一叙述字段缺少中文内容时，保持 `.pending-agent-review` 或写入 `.failed`；该结果不得标记完成。页面标题可直接使用 `OrderService`、`parse_file` 等源码名称，但正文必须是中文。

Build a source-grounded navigation graph from a fixed Git snapshot. The scanner never edits the user's repository; after `init` reports `snapshot-ready`, the Agent may edit the live worktree while AST/LSP construction continues against the detached baseline snapshot. Treat every generated directory as a candidate until every chunk and the global audit pass. The output is deliberately split: `OUTPUT/machine/knowledge.sqlite` is the complete Agent-facing database, while `OUTPUT/human` is a conservative Simplified-Chinese Markdown/Obsidian vault. The compatibility path `OUTPUT/markdown` mirrors the human vault. The human layer is not an entity dump: every visible page is a class/function or a readable aggregation of related classes/functions.

The construction core follows the pinned Graphify pipeline `detect -> extract -> build -> cluster -> report/export`. CKB keeps its stricter Git blob/range manifest, language-provider evidence, deterministic page quotas, segmented recovery, and mandatory Agent review around that core. `OUTPUT/facts` retains rebuildable authoritative facts; machine artifacts retain full provenance and complete relations; Markdown, Logseq pages, and the Chinese `GRAPH_REPORT.md` deliberately omit commit/blob/ID/classification properties and use natural titles and relation sentences. Use `retrieve`, `entity`, `neighbors`, `source`, and `changes` before opening broad source context.

## Choose a route

- For a small or ordinary repository, use the resumable `run` entrypoint.
- For a large repository or a failed stage that needs narrow repair, use `init`, `build-chunk`, `review-pack`, `audit`, `merge`, and `finalize` separately.
- If `OUTPUT/machine/knowledge.sqlite` exists and the user asks an architecture, explanation, or change-location question, use `retrieve --profile fast` first and open only its budgeted Agent pack. Use `precise` for harder queries, `entity` for exact symbols, `neighbors` for bounded graph expansion, `source` for an exact source range, and `changes` for durable Agent records. Use narrow source reading only when retrieval returns `needs-source-read`.
- For an existing knowledge base that multiple Agents may open, run `agent-policy install --out OUTPUT --workspace-root TASK_ROOT` once. This installs audited `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Copilot instructions and an always-on Cursor rule at the knowledge roots and Harness task root. Thereafter Agents must use SQLite retrieval before grep, create durable notes only through `record`, and run `agent-policy check` before claiming maintenance complete; read [references/agent-policy.md](references/agent-policy.md) before changing this contract.
- Always require one explicit output format: `markdown`, `logseq-db`, or `both`.
- A finalized `markdown` projection exposes two audited Logseq file-graph roots. For Logseq 2.0.1 “File to DB graph”, select `OUTPUT` itself; it contains `OUTPUT/logseq/config.edn`. `OUTPUT/markdown` remains a second valid file-graph root and contains linked pages, its own pinned config, and `normalized.edn` for optional EDN import.
- Use repeatable `--scope-path` arguments for a local module or file. Use repeatable `--entry LANGUAGE:PATH#QUALIFIED_NAME` arguments plus `--expand-depth` for a feature slice.
- Use `--page-config CONFIG.json` on the initial `run` or `init` to configure per-file/core/adjacent page limits, visible page sections and headings, appendix expansion, relation limits, context budgets, and review-pack budgets. The normalized configuration is copied to `OUTPUT/page-config.json`, hashed into state, and becomes immutable for resume/finalize.
- For C#, use automatic unique `.sln`/`.slnx`/`.csproj` selection or specify `--csharp-solution` / `--csharp-project`. Never trigger restore unless the user explicitly selected `--allow-dotnet-restore`.
- If the input path is not a Git repository or has no commit, report that precondition and stop without changing it. Only after the user explicitly chooses repository creation, rerun the initial `run` or `init` with `--init-git`; this initializes Git when needed, stages the current snapshot, and creates exactly one initial commit before scanning.

Read [references/workflow.md](references/workflow.md) before running a build. Read [references/migration.md](references/migration.md) before reusing an audited older knowledge base on a newer commit. Read [references/dual-knowledge-layers.md](references/dual-knowledge-layers.md) before consuming or changing the facts, machine, or human layer. Read [references/workspace-mode.md](references/workspace-mode.md) when code edits, analysis notes, change reasons, pitfalls, experiments, or conversations must be retained during the build. Read [references/automation.md](references/automation.md) before enabling automatic conversation or modification synchronization in Codex, Claude Code, OpenCode, DSH, Gemini CLI, GitHub Copilot, Cursor, or another Harness. Read [references/agent-retrieval.md](references/agent-retrieval.md) before broad source search. Read [references/obsidian.md](references/obsidian.md) before changing vault layout, tags, source links, or local editor settings. Read [references/page-configuration.md](references/page-configuration.md) before changing page quotas, content, relation/context limits, or review-pack size. Read [references/human-readable-pages.md](references/human-readable-pages.md) before changing titles, page prose, Wiki, appendices, or visible links. Read [references/graphify-core.md](references/graphify-core.md) before changing clustering, confidence mapping, reports, or scoped queries. Read [references/schema.md](references/schema.md) before editing review JSON or consuming either graph schema. Read [references/audit-contract.md](references/audit-contract.md) before interpreting a failed gate. Read [references/runtime.md](references/runtime.md) when `doctor` reports missing tools or requests permission to deploy the full bundle.

## Fast route

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" run --repo "REPO" --out "OUTPUT" --format markdown
```

Create and edit a complete configuration, then pin it into the initial build:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" page-config --write ".\page-config.json"
& PYTHON "SKILL_DIR\scripts\ckb.py" page-config --validate ".\page-config.json"
& PYTHON "SKILL_DIR\scripts\ckb.py" run --repo "REPO" --out "OUTPUT" --format markdown --page-config ".\page-config.json"
```

For a source directory that has no Git commit, the first command returns exit `2` with a reminder. With explicit user choice, use:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" run --repo "REPO" --out "OUTPUT" --format markdown --init-git
```

The optional `--initial-commit-message`, `--git-author-name`, and `--git-author-email` arguments customize only that first commit. Existing Git repositories with a commit are never recommitted by `--init-git`; dirty existing repositories still fail the immutable-source preflight.

The command stops at the next Agent-review checkpoint. Machine parse batches and Agent review packs are independent. Reopen every source range in the emitted review-pack template, fill every page description or appendix sentence factually in Simplified Chinese, then submit it:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" review-pack --out "OUTPUT" --pack "PACK_ID" --review "REVIEW.json"
& PYTHON "SKILL_DIR\scripts\ckb.py" run --out "OUTPUT" --resume
```

When `status` reports `ready-to-finalize`, run:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" finalize --out "OUTPUT"
```

Retrieve a budgeted page-first context without loading the complete entity graph:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" retrieve --out "OUTPUT" "问题" --budget 1800 --max-pages 8 --profile fast
& PYTHON "SKILL_DIR\scripts\ckb.py" coverage --out "OUTPUT"
& PYTHON "SKILL_DIR\scripts\ckb.py" entity --out "OUTPUT" "OrderService"
& PYTHON "SKILL_DIR\scripts\ckb.py" neighbors --out "OUTPUT" "OrderService" --depth 2
& PYTHON "SKILL_DIR\scripts\ckb.py" source --out "OUTPUT" "OrderService" --context-lines 3
```

For every substantive explanation or analysis, open the returned pack, write the analysis body, and record it before replying:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" record --out "OUTPUT" --kind analysis `
  --title "分析标题" --body "BODY.md" --from-pack "PACK.json"
```

Return both the answer and the record result's Markdown path/Obsidian URI. For code edits, use `change`; use `pitfall`, `experiment`, and one `session` page where relevant.

At project initialization, start one Agent task session as soon as the fixed snapshot exists. This works while segmented construction is still running: the Chinese session note is queued and `finalize` materializes it into the human layer. Finish the session with a Chinese summary; a changed worktree requires `修改内容`、`修改原因` and `验证结果` headings.

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" workspace session-start --out "OUTPUT" --repo "REPO" `
  --question "本次实现或分析任务" --budget 1800 --profile fast
& PYTHON "SKILL_DIR\scripts\ckb.py" workspace session-finish --out "OUTPUT" --repo "REPO" `
  --session "SESSION_ID" --summary "SUMMARY.md" --title "本次修改记录"
& PYTHON "SKILL_DIR\scripts\ckb.py" workspace sessions --out "OUTPUT"
```

`workspace sync` remains available for an intermediate working-tree snapshot. Session and note commands never rewrite the fixed baseline graph.

## Automatic conversation and change synchronization

Automatic capture has two deterministic gates: the repository/Harness must be registered, and the current Harness session must explicitly apply this Skill. A registered project alone remains idle. At the beginning of every task that applies `code-knowledge-builder`, activate the exact Harness session before substantive tool work:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" automation activate `
  --harness codex `
  --session-id $env:CODEX_SESSION_ID `
  --cwd "HARNESS_TASK_ROOT" `
  --registry "REGISTRY"
```

`--session-id` may be omitted when the Harness exposes its documented session environment variable. An explicit `$code-knowledge-builder` or `/code-knowledge-builder` prompt activates the same session automatically. Claude `UserPromptExpansion` and `PreToolUse` for its `Skill` tool, OpenCode command events, and generic `skill.applied` payloads are also accepted when their exact skill name is `code-knowledge-builder`. A plain prose mention of the project name is not an activation signal.

Register the fixed repository/output pair before installing any Hook or Plugin:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" automation register `
  --repo "REPO" --out "OUTPUT" --registry "REGISTRY" `
  [--workspace-root "HARNESS_TASK_ROOT"] `
  --harness codex --harness claude --harness opencode --harness dsh
```

Generate one isolated integration bundle; inspect and merge it through the Harness's normal trust/configuration flow:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" automation render `
  --harness codex|claude|opencode|opencode-v2|dsh|gemini|copilot|cursor|generic `
  --destination "BUNDLE" --python "PYTHON" `
  --ckb "SKILL_DIR\scripts\ckb.py" --registry "REGISTRY"
```

After session activation, all adapters feed the same canonical protocol into `OUTPUT/machine/automation.sqlite`. Events first enter an atomic write-ahead spool, are deterministically redacted and deduplicated, and create one machine-only `pending-agent-review` record at turn stop. Pre-activation events return `ignored: skill-not-applied-in-session` with zero session/event/spool writes. The adapters do not parse Harness transcript files or directly create a reviewed human page.

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" automation status --out "OUTPUT"
& PYTHON "SKILL_DIR\scripts\ckb.py" automation pending --out "OUTPUT"
& PYTHON "SKILL_DIR\scripts\ckb.py" automation review-template `
  --out "OUTPUT" --review-id "REVIEW_ID" --write "REVIEW.json"
& PYTHON "SKILL_DIR\scripts\ckb.py" automation review --out "OUTPUT" --review "REVIEW.json"
```

The Agent must reopen every changed path, write Simplified-Chinese `evidence_note`, provide an exact source-check set, and use `修改内容`、`修改原因`、`验证结果` for a change before promotion. `automation drain` resumes pending spool events; `automation retry` explicitly replays failed events. Machine retrieval and `changes` include pending automation documents without treating them as human-reviewed knowledge.

The former graph commands remain available for exact route/debug work:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" query --out "OUTPUT" "问题" --budget 1500
& PYTHON "SKILL_DIR\scripts\ckb.py" path --out "OUTPUT" "起点" "终点"
& PYTHON "SKILL_DIR\scripts\ckb.py" explain --out "OUTPUT" "类名、函数名或职责关键词"
```

## Incremental migration

Reuse exact-blob syntax facts and Agent-reviewed Chinese descriptions from an older globally audited output while moving to a newer clean Git commit:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" migrate start `
  --from-out "OLD_OUTPUT" --repo "NEW_REPO" --out "STAGING_OUTPUT"
& PYTHON "SKILL_DIR\scripts\ckb.py" migrate status --out "STAGING_OUTPUT"
```

Only `delta-*` review packs require new Agent review. Exact reused facts are re-keyed to the target commit and re-enter the ordinary source/review gates. Run ordinary `finalize` only after `migrate audit` passes; finalize adds the migration gate and still runs every current-version global gate. Keep the old output untouched until the staging output has all three completion markers and the cutover/rollback probe succeeds.

Package completed human-readable examples with a Chinese Wiki:

```powershell
& PYTHON "SKILL_DIR\scripts\ckb.py" showcase --dist "DIST" `
  --sample "cpp=OUTPUT_A" --sample "python=OUTPUT_B"
```

## Completion contract

- Deterministic scripts alone choose `page`, `appendix`, or `boundary`; Agent review verifies source-grounded Chinese descriptions and never changes importance, ownership, ordering, configured quotas, or configured context limits.
- The Graphify-compatible graph must preserve the complete CKB node/link sets, map every relation to `EXTRACTED`, `INFERRED`, or `AMBIGUOUS` with provider evidence, cover every node exactly once in a deterministic community, and retain commit/blob/range provenance. Its pinned upstream is Graphify `0.9.48` commit `b2cd36267456c166788c95be6e68574064a92a42`.
- Only classes, structs/interfaces/records, functions, methods, constructors, and destructors may become standalone human code-unit pages. Every file, directory group, repository entry, and local-scan boundary is rendered as a code-unit aggregation, never as an entity/module/file inventory page.
- Human page titles contain no `实体 ·` / `文件 ·` / `模块 ·` / `仓库 ·` / `边界 ·` prefix. Visible pages have no YAML frontmatter and expose no stable ID, commit, blob, classification, language-provider field, raw relation type, or machine relation count.
- Every generated page has exactly one deterministic page-type tag. Every source-bearing page has one clickable local source link plus its readable relative path/range. Human pages and Agent notes omit hash-like identifiers.
- `OUTPUT/markdown` is a preserved Obsidian vault. Projection replaces only generator-owned files; analysis, change, pitfall, experiment, session, user, and Obsidian workspace files survive rebuilds.
- Every finalized format creates the authoritative `facts/` rebuild layer, the complete `machine/knowledge.sqlite` Agent layer, and the conservative `human/` Chinese Markdown/Obsidian layer. `agent-index.sqlite` remains a compatibility index. Machine and human completion markers are separate and both must agree with the global audit.
- Version 5 retrieval is pure deterministic computation: normalized identifiers/CJK terms, exact anchors, SQLite FTS5 over entity/section/source text, fixed relation weights, degree penalties, and either bounded two-hop propagation (`fast`) or fixed-iteration weighted PageRank (`precise`). It uses no embedding, vector model, network model, or hidden ranking call. Vector retrieval remains outside this release until a later benchmark proves a downstream quality/cost gain.
- Version 5.1 automation is Harness-neutral and project-opt-in. Codex and Claude Code use their respective command Hooks, OpenCode uses generated stable or V2 Plugin adapters, DSH reuses its documented five-event Codex bridge, Gemini/Copilot/Cursor use their native lifecycle names and timeout units, and other Harnesses submit the canonical JSON Schema. Adapter-specific payloads never enter classification, review, or projection logic.
- A Harness task root may be registered separately from the Git `repo_root`. Direct repository matches have priority; workspace matches route the event to the nested source repository, while Git status, changed paths and source evidence remain bounded to that repository. Scratch/output siblings never become source changes.
- Incremental migration reuses a parsed file only when path, language, Git blob and old parse status match exactly. It re-keys all commit-sensitive machine IDs, reuses an Agent review only when the source entity and narrative field shape match, preserves generator-unowned notes, and then executes the full current-version audit contract.
- Automation persistence uses an atomic spool plus `machine/automation.sqlite`; event IDs, turn ownership, changed-path filtering, redaction, FTS exposure, and pending-review creation are deterministic. Replayed or concurrent events must not duplicate turns, paths, or review records.
- Raw or near-raw conversation evidence remains machine-only. A Stop event creates `pending-agent-review`, not a reviewed Markdown page. Human promotion requires a Chinese body, Chinese evidence note, an exact per-path source-check set, resolved knowledge links, and the existing note audit.
- Automatic synchronization never parses `transcript_path`, never captures unregistered repositories, and never changes permissions or blocks a Harness operation. Hook health is reported separately from the fixed source graph completion markers.
- Every completed Markdown knowledge base carries auto-discovered project instructions for Codex, OpenCode, Claude Code, Gemini CLI, GitHub Copilot and Cursor. The protocol fixes the read order to `retrieve fast` → bounded pack → narrow graph/source commands, routes durable writes through `record`, and audits note mirrors, metadata and both SQLite representations. Workspace-root installation is explicit and idempotent; it does not broaden Hook activation or synchronize every conversation into existing pages.
- `machine/knowledge.sqlite` contains every file, declaration, source range, complete relation/evidence set, provider/diagnostic/review fact, community, boundary, human ownership mapping, full fixed source text, Chinese sections, Agent notes, and working-overlay paths. Its FTS and graph commands return source-grounded, token-bounded packs.
- A fixed detached source snapshot, not the live worktree, is the semantic-provider root. Live edits are recorded as a working overlay and never alter the baseline `.complete` commit.
- Accessors, local helpers, thin wrappers, simple predicates, properties, enums, fields, and similar declarations remain complete machine facts but appear only in an embedded appendix. Each appendix row has only the symbol and one Agent-reviewed Chinese sentence.
- Human relations are aggregated and bounded by the pinned page configuration; defaults are 20 direct, 10 aggregate, 8 test, and 8 boundary groups. They are written as natural Chinese navigation sentences, while `graph.json` retains every machine relation and every hidden count.
- Every build emits Chinese `human/INDEX.md`, `human/WIKI.md`, `human/readability-audit.json`, and a byte-compatible `markdown/` vault. The `human-readable-pages` gate requires zero frontmatter pages, zero technical prefixes, zero visible 40-character commit identifiers, zero machine markers/raw relation labels, zero dangling human links, and zero non-Chinese narrative fields.
- Context accounting and review-pack splitting use the pinned page configuration. Defaults remain `ceil(UTF-8 bytes / 3)`, an 80,000-token complete module, a 20,000-token task subgraph, and 20,000 Agent-reserved tokens within 100,000 total.
- `overview`, source location, appendix ownership, and local-scan boundary details remain mandatory audit content. Optional sections, their order and headings, overview field selection, and collapsed/expanded appendix presentation are configurable.
- Keep the fixed snapshot unchanged for the complete baseline build. Source evidence is the commit, blob object, path, and exact range; the user's live worktree may change after snapshot creation.
- A local scan is complete only for its selected paths, expanded entry graph, and recorded one-hop boundary pages.
- C/C++ without a compilation database is labeled `bounded-approximate`; completion still requires successful clangd symbols, zero fatal parse diagnostics, full key-entity coverage, and zero dangling internal targets.
- C# uses Tree-sitter plus csharp-ls/.NET 10. A no-project scan uses an isolated, no-restore fallback project and is labeled `bounded-approximate`. Multiple solutions/projects stop with candidates; generated files and `bin`/`obj` are excluded unless explicitly included or entered.
- Only `finalize` writes `.complete`, `.machine.complete`, and `.human.complete`; all three are checked together. A pending review writes `.pending-agent-review`; any failed gate writes `.failed`.
- Markdown completion additionally requires exact, source-locked `logseq/config.edn` files at both `OUTPUT` and `OUTPUT/markdown`; a missing, altered, falsely sourced, or wrongly located config fails the format gate.
- Report completion only after reopening `.complete`, `audit/global.json`, `graph.json`, the requested knowledge-base artifact, and every chunk review record.

## Scope restraint

Scan only Git-tracked project-owned source by default. Every excluded path remains visible in `scope.json`, and `--include` is the explicit override. The scanner changes the target directory only for an explicitly selected `--init-git` bootstrap; all later scanner steps write only the output, fixed snapshot, and workspace metadata. User/Agent edits in the live worktree are allowed after snapshot readiness and remain separate from the baseline graph until a later committed build.
