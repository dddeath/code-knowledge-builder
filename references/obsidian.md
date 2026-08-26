# Obsidian vault projection

Every build uses `OUTPUT/human` as the primary Obsidian vault and mirrors it to
`OUTPUT/markdown` for compatibility. The generated layout is:

```text
human/
  .obsidian/
  INDEX.md
  WIKI.md
  pages/
  analysis/
  changes/
  pitfalls/
  experiments/
  sessions/
```

The generator owns only files listed in `.ckb-generated-files.json`.  A rebuild
replaces generated pages and configuration while preserving every note folder,
unknown user file, and Obsidian workspace layout.

The minimal configuration enables official core navigation features such as
search, graph, backlinks, outgoing links, tags, page preview, and outline.  It
does not install a community plugin and does not generate `workspace.json`.
检索主路径仍是 `machine/knowledge.sqlite`；Obsidian 搜索只服务人类浏览，不承担完整实体召回。

Generated code pages use exactly one tag:

- code page: `#类型/代码`
- responsibility aggregation: `#类型/职责`
- scan boundary: `#类型/边界`

Agent-created notes use the five tags documented in `workspace-mode.md`.

Every source-bearing page renders one editor URI and the readable repository
path/range.  Local settings live in `OUTPUT/local-openers.json`; change machine
or editor with:

```powershell
& PYTHON scripts\ckb.py relink --out OUTPUT --repo-root REPO --editor vscode
```

Supported modes are `vscode`, `vscode-insiders`, `file`, and an explicitly
provided custom template.  `relink` regenerates projections and re-runs final
audits.  Agent-created notes return an `obsidian://open?path=...` URI so the
calling Agent can link the conversation response directly to the saved note.

所有页面与笔记正文使用简体中文；英文只保留在源码符号、专有名词、路径和必要术语中。Obsidian 文件名可使用源码类名或函数名，中文要求作用于叙述正文而不是强制翻译代码标识符。
