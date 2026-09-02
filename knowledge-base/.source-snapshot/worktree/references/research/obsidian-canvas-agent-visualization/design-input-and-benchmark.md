# CKB 最小 Canvas 合同与纯 Markdown 对照方案

核对日期：2026-09-02

## 设计结论

下一阶段应创建一个独立 CKB Canvas 设计任务，目标是：从冻结 Agent pack、完整 record、人类知识页和精确来源范围生成一个受预算约束的 JSON Canvas 1.0 文件。第一原型采用独立 Skill 编排和确定性脚本，不依赖通用 Obsidian MCP，不修改当前 companion，不写活动稳定知识库。

该结论是设计推荐，不是已实现能力。进入产品实现仍以冻结 benchmark 通过为前提。

## 原型输入合同

输入文件建议命名为 `canvas-request.json`。未知字段拒绝，所有路径在执行前规范化并核对范围。

```json
{
  "schema_version": 1,
  "mode": "agent-pack-navigation",
  "ckb": {
    "output_root": "ABSOLUTE_OUTPUT_ROOT",
    "snapshot_commit": "40_HEX_COMMIT",
    "agent_pack_path": "ABSOLUTE_PACK_MD",
    "agent_pack_sha256": "64_HEX_SHA256",
    "record_path": "ABSOLUTE_PACK_JSON",
    "record_sha256": "64_HEX_SHA256",
    "human_root": "ABSOLUTE_OUTPUT_HUMAN",
    "local_openers_path": "ABSOLUTE_LOCAL_OPENERS_JSON"
  },
  "request": {
    "title": "面向人的画布标题",
    "target_canvas_path": "ABSOLUTE_STAGING_CANVAS",
    "replace": false
  },
  "budget": {
    "max_nodes": 12,
    "max_edges": 16,
    "max_page_nodes": 6,
    "max_record_nodes": 2,
    "max_source_nodes": 3,
    "max_text_nodes": 1,
    "max_groups": 0
  }
}
```

### 输入约束

1. `snapshot_commit` 必须等于 record 固定的代码快照；pack 与 record 必须互相指向同一次检索。
2. pack/record hash 必须与当前字节一致；任一漂移都在写入前失败。
3. `human_root` 必须是同一 `output_root` 的 `human` 投影；目标 `.canvas` 第一阶段必须位于独立 staging，不得直接写活动 vault。
4. `target_canvas_path` 必须以 `.canvas` 结尾，父目录必须在任务授权范围内；符号链接解析后仍须位于该范围。
5. `replace=false` 时目标已存在即失败；`replace=true` 只有在提供目标 baseline hash 与备份路径后才允许继续。
6. 第一原型不接收任意 SQL、任意 glob、自由文本实体列表或模型生成的关系；选择输入只有 pack/record 和其中已绑定的人类页/来源。

## 确定性选择与布局

### 节点选择顺序

1. 创建 1 个焦点 `text` 节点，只显示任务标题，并包含到 `INDEX.md` 的 Obsidian 文件链接。
2. 按 record 的确定性顺序，选择最多 6 个不同 `human_page_file`，生成 `file` 节点；同一人类页只出现一次。
3. 从 `related_documents` 中选择最多 2 个 `status=agent-reviewed` 且有 `human_file` 的记录，生成 `file` 节点。
4. 对最多 3 个需要直接核对源码的页面生成 `link` 节点。URL 必须由 CKB 已验证的 opener renderer 根据 `source_path:start_line-end_line` 生成，不由模型拼接。
5. 候选没有人类页且没有精确来源范围时不进入画布；若请求显式要求该候选，返回 `missing_backlink`，不降级为无链接文本卡片。

### 节点和边预算

| 类型 | 上限 | 用途 |
|---|---:|---|
| 焦点文本节点 | 1 | 任务标题与 `INDEX.md` 回链 |
| 知识页文件节点 | 6 | 预算化 Agent pack 的主要人类入口 |
| 已审阅记录文件节点 | 2 | 分析、变更、实验或 session 入口 |
| 精确来源链接节点 | 3 | editor URI 与源码范围 |
| group 节点 | 0 | 第一原型不使用不可回链的视觉容器 |
| 节点总数 | 12 | 硬上限，不以“尽量填满”为目标 |
| 边总数 | 16 | 硬上限；正常生成目标不超过 13 |

### 允许的边

- 焦点 → 知识页：`检索命中`；
- 焦点 → 已审阅记录：`相关记录`；
- 知识页 → 精确来源：`来源核对`。

第一原型不输出 `calls`、`depends-on`、`contains` 等机器图关系，因为当前 pack/record 没有提供足以面向人类解释这些关系的闭合证据。任何新关系必须在以后合同版本中定义来源字段和验证门。

### 稳定 ID 与位置

- 节点 ID：`sha256("node\0" + role + "\0" + canonical_target)[:16]`；
- 边 ID：`sha256("edge\0" + from_id + "\0" + label + "\0" + to_id)[:16]`；
- 焦点列 `x=0`，知识页/记录列 `x=480`，来源列 `x=960`；
- 同列按 record 顺序使用 `y=0,260,520,...`；
- 焦点节点 `360×180`，页面/记录节点 `360×220`，来源节点 `360×160`；
- 数组顺序固定为焦点、页面、记录、来源；同类按 record 顺序，保证相同输入字节得到相同输出字节。

位置是第一原型的冻结参数，不根据模型输出、窗口大小或 Obsidian 当前 workspace 自动变化。

## 回链和数据门

每个节点必须满足一种回链：

1. `file` 节点的 `file` 是相对 `human_root` 的现存 Markdown 文件；如使用 `subpath`，对应标题或块在目标文件中唯一存在；
2. `link` 节点的 `url` 来自已验证 opener renderer，且可反解为 record 中同一 `source_path` 与精确行范围；
3. 唯一 `text` 节点正文含到现存 `INDEX.md` 的链接。

以下字段不得写入 `.canvas`：机器 ID、内部 gap ID、得分、检索词项、SQL/FTS 统计、pack 绝对路径、hash、token、环境变量或凭据。它们只进入机器 validation manifest，且 manifest 也不得进入人类 Canvas 页面预览。

## 输出合同

成功时生成三个角色，均位于任务授权目录：

1. `TARGET.canvas`：只含 JSON Canvas 1.0 标准字段；
2. `TARGET.canvas.validation.json`：输入 hash、输出 hash、计数、每个节点的回链检查、每条边的端点检查和 `status=passed`；
3. `TARGET.canvas.rollback.json`：目标写前状态、baseline hash/备份、生成 hash、恢复动作和 hash guard。

建议结果形状：

```json
{
  "schema_version": 1,
  "status": "passed",
  "canvas_path": "ABSOLUTE_TARGET.canvas",
  "canvas_sha256": "64_HEX_SHA256",
  "node_count": 10,
  "edge_count": 11,
  "page_nodes": 6,
  "record_nodes": 1,
  "source_nodes": 2,
  "backlinks_checked": 10,
  "dangling_edges": 0,
  "machine_fields_exposed": 0,
  "rollback_manifest": "ABSOLUTE_TARGET.canvas.rollback.json"
}
```

写入顺序固定为：读取并 hash 输入 → 生成内存对象 → schema/预算/回链检查 → 写入同目录临时文件 → 重开并再次解析 → 生成 validation/rollback manifest → 原子替换目标。临时文件、验证文件和目标文件都要重开；仅“命令成功”不算完成。

## 失败结果

所有失败都返回 `status=failed`、一个稳定 `reason`、未改变目标的证明和下一步输入要求。

| `reason` | 条件 | 目标状态 |
|---|---|---|
| `input_drift` | pack/record hash 不匹配 | 未写入 |
| `snapshot_mismatch` | record 快照与请求不一致 | 未写入 |
| `unsupported_record_schema` | record schema 不受支持 | 未写入 |
| `source_outside_scope` | 输入或目标解析后越界 | 未写入 |
| `target_exists` | `replace=false` 且目标存在 | 未写入 |
| `missing_backlink` | 显式目标没有人类页或精确来源 | 未写入 |
| `missing_target` | `file`/`subpath`/来源范围不存在 | 未写入 |
| `budget_exceeded` | 任一硬预算超限 | 未写入 |
| `duplicate_id` | 节点或边 ID 冲突 | 未写入 |
| `dangling_edge` | 边端点不存在 | 未写入 |
| `invalid_canvas` | JSON Canvas 1.0 校验失败 | 未写入 |
| `promotion_drift` | 替换前目标不再等于 baseline hash | 保留用户当前文件，不覆盖 |
| `rollback_drift` | 回滚时目标不等于生成 hash | 保留当前文件，不覆盖 |

不允许静默丢弃已显式要求的节点、自动扩大预算、改写为无回链文本卡片或在错误后保留部分目标写入。

## 回滚合同

### 目标原来不存在

rollback manifest 记录 `baseline_state=absent`。回滚仅在当前目标 hash 等于 `generated_sha256` 时删除目标和本次生成的 validation manifest；当前字节漂移时返回 `rollback_drift`。

### 目标原来存在

生成前把原始字节复制到任务所有的 baseline 文件，并记录 `baseline_sha256`。回滚仅在当前目标 hash 等于 `generated_sha256` 且 baseline 仍等于 `baseline_sha256` 时用 baseline 原子替换目标。恢复后重开目标并核对 hash。

### 隔离探针

原型验收前必须在临时目录执行两条探针：

1. `absent → generated → rollback → absent`；
2. `baseline bytes → generated → rollback → byte-identical baseline`。

另加 drift 探针：生成后人工改一个字节，rollback 必须返回 `rollback_drift` 并保留人工字节。

## 与纯 Markdown 的冻结对照

### 比较对象

- **Markdown baseline**：同一冻结 snapshot、同一 Agent pack/record、同一 `human` 页面和同一 Obsidian 版本；入口只提供 `INDEX.md`、`RECORDS.md`、`WIKI.md` 与 pack 给出的页面链接。
- **Canvas condition**：完全相同的证据集合，额外提供由上述合同生成的单个 `.canvas` 入口；不增加页面、来源、模型摘要或机器实体。

因此比较只测空间导航入口，不把检索质量、页面内容或模型能力差异混入结果。

### 冻结环境

| 字段 | 冻结值 |
|---|---|
| CKB snapshot | `150a1ce8ea3fca0f7ce2f56c731d42a9973ee0e3` |
| Agent pack | `pack-20260901-175741-198169-01.md` 与同名 `.json` |
| Obsidian | 固定一个安装版本、同一主题、默认 core Canvas；第三方插件全部关闭 |
| 窗口 | 1440×900；缩放 100%；Canvas 初始执行 Zoom to fit |
| 数据 | 同一 `OUTPUT/human` 隔离副本；不连接活动稳定知识库 |
| 网络 | 关闭；所有文件和 editor opener 在本机 |
| 计时 | 从显示任务文本开始，到参与者提交目标页/来源/解释为止 |

Obsidian 具体安装版本由原型任务在执行日写入 benchmark fixture；版本变化后不得与旧结果合并。

### 十二个冻结任务

任务分成六对。A/B 是难度相近的变体，不让同一参与者在第二种界面重复已经记住的目标。

| 配对 | A 任务 | B 任务 | 预期证据 |
|---|---|---|---|
| P1 实现定位 | 找到 `obsidian.py` 的人类知识页，并报告源码范围 | 找到 `obsidian_plugin.py` 的人类知识页，并报告源码范围 | page + `source_path:start-end` |
| P2 函数定位 | 找到 `compact_agent_brief` 的作用页与 `358-405` 范围 | 找到 `agent_index.py` 的作用页与完整文件范围 | page + source range |
| P3 已审阅记录 | 找到“人类可读性样例确认与第一开发波次派发”，说明 Canvas 当前所处阶段 | 找到“Code Knowledge Builder 项目说明书结构与验收样例”，说明第 13 章目标 | reviewed record + exact section |
| P4 边界理解 | 说明为什么 Obsidian 搜索不是完整实体召回，并给出人类/机器入口 | 说明 Agent pack 与完整 record 分别保留什么，并给出两个路径 | two facts + paths |
| P5 来源核对 | 从知识页跳到 `scripts/ckb_core/obsidian.py` 的精确来源 | 从知识页跳到 `scripts/ckb_core/llm_wiki_capabilities.py:358-405` | successful source open |
| P6 支持状态 | 判断 CKB 当前是否已支持 Canvas，并给出证据边界 | 判断当前 companion 是否生成 Canvas，并给出已确认职责 | correct “research only” boundary |

执行顺序：

- 序列 1：Markdown 完成 A1/A3/A5 与 B2/B4/B6；Canvas 完成 B1/B3/B5 与 A2/A4/A6；
- 序列 2：交换两个界面；
- 每个序列至少执行 2 次独立会话；同一参与者两次会话间隔至少 24 小时，或使用不同参与者；
- 每次会话内任务顺序由固定 seed 排列，seed 和实际顺序写入结果。

### 指标

| 指标 | 计算 |
|---|---|
| 可发现成功率 | 在 180 秒内提交正确目标页/记录/来源的任务数 ÷ 任务数 |
| 首个正确入口时间 | 从任务开始到第一次打开正确页面或来源的秒数 |
| 跳转次数 | 打开页面、打开来源、返回、切换 INDEX/RECORDS/WIKI/Canvas 各计 1；Canvas pan/zoom 不计 |
| 回退次数 | 打开错误页或来源后返回的次数 |
| 理解得分 | 每任务 0–2：0 错误，1 找到目标但解释缺字段，2 目标与边界均正确 |
| 来源核对率 | P1、P2、P5 中成功打开精确来源的任务数 ÷ 相应任务数 |
| 无证据断言 | 答案中无法回到冻结页或来源的事实数 |
| 视觉负担 | 实际节点、边、可见文字字符和首次 Zoom to fit 后重叠数 |
| 回滚正确率 | 三条隔离探针通过数 ÷ 3 |

### 进入实施的判定阈值

必须同时满足：

1. 结构门：所有 Canvas JSON 解析通过，节点 `≤12`、边 `≤16`、悬空边 `0`、缺失回链 `0`、机器字段暴露 `0`；
2. 来源门：两种条件来源核对率均为 `100%`，无证据断言均为 `0`；
3. 任务门：Canvas 可发现成功率不低于 Markdown，且两者均至少 `11/12`；
4. 理解门：Canvas 平均理解得分不低于 Markdown 超过 5 个百分点；
5. 效率门：Canvas 的“首个正确入口时间中位数降低至少 15%”或“跳转次数中位数降低至少 20%”至少满足一项；
6. 回滚门：三条探针 `3/3`，恢复后的 baseline 字节完全一致；
7. 稳定门：相同输入连续生成 10 次，`.canvas` 与两个 manifest 的规范化内容 hash 完全一致。

“只更美观”或“与 Markdown 持平”不构成实施收益。效率门没有满足时保留纯 Markdown 为默认，不推进 companion/MCP 产品化。

### 立即停止条件

出现任一项即停止本轮并返回设计：

- 任一节点没有人类页或精确来源回链；
- 出现机器 ID、得分、内部检索词项或未审阅关系；
- 生成或回滚写出授权目录；
- Canvas 条件改变了页面集合、来源内容或 Agent pack；
- 目标漂移时仍覆盖或回滚；
- Obsidian、主题、插件、窗口或任务顺序没有写入 fixture；
- 第三方候选只能由 README 证明关键行为，源码/测试和实际原型结果无法闭合。

## 已确认、推断与待验证

### 已确认

- JSON Canvas 1.0 可以用文件节点和 `subpath` 回到 vault 页面与标题；
- CKB 已有预算化 pack、人类页、来源范围和 Obsidian 投影，可提供最小生成输入；
- 当前 companion 与 OpenAI Visualize 都不是 CKB JSON Canvas 生成器；
- 独立 Skill 可以把流程与脚本打包，但权限、选择、验证和回滚必须由 CKB 合同拥有。

### 合理推断

- 12 节点/16 边足以覆盖当前 pack 的 6 个主要页面、2 个记录和 3 个来源入口，同时保留一个焦点节点；
- 独立 Skill 比 MCP/companion 更适合隔离第一原型的权限与变量；
- 只有在时间或跳转指标显著改善且理解/来源不退化时，Canvas 才值得进入产品层。

### 待原型验证

- Obsidian 对 `vscode://` 或其他 custom editor URI 的 Canvas `link` 节点实际行为；
- 文件节点 `subpath` 在当前 Obsidian 固定版本中的跳转精度；
- Canvas 文件在用户手工移动节点后的 managed/unmanaged 所有权边界；
- 页面标题较长时的可读性、预览高度和 Zoom to fit 行为；
- 确定性布局对 12 个冻结任务的实际导航收益。

### 待用户决策

- benchmark 通过后的目标所有权：生成器受管、用户拥有，或只读导出；
- 是否允许 companion 在以后提供刷新和打开命令；
- 是否允许 direct editor URI，还是统一经知识页二跳到来源。
