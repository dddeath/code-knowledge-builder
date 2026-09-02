# CKB Canvas Skill 原型技术设计

设计基线：`62b15376e8de899a2eaeda1d10bcc62bd1b3d2a8`
冻结知识快照：`150a1ce8ea3fca0f7ce2f56c731d42a9973ee0e3`
目标格式：JSON Canvas 1.0
设计状态：可交给隔离原型任务；不表示产品能力已经实现

## 1. 结论与边界

第一原型采用一个独立的 CKB Canvas Skill，由 Skill 调用确定性 Python 脚本。脚本只消费冻结 Agent pack、同名完整 record、固定人类页、固定源码文件和当前 CKB 已验证的 `local-openers.json`；它在调用方授权的隔离 staging 根内生成 `.canvas`、validation manifest 和 rollback manifest。原型不注册 `scripts/ckb.py` 新命令，不修改现有 Obsidian companion，不启动 MCP，不写活动稳定知识库，也不进入 lite、full 或 Obsidian 插件发行合同。

设计冻结以下内容，原型任务不得重新选择：

- record 兼容版本与 pack/record 绑定方式；
- 请求、成功、失败、validation 和 rollback 的 schema；
- 最多 12 个节点、16 条边及其选择、ID、排序和布局；
- staging、重开验证、原子 promotion、replace、并发漂移和 rollback 状态机；
- 内部实验命令与 Skill 的职责边界；
- fixture 目录、稳定失败原因、测试矩阵和 Markdown 对照 runner 合同。

以下内容仍保留为产品阶段的人工决策，不在本设计中写成事实：

- benchmark 通过后 Canvas 进入 `OUTPUT/human`、用户自有目录还是只读导出目录；
- 是否给 companion 增加“打开/刷新 Canvas”；
- 产品形态是否允许直接 editor URI，还是统一经人类知识页二跳到源码；
- 是否把内部实验命令提升为正式 `scripts/ckb.py` 子命令。

研究依据见：

- [能力与数据边界](../../research/obsidian-canvas-agent-visualization/capability-data-boundary-matrix.md)
- [最小合同与 Markdown 对照](../../research/obsidian-canvas-agent-visualization/design-input-and-benchmark.md)
- [研究交接](../../research/obsidian-canvas-agent-visualization/handoff.json)

## 2. 当前仓库事实与设计影响

### 2.1 已确认入口

| 当前入口 | 已确认行为 | 对原型的约束 |
|---|---|---|
| `scripts/ckb.py:384-390,910-945` | `brief` 调用 `retrieve_machine` 或兼容 `retrieve`，再用 `compact_agent_brief` 只返回 pack/record 路径和紧凑状态 | Canvas 不解析 `brief` 的紧凑 JSON 作为 record；它只消费 `brief` 指向的完整 `.json` |
| `scripts/ckb_core/llm_wiki_capabilities.py:358-405` | compact result 的 `schema_version=1`，明确省略词项、实体、得分和统计 | compact schema 1 与完整 machine record schema 3 是两个合同，不混用 |
| `scripts/ckb_core/machine_knowledge.py:1523-1555` | machine record 当前 `schema_version=3`，包含 `selected_entities`、`related_documents`、pack/record 路径、确定性标记和来源状态 | 第一原型只接受完整 machine record 3；兼容 `agent_index` record 1 明确失败 |
| `scripts/ckb_core/agent_index.py:426-554` | 兼容 record 1 的字段是 `selected_pages` 与 `related_notes`，形状不同 | 不为原型维护第二个选择适配器，返回 `unsupported_record_schema` |
| `scripts/ckb_core/source_links.py:17-81,105-180` | `SourceLinkRenderer` 校验相对路径、根边界、editor 类型并生成、审计 URI | 来源节点必须复用该 renderer 与 `audit_source_uri`，不得自行拼 URI |
| `scripts/ckb_core/common.py:62-74` | `json_write` 使用同目录临时文件和 `os.replace` | 原型采用同一写入模式，但增加输入重查、三角色 staging、重开验证和 baseline guard |
| `scripts/ckb_core/agent_protocol_batch.py:866-881` | `_state_file` 记录存在性/hash/mode，`_write_bytes_atomic` 写临时字节后 `os.replace` | replace 与 rollback 复用“存在性 + SHA-256 + 原子替换”思想，不复用批处理私有函数 |
| `scripts/package_release.py:15-31,42-97` | lite/full 打包包含除固定排除项外的仓库文件，核心 ZIP 明确排除 `plugins/` | 原型分支不运行或修改发布打包；实验 Skill 的最终归属需 benchmark 后单独决定 |
| `OUTPUT/state.json` 与 `machine/knowledge.sqlite.meta` | 当前快照 commit 都是 `150a1ce8...`；完整 record 本身没有 snapshot commit | 请求必须另外 pin `state.json`、machine SQLite 和 human projection，不能声称 record 自带 commit |

### 2.2 pack 与 record 的真实边界

Agent pack 是面向 Agent 阅读的 UTF-8 Markdown，没有独立 schema，也不携带 snapshot commit。完整 record 是机器 JSON，当前 machine schema 为 3。原型把 pack 当作不可变、不解析的证据字节，把 record 当作唯一选择序列；两者必须满足：

1. 两个文件位于同一规范化目录，文件 stem 相同；
2. record 的 `pack`、`record` 规范化后分别等于请求路径；
3. 两个请求 hash 与实际字节一致；
4. record 为 `status=passed`、`deterministic=true`、`grep_fallback_required=false`；
5. record 不含 `keyword_fallback` 或 `keyword_fallback_record`；第一 benchmark 只测默认确定性路径；
6. pack 和 record 都位于 `output_root/machine/agent-packs`，解析符号链接后仍在该目录；
7. record 未知顶层字段或未知候选字段触发 `unsupported_record_schema`，不猜测兼容。

### 2.3 snapshot 的真实 guard

原型读取请求固定的 `state.json`、`machine/knowledge.sqlite`、`human/projection.json` 和 `local-openers.json`，并执行以下一致性检查：

- 四个文件的 SHA-256 与请求一致；
- `state.repository.commit == state.source_snapshot.commit == request.snapshot_commit`；
- `state.repository.tree == state.source_snapshot.tree == request.snapshot_tree`；
- SQLite `meta.status=ready`、`meta.schema_version=3`、`meta.repository_commit == request.snapshot_commit`；
- `human_root == output_root/human`，`human/projection.json` 的路径和 hash 与请求一致；
- `local-openers.json` 为 schema 1，且第一原型只接受 `source_view=baseline`；
- `baseline_snapshot_root` 解析后等于 `state.source_snapshot.root`；
- 人类页与源码文件均在请求的 `frozen_evidence` 中，当前 hash 必须一致。

这样 snapshot 一致性来自当前仓库真实状态和 SQLite 元数据，而不是不存在的 record 字段。

## 3. 建议新增模块与公开函数

原型代码根固定为 `prototypes/ckb-canvas-skill/`。这里只定义原型内部公共面；这些函数不加入 CKB 正式公共 API。

```text
prototypes/ckb-canvas-skill/
├── SKILL.md
├── scripts/ckb_canvas.py
└── ckb_canvas/
    ├── contracts.py
    ├── freeze.py
    ├── graph.py
    ├── transaction.py
    ├── commands.py
    └── benchmark.py
```

### 3.1 `contracts.py`

只拥有 JSON Schema 加载、严格校验和稳定结果类型，不访问文件系统。

| 公开实体 | 合同 |
|---|---|
| `load_schema(name) -> dict` | 从固定 schema 目录读取已知 schema 名；未知名失败 |
| `validate_instance(schema_name, value) -> None` | Draft 2020-12 校验，拒绝未知字段 |
| `CanvasFailure` | 稳定 `reason`、`phase`、`exit_code`、目标前后状态和恢复动作 |
| `CanvasSuccess` | 三个角色的路径/hash、计数和目标前后状态 |

### 3.2 `freeze.py`

只拥有输入规范化、hash、版本、路径和来源闭合；不选择节点，不写输出。

| 公开实体 | 合同 |
|---|---|
| `load_and_freeze_request(path) -> FrozenInputs` | 严格解析 request，规范化所有路径，读取并 hash 输入，完成 snapshot 与 pack/record 交叉校验 |
| `recheck_frozen_inputs(frozen) -> None` | promotion 前重算全部输入和证据 hash；任一漂移返回 `input_drift` |
| `resolve_scoped_path(root, candidate, must_exist) -> Path` | 解析 Windows symlink/junction 和现存父目录，保证最终路径仍在根内 |
| `validate_source_range(path, start, end) -> SourceRange` | 要求普通实体 `1 <= start <= end <= line_count`；当前 file 实体允许唯一的 `end=line_count+1` 末尾哨兵，并返回固定源文件 hash |

`FrozenInputs` 只保留规范化值、已验证字节/hash 和 record 序列；后续模块不得再次从 SQLite 扩展候选。

### 3.3 `graph.py`

纯函数模块，拥有候选选择、稳定 ID、布局、JSON Canvas 1.0 子集渲染和内存验证；不访问网络和 Obsidian workspace。

| 公开实体 | 合同 |
|---|---|
| `select_graph(frozen) -> SelectedGraph` | 按第 5 节算法选择最多 12 个节点和 16 条边 |
| `layout_graph(selected) -> CanvasDocument` | 使用冻结坐标和尺寸，不读取窗口或模型输出 |
| `canonical_canvas_bytes(document) -> bytes` | UTF-8、无 BOM、LF、key 字典序、紧凑分隔符、末尾一个 LF |
| `validate_canvas(document, frozen) -> ValidationFacts` | 检查 schema、预算、ID、悬空边、回链、来源范围和机器字段泄露 |

### 3.4 `transaction.py`

只拥有目标 baseline、staging、原子 promotion、replace 和 rollback，不决定图内容。

| 公开实体 | 合同 |
|---|---|
| `capture_baseline(frozen) -> ArtifactBaseline` | 对 canvas、validation、rollback 三个最终路径记录存在性/hash；与 request baseline 精确相等 |
| `stage_bundle(frozen, bytes_by_role) -> StagedBundle` | 每个角色写同父目录唯一临时文件，flush、fsync、关闭、重开并 hash |
| `promote_bundle(staged, baseline) -> PromotedBundle` | 先重查输入和 baseline，再 promotion 两个 sidecar，最后原子替换 canvas；失败清理本次 sidecar |
| `verify_promoted(promoted) -> None` | 重开三角色并核对 schema 与 hash；发生外部漂移时保留外部当前字节 |
| `rollback_from_manifest(path) -> RollbackResult` | hash guard 后恢复三个角色的原始存在性和字节，恢复后重开验证 |

### 3.5 `commands.py`

只编排上述模块并把一个 schema 化 JSON 写到 stdout。诊断写 stderr，stdout 不混入日志。

| 公开实体 | 合同 |
|---|---|
| `generate(request_path) -> CanvasSuccess | CanvasFailure` | 完整执行 freeze → graph → stage → promote → verify |
| `rollback(manifest_path, expected_sha256) -> RollbackSuccess | CanvasFailure` | 先核对 manifest 完整 hash，再执行 guard、恢复和重开验证 |
| `validate_only(request_path) -> ValidationResult | CanvasFailure` | 只到内存验证和 staging 重开，不 promotion |

### 3.6 `benchmark.py`

只读取冻结 runner 输入和 session 观察结果；不改变 Canvas 或 Markdown 证据集。

| 公开实体 | 合同 |
|---|---|
| `run_session(run_path, session_id) -> SessionResult` | 核对环境、展示固定任务顺序、记录计时与跳转事件 |
| `judge_session(run, observations) -> SessionResult` | 按固定答案字段和来源证据计分 |
| `summarize(run, sessions) -> BenchmarkSummary` | 计算两条件指标、七个门和停止原因 |

## 4. CLI 与 Skill 边界

### 4.1 内部实验命令

原型固定使用：

```powershell
python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py generate --request REQUEST.json
python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py validate --request REQUEST.json
python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py rollback --manifest TARGET.canvas.rollback.json --expected-sha256 MANIFEST_SHA256
python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py benchmark --run BENCHMARK-RUN.json --session SESSION_ID
python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py summarize --run BENCHMARK-RUN.json --sessions SESSION-DIR --write SUMMARY.json
```

退出状态固定为：

- `0`：命令完成且输出 schema 通过；
- `2`：请求、版本、路径、输入、目标或回链前置条件不满足；
- `5`：生成对象、Canvas、manifest 或 benchmark 判定未通过验证；
- `6`：promotion 或 rollback 发现并发漂移；
- `7`：文件系统 I/O 失败，目标仍为原字节或外部当前完整字节。

### 4.2 Skill 只编排

`SKILL.md` 的职责仅为：

1. 要求一个已通过 schema 的 request 或 benchmark run；
2. 调用内部命令；
3. 重开命令返回的三个角色；
4. 报告路径、字面状态和退出状态；
5. 需要回滚时调用 manifest，而不是手工编辑 Canvas。

Skill 不选择候选、不生成关系、不改预算、不拼 editor URI、不解释 hash 漂移、不直接写 `.canvas`。这些都由脚本确定性完成。

### 4.3 暂不扩展主 CLI 的理由

当前 `scripts/ckb.py` 已是正式建库、检索、记录、维护和迁移入口。Canvas 的导航收益、custom URI 行为和目标所有权尚未通过冻结对照；此时增加正式子命令会把实验 schema、路径归属和维护承诺提前变成产品合同。独立命令可以复用真实数据格式，同时把失败、撤回和目录删除限制在原型分支。benchmark 通过后，再由单独产品设计决定是否接入主 CLI、companion 或 MCP。

## 5. 稳定选择、ID、排序和布局

### 5.1 规范化

- 所有可见文本执行 Unicode NFC；禁止控制字符，标题长度为 1–120 个 Unicode code point。
- Canvas `file` 值是相对 `human_root` 的 POSIX 路径；不得出现绝对路径、`.`、`..` 或反斜杠。
- Windows 机器路径只进入 validation/rollback manifest；drive letter 规范化为大写，比较不区分大小写，序列化保留解析后的规范路径。
- 第一原型 `local-openers.source_view` 固定为 `baseline`；来源范围从 detached snapshot 打开。

### 5.2 候选选择伪代码

```text
assert record.schema_version == 3
assert request.budget == frozen_budget

required = validate_required_record_ordinals(request.required_entries)
page_candidates = stable_unique(
    record.selected_entities where human_page_file exists,
    key = canonical human_page_file,
    order = record array ordinal
)
record_candidates = stable_unique(
    record.related_documents where status == "agent-reviewed" and human_file exists,
    key = canonical human_file,
    order = record array ordinal
)

selected_pages = required pages in record order
fill selected_pages from page_candidates until 6

selected_records = required records in record order
fill selected_records from record_candidates until 2

source_candidates = first source range bound to each selected page,
                    de-duplicated by (source_path, start_line, end_line),
                    ordered by selected page order then entity ordinal
selected_sources = required sources in source order
fill selected_sources from source_candidates until 3

if any required entry is absent, unbacklinked, invalid or over quota:
    fail without dropping it

nodes = [focus] + selected_pages + selected_records + selected_sources
edges = focus->pages + focus->records + owning_page->sources
assert len(nodes) <= 12 and len(edges) <= 16
```

候选不足时不填造节点。没有人类页且没有精确来源的普通候选被忽略；请求 `required_entries` 显式指定的候选缺回链时返回 `missing_backlink`。

### 5.3 稳定 ID

```text
node_id = sha256(utf8("node\0" + role + "\0" + canonical_target))[0:16]
edge_id = sha256(utf8("edge\0" + from_id + "\0" + label + "\0" + to_id))[0:16]
```

`canonical_target` 固定为：

- focus：`index:INDEX.md\0title:<NFC title>`；
- page：`file:<relative human page>`；
- reviewed record：`record:<relative human record>`；
- source：`source:<audited SourceLinkRenderer URI>`。

16 位 ID 冲突时返回 `duplicate_id`，不加随机 salt。ID 是 Canvas 结构标识，不复制 `entity_id`、`document_id` 或 gap ID。

### 5.4 冻结布局与字段

| role | `x` | `y` | `width × height` | Canvas 类型 |
|---|---:|---:|---:|---|
| focus | 0 | 0 | `360 × 180` | `text` |
| page | 480 | `page_index × 260` | `360 × 220` | `file` |
| record | 480 | `(page_count + record_index) × 260` | `360 × 220` | `file` |
| source | 960 | `source_index × 260` | `360 × 160` | `link` |

节点数组顺序固定为 focus、page、record、source；同类保持上述选择顺序。边数组顺序固定为 `检索命中`、`相关记录`、`来源核对`，每类按起点数组序和终点数组序。所有边固定 `fromSide=right`、`toSide=left`、`fromEnd=none`、`toEnd=arrow`。

focus 文本只含标题和 `[[INDEX]]`。page/record 只写 `file`；source 只写 renderer 产生并通过 `audit_source_uri` 的 `url`。第一原型不写 group、颜色、机器关系或任意扩展键。

### 5.5 确定性字节

Canvas 与两个 manifest 都使用：

```text
UTF-8 without BOM
Unicode NFC
JSON object keys sorted lexicographically
separators = (",", ":")
ensure_ascii = false
exactly one trailing LF
no timestamps, PID, temporary path or random value
```

相同 request 字节、同一冻结证据字节和相同目标 baseline 必须产生相同 Canvas 字节。manifest 的确定性检查使用规范化内容 hash；运行时临时文件名与实时时长不进入 manifest。

## 6. 回链、来源范围与数据泄露门

### 6.1 人类页

每个 file 节点必须同时满足：

1. 路径存在于 request `frozen_evidence.human_files`；
2. hash 与 request 一致；
3. 路径存在于 `human/projection.json`、`human/manifest.json.generated_files` 或受审阅记录目录；
4. 解析后仍位于 `human_root`；
5. 若使用 `subpath`，目标标题或 block ID 在文件中恰好出现一次。第一原型 fixture 默认不使用 `subpath`。

### 6.2 来源范围

每个 link 节点必须同时满足：

1. `source_path` 是 record 现有相对路径；
2. 路径存在于 request `frozen_evidence.source_files` 且 hash 一致；
3. 路径解析到 `baseline_snapshot_root` 内；
4. `start_line`、`end_line` 是整数；普通实体在当前 UTF-8 行数内，`kind=file` 只额外允许当前 parser 的 `end_line=line_count+1` 末尾哨兵；
5. URL 由 `SourceLinkRenderer.uri(source_path,start_line,1)` 生成；
6. `audit_source_uri` 返回无错误。

直接 editor URI 只作为第一原型的受测变量。若固定 Obsidian 版本不能打开它，benchmark 写失败证据并停止产品化；本设计不据此决定最终产品必须使用 editor URI。

### 6.3 Canvas 禁止字段

递归扫描 key 和受控文本，以下机器内容出现一次即 `invalid_canvas`：

- `entity_id`、`document_id`、gap ID、SQLite row ID；
- `score`、`score_breakdown`、`terms`、`anchors`、`seed_entity_ids`、`retrieval_stats`；
- pack/record/state/SQLite 的绝对路径与 hash；
- token、缓存、环境变量、凭据或 MCP 字段；
- record 未证明的 `calls`、`depends-on`、`contains` 等机器关系。

绝对 editor URI 是显式允许的 source link，不属于 pack/record 内部路径泄露；validation manifest 记录它来自哪个固定 source range。

## 7. 生成与 promotion 状态机

### 7.1 状态

```text
NEW
 └─validate request/schema/path─> REQUEST_VALID
     └─read/hash/cross-check─> FROZEN
         └─select/layout/validate memory─> RENDERED
             └─capture three-role baseline─> BASELINED
                 └─write/reopen/hash temp bundle─> STAGED
                     └─recheck inputs + baseline─> PROMOTION_READY
                         └─sidecars then canvas os.replace─> PROMOTED
                             └─reopen all roles/hash/schema─> VERIFIED
```

`REQUEST_VALID` 前不得创建 staging。`PROMOTION_READY` 前不得改变三个最终路径。所有状态转移只有一个前驱；失败结果记录最后完成状态和失败 phase。

### 7.2 路径与 staging

- `authorized_staging_root` 必须已存在且是目录；所有目标、sidecar、backup 和临时文件解析后都在该根内。
- `target_canvas_path` 以 `.canvas` 结尾；sidecar 固定为 `.validation.json` 和 `.rollback.json` 后缀。
- 临时文件与对应最终文件在同一父目录，保证 `os.replace` 不跨卷。
- 临时名可以含 PID/随机值，但不写进任何持久 manifest；存在冲突时重新创建临时名，不改变输出字节。
- 每次写临时文件后执行 flush、fsync、close、reopen、parse 与 SHA-256 核对。

### 7.3 replace baseline

request 为三个最终角色分别固定 baseline：

- `replace=false`：canvas、validation、rollback 都必须 `state=absent`；任一已存在返回 `target_exists`；
- `replace=true`：canvas 必须 `state=present` 并给出 SHA-256；两个 sidecar 分别声明 absent 或 present；present 角色必须给出 SHA-256。backup 根必须为空且在授权 staging 根内。

replace 时先把所有 present baseline 字节写入 backup 临时文件，重开核对，再原子变成固定 backup 文件。rollback manifest 记录三个角色各自的原始状态、hash 和 backup hash。baseline backup 在成功 rollback 后才删除。

### 7.4 promotion 次序

1. 重算 request 所有输入、证据和三个 baseline hash；
2. promotion validation manifest；
3. promotion rollback manifest；
4. 最后用 `os.replace` promotion canvas；
5. 重开 canvas、validation、rollback，核对各自 schema 和预期 hash；
6. 写成功 JSON 到 stdout。

Canvas 最后替换，因此前置失败时目标 Canvas 保持 baseline。每个角色由同目录 `os.replace` 完成，目标只可能是完整旧字节或完整新字节，不出现部分文件。

若步骤 2 或 3 后、步骤 4 前失败，脚本按本次 staged hash 删除或恢复已 promotion sidecar，再核对三个角色仍等于 baseline。若步骤 4 后重开时发生外部并发变化，脚本不覆盖外部当前字节，返回 `promotion_drift`；该字节是外部完整写入，不被错误描述为本次部分写入。

### 7.5 并发漂移

在 `BASELINED`、`PROMOTION_READY` 和每次 `os.replace` 前都重新解析父目录和现存路径，并检查预期状态/hash：

- 输入或证据变化：`input_drift`，不 promotion；
- 目标/sidecar 从 absent 变 present、从 present 变 absent或 hash 变化：`promotion_drift`；
- 符号链接或 junction 解析结果改变：`source_outside_scope`；
- rollback 时任一当前生成角色不等于 manifest 记录的 generated hash：`rollback_drift`。

锁文件不替代 hash guard。原型可用一个 sibling lock 避免同进程族重复工作，但拿到锁后仍执行全部 drift 检查；锁路径和时间不进入确定性 manifest。

## 8. rollback 状态机

```text
ROLLBACK_NEW
 └─load/validate manifest─> ROLLBACK_VALID
     └─reopen current roles and backups─> ROLLBACK_GUARDED
         └─restore present baselines / remove absent baselines─> ROLLED_BACK
             └─reopen and compare exact baseline state/hash─> ROLLBACK_VERIFIED
```

执行规则：

1. 先按命令参数 `expected_sha256` 核对 rollback manifest 完整字节，再读取整个 manifest 到内存；恢复 rollback sidecar 本身时不再依赖磁盘当前内容。
2. 当前 Canvas 必须等于 `generated_sha256`；validation 与 rollback sidecar 也必须等于 manifest/成功结果固定的生成 hash。
3. 原状态为 present 的角色，其 backup 必须存在且 hash 正确；用 backup 同目录临时副本原子替换。
4. 原状态为 absent 的角色，只在当前 hash 等于本次 generated hash 时删除。
5. rollback manifest 自身最后恢复或删除。
6. 重开三个最终路径，要求存在性与 baseline 完全一致；present 字节必须 byte-identical。
7. 全部恢复验证通过后才删除本次 backup 根。

任何 guard 不一致返回 `rollback_drift` 并保留当前字节与 backup。I/O 失败返回 `io_failure`，恢复动作可对照 manifest 重试；脚本不得用 baseline 覆盖 hash 未知的当前文件。

## 9. 稳定失败语义

| `reason` | phase | exit | 触发条件 | 目标最终状态 | 恢复动作 |
|---|---|---:|---|---|---|
| `invalid_request` | request | 2 | request 不符合 schema、未知字段或条件分支 | 未检查或未改变 | 修正 request |
| `unsupported_record_schema` | freeze | 2 | 非 machine record 3、未知 record 字段或禁用变体 | 未改变 | 用当前 `brief` 的完整 machine record 3 重建请求 |
| `pack_record_mismatch` | freeze | 2 | stem、目录或 record 自指路径不一致 | 未改变 | 重新冻结同一次检索的 pack/record |
| `input_drift` | freeze/promotion | 2 | 请求固定的任一输入或 evidence hash 改变 | 未改变 | 重新生成 hash 和 request |
| `snapshot_mismatch` | freeze | 2 | state、snapshot、SQLite commit/tree 不一致 | 未改变 | 使用同一固定 CKB snapshot |
| `source_outside_scope` | request/freeze/promotion | 2 | 输入、目标、backup、symlink 或 junction 解析后越界 | 未改变 | 移到授权根并移除越界重解析 |
| `target_exists` | baseline | 2 | `replace=false` 的任一最终角色已存在 | 三角色保持原状 | 改目标或提供完整 replace baseline |
| `missing_backlink` | select | 2 | required candidate 没有人类页或精确来源 | 未改变 | 移除 required 项或补齐已审阅回链后重新 brief |
| `missing_target` | freeze/validate | 2 | 人类页、INDEX、source 文件、backup 或唯一 subpath 不存在 | 未改变 | 恢复固定文件并更新 hash |
| `invalid_source_range` | freeze/validate | 2 | 行范围非法、越界或 URI 不能反解 | 未改变 | 使用 record 中有效精确范围 |
| `budget_exceeded` | select/validate | 5 | required 节点或边超过任一硬预算 | 未改变 | 缩小 required 项；不得自动扩预算 |
| `duplicate_id` | validate | 5 | 节点或边稳定 ID 冲突 | 未改变 | 调查 canonical target 冲突 |
| `dangling_edge` | validate | 5 | 任一边端点不在节点集合 | 未改变 | 修正确定性选择实现 |
| `invalid_canvas` | validate/reopen | 5 | JSON Canvas schema、字段、回链或泄露门失败 | baseline；已 promotion 时按 guard 补偿 | 修正生成器并重跑 validate |
| `promotion_drift` | promotion/reopen | 6 | baseline 检查后目标被并发改变 | 保留并发当前完整字节 | 人工确认当前目标后重新冻结 baseline |
| `rollback_drift` | rollback | 6 | 当前生成角色或 backup 与 manifest hash 不同 | 保留当前字节和 backup | 人工处理漂移；不得强制覆盖 |
| `io_failure` | staging/promotion/reopen/rollback | 7 | 创建、flush、fsync、replace、reopen 或删除失败 | baseline 或外部当前完整字节；不留部分 Canvas | 保留 staging/backup，排除 I/O 原因后按 manifest 重试 |

失败 JSON 必须给出 `before`、`after`、`changed` 与 recovery；不能只输出异常字符串。`changed=true` 只允许表示外部并发字节不同，不能表示本次留下未验证的 Canvas。

## 10. 原型实现完成门

原型只有同时满足以下条件才可进入冻结 Markdown 对照：

1. 五个核心 schema、JSON Canvas 子集 schema 和 benchmark schema 均由 Draft 2020-12 validator 解析；
2. success fixture 与每个稳定 failure fixture 均通过对应 schema；
3. 同一 success 输入连续生成 10 次，Canvas 原始 SHA-256 相同，两个 manifest 规范化内容 SHA-256 相同；
4. 节点 `<=12`、边 `<=16`、悬空边 0、缺失回链 0、机器字段泄露 0；
5. absent、present 和 drift 三条 rollback probe 全部通过；
6. Windows 中文路径、长路径、symlink/junction、损坏 JSON、悬空边和并发目标变化都有独立测试；
7. `git diff` 只含原型任务允许路径，未接线主 CLI、companion、MCP、发布包或活动知识库；
8. benchmark runner 用同一 pack、record、人类页、来源、任务和预算运行 Markdown 与 Canvas 条件。
