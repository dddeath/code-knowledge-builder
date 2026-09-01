# Page configuration

## Entry and pinning

Generate the complete default JSON with:

```powershell
& PYTHON scripts\ckb.py page-config --write .\page-config.json
```

The input may also be a partial JSON containing only changed keys, but it must include `schema_version: 1`. Validate it before a build:

```powershell
& PYTHON scripts\ckb.py page-config --validate .\page-config.json
```

Pass it only to the initial `run` or `init` with `--page-config`. CKB merges defaults, validates all fields, writes canonical JSON to `OUTPUT/page-config.json`, and stores its SHA-256 in state, scope, graph, projections, global audit, and `.complete`. Resume, rebuild, merge, audit, and finalize read that pinned copy. Editing or deleting it is configuration drift and exits `6`; start a new output directory to use a different configuration.

The complete packaged default is [page-config.default.json](page-config.default.json).

## Page limits

`page_limits` controls independently navigable key-entity pages. File aggregation pages always exist and are not counted in these values.

- `ordinary_file`: maximum key-entity pages for an ordinary source file.
- `core_file`: maximum key-entity pages in a file reached as the directly selected entry core.
- `adjacent_file`: maximum key-entity pages in one file directly adjacent to an entry core.
- `core_per_entry`: maximum core pages selected for one entry cluster.
- `adjacent_per_entry`: maximum adjacent pages selected for one entry cluster.

Defaults are `1`, `4`, `1`, `4`, and `3`. Values may be zero to keep only aggregation pages. Ranking, overlap deduplication, ownership, and tie breaks remain deterministic; Agent review never chooses or changes pages.

## Page content

The three ordered arrays under `content` control which sections are rendered and their order:

- `code_page_sections`: code-unit and per-file aggregation pages;
- `aggregate_page_sections`: repository and directory-responsibility pages;
- `boundary_page_sections`: one-hop local-scan boundary aggregations.

Recognized code sections are `overview`, `change_when`, `source_location`, `partial_fragments`, `related_code`, `backlinks`, `tests`, `hidden_relation_hint`, and `appendix`. Aggregate pages accept `overview`, `related_code`, `backlinks`, `tests`, and `hidden_relation_hint`. Boundary pages accept `overview`, `boundary_details`, `related_code`, `backlinks`, and `hidden_relation_hint`.

The source-audit contract keeps these sections mandatory:

- code: `overview`, `source_location`, `appendix`;
- aggregate: `overview`;
- boundary: `overview`, `boundary_details`.

`overview_fields` selects one or both reviewed fields, in display order: `meaning` and `role`. `appendix_mode` is `collapsed` or `expanded`. `headings` changes the visible Markdown heading for each named section without changing machine queries or audit semantics. Heading values must be one non-empty line of at most 64 characters.

## Relations, context, and review packs

`relation_limits` configures visible groups for `direct`, `aggregate`, `test`, and `boundary`. Hidden groups and all original machine links remain in `graph.json`.

`context` configures deterministic token accounting:

- `module_max_tokens` and `task_max_tokens`;
- `total_max_tokens` and `reserved_agent_tokens`;
- `bytes_per_token` for `ceil(UTF-8 bytes / bytes_per_token)`.

The task limit cannot exceed the module limit. Module plus Agent-reserved tokens cannot exceed total tokens.

`review_packs.page` and `review_packs.appendix` each configure `max_files`, `max_items`, and `max_tokens`. Their token limit cannot exceed the non-Agent context budget. These settings change only deterministic pack partitioning; every selected entity still requires Agent review.

## Minimal override example

```json
{
  "schema_version": 1,
  "page_limits": {
    "ordinary_file": 2,
    "core_file": 5
  },
  "content": {
    "code_page_sections": [
      "overview",
      "source_location",
      "related_code",
      "appendix"
    ],
    "overview_fields": ["role"],
    "appendix_mode": "expanded",
    "headings": {
      "source_location": "源码落点",
      "appendix": "辅助代码"
    }
  },
  "relation_limits": {
    "direct": 12
  }
}
```

Unknown keys, unknown/duplicate sections, invalid types, out-of-range values, missing mandatory sections, and inconsistent budgets exit `2` before the output directory is created.
