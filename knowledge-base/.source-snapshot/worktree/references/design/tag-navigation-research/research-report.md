# 机器 tag 下沉与人类导航研究结论

## 结论

本实验采用“机器层 assertion，确定性审计，人类层只投影 confirmed tag”的闭环。tag 不直接进入 CKB 稳定页面，也不改变当前每页唯一 `#类型/...` 标签合同。实验投影是独立 JSON，可在以后由管理任务决定是否转为 Obsidian 可点击 tag、Properties 字段或单独导航页。

这一选择保留了两类职责：Agent 负责提交可追溯的 propose、support、oppose 或 retract 事件；脚本负责幂等去重、单 Agent 单票、来源独立性、固定 commit、证据时效、反对比例、状态排序和每页配额。Agent 不能直接把建议写成人类 tag。

## Obsidian 三种入口的适用范围

### Tags

Tags 是本实验的首选人类导航语义。它们可点击、可用 `tag:` 搜索、支持 `/` 层级，并可由 Tags view 汇总。限制是 tag 不区分大小写、不能含空格，而且它只能表达“页面属于某主题”，不能表达支持票、反对票、证据来源、commit 或废弃原因。

### Properties

Properties 能保存 YAML 结构化字段并用 `[property:value]` 搜索，但属性类型在 vault 内按名称统一，不支持嵌套属性，也没有内建批量编辑。CKB 当前人类页还禁止 frontmatter，因此本实验只把 Properties 视为未来可选的展示层，不把它作为机器事实或当前投影格式。

### Canvas

Canvas 能把 note、附件、网页和关系边放入二维空间，并使用 MIT 的 JSON Canvas 1.0。它适合比较空间入口是否减少跳转，但 text card 不进入 backlinks，网页卡片可能访问网络，Canvas 也没有 tag 投票状态合同。因此本实验继续运行已有 Canvas 兼容测试，不把 tag 原型接入 Canvas 生成器。

## 冻结状态机

状态只有 `candidate`、`confirmed`、`contested`、`deprecated`：

- `candidate`：已有 proposal 或当前 support，但票数、独立 Agent、独立来源或其他确认门未全部满足；
- `confirmed`：当前 commit 上、时效内的 support 至少 2 票，来自至少 2 个 Agent 和 2 个独立来源，反对比例不超过 0.25，且没有活动票发生 commit 漂移或过期；
- `contested`：当前 commit 且时效内的活动票中，反对票比例大于 0.25；
- `deprecated`：曾有投票，但当前没有可用 support，原因可以是全部撤销、证据过期或 commit 漂移。

同一 Agent 对同一 `target + tag` 只有按时间和 assertion ID 排序后的最后一张未撤销 vote 生效。相同幂等键与相同 payload 是重复提交；相同幂等键与不同 payload 是冲突并终止事务。proposal 不计 support 票。

## 人类投影

只有 `confirmed` 进入投影。每页最多 3 个 tag，排序依次使用 support 票数降序、反对比例升序、独立来源数降序和规范化 tag 字典序。超出配额的 confirmed tag 留在机器审计结果中，并以 `PAGE_TAG_QUOTA_EXCEEDED` 记录，不增加页面。

投影只输出 `page`、`tag` 和可复制的 `tag:#...` 搜索表达式，不输出 Agent key、机器 assertion ID、证据 hash、commit、SQLite 字段或票明细。

## 隐私与许可边界

assertion schema 没有自由文本、对话、Prompt、环境变量或 secret 字段；证据只保存 source ID、类型、仓库相对路径、结构化 locator、SHA-256、commit 和时间。SQLite、审计、投影与 benchmark 都在本地运行。官方来源只保存 URL、访问日期、许可元数据和中文释义。

Obsidian 应用可免费使用，但其文档和应用内容不是开放内容；本仓库不复制这些正文。JSON Canvas 使用 MIT。SQLite 代码与文档为 Public Domain。Git 项目使用 GPL-2.0，本实验只把 commit ID 当固定快照标识。

## 隔离导航对照的解释边界

固定 fixture 用同一组页面、同一批任务和逐题访问记录比较 `no_tag` 与 `confirmed_tag`。脚本重算找到入口所需步骤、误导链接、页面增量和冲突数。该结果只证明冻结 fixture 中的导航路径变化，不等同于真实用户、真实 Obsidian 版本或稳定知识库效果。

本轮 6 个固定任务的脚本重算结果为：总步骤 `19→7`，中位步骤 `3→1`，误导链接 `5→1`，两组页面数均为 11，页面增量 0，tag 冲突 0。结果文件明确写入 `effect_claim=fixture-navigation-signal-only`，因此它只是一条进入真实 Obsidian 人工对照前的导航信号。

## 进入生产前的最小决策

1. **tag 命名空间**：继续使用独立 `#导航/...`，还是允许它与当前唯一 `#类型/...` 标签并存；
2. **身份与来源登记**：哪些 Agent key 算独立投票者，哪些 source ID 算独立证据，以及谁维护这两个登记表；
3. **投影所有权**：投影是生成器受管、用户可编辑，还是只读导出；选择后才能定义刷新与回滚冲突规则。

在这三项决定前，生产接入保持关闭。
