# Human-readable page contract V3

## Version and migration boundary

The built-in human-page registry uses `schema_version=3` and
`contract_version=3.0.0`. An input declaring the former `1.0.0` contract is
rejected with `contract-version-incompatible`; the caller must explicitly
rewrite the page against the V3 section list. Generators must not silently map
old headings to new headings because that would make a page appear reviewed
under constraints it never received.

The built-in registry still contains exactly fourteen page types: `INDEX`,
`WIKI`, `RECORDS`, `REFERENCES`, `responsibility`, `change`, `analysis`,
`pitfall`, `experiment`, `session`, `reference`, `learning-note`, `feedback`,
and `README`. V3 changes the contract and authoring representation; it does not
add another page family, database, dependency, or projection state machine.

## Progressive disclosure levels

Human and machine artifacts retain distinct responsibilities:

- **L1 — task entry.** `README`, `INDEX`, `WIKI`, `RECORDS`, and `REFERENCES`
  tell a reader which task can be completed, what direct result they will get,
  and the minimum Prompt needed to direct an Agent.
- **L2 — current explanation.** `responsibility`, `change`, `analysis`,
  `pitfall`, `session`, `learning-note`, and `feedback` summarize current
  function, conclusions, affected scope, test-coverage meaning, decisions, and
  applicability boundaries.
- **L3 — experiment and source summary.** `experiment` and `reference` may name
  comparison objects, tested function/performance dimensions, a few registered
  human metrics, sources, and the boundary of the conclusion.
- **L4 — machine evidence.** Complete commands, complete test counts, gate
  checklists, raw stdout/stderr, complete hashes, exit statuses, SQLite state,
  manifest content, maintain subchecks, and rollback probes remain in machine
  records or external verification artifacts. They are referenced through
  `machine_evidence_refs` and are not rendered into ordinary human Markdown.

A human experiment summary may say that native-text PDF, scanned pages, page
location, and code-block retention were tested while code layout remains
limited. It may also include a few decision-relevant metrics. It must not paste
the complete reproduction or audit record merely to prove that summary.

## Complete section contract

Every required or optional section serializes the same fields:

- `required_content`: questions or facts the section must answer;
- `allowed_content`: narrative, entities, metrics, and links that may appear;
- `forbidden_content`: content that does not belong in the section;
- `length_budget`: character, paragraph, list-item, and human-metric limits;
- `key_entity_budget`: the section-scoped limit for directly named entities;
- `link_budget`: the count and permitted target types for visible links;
- `source_requirements`: required source or record classes;
- `freshness_rule`: how current, supported, and tested claims bind evidence;
- `disclosure_level`: `L1`, `L2`, or `L3`;
- `empty_behavior`: `error`, `omit`, or `explicit-empty`.

Required sections use `empty_behavior=error`. Optional sections normally use
`empty_behavior=omit`; an empty optional heading is not retained as decoration.
The registry, deterministic serialization and hash, proposal schema, authoring
skeleton, renderer, and validator use these names without aliases.

## Confirmed navigation titles

Navigation pages may use task-oriented headings:

- `INDEX`: `先选择你要完成的任务`, `按职责浏览代码`, `查找项目记录`, optional
  `查找外部资料`, and `让 Agent 精确定位`;
- `WIKI`: `从哪里开始`, `各类页面负责什么`, `如何追踪方案与实现变化`,
  `如何让 Agent 帮助阅读`, and `深入了解`;
- `RECORDS`: `先选择你要查找的内容`, `分析与方案`, `实现与修改`, `实验与性能`,
  `问题与限制`, `会话与方案变化`, and `让 Agent 帮助查找`;
- `REFERENCES`: `这些资料能回答什么`, `按主题选择资料`, and
  `让 Agent 帮助查找`;
- `README`: `先选择你要完成的任务`, `了解本项目知识库结构`,
  `让 Agent 安装本项目`, `让 Agent 解释自己的项目`,
  `安装后继续指挥 Agent`, and optional `实验功能`.

`README` is a human task entry, not a human command-line tutorial. Installation
and project explanation remain separate Prompts. Its first screen contains
exactly three task rows: understand the knowledge-base structure, ask an Agent
to install the project, or ask an Agent to explain the reader's project. Each
later task card separates `你会直接得到` from `复制给 Agent`. The continuation
section appears after those three first-screen tasks and tells the reader how
to ask the Agent to read, locate, modify, or verify one problem after
installation.

## Confirmed formal-page titles

Formal content pages use stable written headings:

- `responsibility`: `职责说明`, `适用场景`, `功能结果`, `关联范围`, `当前边界`,
  `深入阅读`;
- `change`: `修改内容`, `修改时间`, `修改原因`, `实现概述`, `关联特性`,
  `当前结果`, `适用边界`, `深入阅读`;
- `analysis`: `当前结论`, `问题关联`, `事实基础`, `结论应用`, `未决事项`,
  `后续建议`, `深入阅读`;
- `pitfall`: `问题现象`, `触发条件`, `影响范围`, `原因说明`, `处理方式`,
  `当前结果`, `适用边界`, `深入阅读`;
- `experiment`: `实验问题`, `比较对象`, `功能与性能覆盖`, `结果摘要`, `结论`,
  `适用边界`, `后续工作`, `深入阅读`;
- `session`: `任务目标`, `执行范围`, `关键决策与方案变化`, `当前结果`,
  `可用成果`, `未决事项`, `后续行动`, `深入阅读`;
- `reference`: `资料概述`, `适用问题`, `关键结论`, `来源`, `适用边界`,
  `深入阅读`;
- `learning-note`: `学习问题`, `解释摘要`, `应用方式`, `关联内容`, optional
  `后续问题`;
- `feedback`: `反馈内容`, `影响范围`, status-dependent `处理结论`, `当前状态`,
  and `后续行动`.

## Authoring representation

`page-author init` returns both a typed skeleton and `section_constraints`. Each
section input separates:

- `human_summary`, the only field rendered into the Markdown section;
- `key_entities`, `metrics`, and visible `links`, used for section budgets;
- `source_refs`, used to bind descriptive claims;
- `machine_evidence_refs`, used to retain L4 evidence outside the rendered body.

Every visible Markdown link must have an exact entry in the owning section's
`links` array with `target`, `kind`, and non-empty `purpose`. A visible but
undeclared link, a declared but unused target, and repeated targets with
conflicting kind or purpose are deterministic failures. The seven formal page
types that contain `深入阅读` require at least one such link. When no deeper
document exists, that link points to the existing internal Agent-question entry
and states the question the Agent should continue locating; it does not create
a second navigation state machine.

`new` renders a complete candidate. `supplement` adds only missing sections to a
hash-pinned source. `revise` replaces one uniquely located paragraph with a new
`human_summary` and requires structured `source_refs`. None of these modes
writes generator-managed human or Markdown projections directly.

The validator parses headings and section ranges before applying constraints.
L4 detection is therefore scoped by page type, section, disclosure level, and
structured evidence input rather than by a global technology-word blacklist.
Normal technical prose may mention SQLite, manifests, tests, or rollback as
concepts; literal command shapes, complete counts, raw result fields, full
hashes, database verdicts, manifest bodies, maintain subresults, and rollback
probe output are rejected from L1–L3 summaries. Complete test-total forms such
as `Ran N tests`, `N tests`, `通过 N 项测试`, and `测试总数：N` are L4. A coverage
sentence such as `已测试原生文本 PDF、扫描页、页码定位和代码块保留` remains a valid
L3 summary when its current-fact source and observation time are registered.

## Source traceability

Progressive disclosure does not remove provenance. Human pages may keep a few
descriptive links to source ranges, experiments, references, and work records.
Each visible link states why the reader would open it. Complete provenance,
fixed-source text, relation sets, operation logs, and validation artifacts stay
available in `facts/`, `machine/knowledge.sqlite`, `workspace-meta`, or external
verification artifacts for Agent retrieval.

## Proposal and projection boundary

Output-local template proposals use the same V3 section constraint fields. An
Agent or human submission creates only a `pending` proposal. Activation still
requires an explicit human audit pinned to the proposal version and content
hash; proposal submission does not bypass review.

V3 authoring packages contain a validated `body.md` and machine-only routing
`manifest.json` in a new staging directory. `body.md` contains no source or
machine-evidence target merely because it was declared. The manifest retains a
registry-ordered `section_evidence.sections` list containing each section ID,
heading, disclosure level, normalized `source_refs`, and normalized
`machine_evidence_refs`, plus `section_evidence_sha256`. File-shaped targets
must remain within `workspace_root`, exist, and match their declared SHA-256.
The packager copies each such file to
`evidence/<sha256>/<source-basename>` inside the package, rewrites `target` to
that manifest-parent-relative path, and retains `original_target`, SHA-256,
and `package_owned=true`. Opaque URI targets keep their original target bytes
and receive `target_basis=uri`. `package_owned_paths` lists the body, manifest,
and copied evidence so rollback removes only the package directory and never
the source evidence. The package reopens every copy and the manifest, checks
all hashes, and remains resolvable after the whole directory moves to another
location on the same filesystem before returning `next_entry`.

Existing generators remain the sole owners of `human/pages`, `markdown/pages`,
navigation outputs, mirror parity, and both SQLite indexes. A later integration
may migrate existing pages only through an explicit, separately reviewed
migration.

## Completion checks

A V3 implementation is complete only when:

1. all fourteen built-in types expose the complete section fields;
2. repeated serialization produces identical bytes and registry hashes;
3. confirmed headings match exactly and old `1.0.0` input has explicit failure;
4. authoring skeletons expose section constraints and render only
   `human_summary`;
5. positive experiment summaries retain coverage, comparison, a few metrics,
   and conclusion boundaries;
6. negative L4 fixtures fail deterministically;
7. descriptive source, experiment, reference, and work-record links remain
   registered, purposeful, and valid, with one deep link on each formal page
   that contains `深入阅读`;
8. proposals remain pending until human audit;
9. package manifests retain normalized section evidence and reject target
   drift;
10. affected tests and complete repository regression pass against the actual
   behavior.
