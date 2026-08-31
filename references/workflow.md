# Workflow

## Preconditions and supported source

The baseline source boundary starts as a clean Git checkout at a fixed commit. `init` immediately creates a detached source snapshot and all semantic providers use that snapshot. After snapshot readiness, the user's live worktree may change while the baseline continues. Supported suffixes are `.c`, `.h`, `.cc`, `.cpp`, `.cxx`, `.hpp`, `.js`, `.mjs`, `.cjs`, `.py`, and `.cs`.

If no repository or commit exists, `init`/initial `run` exits `2` and points to `--init-git`. Use that option only after the user chooses it. It creates at most one initial commit and never absorbs dirt into an existing repository. Git bootstrap options are rejected on resume.

Run `doctor --json` first. Exit `3` means a dependency is missing or the private full runtime is waiting for deployment.

## Scope and C# project selection

- Repeat `--scope-path PATH` for selected directories/files.
- Repeat `--entry LANGUAGE:PATH#QUALIFIED_NAME` for exact symbols; bare symbols must be globally unique.
- Entry expansion defaults to callers and callees at depth 1. One-hop targets outside the selected scope become grouped boundary pages.
- C# project metadata (`.sln`, `.slnx`, `.csproj`, `global.json`, Directory.Build/Packages files, NuGet.Config, `.props`, `.targets`) is evidence, not ordinary source pages.
- C# defaults exclude `bin/**`, `obj/**`, `*.g.cs`, `*.g.i.cs`, `*.Designer.cs`, and `*.AssemblyInfo.cs`. Exact `--include` and path-qualified `--entry` override those exclusions.
- One `.sln`/`.slnx` is auto-selected before one `.csproj`. Ambiguity exits `2` with candidates; resolve it with `--csharp-solution` or `--csharp-project`.
- No project metadata creates an isolated fixed-commit fallback project and labels C# `bounded-approximate`; it performs no restore. Network-capable restore occurs only with explicit `--allow-dotnet-restore`, in a private worktree/package cache with hashes and rollback.

## C/C++ 语义精度与解析边界

- 固定源码快照包含有效的 `compile_commands.json` 时，clangd 使用该 compilation database，并把 provider precision 记录为 `exact`；仓库中的 SCons 配置不会覆盖这条路径。
- 没有 compilation database 时，CKB 不运行 SCons、不执行项目脚本且不联网，只静态扫描最多 500 个受支持的构建文件。`SConstruct` 与任意层级的 `SConscript` 和既有 CMake、Meson、Make、Visual C++ 文件使用同一套固定标准匹配规则。
- 只有全部匹配得到唯一标准时才使用构建证据；记录包含来源路径、匹配文本、候选集合和最终选择。无证据使用 `c17`/`c++17` 并记录 `fallback-no-evidence`，冲突证据使用相同固定默认值并记录 `fallback-ambiguous-evidence`。这条路径的 provider precision 始终是 `bounded-approximate`。
- pinned Tree-sitter C++ grammar 对有效的 `template class Box<int>;`/`template struct Box<int>;` 会产生一个可识别的缺失 `identifier`。解析器只恢复这个完整 AST 形状并写入 `parse.recoveries`；其他 `ERROR`/`MISSING` 节点继续写入 `parse.diagnostics` 并使语法门失败。显式模板实例化本身不生成类或函数实体，`const T &x(expr);` 的块内歧义形状只保留为所属函数下的声明事实。

## Resumable route

1. Run `run --repo REPO --out OUTPUT --format markdown|logseq-db|both` with optional selectors and optional initial `--page-config CONFIG.json`.
2. The command creates the fixed source snapshot, catalogs Git blobs, computes deterministic navigation, plans parse batches and separate review packs, builds the next batch, and exits `4` at the next review pack.
3. Reopen every exact source excerpt. For page packs, write factual Chinese meaning/role/change trigger. For appendix packs, write one useful Chinese sentence. Preserve classification, owner, path, and lines.
4. Submit `review-pack --out OUTPUT --pack PACK_ID --review REVIEW.json`, then `run --out OUTPUT --resume`.
5. Repeat until `status --json` has no pending batch or review pack, then run `finalize`.

Repair commands remain available:

```text
doctor
init
build-chunk --stage syntax|semantics|classify|project|all
review-pack
review-chunk                 legacy combined-batch compatibility
audit --chunk BATCH_ID
merge
audit --global
finalize
status --json
```

## Navigation and context

The script deterministically limits independent pages and visible relation groups while retaining all entities and relations in `graph.json`. Visible pages are only classes/functions or aggregations of related classes/functions. Their titles, prose, Wiki, appendices, and links follow `human-readable-pages.md`; page quotas, optional section order/headings, appendix mode, relation limits, context limits, and review-pack limits follow the immutable `OUTPUT/page-config.json` described in `page-configuration.md`.

Create a context bundle with:

```powershell
& PYTHON scripts\ckb.py context --out OUTPUT --module MODULE [--entry ENTITY]
```

With defaults, canonical module context at or below 80,000 estimated tokens emits a full-module bundle. Otherwise `--entry` is required and deterministic graph expansion is capped at 20,000. A pinned page configuration may change both limits and the byte divisor; the emitted context record always states the exact formula and limits.

For ordinary Agent analysis, use the complete machine SQLite index instead of
loading the complete module/context or JSON graph:

```powershell
& PYTHON scripts\ckb.py retrieve --out OUTPUT "问题" --budget 1800 --profile fast
```

Open the returned Agent pack. A `needs-source-read` result is the explicit signal for the narrowest source-range read. See `agent-retrieval.md`. Version 5 retrieval uses no vector model; `fast` and `precise` are both deterministic.

## Live work and knowledge notes

After `init`, use `workspace session-start` to establish one task record while the baseline continues from the detached snapshot. It works before finalization by queueing a Chinese session page. Use `record` for source-linked analysis, change, pitfall, or experiment pages. Finish with `workspace session-finish`; a dirty working tree requires Chinese `修改内容`、`修改原因` and `验证结果` headings. Reprojection materializes pending notes exactly once, preserves every note directory, and refreshes `machine/knowledge.sqlite` plus the compatibility index; see `workspace-mode.md`.

For automatic updates across Codex, Claude Code, OpenCode, DSH, Gemini CLI, GitHub Copilot, Cursor, or another Harness, first register the repository/output pair and render the matching integration bundle. When the Harness runs from a parent task directory, register that directory with `--workspace-root`; route matching may use it, but Git and changed-path evidence stay bounded to `--repo`. Harness events enter `machine/automation.sqlite` through a recoverable spool and remain `pending-agent-review` until an Agent submits Chinese source checks. This automation supplements the manual workspace commands; it does not change the fixed snapshot or create reviewed human pages from raw conversation events. See `automation.md`.

When an older output already passed every gate and the new commit changes only part of the selected source, use `migrate start` rather than discarding reviewed facts. Exact Git blobs reuse parse facts and compatible Chinese reviews after deterministic ID re-keying; delta entities receive independent review packs. The staging output still runs every ordinary current-version gate before cutover. See `migration.md`.

## Output formats

After all review packs pass, `merge` produces the source-authoritative CKB graph. Global audit writes the rebuildable `facts/` layer, runs pinned Graphify `build -> cluster -> report/export`, emits the conservative Chinese `human/` Markdown vault and compatibility `markdown/` mirror, optionally projects Logseq DB, then builds `machine/knowledge.sqlite`. `graphify-out/graph.json` remains a complete machine navigation projection, `communities.json` is the deterministic subsystem partition, and `GRAPH_REPORT.md` is its bounded Chinese human overview.

The human vault contains prefix-free linked pages, one deterministic type tag per page, clickable source entries, preserved `.obsidian` settings, Agent note directories, Chinese `INDEX.md`/`WIKI.md`, `readability-audit.json`, and pinned file-graph configs. Every requested format emits this human vault; Logseq mode additionally imports canonical EDN, validates the graph, exports SQLite, and queries counts. In Logseq 2.0.1, choose **File to DB graph** and select `OUTPUT`; the importer sees `logseq/config.edn`. `OUTPUT/human` and `OUTPUT/markdown` are valid Obsidian/file-graph roots, while `pages` is only their generated page directory. `both` requires byte-identical EDN and logical parity. A failed snapshot, facts, machine, Chinese-description, Obsidian, note, Graphify, readability, review, source, budget, or format check prevents all completion markers.

After two or more completed outputs pass readability, create a portable Chinese showcase:

```powershell
& PYTHON scripts\ckb.py showcase --dist DIST `
  --sample "cpp=CPP_OUTPUT" --sample "python=PYTHON_OUTPUT"
```

The showcase contains only human pages, Logseq file-graph config, Chinese Wiki, responsibility report, readability audit, and a hash manifest. Machine graphs remain in the full build output.
