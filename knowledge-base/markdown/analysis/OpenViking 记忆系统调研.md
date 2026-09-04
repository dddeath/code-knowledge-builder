# OpenViking 记忆系统调研

标签：#类型/分析

## 结论

OpenViking 不是一个只把对话切片后写入向量库的“记忆插件”，而是一个面向 AI Agent 的上下文数据库。它把 **Resource、Memory、Skill** 统一组织在 `viking://` 虚拟文件系统中，用会话提交驱动长期记忆提取，用 YAML 模板约束记忆类型与字段，用文件内容作为权威数据源，用向量索引和目录层次完成召回，再按 token 预算把结果装配成可注入 Agent 的上下文。

本次调研固定到 **OpenViking v0.4.17**，结论可以概括为四点：

1. **写入链路有状态。** `session.commit()` 先保存原始会话归档，再异步执行结构化摘要、记忆提取、文件更新、向量化和完成标记；记忆不是聊天记录的副本，而是从会话中抽出的持久状态。
2. **记忆演化是“LLM 决策 + 确定性落盘”。** LLM 读取相关旧记忆并输出结构化增删改操作，系统再用 `patch`、`replace`、`sum`、`immutable` 等字段级合并规则执行更新；这比让模型直接自由改文件更可控，但记忆选择和内容生成仍然依赖模型。
3. **读取链路强调分层与预算。** `find()` 提供低延迟单查询，`search()` 增加会话意图分析、目录递归和 rerank，`search(mode="context")` 再统一完成分类配额、逐级降级、跨轮去重和 token 装配。
4. **它与 Code Knowledge Builder（CKB）解决的问题不同。** OpenViking 面向持续变化的会话状态、用户偏好、事件和 Agent 经验；CKB 面向固定 Git 快照上的完整代码事实、确定性检索和人工审阅知识页。两者可以互补，但不能把 OpenViking 的动态记忆当成 CKB 的源码事实层。

推荐把 OpenViking 视为“Agent 运行时上下文与长期记忆基础设施”，而不是“已经替代代码知识库、审计记录或所有记忆治理工作的统一答案”。

## 调研范围与证据边界

### 固定对象

- 调研日期：2026-08-30。
- 代码与文档版本：OpenViking `v0.4.17`。
- 证据来源：版本化官方仓库、官方文档、官方基准说明和 VikingMem 论文摘要。
- 核心源码范围：`openviking/session`、`openviking/session/memory`、`openviking/retrieve`、`openviking/storage`、内置 memory YAML 模板及 `benchmark/RAG`。

### 本文如何区分证据

- **已确认事实**：可以由 `v0.4.17` 的文档、源码或配置直接支持。
- **分析判断**：由多处已确认事实推导，正文会说明推导依据。
- **待运行核验**：需要真实模型、Embedding、Rerank、数据集或生产部署才能确认；本次没有配置外部模型，也没有重新运行官方 benchmark。

OpenViking 官方说明，开源项目只实现了 VikingMem 论文中的**部分核心能力**。因此，论文中的事件—实体演化、时间压缩和最高性能结果不能自动等同于 `v0.4.17` 开源代码的全部现状。

## OpenViking 管理的不是单一记忆，而是三类上下文

OpenViking 将 Agent 上下文分成三类：

| 类型 | 主要内容 | 谁触发写入 | 典型生命周期 |
|---|---|---|---|
| Resource | 文档、代码库、网页、规则等外部知识 | 用户或应用导入 | 长期、相对静态 |
| Memory | 用户偏好、实体、事件、任务案例、执行轨迹和经验 | Agent 从会话与执行中提取 | 长期、持续更新 |
| Skill | Agent 可调用的能力定义与配套文件 | 用户或系统添加 | 长期、定义相对静态 |

这个分类的关键价值不是名称，而是把“事实材料”“交互后形成的状态”“可调用能力”拆成不同生命周期。Skill 的执行经验写入 Memory，而不是反向修改 Skill 定义；Resource 作为外部材料保留，Memory 可以链接 Resource，但不应伪装成原始资料。

典型命名空间如下：

```text
viking://resources/...                         账户内共享 Resource
viking://user/{user_id}/resources/...          用户私有 Resource
viking://user/{user_id}/memories/...           用户长期 Memory
viking://user/{user_id}/skills/...             用户 Skill
viking://user/{user_id}/peers/{peer_id}/...    稳定 Peer 的资源或记忆
viking://user/{user_id}/sessions/{session_id}  会话与归档
```

`viking://~/...` 是当前认证用户主目录的别名。底层存储还会添加 `account_id` 前缀，文件系统与检索都按请求上下文过滤，避免“能搜到但读不到”或“能读到但不应被检索”的身份错位。

## 总体架构：文件保存内容，向量索引保存入口

OpenViking 的主链路是：

```text
Client / HTTP / CLI
        │
        ▼
Service：FS / Search / Session / Resource / Pack / Debug
        │
        ├─ Parse：文档解析、目录树、语义任务
        ├─ Session：消息、使用记录、归档、提交
        ├─ Compressor：模板化记忆提取与更新决策
        ├─ Retrieve：意图分析、目录递归、rerank、上下文装配
        └─ Storage：VikingFS + AGFS/RAGFS + Vector Index
```

存储采用双层结构：

| 层 | 职责 | 是否是内容权威源 |
|---|---|---|
| AGFS/RAGFS | 保存原始文件、记忆 Markdown、会话归档、L0/L1 语义侧车和多媒体 | 是 |
| Vector Index | 保存 URI、父 URI、向量、摘要和标量元数据，用于召回与过滤 | 否 |

这一设计让文件内容与检索索引可以分别扩展，也明确了故障恢复方向：索引异常时应从内容层重建，而不是把向量库中的摘要当作唯一真相。`rm` 与 `mv` 会同步向量记录；语义生成与 Embedding 通过持久队列异步完成，因此“文件已写入”和“新内容已可被语义检索”是两个不同状态。

## L0、L1、L2 是目录语义层，不等于三种长期记忆

OpenViking 的三层加载模型是：

| 层 | 默认形式 | 默认正文上限 | 作用 |
|---|---|---:|---|
| L0 Abstract | 目录内 `.abstract.md` | 256 字符 | 向量召回与快速相关性判断 |
| L1 Overview | 目录内 `.overview.md` | 4000 字符 | rerank、目录导航和是否深入的判断 |
| L2 Detail | 原始文件与子目录 | 无统一上限 | 按需读取完整内容 |

需要注意两个容易混淆的事实：

1. L0/L1 主要是**目录级语义侧车**，普通文件并不会一一拥有同名 L0/L1 文件；文件摘要会聚合进所在目录的 L1。
2. `search(mode="context")` 对记忆叶子还有一套“注入详情层级”：可以返回 `uri`、`abstract`、`overview` 或 `full`。这套详情层级复用目录语义的名称，但针对 Memory 时会从记忆正文的 `# Summary` 或向量摘要中选取内容，不应机械理解为磁盘上存在三份记忆文件。

目录语义采用自底向上的生成流程：文件摘要进入叶目录 L1，再抽出 L0，再由子目录 L0 聚合父目录。`v0.4.17` 文档明确说明，当前向父目录持续冒泡的路径只应用于 Resource/Skill；Memory 目录虽复用 `SemanticProcessor`，但不能据此假设整棵 Memory 树都具有同样的父级刷新行为。

## 会话提交如何形成长期记忆

### 会话生命周期

会话的基本生命周期是：

```text
create → add_message / used → commit → 查询后台 task
```

消息可包含文本、图片、上下文 URI 引用和工具调用。`used()` 记录本轮实际使用过的上下文或 Skill；提交后的后台阶段会据此更新向量记录中的 `active_count`，为可选的热度排序提供数据。

### 两阶段提交

`session.commit()` 将高延迟的 LLM 工作与原始会话持久化分开：

```text
阶段一：同步归档
  选择应归档和保留的消息
  → 写入 archive_NNN/messages.jsonl
  → 更新当前消息状态
  → 发布持久 session_commit 任务
  → 返回 task_id

阶段二：异步处理
  从归档恢复消息
  → 生成结构化摘要和 L0/L1
  → 提取长期 Memory
  → 写 memory_diff.json
  → 更新 active_count
  → 写 .done 或失败状态
```

这条边界很重要：调用 `commit()` 成功返回，只说明归档与后台任务已被接受；调用方仍要轮询 task，确认记忆提取、向量任务和完成标记的最终状态。

### 会话保留与压缩

OpenViking 可以按最近消息数或“用户 Turn + token 预算”保留活跃上下文，把更早内容移入归档。Turn 规划会保持 Assistant 消息与对应工具结果的原子关系；超预算时优先保留最新用户锚点和最后一个 Assistant Step，并以不修改原始持久消息的方式生成截断视图。

自动提交不是所有会话默认开启。只有会话保存了 `auto_commit_policy` 才会启用，推荐默认阈值包括待处理 150000 tokens、100 条消息或空闲 1 天。它们是触发归档和提取的策略，不是长期 Memory 的自动删除策略。

## Memory V2 的类型、路径和更新方式

`v0.4.17` 使用 YAML 模板注册记忆类型。模板可以定义目录、文件名、字段、正文模板、Embedding 模板、是否启用、提取阶段和字段合并规则。内置类型如下：

| 类型 | 默认位置 | 模式 | 主要含义 |
|---|---|---|---|
| `profile` | `~/memories/profile.md` | upsert | 用户职业、背景、沟通和工作习惯 |
| `preferences` | `~/memories/preferences/{user}/{topic}.md` | upsert | 按用户与主题组织的偏好 |
| `entities` | `~/memories/entities/{category}/{name}.md` | upsert | 人、组织、项目、地点等稳定实体卡片 |
| `events` | `~/memories/events/{年}/{月}/{日}/{event}.md` | add-only | 决策、里程碑和发生过的事件 |
| `identity` | `~/memories/identity.md` | upsert | Assistant 名称、气质、自我介绍等身份信息 |
| `soul` | `~/memories/soul.md` | upsert | Assistant 原则、边界、风格与连续性 |
| `cases` | `~/memories/cases/{case}.md` | upsert | 可用于训练与评估的任务案例 |
| `trajectories` | `~/memories/trajectories/{name}_{time}.md` | agent/add-only | 从执行过程提取的可复用轨迹 |
| `experiences` | `~/memories/experiences/{name}.md` | agent/upsert | 从结果中提炼的可迁移经验 |
| `tools` | `~/memories/tools/{tool}.md` | 默认关闭 | 工具调用次数、适用条件和失败模式 |
| `skills` | `~/memories/skills/{skill}.md` | 默认关闭 | Skill 使用统计和经验；不同于独立 Skill 定义 |

`profile`、`preferences`、`entities`、`events`、`identity`、`soul` 和 `cases` 属于用户记忆提取阶段；`trajectories` 与 `experiences` 属于执行派生的 Agent 阶段。Memory Policy 可以控制 self、peer、允许的记忆类型和 working memory。选择 `experiences` 会联动启用完整 Agent Evolution 路径，并纳入 `cases` 与 `trajectories`；反之，单独列出后两者会被策略忽略。

### 自定义模板的能力与风险

自定义模板可以通过 `memory.custom_templates_dir` 覆盖内置定义，因此应用能够增加业务记忆类型而不修改核心提取器。代价是模板已经成为数据模型和行为合同：目录或文件名模板决定身份归属，字段类型决定结构，`merge_op` 决定更新语义，Embedding 模板决定召回表示。模板变更需要同时验证旧文件兼容、路径迁移、检索可见性、冲突处理与回滚。

## 记忆更新为什么不是简单覆盖

### 先取回旧记忆，再让模型提出操作

Memory V2 的提取流程大致是：

```text
会话消息
  → 加载当前 Memory Schema
  → 按 Schema 目录预取相关旧记忆
  → LLM ReAct：必要时 read，最终输出结构化操作
  → 解析 page_id 与目标 URI
  → 隔离检查与字段合并
  → 写文件 / 删除文件 / 写链接
  → 记忆叶子向量化与目录语义刷新
```

多文件类型会先根据当前会话构造语义查询，在相关目录中检索候选；`eager_prefetch` 开启时再读取前 N 个结果。单文件类型如 `profile.md` 会直接读取。提取 Agent 只有 read/search 能力，不直接调用 write；系统要求修改已有记忆前读取完整文件，并把最终操作绑定到临时 `page_id`，降低模型把补丁应用到错误页面的概率。

### 字段级合并算子

| 合并算子 | 作用 | 典型字段 |
|---|---|---|
| `patch` | 对现有字符串应用精确 SEARCH/REPLACE 或 DELETE block | profile 内容、偏好正文、轨迹正文 |
| `replace` | 用新值替换旧值 | 经验正文、被替代关系 |
| `sum` | 累加数值 | 工具调用次数、成功次数、失败次数 |
| `immutable` | 首次确定后保持稳定 | 实体名称、类别、事件名、案例签名 |

这套设计把“应该写什么”留给 LLM，把“怎样按字段落盘”交给确定性代码。补丁校验要求 SEARCH 来自已读取页面、文本唯一且连续；系统在写入前还会处理同批次 upsert/delete 冲突、大小写冲突、Peer 归属和缺失 URI。

它仍不是完全确定性的记忆系统：哪些信息值得记录、归入何种类型、怎样概括、是否与旧内容冲突，仍受 VLM、模板和上下文影响。工程验收必须测重复提交、模型切换、语言切换、矛盾输入、跨 Peer 输入和部分失败，而不能只检查文件是否生成。

## `memory_diff.json` 提供了审计证据，但不是现成的回滚命令

每次成功运行长期记忆提取后，归档目录会保存 `memory_diff.json`，列出：

- 新增：URI、memory type 和写入后的内容；
- 更新：URI、修改前和修改后的内容；
- 删除：URI 与删除前内容；
- 跳过：稳定原因码与说明；
- 汇总：各类操作数量。

这是重要的可追踪性设计，因为可以回答“哪次会话改变了哪份长期状态”。源码还会过滤最终内容没有变化的伪更新。

但在 `v0.4.17` 已检查的公开代码与文档中，`memory_diff.json` 的消费者主要用于任务结果和训练产物报告，没有发现一个把该文件直接反向应用的通用 Memory rollback API 或 CLI。因而“可用于回滚”目前应理解为**具备构造回滚所需的前后内容证据**，不是“已经提供一键、并发安全、索引同步的自动回滚”。生产接入若需要撤销，仍应实现受 URI、版本和当前内容守卫的补偿操作，并验证向量索引同步。

## 检索分成列表召回、会话理解和上下文装配

### `find()` 与 `search()`

| 能力 | `find()` | `search()` |
|---|---|---|
| 查询形式 | 单个原始查询 | LLM 生成 0–5 个 `TypedQuery` |
| 是否依赖会话 | 否 | 可使用会话摘要、最近消息与当前问题 |
| 典型延迟 | 较低 | 较高 |
| 适用场景 | 已知目标、简单检索 | 多意图任务、跨 Memory/Resource/Skill 规划 |

`search()` 的 IntentAnalyzer 将查询分到 MEMORY、RESOURCE、SKILL，并给出优先级。层次检索先在全局向量索引找起始目录，再用优先队列递归搜索子节点，默认在三轮 top-k 不变后收敛。THINKING 模式且配置了 rerank 时会重排；rerank 失败则回退到向量分数。

### `search(mode="context")`

这个接口把“搜结果”和“组装可注入上下文”合成一次服务器操作：

```text
L1：可选的会话查询扩展，最多 3 个查询，超时回退原查询
L0：按 quota/purpose 分桶召回，或执行不分桶的全域检索
L2：在 max_tokens 内选择 uri/abstract/overview/full
L3：可选 LLM digest；失败时保留原始 rendered 结果
```

预算算法先让每个候选占据所属类别的默认层，再按得分顺序把剩余预算用于加深，而不是让第一个高分结果吃完整个上下文。单条候选的普通上限约为 `max_tokens ÷ candidate_count × 2`；超限时退回更浅层，不截断半段正文。所有结果至少可以保留 URI，最后一次加深仍受总 token 预算约束。

`purpose="chat"` 与 `purpose="coding"` 提供不同的绝对分类配额。会话模式还可以在 `{session_uri}/.recall_log.json` 中记录已注入 URI，并用 `dedup_turns` 做跨轮冷却；这解决了“每一轮都重复塞回同一记忆”的上下文浪费。

旧 `/api/v1/search/recall` 在 `v0.4.17` 已被标记为弃用，它只是 `search(mode="context")` 的兼容预设。新接入应使用 context 模式，避免把旧参数与新分层装配语义混在一起。

## 热度是可选排序信号，不是自动遗忘

OpenViking 可以把语义得分与热度混合：

```text
hotness = sigmoid(log1p(active_count)) × exp(-ln(2) × age_days / 7)
final = (1 - hotness_alpha) × semantic + hotness_alpha × hotness
```

其中 `active_count` 来自会话记录的实际使用，`updated_at` 提供时效信号，默认半衰期为 7 天。`retrieval.hotness_alpha` 默认是 `0.0`，即默认不改变纯语义分数。

源码中的“cold/hot lifecycle”当前主要表现为评分函数与统计分布。它不会因为记忆变冷就自动删除、压缩或迁移文件；会话归档也只是把活跃消息移到历史目录。若业务需要真正的遗忘、过期、合并和合规删除，仍要设计明确的 TTL、保留策略、引用检查、索引删除、审计和恢复流程。

## 并发、恢复、隔离与隐私边界

### 并发与崩溃恢复

- 文件写入使用精确路径锁；目录删除与资源生命周期使用树锁。
- `.abstract.md` 和 `.overview.md` 用 `coalesce_version` 丢弃过期后台结果，最终写回再短暂持有精确路径锁。
- `session_commit` 任务保存在 QueueFS 的 SQLite 队列中，进程重启后继续阶段二。
- 锁文件可以过期清理；默认过期时间为 30 秒。
- 向量索引中的孤儿记录可在后续 L2 读取时清理。

这些机制提高的是“任务可恢复”和“旧异步结果不覆盖新结果”。它们不等于跨内容层与向量层的同步数据库事务；业务仍需把“文件已持久化、语义已生成、向量已可见、任务最终完成”分开观测。

### 多租户与加密

正式多租户模式使用 `account_id` 作为外层租户边界，`user_id` 隔离用户 Memory 与 Session，`peer_id` 只是在当前用户下的内容范围。Resource 可以在账户内共享，Memory 默认不跨用户共享。

静态加密采用信封加密：实例 Root Key 派生账户 KEK，每次写入生成文件 DEK，用 AES-256-GCM 加密内容，再用账户 KEK 加密 DEK。这个机制保护静态文件并加强账户隔离，但不能替代应用层的最小化采集和秘密过滤。

### 敏感信息的明确边界

`v0.4.17` 的 Privacy Config 文档明确把占位符提取、版本管理和读取时恢复限定在 Skill 内容；本次检查的 Memory 提取管线没有发现通用的高熵 secret scrub 或 credential redaction。由此得到的工程判断是：如果会话中出现 API Key、Token 或其他敏感值，不能仅依赖静态加密与租户隔离来阻止它被抽入长期 Memory 和向量索引。

生产接入至少需要：提交前会话脱敏、Memory 写入前字段级过滤、向量化前二次检查、可验证删除、密钥轮换和泄露响应。该结论是对当前公开实现边界的分析，不是对任何具体部署已经泄露数据的判断。

## 官方评测说明了潜力，也必须保留版本与实验边界

### 官方集成评测

`v0.4.17` README 引用的是 OpenViking **0.3.22** 的评测，不是本次版本的新鲜复验。官方报告给出的结果包括：

- LoCoMo 用户记忆：OpenClaw 24.20% 原生对 82.08% 接入 OpenViking；Hermes 33.38% 对 82.86%；Claude Code 57.21% 对 80.32%。
- 输入 token 降低 34.3%–91.0%，查询延迟降低 58.45%–66.10%。
- tau2-bench：Retail 任务成功率提升 6.87 个百分点，Airline 提升 11.87 个百分点。
- 记忆评测使用 Doubao 2.0 Pro 与 Doubao-embedding-vision-251215。

这些数字能证明“在指定 Agent、模型、数据集和版本下具有明显收益”，但不能证明：

- `v0.4.17` 在任意模型或本地 Embedding 下仍有相同收益；
- 所有记忆类型都达到 80% 以上精度；
- 删除、矛盾更新、跨 Peer 隔离和隐私场景已经被同一 benchmark 覆盖；
- OpenViking 在任意代码任务上都优于确定性代码检索。

### 仓库内 RAG benchmark

仓库提供 FinanceBench、LoCoMo、Qasper 和 SyllabusQA 的可复现 RAG 脚本，测量 Recall、F1、LLM Judge Accuracy、延迟与 token。README 中列出的 top-5 参考结果采用固定抽样和 Doubao 模型，例如 LoCoMo 80 个问题的平均 Recall 为 0.592、标准化 Accuracy 为 0.600。

这组“把数据集作为 Resource 摄取后进行 RAG 问答”的结果，与前述“Agent 集成后的长期 Memory”评测不是同一个实验，不能混成一个统一准确率。

### VikingMem 论文关系

VikingMem 将 Memory Base 概括为高价值选择性提取、持续状态演化和可迁移抽象，并提出事件—实体联动、时间压缩和时间加权召回。论文摘要报告相对基线最高提升 30% 的记忆检索效果。OpenViking README 只声明开源了论文的部分核心能力，因此本文只把论文用于解释设计方向，不把论文数字当作 `v0.4.17` 当前开源实现的直接验收结果。

## OpenViking 与 CKB 的职责对照

| 维度 | OpenViking | CKB | 当前判断 |
|---|---|---|---|
| 主要对象 | 会话、用户/Peer Memory、Resource、Skill | 固定 Git 快照上的代码事实与审阅知识 | 对象不同，适合分层组合 |
| 权威数据源 | AGFS/RAGFS 文件内容 | Git commit/blob/range 与可重建 facts | 都重视内容源，但来源合同不同 |
| 写入时机 | 会话 commit 后动态提取与更新 | 固定图不变；分析、变更、实验、会话通过 record 写入可变层 | CKB 更适合审阅后沉淀，OpenViking 更适合运行时持续学习 |
| 检索 | 向量/混合召回、目录递归、可选 LLM 规划与 rerank | SQLite FTS5、固定权重图传播、固定预算 | CKB 更确定，OpenViking 对自然语言与跨类型上下文更灵活 |
| 更新语义 | YAML Schema + 字段 merge op + LLM 操作 | 生成器管理固定层，人工记录显式追加或新建 | 两者都应避免模型自由覆盖稳定内容 |
| 人类阅读 | 文件系统可浏览，Memory 为 Markdown，Resource 保留原文 | 专门的简体中文 Human/Obsidian 投影与工作记录导航 | CKB 的人类层治理更强 |
| 来源追溯 | URI、会话归档、memory diff、Resource 链接 | commit/blob/range、精确源码范围、Agent pack、记录回链 | CKB 对代码修改证据更精细 |
| 生命周期 | 动态记忆、归档、热度、去重、后台队列 | 固定基线、增量迁移、overlay、Agent 审阅与完成门 | 可分别承担运行时层与工程知识层 |
| 外部资料 | PDF/MD/HTML/代码可作为 Resource 摄取 | 外部资料只能进入审阅分析记录，不能冒充源码实体 | OpenViking 适合原始资料库，CKB 适合代码事实库 |

CKB 当前可从以下知识页继续核对内部实现：[[sync_human_layer 与 _source_manifest 的协作实现]]、[[retrieve_machine 与 estimated_tokens 的协作实现]]、[[ingest_event 与 default_registry_path 的协作实现]]、[[start_session 与 _session_directory 的协作实现]]。

## 对 CKB 可以借鉴什么

### 值得借鉴

1. **把检索结果装配作为独立层。** OpenViking 的 URI 保底、分类配额、先广后深、单条预算上限和跨轮去重值得单独评测，而不是把“召回 top-k”直接等同于“最终给 Agent 的上下文”。
2. **字段级合并算子。** `patch`、`replace`、`sum`、`immutable` 把动态知识更新转成可验证的操作，可用于思考 CKB 可变记录中的结构化追加和冲突处理。
3. **每次动态记忆更新留下 diff。** CKB 已有 record 元数据、索引和审计；若以后增加自动整合，可以继续坚持每次增删改都保留 before/after、来源会话和跳过理由。
4. **把身份范围贯穿文件系统与检索。** 不只在 API 入口鉴权，还要让实际搜索范围、读取范围、写入路径和 Peer 归属共享同一请求上下文。
5. **异步状态可观测。** “已接受、处理中、已完成、失败”应明确分开，并暴露队列、模型、Embedding、rerank 和索引可见性指标。

### 不应直接照搬

1. **不让 LLM 意图分析进入 CKB 固定基线检索的必经路径。** CKB 的确定性与跨进程一致性是重要合同；LLM query planner 只能作为可选实验层。
2. **不把未经 Agent 审阅的会话抽取直接晋升为稳定人类知识。** OpenViking 的自动记忆适合运行时，但 CKB 的正式分析、变更和实验仍应通过 `record` 和审计门。
3. **不把向量索引当成源码事实。** CKB 的实体、关系和来源范围必须继续由固定 Git 快照支撑。
4. **不把 L0/L1/L2 名称直接套到 CKB 三层知识库。** OpenViking 的三层主要表达加载深度；CKB 的 facts/machine/human 表达不同消费者与不同完整性合同。

## 何时选择 OpenViking

适合采用 OpenViking 的场景：

- Agent 需要跨多轮、多会话记住用户偏好、稳定实体、事件和执行经验；
- 同一 Agent 需要统一搜索私有 Memory、外部 Resource 与可调用 Skill；
- 应用愿意运行独立服务，并接受 VLM、Embedding、可选 rerank 的成本与运维；
- 需要用户/Peer/账户隔离、远程 HTTP 接入、异步处理和 Prometheus 指标；
- 可以为动态记忆建立脱敏、删除、冲突更新和质量评测流程。

不适合作为唯一方案的场景：

- 需要完全确定、零模型依赖的检索结果；
- 需要 commit/blob/range 级源码事实与精确修改证据；
- 需要未经模型判断的法规留存、账务记录或其他强一致权威数据；
- 不能接受会话内容进入外部 VLM、Embedding 或 rerank provider；
- 只需要一个小型、静态、可用关键词直接定位的文档集合。

## 建议的最小验证方案

如果后续要评估是否把 OpenViking 接入现有 Agent/CKB 工作流，建议先做一个隔离 PoC，而不是直接导入全部历史：

1. **固定版本与配置**：使用明确 tag，记录 VLM、Embedding、rerank、`hotness_alpha`、Memory Policy 和自定义模板。
2. **固定三类任务**：用户偏好更新、跨日事件问答、代码任务经验复用；每类同时包含创建、矛盾更新、删除和无关输入。
3. **设置对照组**：原生 Agent 记忆、OpenViking、仅 Resource RAG 三组使用同一模型和问题。
4. **分别测量**：记忆提取 Precision/Recall、矛盾率、删除残留率、跨用户/Peer 泄漏率、Recall@K、最终回答准确率、输入 token、P50/P95 延迟、模型调用次数和后台完成时间。
5. **执行故障注入**：在 archive 后、Memory 写入中、向量入队后分别终止服务，验证 QueueFS 恢复、`.done`/失败状态、memory diff 和索引可见性。
6. **执行隐私探针**：在会话中放入专用假 Token，确认提交前脱敏、Memory 文件、向量召回、日志、备份和删除后的所有副本都不再返回该值。
7. **设定采用门**：只有下游任务质量提高、token/延迟在预算内、矛盾与隐私门通过、回滚与删除可验证时，才扩大范围。

## 已确认限制与待核验项

### 已确认限制

- Memory 的父级语义冒泡没有与 Resource/Skill 完全相同的当前合同。
- 热度排序默认关闭，也不自动执行冷数据删除或时间压缩。
- Privacy Config 的占位符提取/恢复当前面向 Skill，不是通用 Memory secret scrub。
- `memory_diff.json` 提供前后内容证据，但公开实现中未发现通用一键 Memory rollback 入口。
- context 模式当前不支持 `target_uri`，按类别 quota 也只覆盖指定桶；其他内置记忆进入通用 `memories` 类别。
- 自动提取、query expansion、rerank、摘要和可选 digest 都可能产生模型成本与结果波动。

### 仍需运行核验

- `v0.4.17` 在本项目实际数据、模型和 Windows/WSL 环境中的提取质量与稳定性。
- 官方 0.3.22 集成 benchmark 在当前版本与当前模型上的复现结果。
- 自定义 Memory Schema 升级后的旧数据迁移与向量重建成本。
- 高并发同一用户、同一实体和跨 Session 合并时的冲突率。
- 删除、备份、OVPack 恢复、向量重建和多写存储组合下的端到端一致性。

## 来源

### OpenViking v0.4.17 官方文档与源码

- [OpenViking v0.4.17 中文 README：定位、评测与许可证](https://github.com/volcengine/OpenViking/blob/v0.4.17/README_CN.md)
- [架构概览](https://github.com/volcengine/OpenViking/blob/v0.4.17/docs/en/concepts/01-architecture.md)
- [Resource、Memory、Skill 类型与内置 Memory](https://github.com/volcengine/OpenViking/blob/v0.4.17/docs/en/concepts/02-context-types.md)
- [L0/L1/L2、语义侧车与 freshness](https://github.com/volcengine/OpenViking/blob/v0.4.17/docs/en/concepts/03-context-layers.md)
- [AGFS/RAGFS 与向量索引双层存储](https://github.com/volcengine/OpenViking/blob/v0.4.17/docs/en/concepts/05-storage.md)
- [Resource、Skill、Memory 的提取路径](https://github.com/volcengine/OpenViking/blob/v0.4.17/docs/en/concepts/06-extraction.md)
- [意图分析、目录递归与 rerank](https://github.com/volcengine/OpenViking/blob/v0.4.17/docs/en/concepts/07-retrieval.md)
- [Session 提交、Memory Diff 与存储结构](https://github.com/volcengine/OpenViking/blob/v0.4.17/docs/en/concepts/08-session.md)
- [路径锁、QueueFS 与崩溃恢复](https://github.com/volcengine/OpenViking/blob/v0.4.17/docs/en/concepts/09-transaction.md)
- [多租户账户、用户与 Peer 边界](https://github.com/volcengine/OpenViking/blob/v0.4.17/docs/en/concepts/11-multi-tenant.md)
- [分层、预算和跨轮去重的 context 装配](https://github.com/volcengine/OpenViking/blob/v0.4.17/docs/en/api/06-retrieval.md#searchmodecontext)
- [Memory API 与弃用的 recall 兼容入口](https://github.com/volcengine/OpenViking/blob/v0.4.17/docs/en/api/16-memory.md)
- [Memory V2 Schema 注册器](https://github.com/volcengine/OpenViking/blob/v0.4.17/openviking/session/memory/memory_type_registry.py)
- [Memory 提取 ReAct 循环](https://github.com/volcengine/OpenViking/blob/v0.4.17/openviking/session/memory/extract_loop.py)
- [Memory 文件更新、删除与向量化](https://github.com/volcengine/OpenViking/blob/v0.4.17/openviking/session/memory/memory_updater.py)
- [上下文 token 预算算法](https://github.com/volcengine/OpenViking/blob/v0.4.17/openviking/retrieve/context_assembler/budget.py)
- [热度评分](https://github.com/volcengine/OpenViking/blob/v0.4.17/openviking/retrieve/memory_lifecycle.py)
- [RAG benchmark 说明与参考结果](https://github.com/volcengine/OpenViking/blob/v0.4.17/benchmark/RAG/README_zh.md)

### 研究来源

- [VikingMem: A Memory Base Management System for Stateful LLM-based Applications](https://arxiv.org/abs/2605.29640)

## 最终判断

OpenViking 已经形成一条较完整的 Agent 长期记忆工程链路：会话归档提供原始证据，Memory Schema 定义状态形状，ReAct 提取器提出结构化操作，字段合并器控制更新，VikingFS 保存权威内容，向量与目录检索负责召回，context assembler 控制注入预算，QueueFS、锁、指标、多租户和加密补齐服务化能力。

它最值得关注的不是“用了向量数据库”，而是把**记忆写入、演化、召回、注入和恢复**拆成了可以分别配置和观测的阶段。当前仍需谨慎对待模型非确定性、Memory 级秘密过滤、真正的自动遗忘、通用回滚和版本迁移。对 CKB 而言，合理方向是保持固定代码事实层不变，选择性借鉴 OpenViking 的动态记忆 Schema、上下文装配预算、跨轮去重和更新 diff，而不是把两种系统合并成一个含义模糊的“统一知识库”。

## 相关知识页

- [[start_session 与 _session_directory 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]
- [[sync_human_layer 与 _source_manifest 的协作实现]]
- [[ingest_event 与 default_registry_path 的协作实现]]
- [[render_integration 与 harness_retrieval_contract 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[doctor_report 与 _version_matches 的协作实现]]
- [[parse_file 与 _language 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
- [打开源码：scripts/ckb_core/knowledge_layers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:1:1)  `scripts/ckb_core/knowledge_layers.py:1-239`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1632`
- [打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-502`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/providers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/providers.py:1:1)  `scripts/ckb_core/providers.py:1-596`
- [打开源码：scripts/ckb_core/parsers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/parsers.py:1:1)  `scripts/ckb_core/parsers.py:1-437`
