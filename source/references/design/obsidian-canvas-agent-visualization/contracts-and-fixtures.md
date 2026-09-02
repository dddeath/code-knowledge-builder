# CKB Canvas 接口、schema 与 fixture 合同

本目录中的 JSON Schema 和 fixture 是第一原型的规范输入。实现可以使用显式字段校验器，不要求新增通用 schema 运行时依赖；但实现行为必须与这些 Draft 2020-12 schema 一致，且测试必须证明未知字段被拒绝。

## 1. Schema 清单

| 文件 | 角色 | 未知字段 |
|---|---|---|
| [`schemas/canvas-request.schema.json`](schemas/canvas-request.schema.json) | `generate`/`validate` 的唯一请求 | 所有 object 层级拒绝 |
| [`schemas/canvas-success.schema.json`](schemas/canvas-success.schema.json) | 成功 stdout | 拒绝 |
| [`schemas/canvas-failure.schema.json`](schemas/canvas-failure.schema.json) | `generate`、`validate`、`rollback`、`benchmark` 失败 stdout | 拒绝 |
| [`schemas/canvas-validation-manifest.schema.json`](schemas/canvas-validation-manifest.schema.json) | 输入、snapshot、回链和 Canvas 验证证据 | 拒绝 |
| [`schemas/canvas-rollback-manifest.schema.json`](schemas/canvas-rollback-manifest.schema.json) | 三角色 baseline、generated guard 和恢复动作 | 拒绝 |
| [`schemas/json-canvas-1.0-ckb-subset.schema.json`](schemas/json-canvas-1.0-ckb-subset.schema.json) | 第一原型可生成的 JSON Canvas 1.0 子集 | 拒绝扩展键；不允许 group |
| [`schemas/benchmark-run.schema.json`](schemas/benchmark-run.schema.json) | 12 项 Markdown/Canvas runner 输入 | 拒绝 |
| [`schemas/benchmark-session-result.schema.json`](schemas/benchmark-session-result.schema.json) | 一个 sequence/condition block 的观察结果 | 拒绝 |
| [`schemas/benchmark-summary.schema.json`](schemas/benchmark-summary.schema.json) | 汇总指标、七门和推进决策 | 拒绝 |

Schema 自身只表达结构约束。路径解析、hash、SQLite meta、record allowlist、源码行范围、ID 冲突、边闭合、机器字段泄露和并发漂移由确定性语义校验器完成。

## 2. `canvas-request` 冻结字段

### 2.1 CKB 输入

`ckb` 对以下角色同时固定绝对路径和 SHA-256：

- `state.json`；
- `machine/knowledge.sqlite`；
- Agent pack Markdown；
- 同名完整 machine record JSON；
- `human/projection.json`；
- `human/manifest.json`；
- `local-openers.json`。

请求另外固定 `snapshot_commit`、`snapshot_tree`、`record_schema_version=3`，以及本次候选可能使用的 `frozen_evidence.human_files` 与 `frozen_evidence.source_files`。evidence 路径都相对各自根，禁止绝对路径、反斜杠和 `..`。

### 2.2 目标与 baseline

`request` 固定：

- 面向人的 `title`；
- 原型变量 `source_link_mode=verified-editor-uri`；
- `authorized_staging_root`；
- `target_canvas_path`；
- 空的或任务所有的 `backup_root`；
- `replace`；
- canvas、validation manifest、rollback manifest 三个角色各自的 baseline；
- 可选 `required_entries`，只通过 record 数组 ordinal 引用候选，不接收自由文本实体或机器 ID。

`replace=false` 时三个 baseline 都必须 absent。`replace=true` 时 Canvas baseline 必须 present，两个 sidecar 分别声明 absent 或 present。present baseline 必须带 SHA-256；实际 backup 路径由 `backup_root + role` 确定性派生并写进 rollback manifest。

### 2.3 硬预算

预算不是可调建议，schema 固定为：

```json
{
  "max_nodes": 12,
  "max_edges": 16,
  "max_page_nodes": 6,
  "max_record_nodes": 2,
  "max_source_nodes": 3,
  "max_text_nodes": 1,
  "max_groups": 0
}
```

原型调用方不能通过 request 提高预算。以后修改预算必须升 schema version 并重新执行 Markdown 对照。

## 3. Machine record 3 兼容合同

### 3.1 接受的顶层字段

必须存在：

```text
schema_version status question profile budget estimated_tokens
terms anchors seed_entity_ids selected_entities related_documents
open_feedback pack record retrieval deterministic source_grounded
grep_fallback_required
```

允许的可选字段只有：

```text
retrieval_stats pending_agent_review
```

出现 `keyword_fallback`、`keyword_fallback_record` 或其他未知字段统一返回 `unsupported_record_schema`。第一原型要求：

```text
schema_version == 3
status == "passed"
deterministic == true
source_grounded == true
grep_fallback_required == false
pending_agent_review absent or false
```

### 3.2 `selected_entities`

允许字段固定为：

```text
entity_id name qualified_name kind source_path start_line end_line
human_page_title human_page_file display_mode score score_breakdown
reasons sections
```

Canvas 选择器只消费数组 ordinal、`kind`、`source_path`、`start_line`、`end_line`、`human_page_file` 和 `human_page_title`。`entity_id`、score、score breakdown、reasons 和 sections 只用于 record 兼容校验，不得进入 Canvas。

### 3.3 `related_documents`

允许字段固定为：

```text
document_id title kind status human_file source_path start_line end_line
severity target content_excerpt
```

Canvas 只接受 `status=agent-reviewed` 且有 `human_file` 的项。`gap`、feedback、pending review、没有人类页的记录都不进入第一原型画布。`document_id` 不进入 Canvas。

### 3.4 文件范围末尾哨兵

当前 parser 对完整 file 实体可能记录 `start_line=1,end_line=line_count+1`。因此语义校验规则为：

- 非 file 实体：`1 <= start_line <= end_line <= line_count`；
- file 实体：允许相同规则，或唯一的 `start_line=1,end_line=line_count+1`；
- 其他 `line_count+1` 形状失败为 `invalid_source_range`。

该例外只兼容当前真实 record，不改变 JSON Canvas 或 editor URI；URI 仍打开 `start_line`。

## 4. 成功角色

成功 fixture 位于 [`fixtures/success/`](fixtures/success/)：

| 文件 | 说明 |
|---|---|
| `canvas-request.json` | 含 Windows 中文路径、固定 commit/tree、hash、evidence、baseline 和 required entries |
| `ckb-navigation.canvas` | 1 个 focus、1 个 page、1 个 reviewed record、1 个 source，3 条允许边 |
| `ckb-navigation.canvas.validation.json` | 所有输入、结构、回链、范围和泄露门通过 |
| `ckb-navigation.canvas.rollback.json` | absent baseline 的三角色删除动作与 guard |
| `canvas-success.json` | stdout 结果，包含三个角色的路径、hash、字节数和计数 |

这些文件是 schema/序列化样例，不是活动知识库产物。绝对路径使用 `C:\fixture\...` typed fixture 根，原型测试在 `%TEMP%` 下实例化并重新计算 hash。

rollback manifest 的 `expected_manifest_content_sha256` 计算规则固定为：把该字段临时设为 64 个 `0`，按规范 JSON 序列化并 SHA-256；完整 manifest 的 SHA-256 另由成功结果返回。`rollback` 命令必须同时接收完整 manifest 的 expected hash。

## 5. 失败结果与 fixtures

[`fixtures/failure-catalog.json`](fixtures/failure-catalog.json) 是稳定原因全集；[`fixtures/failure-results/`](fixtures/failure-results/) 为每个原因提供一个通过 failure schema 的字面结果。

| 分组 | 原因 |
|---|---|
| 请求与版本 | `invalid_request`、`unsupported_record_schema`、`pack_record_mismatch` |
| 冻结输入 | `input_drift`、`snapshot_mismatch`、`source_outside_scope` |
| baseline 与回链 | `target_exists`、`missing_backlink`、`missing_target`、`invalid_source_range` |
| 生成验证 | `budget_exceeded`、`duplicate_id`、`dangling_edge`、`invalid_canvas` |
| 并发与 I/O | `promotion_drift`、`rollback_drift`、`io_failure` |

每个 fixture 都含：触发 detail、固定退出状态、`before`/`after`、`changed`、恢复 action 和需要重新提供的输入。逐原因的触发条件、目标状态和恢复动作以 [`technical-design.md` 第 9 节](technical-design.md#9-稳定失败语义) 为规范。

## 6. Runtime fixture 目录

原型测试固定使用：

```text
%TEMP%\ckb-canvas-fixtures\CASE_ID\
├── output\
│   ├── state.json
│   ├── local-openers.json
│   ├── machine\knowledge.sqlite
│   ├── machine\agent-packs\pack-fixture.{md,json}
│   ├── human\{INDEX.md,manifest.json,projection.json}
│   ├── human\pages\...
│   └── .source-snapshot\worktree\scripts\...
├── staging\
├── outside\
└── request.json
```

测试不得把绝对临时根提交进 fixture。builder 在运行时替换 typed fixture 根、创建最小 SQLite `meta` 表、计算真实 hash，并在测试结束删除目录。

[`fixtures/fixture-catalog.json`](fixtures/fixture-catalog.json) 冻结以下 12 个 setup：

1. absent + Windows 中文路径成功；
2. replace 成功；
3. 250–259 字符 Windows 长路径；
4. 指向授权根内的 symlink；
5. 指向根外的 symlink/junction；
6. 损坏 request JSON；
7. 损坏 record JSON；
8. 悬空边注入；
9. baseline 后并发目标变化；
10. absent rollback；
11. present rollback；
12. rollback drift。

## 7. 原型测试矩阵

| 测试 ID | setup/fixture | 断言 |
|---|---|---|
| `request_unknown_field` | success request 加任意顶层和嵌套字段 | `invalid_request`，exit 2，staging 未创建 |
| `record_v1_rejected` | 兼容 `agent_index` record 1 | `unsupported_record_schema`，exit 2 |
| `record_keyword_variant_rejected` | record 3 加 `keyword_fallback` | `unsupported_record_schema` |
| `pack_record_crosslink` | record.pack 或 stem 不同 | `pack_record_mismatch` |
| `snapshot_commit_tree` | state/snapshot/SQLite 三者逐项漂移 | `snapshot_mismatch` |
| `human_and_source_hashes` | 每个固定 evidence 单独改 1 byte | `input_drift` |
| `chinese_path_success` | catalog 1 | 三角色成功、NFC、UTF-8、可重开 |
| `windows_long_path` | catalog 3 | 明确成功或 `io_failure`；目标不截断、不部分写 |
| `symlink_inside` | catalog 4 | 规范化后在根内，允许执行 |
| `symlink_outside` | catalog 5 | `source_outside_scope`，目标未改变 |
| `corrupt_json` | catalog 6/7 | 稳定失败 JSON；无 Python traceback 混入 stdout |
| `selection_budget` | required pages 7、records 3、sources 4 | 各自 `budget_exceeded`；不静默丢 required 项 |
| `selection_dedup_order` | 重复 page/source 与同分候选 | 首次 ordinal 保留，数组和字节稳定 |
| `stable_id_collision` | collision test hook | `duplicate_id`，不加随机 salt |
| `dangling_edge` | catalog 8 | `dangling_edge`，exit 5 |
| `machine_field_scan` | 节点文本、key、edge label 分别注入机器字段 | `invalid_canvas` |
| `canvas_reopen` | staged Canvas 截断或增加未知键 | `invalid_canvas`，baseline 未改变 |
| `replace_three_roles` | catalog 2 | 三个 baseline/backup hash 全部记录 |
| `promotion_concurrency` | catalog 9 | `promotion_drift`，并发字节保留 |
| `rollback_absent` | catalog 10 | Canvas 与两个 sidecar 全 absent |
| `rollback_present` | catalog 11 | 三角色 byte-identical baseline |
| `rollback_drift` | catalog 12 | exit 6，人工改动与 backup 保留 |
| `io_faults` | write/flush/fsync/replace/reopen/delete fault injection | `io_failure`；Canvas 只为完整旧/新/外部当前字节 |
| `determinism_10x` | success fixture 十个隔离副本 | Canvas 原始 hash 1 种；两个 manifest 规范化 hash 各 1 种 |

测试只允许通过明确 fault hook 改变阶段行为；生产命令不能暴露“跳过校验”“强制覆盖”“扩大预算”参数。

## 8. Schema 变更规则

- schema 1 期间可以收窄实现 bug，但不能增加字段、原因、节点类型、边标签或预算；
- 增加 record 版本、Canvas 字段、关系或 source link mode 必须升请求与相关结果 schema；
- schema 升级必须增加旧 fixture 的兼容/拒绝测试，并重新执行 10 次确定性与 Markdown 对照；
- 第一原型失败时保留 schema 1 作为实验记录，不把未通过合同并入主 CLI。
