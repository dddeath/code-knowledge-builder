# Tag assertion 与状态机合同

## 输入事件

`tag-assertion.schema.json` 是唯一事件合同。根对象禁止额外字段。

- `propose`：必须有证据，`stance=null`，只创建候选，不计票；
- `vote`：必须有证据，`stance` 为 `support` 或 `oppose`；
- `retract`：必须指定同一 Agent、同一 target、同一 tag 的既有 assertion，`stance=null` 且 `evidence=null`。

`actor.key` 是不含姓名、邮箱或账户的本地 opaque key。`evidence` 不保存 source 正文，只保存结构化定位与 hash。所有路径必须是 `/` 分隔的仓库相对路径。

## 重放顺序与幂等

1. assertion 先按 `recorded_at`、再按 `assertion_id` 排序；
2. SQLite 对 `assertion_id` 和 `idempotency_key` 建立 `UNIQUE`；
3. 相同幂等键且 canonical payload 相同记为 `duplicate`，不新增行；
4. 相同幂等键但 payload 不同返回 `IDEMPOTENCY_CONFLICT`，整批事务回滚；
5. retract 只能撤销更早的 assertion；跨 Agent、target 或 tag 的 retract 返回 `INVALID_RETRACTION`。

## 活动票

撤销事件先移除被撤销 assertion。每个 `actor.key + target.path + tag` 只保留最后一张未撤销 vote；更早 vote 标记为 superseded。proposal 永远不计票。

## 固定阈值

阈值来自 `policy.schema.json` 校验后的 JSON：

| 字段 | fixture 值 | 作用 |
|---|---:|---|
| `min_support_votes` | 2 | 最少 support 票数 |
| `min_independent_agents` | 2 | 最少独立 Agent key |
| `min_independent_sources` | 2 | support 证据的最少独立 source ID |
| `max_opposition_ratio` | 0.25 | `oppose / (support + oppose)` 上限 |
| `max_evidence_age_days` | 90 | `as_of - evidence.observed_at` 上限 |
| `max_tags_per_page` | 3 | 人类投影配额 |

确认还要求所有活动 vote 的 evidence commit 等于审计 `current_commit`，并且所有活动 vote 均在时效内。未来时间、非法 SHA、绝对路径、`..`、未知字段或自由文本均在写库前失败。

## 原因码

- `CONFIRMED_THRESHOLDS_MET`
- `PROPOSAL_ONLY`
- `SUPPORT_VOTES_BELOW_MINIMUM`
- `INDEPENDENT_AGENTS_BELOW_MINIMUM`
- `INDEPENDENT_SOURCES_BELOW_MINIMUM`
- `OPPOSITION_RATIO_EXCEEDED`
- `COMMIT_DRIFT`
- `STALE_EVIDENCE`
- `ALL_SUPPORT_RETRACTED`
- `NO_ACTIVE_SUPPORT`
- `PAGE_TAG_QUOTA_EXCEEDED`

原因码去重后按固定字典序输出。状态排序固定为 target path、tag。
