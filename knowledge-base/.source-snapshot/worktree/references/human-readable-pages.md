# Human-readable page contract

## Separation of concerns

Machine artifacts (`facts/`, `machine/knowledge.sqlite`, `graph.json`, projection JSON, audit records, review packs) retain stable IDs, commits, blobs, ranges, providers, confidence, classification, ownership, complete relations and full fixed source. Human artifacts (`human/INDEX.md`, `human/WIKI.md`, `human/pages/*.md`, the compatibility `markdown/` vault, Logseq page blocks, and `GRAPH_REPORT.md`) explain the code and do not repeat those machine properties.

Agent analysis/change/pitfall/experiment/session notes are human artifacts. They
link generated pages and source entries but contain no frontmatter or hash-like
identifier. Their machine evidence lives under `workspace-meta`.

`INDEX.md` separates four task intents before presenting details: understand or
modify code, find prior work records, locate an exact source unit, and learn the
reading rules. `RECORDS.md` is the human entry for all durable Agent notes. It
groups the complete note set by purpose and extracts one Chinese description
from each record with a fixed script. It never receives a benchmark query or a
manually selected page list.

## 简体中文叙述

每项含义、职责、修改时机、来源说明、附录句子、关系叙述、Wiki、分析、修改原因、踩坑、实验和会话总结必须使用简体中文。英文仅用于专有名词、源码符号、路径、命令和必要术语。页面标题可以原样使用英文类名或函数名，但正文不得是纯英文说明。Agent 在逐实体审阅时负责依据源码写出中文叙述；脚本在审阅提交、全局图、人类层和机器层四处确定性复核。

## Allowed human pages

- **Code-unit page:** one class-like type, function, method, constructor, or destructor.
- **Code-unit aggregation:** the related types/functions implemented by one file, one directory responsibility group, the project entry, or one local-scan boundary.

Properties, fields, enums, accessors, local helpers, thin wrappers, and simple predicates remain appendix entries even when an entry selector names them. The nearest class/function or file aggregation becomes the landing page.

## Titles and filenames

- Use the shortest source-recognizable class/function name.
- A method may use `Class.method`.
- An implementation aggregation uses titles such as `OrderCoordinator 相关实现` or `Order 与 OrderLine 的协作实现`.
- A directory aggregation uses `<directory> 职责导览`.
- Add a natural parenthetical qualifier only for a real collision, such as `（接口）`, `（实现）`, or a source stem.
- Never prefix titles with entity, file, module, repository, or boundary labels.
- Never put IDs or hashes in titles or filenames.

## Type tags and source links

Each generated page has exactly one tag selected by deterministic page type:

- code-unit/file aggregation: `#类型/代码`
- repository/module responsibility aggregation: `#类型/职责`
- local scan boundary: `#类型/边界`

Do not add language, visibility, lifecycle, module, or relation tags. Agent note
tags are fixed by note kind. Render tags as one inline `标签：#类型/...` line,
not YAML frontmatter.

Every source-bearing page renders one clickable local editor link followed by
the repository-relative path and line range. The URI is derived from
`local-openers.json`; it does not alter page identity or classification.

## Page prose

A code-unit or implementation aggregation contains only useful reading content. The pinned page configuration controls optional section presence, order, headings, overview field selection, and collapsed/expanded appendix presentation:

1. one reviewed description and responsibility;
2. when a developer would modify it;
3. the source path and line range;
4. natural-language links to collaborating code, callers, and tests;
5. the audited internal-details appendix, collapsed by default.

The overview, source location, appendix ownership, aggregate overview, and local boundary details cannot be removed because they carry the human completeness and source-location contract. `change_when`, partial-fragment details, outgoing collaboration, backlinks, tests, and the hidden-relation hint are optional configured sections.

Omit empty sections. Translate relations into short Chinese sentences such as “实现时会用到”, “会调用”, “由测试覆盖”, and “继续浏览”. Do not show relation IDs, raw relation types, confidence, degree, cohesion, or aggregate machine counts.

Appendix tables have exactly two human columns: code symbol and one-sentence responsibility. IDs, kinds, source ranges, and relation counts remain in the machine layer.

## Wiki and Graphify report

Every Markdown projection contains a Chinese `WIKI.md` explaining reading order, page shapes, modification workflow, work-record lookup, Graphify task narrowing, and Logseq opening. `GRAPH_REPORT.md` presents classes/functions grouped by responsibility; commits, confidence tiers, node counts, degrees, classifications, community IDs, and cohesion remain only in JSON.

The work-record index has one `#类型/导览` tag, no frontmatter, no machine IDs,
and one entry per note title. Each entry contains a double link and one useful
Chinese sentence. Empty note categories remain visible as explicit empty
states, so a missing section cannot be mistaken for an omitted record.

## Completion gate

`readability-audit.json` must report `passed`. The deterministic gate checks zero frontmatter pages, zero prefixed titles, zero visible commit/hash identifiers, zero machine markers, zero raw relation labels, zero page-property lines, zero non-Chinese narrative fields, exactly one allowed type tag, a clickable source link where required, class/function-only standalone pages, complete Wiki sections, valid double links, a task-first `INDEX.md`, and exact work-record coverage in `RECORDS.md`. A readability failure prevents `.complete`、`.human.complete` and `.machine.complete`.
