# CKB Canvas 与纯 Markdown 冻结对照合同

## 1. 比较问题

对照只回答一个问题：在完全相同的 CKB 证据集合上，增加一个受 12 节点、16 边预算约束的 Canvas 入口，是否比纯 Markdown 导览更快、更少跳转，同时不降低来源核对和理解正确性。

Canvas 条件不能增加页面、来源、摘要、机器实体、模型调用或搜索能力。若证据集不同，本轮结果直接 `stopped`，不计算效果。

## 2. Runner 输入和输出

规范输入是 [`fixtures/benchmark/benchmark-run.json`](fixtures/benchmark/benchmark-run.json)，由 [`schemas/benchmark-run.schema.json`](schemas/benchmark-run.schema.json) 校验。它固定：

- canvas request、snapshot commit/tree、pack、record 和人类/来源 evidence hash；
- Markdown 与 Canvas 的入口；
- Obsidian 版本 slot、默认主题、第三方插件关闭、1440×900、100% 缩放、离线和 Zoom to fit；
- 12 个任务、期望页、期望来源范围和回答事实；
- 两个 sequence、四个 condition assignment、每个 block 的 seed 和实际 task order；
- 每个 sequence 至少 2 个独立 session，同一参与者间隔至少 24 小时，或改用不同参与者；
- 指标、七个门、三条 rollback probe 和 10 次确定性重复。

一个独立 session 在同一 sequence 中执行两个互不重复的 condition block：

- `sequence-1`：Markdown → Canvas；
- `sequence-2`：Canvas → Markdown。

每个 block 单独输出一个 [`benchmark-session-result`](schemas/benchmark-session-result.schema.json)，两个 block 共享 `session_id`，但 `condition` 和 task order 不同。至少需要 4 个独立 session、8 个有效 block。汇总输出符合 [`benchmark-summary.schema.json`](schemas/benchmark-summary.schema.json)。

示例结果只用于 schema 验证：

- [`benchmark-session-result.json`](fixtures/benchmark/benchmark-session-result.json)
- [`benchmark-summary.json`](fixtures/benchmark/benchmark-summary.json)

示例中的通过值不是实测结论，原型不得复制为 benchmark 结果。

## 3. 十二个任务的固定答案对象

| ID | 问题 | 正确页 | 正确来源范围或主张 |
|---|---|---|---|
| `P1A` | 定位 `obsidian.py` | `pages/audit_obsidian 与 prepare_vault 的协作实现.md` | `scripts/ckb_core/obsidian.py:1-166` |
| `P1B` | 定位 `obsidian_plugin.py` | `pages/register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现.md` | `scripts/ckb_core/obsidian_plugin.py:1-262` |
| `P2A` | 定位 `compact_agent_brief` | `pages/maintenance_check 与 capability_matrix 的协作实现.md` | `scripts/ckb_core/llm_wiki_capabilities.py:358-405` |
| `P2B` | 定位 `agent_index.py` | `pages/retrieve 与 _tokens 的协作实现.md` | `scripts/ckb_core/agent_index.py:1-555` |
| `P3A` | 找到人类可读性派发记录 | `sessions/人类可读性样例确认与第一开发波次派发.md` | Canvas 是独立研究/设计任务，尚未成为已支持能力 |
| `P3B` | 找到项目说明书记录 | `analysis/Code Knowledge Builder 项目说明书结构与验收样例.md` | 提交第 13 章目标与精确章节证据 |
| `P4A` | 解释 Obsidian 搜索边界 | `INDEX.md` | 人类导航入口与 `machine/knowledge.sqlite` 完整机器入口 |
| `P4B` | 解释 pack/record 边界 | `INDEX.md` | pack 是预算化正文；record 保留完整候选、词项、得分和统计 |
| `P5A` | 从知识页打开 `obsidian.py` | 对应知识页 | 固定来源实际打开成功 |
| `P5B` | 打开 `llm_wiki_capabilities.py:358-405` | 对应知识页 | 固定来源实际打开成功 |
| `P6A` | 判断 CKB 是否已支持 Canvas | 派发记录 | 当前只有研究和设计输入，没有产品实现 |
| `P6B` | 判断 companion 是否生成 Canvas | companion 作用页 | companion 已确认职责不含 Canvas 生成 |

其中 file entity 的 `end_line=line_count+1` 是当前固定 record 形状，不代表 UI 必须打开不存在的末行；source open 以 `start_line` 为 URI 锚点，答案仍报告 record 的精确范围。

## 4. Block 分配与顺序

`sequence-1`：

- Markdown：`P4B,P1A,P6B,P3A,P2B,P5A`；
- Canvas：`P5B,P2A,P3B,P6A,P1B,P4A`。

`sequence-2` 交换两个界面接触的 A/B 集：

- Markdown：`P3B,P6A,P1B,P4A,P5B,P2A`；
- Canvas：`P2B,P5A,P4B,P1A,P3A,P6B`。

runner 不在执行时调用随机库；`order_seed` 只记录冻结顺序来源，实际顺序以 JSON 数组为准。这样跨 Python/Node/平台不会因为 PRNG 不同改变任务顺序。

## 5. 事件与计分

### 5.1 计时

从 runner 显示任务文本并确认窗口前台开始，到参与者提交页面、来源和解释结束。每任务最多 180 秒。后台加载和前一任务清理在下一任务开始前完成，不计入任务时间。

### 5.2 跳转

以下每次计 1：

- 打开 Markdown 页面；
- 打开精确来源；
- 返回；
- 在 `INDEX.md`、`RECORDS.md`、`WIKI.md`、Canvas 间切换。

Canvas pan、zoom、框选和移动视口不计跳转，但写入 `visible_text_characters`、`overlap_count` 和观察备注。

### 5.3 正确性

- `success=true`：在 180 秒内提交正确页/记录；需要来源的任务还必须提交正确 path 与 range。
- `comprehension_score=2`：目标正确，且 `required_facts` 全部由冻结页/来源支持。
- `comprehension_score=1`：目标正确，但缺少至少一个 required fact 或边界字段。
- `comprehension_score=0`：目标错误、超时或给出与冻结证据冲突的支持状态。
- `source_verified` 只对 `P1`、`P2`、`P5` 计分；其他任务写 `null`。
- `unsupported_assertions` 是答案中不能回到冻结页/来源的事实条数，不能用“整体印象正确”抵消。

## 6. 汇总算法

只使用 environment verified、顺序匹配、证据 hash 匹配且未触发 stop 的 block。

```text
discoverability_success_rate = success trials / valid trials
first_correct_entry_seconds = 各条件成功 trial 的中位数
navigation_count = 各条件有效 trial 的中位数
comprehension_percent = sum(score) / (2 * valid trials) * 100
source_verification_rate = verified P1/P2/P5 trials / valid P1/P2/P5 trials
time_reduction = (markdown_median - canvas_median) / markdown_median
navigation_reduction = (markdown_median - canvas_median) / markdown_median
```

同一 task 在多个 session 中保留独立 trial，不先做主观多数表决。`11/12` 转换成预先固定的成功率下限 `0.9166666667`，避免 session 数增加后重新定义“一个任务是否成功”。

## 7. 七个完成门

| 门 | 必须满足 |
|---|---|
| 结构 | JSON 可解析；节点 `<=12`、边 `<=16`、悬空边 0、缺失回链 0、机器字段 0 |
| 来源 | 两条件 `source_verification_rate=1.0`，无证据断言均 0 |
| 任务 | 两条件成功率均 `>=0.9166666667`，Canvas 不低于 Markdown |
| 理解 | Canvas 理解百分比最多比 Markdown 低 5 个百分点 |
| 效率 | 时间中位数降低 `>=15%` 或跳转中位数降低 `>=20%` |
| 回滚 | absent、present、drift 三条 probe `3/3` |
| 稳定 | 同一输入 10 次 Canvas 原始 hash 相同，两个 manifest 规范化 hash 各只有一种 |

全部通过时 summary 为 `passed`，decision 为 `advance-to-product-decision`。这只允许进入产品归属决策，不自动修改 companion、主 CLI 或活动知识库。

效率门失败但结构、来源和理解未退化时，decision 固定为 `keep-markdown-default`。任一结构/来源/权限/漂移边界失败时为 `return-to-design`。session 数不足时为 `collect-more-sessions`。

## 8. 立即停止

出现以下任一项，本轮 `status=stopped`，不与通过轮混合：

- 缺失回链；
- 机器字段进入 Canvas；
- 写出授权目录；
- 两条件 evidence hash 不同；
- promotion/rollback drift 后仍覆盖；
- Obsidian 版本、主题、插件、窗口或任务顺序未冻结；
- fixed Obsidian 版本不能从 Canvas 打开测试 editor URI；
- file node/subpath 行为与冻结答案不一致。
