# Output schema

## Layout

```text
OUTPUT/
|-- state.json
|-- page-config.json              normalized immutable page/content/budget configuration
|-- graphify-out/
|   |-- graph.json                    Graphify node-link projection with complete CKB parity
|   |-- communities.json              signed deterministic community membership
|   |-- GRAPH_REPORT.md               bounded Chinese graph report
|   |-- projection.json               counts, hashes, versions, and source commits
|   `-- queries/                      persisted bounded query results
|-- logseq/
|   `-- config.edn                    primary Logseq 2.0.1 file-import root config
|-- scope.json
|-- catalog.json
|-- navigation-plan.json
|-- parse-batches/                 machine segmentation metadata
|-- chunks/batch-NNNN/            compatibility path for batch artifacts
|   |-- candidate.json
|   |-- semantic-LANGUAGE.json
|   |-- agent-review.json
|   `-- audit.json
|-- review-packs/
|   `-- KIND-pack-NNNN/
|       |-- review-template.json
|       |-- agent-review.json
|       `-- audit.json
|-- graph.json                     complete machine facts and relations
|-- facts/                         rebuildable authoritative facts
|   |-- graph.json
|   |-- source-manifest.json
|   |-- review-manifest.json
|   `-- audit.json
|-- boundary.json
|-- .source-snapshot/
|   `-- worktree/                  detached baseline provider root
|-- local-openers.json             machine-local source editor mapping
|-- machine/
|   |-- knowledge.sqlite           complete Agent database and FTS5/graph index
|   |-- automation.sqlite          opt-in Skill activations, Harness sessions, turns, events, paths, pending reviews and FTS
|   `-- agent-packs/               budgeted deterministic Agent reading packs
|-- agent-index.sqlite             legacy-compatible page retrieval index
|-- workspace-meta/
|   |-- working-overlay.json
|   |-- working.patch
|   |-- notes/                     machine note records
|   |-- pending-notes/             sessions/changes queued during construction
|   |-- sessions/                  deterministic Agent task lifecycle records
|   `-- automation/
|       |-- spool/pending/ processed/ failed/
|       `-- pending-reviews/       machine drafts plus Agent-review sidecars
|-- context/                       requested context bundles
|-- audit/global.json
|-- human/                         conservative Chinese Markdown/Obsidian vault
|   |-- .obsidian/
|   |-- INDEX.md
|   |-- WIKI.md
|   |-- pages/
|   |-- analysis/ changes/ pitfalls/ experiments/ sessions/
|   |-- readability-audit.json
|   `-- projection.json
|-- markdown/                      compatibility mirror, emitted for every format
|   |-- .obsidian/                minimal generated vault configuration
|   |-- .ckb-generated-files.json generator ownership list
|   |-- INDEX.md
|   |-- WIKI.md                    Chinese reading and modification guide
|   |-- pages/
|   |-- analysis/                 preserved Agent analysis pages
|   |-- changes/                  preserved code-change pages
|   |-- pitfalls/                 preserved failure/lesson pages
|   |-- experiments/              preserved experiment pages
|   |-- sessions/                 preserved task conversation summaries
|   |-- logseq/
|   |   `-- config.edn            secondary Markdown-root file-graph configuration
|   |-- normalized.edn
|   |-- context-budget.json
|   |-- readability-audit.json     deterministic human-page gate
|   `-- projection.json
|-- logseq-db/                     when requested
|   |-- db.sqlite
|   |-- normalized.edn
|   |-- context-budget.json
|   `-- projection.json
|-- .pending-agent-review
|-- .failed
|-- .machine.complete
|-- .human.complete
`-- .complete
```

`.pending-agent-review` and `.failed` are mutually exclusive with the completion set. A valid completion contains `.complete`, `.machine.complete`, and `.human.complete` together. Rebuilding or auditing withdraws all three. `page-config.json` is canonical JSON copied during initialization. Its hash is repeated in state, scope, `graph.json`, projection JSON, the global audit, and `.complete`; drift exits `6`.

`source_snapshot` is recorded in state, scope, and catalog with its detached
worktree root, baseline commit/tree, and readiness state. New workspace-note,
source-link, and Agent-index schemas add no hash field. Human pages and notes
also omit hash-like identifiers; established machine provenance fields remain
in the canonical graph and completion records.

The root `graph.json` is the CKB audit graph and remains the source of truth.
`graphify-out/graph.json` uses Graphify node-link shape: `nodes`, `links`,
`hyperedges`, graph metadata, and `built_at_commit`. Node IDs and link IDs are
identical to the CKB graph. Graphify nodes add community labels but retain CKB
commit, blob, exact range, classification, owner page, review status, and Chinese
description. Graphify links rename CKB `type` to `relation` and add deterministic
confidence fields while retaining provider and evidence.

## Machine entity and navigation decision

Every named declaration in `graph.json` keeps stable `id`, `kind`, `name`, `qualified_name`, `language`, Git commit/blob/path, exact byte and line ranges, parent, parse-batch ID, classification evidence, deterministic final classification, and owner page. C# partial types add a logical entity plus all fragment blobs and ranges.

The only machine classifications are:

- `page`: file aggregation or independently navigable class/function;
- `appendix`: complete machine fact projected as an embedded appendix row;
- `boundary`: one-hop target outside a local scan, grouped by path in human output.

Page review fields are `meaning_zh`, `role_zh`, `change_when_zh`, and `evidence_note`. Appendix review fields are `description_zh` and `evidence_note`. All submitted records retain source path/lines and `status: agent-reviewed`. Agent review does not alter deterministic classification or owner. The visible projection maps an entity page to `human_page_kind: code-unit` and repository/directory/file/boundary pages to `code-unit-aggregate`.

## Relations and projections

Machine links keep stable ID, type, source, target, provider, evidence, and cross-batch state. Human links aggregate entity relations by source page, target page, and type, storing `count` plus original link IDs in projection JSON, then apply the configured visible budgets. Markdown and Logseq page prose translates those links into natural Chinese and does not expose type, count, or link ID. Backlinks are generated from the retained visible set.

An appendix row displays only the symbol and `description_zh`; kind, source, machine ID, and counts remain only in machine/audit artifacts. Markdown and Logseq both derive from one logical projection. Canonical EDN count contracts use human block prefixes (`页面说明`, `源码入口`, `内部实现`, `边界协作`, `协作`) instead of CKB IDs. Every page also has one `标签：#类型/...` block.

## 事实层、机器知识库与工作笔记

`facts/graph.json` 必须与根 `graph.json` 字节一致。`facts/source-manifest.json` 保存每个实体的 commit、blob、路径和精确范围；`review-manifest.json` 保存所有审阅包状态。该层只用于重建与审计，不直接作为人类页面。

`machine/knowledge.sqlite` 使用普通表保存 `files`、`entities`、`source_ranges`、`relations`、`relation_evidence`、`providers`、`diagnostics`、`reviews`、`modules`、`communities`、`community_members`、`boundaries`、`human_projection`、`documents`、`sections`、`section_sources`、`document_links`、`terms` 和 `workspace_changes`。`entity_fts`、`section_fts`、`source_fts` 为 FTS5 trigram 派生索引。固定源码每个文件只保存一次；实体章节只保存有界源码片段。

所有叙述字段必须含简体中文内容；源码专有名词和代码标识符可保持英文。机器层审计会将英文说明字段列为错误。

`agent-index.sqlite` contains ordinary `pages`, `symbols`, `edges`, `terms`,
`notes`, and `note_links` tables plus FTS5 trigram tables. It is rebuilt from
the audited projection and remains only for old interface compatibility. It does not contain a hash column.

`workspace-meta/working-overlay.json` stores baseline commit, current HEAD,
changed/untracked paths, patch path, capture time, and clean/dirty status. The
patch omits Git `index` lines. A human note sidecar stores note kind, title,
file, linked page titles, source links, optional query/pack record, review
status, Obsidian URI, and update time.

`workspace-meta/sessions` 保存会话启动/结束状态、问题、确定性检索记录、初始与最终覆盖层以及关联笔记。构建期间产生的中文笔记先进入 `pending-notes`，最终投影后按查询结果或变化路径确定性链接到人类知识页。

`machine/automation.sqlite` 使用独立 schema 保存 `skill_activations`、`sessions`、`turns`、`events`、`tool_events`、`changed_paths`、`pending_reviews` 和 `automation_fts`。事件先通过项目注册和 session Skill 激活双门，再经递归脱敏、仓库内路径过滤和写前 spool，以稳定事件/会话/轮次键写入。`skill_activations` 的唯一键由 Harness、session、仓库根和精确 skill name 组成；激活前事件保持零 spool/事件写入。`pending_reviews.status` 只能从 `pending-agent-review` 经 `automation review` 进入 `agent-reviewed`；Hook 本身没有该状态转换权限。

自动化注册表 schema 3 的每个项目包含唯一 `repo_root`、`knowledge_output`、可重复 `workspace_roots`、Harness 集合、脱敏配置、`required_skill: code-knowledge-builder` 和 `require_skill_activation: true`。事件先按直接仓库根匹配，再按 workspace 根匹配；匹配结果只决定项目路由，Git status 与 changed-path 相对化始终以 `repo_root` 为边界。schema 1/2 在读取时补齐工作区和 Skill 激活字段，并在下一次登记时写成 schema 3。

自动化审阅 sidecar 保存 `review_id`、kind、机器草稿、changed paths、Harness/会话证据和状态。Agent 提交记录增加中文 `evidence_note`、与 changed paths 完全相等的 `source_checks`、审阅正文和正式人类 note 路径。人类页继续遵守无 frontmatter、无 hash-like 标识和单标签规则。

增量迁移增加 `migration/plan.json`、`migration/audit.json` 和 `migration/reused-reviews/*.json`。plan 记录旧/新版本、固定 commit、精确复用文件、旧到新机器 ID 映射、复用/增量审阅计数及可变文件保全记录；这些字段只存在于机器层。最终 `graph.json`、facts、SQLite 和人类投影仍使用当前普通 schema。

The Markdown `projection.json` records both roots. `logseq_import_root` describes `OUTPUT`, which is the primary directory selected by Logseq 2.0.1 “File to DB graph”. `logseq_file_graph` describes `OUTPUT/markdown`. Each record contains the graph root, absolute and relative config paths, SHA-256, upstream Logseq commit, and source URL. Both `logseq/config.edn` files must be byte-identical to the pinned template before the Markdown format gate can pass.

## Repository and C# provenance

追加中心使用 `scope-extension/state.json`、`scope-extension/plan.json` 和 `scope-extension/audit.json`，schema version 为 `1`。state 固定 operation ID、旧 OUTPUT、staging、repo、commit 与规范化请求；plan 固定五个 scope 维度的 retained/added/removed、精确 blob/review 复用、关系影响集合、旧层清单和不可变保留基线；audit 保存固定分类的门结果、双 SQLite 完整性/外键与 maintain 状态。切换控制记录位于 OUTPUT 同级，额外保存旧/新逐文件 SHA-256 树清单、备份绝对路径、`parent_operation_id`、`chain_depth`、可恢复失败尝试和 rollback 后重新激活的父操作。当前 active 操作由 OUTPUT 全树与 `modified_manifest` 唯一匹配，不由文件名排序决定；缺少 parent 字段的旧记录通过唯一相邻 manifest 推导。以上机器记录不保存 Prompt、secret、完整命令或 stdout/stderr。

`repository.git_bootstrap` records the optional one-time Git initialization. `scope.csharp_workspace` records automatic/explicit project selection, exact or bounded precision, the no-restore fallback project, or an explicitly allowed isolated restore. Restore and fallback records include worktree commit, generated project or artifact hashes, environment, command output, and rollback path.

## Completion record

`.complete` records schema, commit, selected scope, format, precision, parse batches, pinned page configuration path/hash, global audit, graph, and emitted projections. `.machine.complete` names the facts/machine audit records; `.human.complete` names the human/readability records. They exist only after every parse batch, review pack, Simplified-Chinese description gate, source gate, configuration pin, navigation quota, relation budget, context contract, and requested format gate passes.
