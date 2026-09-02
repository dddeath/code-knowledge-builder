# Code Knowledge Builder 秋招面试官拷问手册

标签：#类型/分析

## 结论与使用方法

这份手册当前主要用于准备本工作区 `E:\deepseek_memory` 的 DSH Layered Memory / `sensory-memory-plugin` 项目面试，重点回答项目为什么需要大量 benchmark、每组实验分别证明什么、Badcase 集中在哪里、黑盒边界怎样固定，以及当前结果能说到哪一步。Code Knowledge Builder 的架构与工程方法继续作为辅助项目材料保留，但不能代替记忆插件的效果证据。

推荐按以下顺序复习：

1. **先讲本工作区项目**：读“DSH Layered Memory 项目主线”和“本工作区 Benchmark 全景图”，形成 30 秒、3 分钟和 10 分钟表达。
2. **再讲因果证据**：区分内部消融、同协议外部对照、多预算压力实验、真实 Terminal 连续任务和公开 benchmark。
3. **主动讲失败**：低压 A/C 持平、MemGym held-out 总门失败、来源蕴含缺口、temporal 误替代、空 recall 和 E5 Sidecar 内存都属于项目能力边界。
4. **最后讲下一轮**：优先选择 170K–250K 真压力任务，做短窗口 A、完整轨迹 B、插件 C 的同模型黑盒，并统计任务成功、实际 Provider token、再获取成本和跨边界稳定性。

面试时每个数字都要同时给出：实验对象、组别、上下文档位、题数、Judge、结果和不能外推的边界。报告文件生成、测试脚本通过或单题 token 下降都不单独等于效果成立。

## 本工作区项目：DSH Layered Memory 主线

### 一句话介绍

这是一个不修改 DSH 核心的外部上下文管理插件：在真实上下文压力达到 65% 后，把冷的完整对话 transaction 切成约 2K-token Parent 和约 384-token Child，从 surface 卸载到当前 session sensory，再用词法/E5 在 Child 上定位、按 source 和 coverage 选择完整 Parent 回放，从而在保留可追溯原文的同时控制模型可见上下文。

### 三十秒版本

DSH 原生 `compaction-basic` 会把长历史统一摘要，容易丢低频事实；直接保留全历史又会达到窗口和成本上限。项目把“检索粒度”和“披露粒度”分开：Child 用于定位，Parent 保存完整 user/assistant/tool 事务；压力达到门后才卸载，未达到压力时保持旁路。旧版 LongMemEval 内部归因中，原生摘要为 9/40、只保留可恢复压缩为 21/40、完整方法为 26/40；新版与 OpenViking 同协议对照中，sensory 为 27/40、OpenViking 为 21/40，同时回答链 Provider token 低 26.6%。但低压 256K A/C40 又得到 33/40 对 33/40且没有发生迁移，说明题目没有触发目标机制时只能证明非劣，不能宣传压缩收益。

### 三分钟版本

**问题。** 长窗口只是容量，不保证模型稳定利用中部历史，也不能保证 prefix cache、Provider token 和多步工具成本可控。统一摘要便宜，但低频事实、工具参数、时态更新和来源关系容易被改写或删除。

**架构。** 插件在 DSH `agent/turn-stopping` 封存完整 transaction，在 `agent/pre-step` 读取真实 token meter 和 Layer Ledger；达到约 65% 压力后，把冷 Parent 从 surface replacement 到 session sensory，目标压回约 35%。Child 同时保存词法信息和 E5 向量；Matcher 做查询分解、宽召回、Parent 聚合、source hard gate、时态和 coverage 选择。`sensory_recall` 只展示候选，`sensory_open` 展开可追溯原文。

**为什么需要多组 benchmark。** LongMemEval 测事实、跨 session、知识更新、时间和弃答；NoLiMa 测低词面重合的语义召回；MemGym-DR 测不同预算和多跳深度下 memory manager 的边际收益；256K Terminal 测真实 compaction、工具事务、迁移、来源、污染和 token 账单；Terminal-Bench 测公开任务兼容；OpenViking 对照测外部系统竞争；内存生命周期测试测 Bridge、插件 Map 和 E5 Sidecar 是否可持续运行。任何单一分数都覆盖不了这些目标。

**当前结论。** 可恢复压缩比统一摘要更能保存 answerable 事实；E5 在 NoLiMa 的低词面重合场景显著有用；Section Whole Unit 暴露了“先做一次完整单元选择，再决定是否让模型多步 recall/open”可能更经济。另一方面，多预算 MemGym held-out 总门失败、Terminal 发现来源可追溯不等于证据蕴含、256K A/C40 是低压持平，说明系统仍需要在真压力、多预算、来源正确性和再获取成本上继续收敛。

### 项目机制与证据的对应关系

| 机制 | 要解决的问题 | 必须看到的运行证据 | 主要 benchmark |
|---|---|---|---|
| 压力驱动卸载 | 不在低压时提前破坏完整历史 | 实际 Provider 输入越过 65% 门、working→sensory、surface replacement | Context Pressure、256K Terminal |
| Parent/Child | 小粒度定位与完整事务披露冲突 | Child 候选、Parent selected、tool-call/result 配对完整 | MemGym-DR、LongMemEval |
| 词法 + E5 | 同义表达与精确名称需要不同通道 | vector candidates、lexical fallback、E5 合同状态 | NoLiMa、E5/no-E5 消融 |
| source/coverage | 相关不等于可回答、单条证据不等于覆盖完整 | sourceRefs、fact recall、query-evidence entailment | Terminal 256K、MemGym |
| session scope | 全局索引会造成跨题与跨会话污染 | 独立 DSH_HOME/workspace/session/store、cleanup 后 scope 为 0 | 全部正式 A/B/C |
| 多步 recall/open | 模型可按需恢复原文，但可能放大成本 | 主请求数、工具调用、Provider token、再获取次数 | LongMemEval、Section baseline |
| 资源生命周期 | Sidecar 与 Bridge 引用可能使长跑不可持续 | working set、private bytes、最低可用内存、进程退出 | 256K AC40 memory-safe |

## 辅助项目：Code Knowledge Builder 架构与方法

### 一句话介绍

CKB 是面向代码 Agent 和工程师的多语言代码知识基础设施：它从固定 Git 快照提取完整、可追溯的代码事实，用确定性 SQLite 与图检索把自然语言任务压缩成预算内的源码入口，同时生成受控数量、简体中文、可直接导航的人类知识页。

### 三十秒介绍

未知仓库中的代码 Agent 常遇到两个问题：直接宽搜会加载过多无关上下文，而让模型自由总结整个仓库又会产生不稳定的页面归属和检索结果。CKB 用 Tree-sitter 获取统一语法结构，用语言服务器补充语义证据，把事实层、机器检索层和人类阅读层分开；分类、排序、配额、关系预算和完成门都由脚本确定，Agent 只在固定源码范围内写中文解释。查询阶段使用 FTS5、固定权重图传播和 token 预算，先定位文件与职责，再通过精确实体或源码范围命令落到函数。

### 三分钟介绍

**问题。** 大仓库里，业务意图通常不是源码符号。单纯 `grep` 对已知符号很快，但面对“修改会话停止后的记录逻辑”这类问题，工程师需要自己构造关键词、阅读很多文件并恢复调用关系；直接把全仓 Markdown 或源码交给 Agent，又会增加 token 成本和决策波动。

**核心约束。** 项目要求来源可追溯、构建可恢复、检索可重复、人类页面可读，并且活动开发不能污染长期基线。于是系统不能把“模型觉得重要”当作稳定结构，也不能用页面少来换取机器事实缺失。

**设计。** 系统先锁定干净 Git 提交和 blob/range 来源，用 Tree-sitter 抽取跨语言语法实体，用 Pyright、TypeScript Language Server、clangd 或 csharp-ls 提供语义证据；然后形成事实层 `facts/`、机器层 `machine/knowledge.sqlite` 和人类层 `human/`。完整实体和关系留在机器层，人类层只投影类、函数或职责聚合页，辅助实现进入一句中文附录。

**确定性。** 页面选择、附属实体归属、排序、配额、关系裁剪、检索权重、同分规则和审计门由脚本固定。Agent 重新打开精确源码范围，补写中文含义、职责、修改时机和来源核对，但不重新决定重要性。这样把模型不确定性限制在可审阅的叙述层。

**检索。** `fast` 使用标识符与中文词项、SQLite FTS5、固定元数据权重和有界两跳图传播；`precise` 增加固定源码全文检索和固定轮次加权 PageRank。结果严格受 token 预算和最大页面数限制，并携带源码路径与范围。精确符号任务再使用 `entity`、`neighbors` 或 `source`，而不是回到全仓宽搜。

**验证。** 截至本文记录时，自身知识库只读覆盖检查返回 31 个文件、483 个实体、1,985 条关系，483/483 实体已审阅，SQLite 完整性正常。独立的 5.1.4 冻结基准中，`machine-fast` 两轮目标源码 Recall@8 均为 100%，上下文相对 Markdown 宽扫减少 80.43%，中位延迟约 20.85–21.20 ms，零回退且跨进程结果一致；但辅助符号召回只有 16.67%，因此结论只覆盖“用较少上下文定位目标源码路径”，不等同于真实修改任务已经完成。

**取舍。** 项目不宣称全面替代 `grep`。Flask 3.1.3 的十题实验中，常驻检索与人工 `git grep` 的目标文件 Recall@8 都是 100%，常驻检索把可见上下文从 11,228 tokens 降到 2,294 tokens，中位延迟约 24.9 ms，而 `git grep` 约 73.2 ms；但精确符号召回为 40%，低于 `grep` 的 100%。推荐工作流是先用 CKB 定位文件、职责和相邻关系，再用精确符号查询或窄范围 `grep` 落点。

### 十分钟展开顺序

1. **先画边界**：输入是固定 Git 快照，输出是事实、机器、人类三层，活动工作树作为独立 overlay。
2. **再画主链路**：`detect → extract → build → cluster → review → merge → finalize`。
3. **解释两类消费者**：Agent 需要完整、预算化、来源绑定的机器检索；人类需要少页面、中文职责、明确修改与验证入口。
4. **解释确定性分工**：脚本决定结构和预算，Agent 只做精确来源上的解释与审阅。
5. **解释检索算法**：词项与锚点召回种子，固定权重排序，图扩展，预算裁剪，窄接口二次定位。
6. **解释生命周期**：分段状态、断点恢复、精确 blob 迁移、活动会话与变更记录、三重完成门。
7. **最后给数字与边界**：分别报告文件召回、符号召回、上下文、延迟、构建成本和下游任务尚未验证的部分。

## 项目问题、需求和非目标

### 要解决的问题

- 自然语言任务与源码标识符之间存在词汇差距。
- 宽范围搜索容易暴露大量无关文件和源码片段，增加 Agent token 与人工判断成本。
- 单一 Markdown 知识库难以同时满足机器完整召回和人类低认知负担。
- 让 Agent 自由决定“哪些实体重要、页面怎样归属”会导致重复构建结果漂移。
- 长构建和逐实体审阅中任一阶段失败，都可能造成大规模返工。
- 活动工作树持续变化，不能悄悄改写已经审计的固定基线。
- 会话和修改记录需要自动采集，但原始对话不能未经审阅直接进入稳定人类知识层。

### 功能需求

1. 支持 C、C++、C#、标准 JavaScript 和 Python 的代码事实提取。
2. 所有实体、关系、说明和源码范围可追溯到固定来源。
3. 支持全仓、路径范围和入口扩展三种扫描边界。
4. 构建可分段、可恢复、可审计，并在失败后只重跑必要阶段。
5. Agent 能通过自然语言获得预算内的相关页面、实体和源码入口。
6. 人类页面使用简体中文，控制数量和信息密度，并能形成修改与验证计划。
7. 可变分析、变更、实验、踩坑和会话记录能长期保留，不被生成器覆盖。
8. 自动化事件具备显式项目登记、会话级激活、脱敏、幂等和人工审阅门。

### 质量属性

| 属性 | 设计响应 | 验证方式 |
|---|---|---|
| 正确性 | 固定 commit、blob、精确 range、语义提供器证据 | 来源范围复核、关系端点审计、提供器诊断门 |
| 可重复 | 固定权重、固定轮次、固定排序、无随机采样 | 重复查询结果签名一致 |
| 可恢复 | 解析批次和审阅包独立保存 | 中断后从失败阶段继续 |
| 可读性 | 机器与人类投影分离，首屏结果优先 | 导航、关系、信息负担和冻结任务门 |
| 可维护 | 生成器只拥有清单内文件，可变笔记独立 | 镜像、元数据、双索引和策略审计 |
| 性能 | FTS5、批量 SQL、缓存、常驻 stdio、预算渲染 | P50、P95、上下文 tokens、缓存命中 |
| 可回滚 | 原始哈希、变更清单、补丁、隔离探针 | 回滚后字节与基线一致 |

### 明确非目标

- 不把任意网页、论文或对话直接当作源码实体写入固定事实图。
- 不用向量模型替代当前确定性检索，除非冻结 benchmark 证明下游质量与成本收益。
- 不把人类 Markdown 页面当作完整事实数据库。
- 不把文件召回率包装成精确符号召回或代码修改成功率。
- 不自动初始化非 Git 目录；只有用户明确选择后才建立一次初始提交。
- 不让自动化 Hook 阻塞 Harness 正常工作，也不把原始会话直接晋升为稳定知识页。

## 总体架构和数据流

```text
干净 Git 提交
    │
    ├─ 固定 blob/range 与 detached snapshot
    │        │
    │        ├─ Tree-sitter：跨语言语法实体
    │        └─ LSP：定义、引用、诊断等语义证据
    │
    ├─ detect → extract → build → cluster
    │        │
    │        ├─ facts：可重建事实与计数合同
    │        ├─ machine：完整 SQLite、FTS、关系、源码、记录
    │        └─ review packs：限定源码范围的 Agent 中文审阅
    │
    ├─ merge → finalize → 三重完成门
    │        ├─ human：保守中文知识页
    │        └─ markdown：兼容镜像
    │
    └─ retrieve / entity / neighbors / source / changes
             └─ 预算内 Agent pack 与精确源码入口

活动工作树 ──> overlay / session / change / automation pending review
```

### 三层数据职责

| 层 | 保存什么 | 为什么单独存在 | 不能替代什么 |
|---|---|---|---|
| `facts/` | 图、来源清单、审阅清单、计数合同 | 保证机器库可重建，固定审计边界 | 不能直接作为人类文档 |
| `machine/knowledge.sqlite` | 全部实体、范围、关系、证据、源码、中文章节、记录与 FTS | 为 Agent 提供完整、可查询、预算化的知识 | 不能用“完整”证明人类可读 |
| `human/` 与 `markdown/` | 受配额控制的中文页面和长期人工记录 | 降低人的阅读与导航成本 | 不能用“页面少”证明事实完整 |

### 固定基线与活动工作树

固定快照回答“这条知识基于哪一版源码”；活动工作树回答“当前正在改什么”。语义提供器始终读取 detached 基线，活动变化进入 overlay 或变更记录。这样既允许构建期间继续开发，也防止尚未审阅的修改污染完成标记。

### 构建状态机

1. `init` 完成 Git、范围、运行时和配置预检，并建立固定快照。
2. `build-chunk` 分批解析语法与语义事实。
3. `review-pack` 要求 Agent 重开指定源码范围并写中文说明。
4. `audit` 检查批次内部实体、关系、来源、中文和边界。
5. `merge` 解析跨批次关系并生成完整图。
6. `finalize` 生成机器、人类投影并执行全局完成门。
7. 只有固定事实、机器层、人类层和格式门全部通过，才写入三个完成标记。

## 基础概念速查

### 抽象语法树与 Tree-sitter

抽象语法树（AST）把源码文本转换成有层级的语法结构，例如函数、类、参数和调用表达式。Tree-sitter 是增量语法解析器，优点是多语言接口一致、容错强、适合批量提取；局限是它主要知道“语法长什么样”，不总能可靠判断跨文件符号真正指向谁。

### 语言服务器协议

语言服务器协议（LSP）把编辑器与语言语义服务解耦，可提供定义、引用、符号和诊断。CKB 使用 LSP 补足 Tree-sitter 的跨文件语义，但不会把任一提供器结果当作无条件真值；协议失败、致命诊断、合法空结果和近似模式必须分开记录。

### Git commit、blob 和源码范围

commit 固定仓库状态，blob 固定单个文件内容，range 固定声明所在行区间。三者共同形成来源证据。只存路径不够，因为同一路径在不同提交中可能表示不同实现；只存 commit 也不够，因为面试或修改定位需要落到具体文件与范围。

### 知识图谱

知识图谱用节点表示文件、类、函数等实体，用边表示定义、引用、调用、包含或测试覆盖等关系。CKB 的图用于有限关系扩展和职责群导航，不直接把完整图倾倒成人类页面。

### SQLite FTS5

FTS5 是 SQLite 的全文检索模块。CKB 对实体名、限定名、中文职责、章节和固定源码建立索引，优点是本地、可复现、易做事务与完整性检查；不足是纯词法检索仍存在同义词和精确符号歧义，需要固定词项归一、元数据权重和图关系补充。

### PageRank 与有界图传播

PageRank 根据图连接关系迭代分配重要性。CKB 的 `precise` 使用固定轮数、固定重启率和固定权重，保证同一输入产生同一结果；`fast` 则采用有界两跳传播，减少跨模块计算。两者都只是排序方法，不是正确性证明。

### token 预算

token 预算限制返回给 Agent 的可见上下文。系统先排序候选，再在预算内保留紧凑目标和必要章节；长章节超预算时截断章节，而不是静默丢掉整个目标。预算控制的是消费成本，不应改变底层事实完整性。

### Recall@8 与精确符号召回

Recall@8 表示前八个候选是否包含预先定义的相关目标。文件 Recall@8 回答“应修改的文件是否出现”，精确符号召回答“具体函数或类是否出现”。二者必须分别报告；文件召回 100% 不代表已经定位到函数，更不代表修改成功。

### P50、P95 与冷启动

P50 是中位延迟，P95 反映较慢请求的尾部体验。完整 CLI 延迟包含进程启动、数据库打开和渲染；常驻 stdio 的稳态延迟复用进程和缓存。面试中必须分别报告冷启动、首个缓存未命中和稳态请求，不能只挑更好看的数字。

### 确定性、幂等与原子性

- **确定性**：同一输入、状态和配置得到相同排序与输出。
- **幂等**：同一事件重复提交不会生成重复会话、轮次或记录。
- **原子性**：一次状态替换要么完整成功，要么保持旧状态，避免半写入。

### spool、WAL 和 checkpoint

spool 是先落盘、后处理的写前队列，用于中断恢复；WAL 是 SQLite 的预写日志模式，允许更稳健的事务与并发读取；checkpoint 把阶段进度和输入证据固定下来，避免失败后从头扫描。三者解决的层次不同，面试中不要混为一个概念。

### 投影、镜像和生成器所有权

投影是从机器事实生成面向特定读者的视图。`human/` 是人类投影，`markdown/` 是兼容镜像。生成器只替换清单中自己拥有的文件，人工分析、变更和编辑器工作区保持独立，避免重建知识库时丢失长期知识。

### canary、审计门和完成标记

canary 是小范围真实链路探针；审计门是可重新计算的验收规则；完成标记只是审计通过后的结果文件。命令退出成功、文件生成或标记存在都不单独等于任务完成，仍需核对目标行为和证据。


### Benchmark、评测对象与可证伪主张

Benchmark 不是先选一个数据集再堆指标，而是先写清楚要证伪的项目主张。CKB 至少有四类主张：能否定位正确文件、能否落到正确符号、能否用更少上下文完成真实任务、建库成本能否在多次任务中摊销。每类主张对应不同实验；文件 Recall@8 通过，只能支持第一类，不能跨级证明代码修改成功。

### Gold set、数据划分与标签粒度

Gold set 是评测前冻结的标准答案集合。代码检索题至少要标注可接受目标文件、目标符号、证据范围和允许的等价入口；端到端修改题还要标注验收测试、禁止改动范围和可接受补丁边界。调参集、验证集和隐藏测试集按问题族或仓库拆分，避免同一业务表达的改写同时出现在调参与测试中。存在多个正确入口时使用集合标签，不把唯一作者路径强行当成唯一真值。

### 组件评测、工作流评测与端到端评测

- **组件评测**：只测检索器，输入冻结查询，输出文件、符号与阅读包，主要看 Recall、排序、上下文和延迟。
- **工作流评测**：让 Agent 使用给定检索工具完成定位，观察二次检索次数、工具调用、总 tokens 和墙钟时间。
- **端到端评测**：从自然语言任务开始，以补丁、测试和禁止改动检查作为结果，衡量任务成功率、误改文件和回滚能力。

三层应形成诊断漏斗：组件失败可以直接定位检索问题；组件通过而任务失败，才继续检查提示、工具规划、源码理解和修改能力。端到端指标最接近价值，但不适合作为唯一诊断指标。

### Badcase、失败分桶与错误预算

Badcase 是在冻结协议下失败或接近失败门的样例，不是事后挑出的“模型表现不好”。先按可确定字段分桶，例如词汇差距、同名符号、跨文件关系、图枢纽噪声、token 截断、合法空 LSP、过期快照、无答案误召回、冷启动和跨题污染；再统计每桶数量、影响指标和复现条件。错误预算规定每类失败可容忍的上限，能防止总体平均值掩盖某一关键问题族完全失效。

### 黑盒、灰盒与白盒实验

黑盒实验只比较用户可见输入、工具合同和最终结果，不向执行 Agent 暴露实现分组；灰盒实验允许读取阶段指标，适合定位“召回、排序还是预算”哪一层出错；白盒实验直接做权重、关系或缓存消融。三者回答的问题不同：黑盒用于判断产品方案是否更好，灰盒用于诊断，白盒用于归因，不能把白盒微基准包装成用户任务收益。

### 配对实验、置信区间与显著性

同一道题在各方案上运行形成配对样本，可以抵消题目难度差异。二元任务成功率适合报告逐题胜负表、置信区间并在样本足够时使用 McNemar 检验；tokens、延迟和工具调用等连续指标优先报告中位数、P95、逐题差值及 bootstrap 置信区间。统计显著不等于工程上值得，因此还要预先写最小有意义改进和硬质量门。

## 核心设计方法与设计理念

### 方法一：先固定边界，再讨论智能

源码版本、路径范围、语言提供器、页面配置、token 预算和验收题集先固定，模型只在边界内工作。这样失败时能判断是来源、解析、排序、审阅还是验证问题，而不是把所有偏差归因于“模型不稳定”。

### 方法二：完整事实与低认知负担分离

机器层追求不丢事实，人类层追求只显示高价值入口。把两者做成同一个页面集合，会在“完整但难读”和“简洁但信息丢失”之间反复摇摆。三层设计把矛盾变成两个独立验收目标。

### 方法三：脚本掌握结构，Agent 掌握解释

重要性、归属、排序、配额和完成门适合确定性程序；职责解释、修改时机和关系意义需要理解源码上下文，适合 Agent。分工不是排斥模型，而是把模型放到可审阅、可追溯的部分。

### 方法四：证据先于叙事

每个项目亮点先确定输入、命令、原始记录、结果和失败门，再组织简历与面试表达。只要一个数字不能回到冻结协议和原始记录，就不应写成普遍效果。

### 方法五：任务完成优先于页面合规

中文、标签、双链和源码链接是基础门；真正的人类可读还要求读者能找到入口、理解职责、形成修改方案并找到验证路径。页面结构通过不能替代真实任务行为验证。

### 方法六：失败局部化与可恢复

解析批次、语义提供器、审阅包、合并和投影各自保存状态。失败只重跑受影响阶段；迁移只复用路径、语言、blob 和旧状态完全匹配的事实。这样控制大型仓库的时间和上下文成本。

### 方法七：默认保守，效果通过 benchmark 赢得

向量检索、更多页面、自动晋升和复杂缓存都可能改善某个局部指标，也可能引入成本和不可解释性。项目先选择本地、确定性、可审计方案；新能力必须在冻结协议下证明下游收益，再进入主路径。

### 方法八：把负面结果作为设计输入

精确符号召回不足、构建审阅成本较高、冷启动比 `grep` 慢，都不是应隐藏的缺点。负面结果直接决定二阶段符号重排、常驻进程、增量迁移和下游 Agent benchmark 的优先级。

### 方法九：配置与完成门一起版本化

页面配额、可见章节、关系预算、上下文预算和审阅包预算不是运行时随意调节的展示参数，而是构建结果的一部分。初始构建会把规范化配置复制到输出并写入状态；恢复和最终审计继续使用同一份配置。这样可避免为了让结果通过而在构建中途改变配额，也让迁移、benchmark 和回滚能够比较同一合同下的结果。


### 方法十：用分层门禁代替单一总分

先把来源完整、文件召回、符号召回和任务成功设为质量门，再比较上下文、延迟、构建成本和维护成本。只要硬质量门退化，就不允许用更快或更省 token 抵消；通过质量门后，再看成本是否达到预先定义的最小收益。这样避免人为调整权重，让一个好看的综合分掩盖关键错误。

### 方法十一：冻结协议、保留失败、一次只改一个假设

正式运行前冻结仓库提交、题集、Gold set、分组、预算、缓存状态、执行顺序、重复次数和停止条件。优化阶段保留全部 Badcase，每轮只针对一个主要根因修改，例如“文件内符号二次重排”，然后同时回放历史回归集和隐藏测试集。失败题不能因“标签有争议”被直接删除；需要更正时必须保留修订记录并重跑全部方案。

## 核心设计取舍速查

| 设计问题 | 当前选择 | 选择理由 | 代价与补偿 |
|---|---|---|---|
| 语法还是语义 | Tree-sitter + LSP | 统一多语言结构，同时补充跨文件语义 | 工具链更复杂；用提供器证据和诊断门隔离 |
| 一个知识库还是三层 | facts + machine + human | 同时满足可重建、机器完整、人类可读 | 投影一致性成本；用计数、镜像和全局审计保证 |
| 模型排序还是固定排序 | 确定性脚本 | 可复现、可回归、可解释 | 语义泛化有限；保留 Agent 中文说明和后续 benchmark |
| 向量还是 FTS5 + 图 | 当前选择后者 | 本地、低依赖、无隐藏模型排序 | 同义词与符号歧义；用词项归一、锚点、二次精确查询 |
| 全量重建还是增量迁移 | 精确 blob 复用 | 只复用字节完全相同的事实与匹配审阅 | 变更文件仍需重建；换取来源可信度 |
| 活动仓库还是 detached 快照 | 固定快照做语义根 | 基线不受开发中修改污染 | 需要 overlay 表示当前变化 |
| 自动记录还是人工记录 | 自动采集 + 人工晋升 | 减少遗漏，又不让原始对话污染稳定知识 | 增加 pending review；用检索暴露待办 |
| 更多页面还是保守页面 | 配额与附录 | 降低人类导航负担 | 细节不在首屏；机器层保留完整事实 |
| 一次性 CLI 还是常驻 stdio | 两者并存 | CLI 简单，stdio 降低稳态延迟 | 生命周期更复杂；分别验证冷启动与稳态 |
| 单一综合分还是分层门禁 | 分层质量门 + 成本向量 | 防止速度或 token 掩盖正确性退化 | 指标较多；用固定决策顺序而非临时加权 |
| 白盒消融还是黑盒任务 | 两类实验分开 | 白盒解释原因，黑盒验证用户收益 | 需要两套协议；共享同一冻结对象和证据编号 |

## 本工作区 Benchmark 设计、结果与证据边界

### 为什么这个项目必须做“组合 benchmark”

本项目同时改变上下文生命周期、记忆表示、检索、工具协议和资源进程。如果只看最终 QA 分数，无法判断提升来自压缩、检索、模型重复、工具多步读取还是 Judge；如果只看压缩率，又会遗漏事实是否被召回、Provider 是否因再获取反而多付 token、工具参数是否正确和下一阶段任务是否能继续。因此评测采用五层证据链：

1. **结构门**：消息、tool-call/result、sourceRefs、session scope、pending transition 和 cleanup 是否正确。
2. **组件归因**：去 recall、去 E5、Section、LongLLMLingua、Parent/Child rerank 分别测哪一机制。
3. **任务质量**：LongMemEval、NoLiMa、MemGym-DR 的配对分数、fact recall 和能力桶。
4. **真实压力与连续任务**：32K/256K Context Pressure、Terminal 七阶段，观察 compaction、迁移、planner、最终状态和 token 曲线。
5. **外部与公开可比性**：OpenViking 同协议对照、Terminal-Bench 官方 verifier、LongMemEval 官方格式；研究路线再接 MemoryArena、AgentLongBench 和 Mem2ActBench。

### 本工作区 Benchmark 全景图

| 证据链 | 组别与规模 | 当前结果 | 能支持的结论 | 不能支持的结论 |
|---|---|---|---|---|
| LongMemEval 内部消融 | 固定 cleaned 40题 | H0 9、仅压缩21、no-E5 25、完整26、Section27、LongLLMLingua10 | 可恢复压缩明显优于统一摘要；多步工具并非唯一好路径 | 各分支不能拼成严格逐组件累加曲线；40题不是发布级统计 |
| NoLiMa E5 消融 | 40题 | no-E5 4、完整12；配对9胜1负，McNemar p=0.0215 | E5 对低词面重合的语义召回有明显增量 | 不能外推为所有长对话都需要 E5 |
| OpenViking 同协议外部对照 | O/C 各40题 | OpenViking21，sensory27；可见峰值均值-20.1%，回答链 Provider token-26.6% | 当前 sensory 在同一 DSH 底座上质量和回答链成本同时更好 | OpenViking 约20.78M VLM记忆构建 token 必须单列；不是内部消融曲线 |
| Context Pressure | 32K held-out 12对、256K 6点 | 32K A=11/12、C=12/12；256K A=C=6/6；原生 compaction 成对避免率1.0 | 压力驱动策略可在小样本上避开原生 compaction且不降任务结果 | 小样本不等于广泛显著收益 |
| Terminal 256K Chunk-only | A/C七阶段 | A/C 7/7；C最终上下文-70.81%，峰值-33.50%，Provider token却+18.39% | 真正触发迁移后最终上下文显著缩短，工具结构和最终事实保持 | 最终上下文短不等于累计非缓存 token 更低；来源蕴含和时态仍有缺陷 |
| Parent/Child MemGym-DR | development/held-out 多预算 | held-out C−A：8K +0.1083、16K -0.0583、32K -0.0083、256K +0.0333；fact recall0.9444<0.95 | 不同预算下收益不单调；256K有小幅正增益 | `heldout.passed=false`，不能说所有档位提升 |
| LongMemEval 256K AC40 | A/C各40题 | 33/40对33/40，C胜1平38负1；最大输入116,542，迁移0 | 低压完整上下文模式下总体非劣 | 没触发169K压力门，不能证明压缩或召回收益 |
| 官方 Terminal/LongMem smoke | Terminal 2题、LongMem 2题 | Terminal A/C均2/2 strict；LongMem A/C均2/2含Gold | 公开链路、隔离和兼容性入口可工作 | LongMem输入仍46–113K、catalog0；不是32K压力分，也不是500题官方accuracy |
| 资源生命周期 | 224次内存采样等 | Node空载增量个位数MiB；E5热态约0.8GiB；复用Sidecar曾出现约65.9GiB私有提交 | 插件Node本体轻，E5与PyTorch allocator决定长跑策略 | 逐题重启是有效隔离，不是allocator根因修复 |

### 各组实验到底测什么

#### LongMemEval 内部消融

- **H0 原生摘要 9/40**：只使用 DSH `compaction-basic`，回答“统一摘要能保住多少历史事实”。
- **仅压缩 21/40**：保留压力卸载与可恢复 Parent，但移除 recall/open，测“结构化保留本身”的贡献。
- **no-E5 25/40**：保留 recall/open 和 Parent/Child，仅关闭 E5，测词法路径上限。
- **完整方法 26/40**：加入词法、E5、recall/open；旧版主请求191、工具263，暴露多步再获取成本。
- **Section Whole Unit 27/40**：零依赖、query-aware、完整 transaction 一次选择，40次主请求和663,700 Provider token，提示“先一次选择，再工具下钻”可能是更好的控制面。
- **LongLLMLingua 10/40**：当前 GPT-2/LongLLMLingua 配置与多 session 对话结构匹配较弱，不能用通用压缩器名称代替任务适配验证。

仅压缩和 no-E5 是两条独立分支：前者保留 E5 但删除工具召回，后者保留工具召回但删除 E5。21→25→26不能解释成按顺序逐组件增加。

#### 新版 sensory 与 OpenViking

O/C 使用相同 DSH 原生压缩、DeepSeek 模型、32K上限和40题。sensory 27/40、OpenViking 21/40；sensory 主要在知识更新（7/8对3/8）和弃答（4/8对0/8）领先，但在多会话和时间题各少1题。sensory 主请求102、记忆工具90，已比旧版191/263明显收敛；仍未达到理想的一题一次主请求。

OpenViking 的约20.78M VLM记忆构建 token 与两组 DeepSeek 回答链 token 分栏记录。只比较回答链会遗漏外部记忆构建成本；把两种 token 直接相加又会混合不同模型和阶段，因此报告必须同时展示。

#### Terminal 256K 为什么重要

七阶段 Terminal 任务在同一真实 session 中产生事实、工具调用、长终端输出和多轮依赖。C 发生3次 working→sensory、110个chunk、2次planner，最终请求56,359 token，对A的193,102减少70.81%；但全程 Provider input+output反而比A高18.39%。这说明项目必须同时看“最终 prompt 是否变短”和“为恢复历史累计付了多少非缓存 token”。

该实验还发现两个高价值 Badcase：selected chunk可追溯到source，不代表它回答当前query；temporal supersession 把技术讲解中的“更新为”误识别成业务事实替代。它们都不会被最终答案关键词命中率充分暴露。

#### 256K AC40 为什么只能叫低压回归门

A/C均33/40，C胜1、平38、负1，但C最大主输入116,542，只占260,096硬门约44.8%，低于插件约169,062压力阈值。working→sensory、catalog、memory retrieval plan全部为0。C还因4题空 `sensory_recall` 增加5个step和约6.48%的经济token。因此可信结论是“插件低压旁路总体非劣”，不是“256K压缩有效”。

### 评测标准如何构建

#### 第一层：硬结构门

以下任一失败，效果分数不进入正式结论：

- A/B/C不是同一题、同一顺序或同一环境；
- Provider实际输入超过声明硬门；
- 中间system消息、tool-call/result失配或未完成transition不为0；
- session/workspace/store/index未逐题隔离；
- C cleanup后仍保留本题scope或Bridge handle；
- 向量required时E5合同不匹配却悄悄回退；
- Judge只修C不重算A，或看到答案后改题/改阈值；
- prompt trace、usage、最终回复和环境状态缺失。

#### 第二层：效果门

| 维度 | 主指标 | 推荐门 |
|---|---|---|
| 任务结果 | 官方reward、测试通过、LongMem分数、最终环境状态 | C在依赖记忆的题上不低于A；发布结论需独立held-out |
| 证据保真 | fact recall、sourceRefs、query-evidence entailment、时态有效性 | source可回读只是基础；目标事实与当前query必须一致 |
| 压缩程度 | 最终/峰值可见token、messages、checkpoint/catalog数量 | 真实越过压力门后再统计；最终可见上下文目标下降≥40% |
| 再获取成本 | recall/open/planner次数、重读token、工具回合 | 任务不降时越少越好；报告每题分布和长尾 |
| Provider成本 | input、output、cacheRead、非缓存token、辅助模型token | 非缓存Provider token高于A超过10%单列为成本门失败 |
| 稳定性 | 多预算曲线、重复边界、跨进程、跨题污染 | 不能只选单一最好档位；污染和未settled transition必须为0 |
| 资源 | working set、private bytes、最低可用内存、退出回收 | 长跑不能线性增长；Sidecar隔离策略必须写入协议 |

#### 第三层：统计与冻结

- 题目是质量统计单元，同题的多次请求不是独立样本。
- A/C必须逐题配对，报告胜/平/负和能力桶，不只报均值。
- 二元成败可用 McNemar；连续token/延迟用逐题差、P50/P95和bootstrap区间。
- development用于调参；held-out一旦打开就冻结，失败后不继续围绕同一held-out调权重。
- 多预算必须同时报告8K/16K/32K/256K，不能只挑256K正值。
- 500题、MemoryArena或AgentLongBench尚未真实运行时，只能作为后续协议，不能写成已有结果。

### Badcase 集中方向与对应优化

| Badcase | 当前证据 | 根因判断 | 优化方向 | 回归检查 |
|---|---|---|---|---|
| 低压题伪装成压缩测试 | AC40最大116,542，迁移0 | contextWindow标签不等于实际Provider输入 | 选170K–250K权威题；保留260,096硬门；禁止seed finalize | 必须出现working→sensory、catalog/selected Parent和实际token曲线 |
| supporting Parent被dense distractor挤出 | MemGym题40739，top-8全distractor | 单路dense召回与top1 coverage过强 | 词法guarantee、混合rerank、source/coverage分离 | fact recall、4-hop、selected≤6与全档位分数同时过门 |
| 过度压缩Parent数量 | 固定2个Parent使fact recall 0.9208→0.7375 | 只追求token，忽略多跳覆盖 | 用边际coverage停止，不固定最小数量 | 可见token下降同时fact recall不退化 |
| 来源可追溯但不蕴含答案 | Terminal planner选错技术说明chunk | source validation只验同源，不验query-answer关系 | 增加query-evidence entailment和目标字段覆盖门 | 人工冻结Badcase与确定性字段匹配一起回放 |
| temporal误替代 | 技术文档“更新为”触发3次错误supersession | 只看更新词，没有实体/字段/时间同一性 | 实体+字段+时间+来源联合门；业务与技术讲解分型 | 8421→8521类更新必须保留最新、隐藏旧值 |
| recall/open工具过度调用 | 旧版191主请求/263工具；新版仍102/90 | 工具schema常驻、每次近6个Parent、无边际停止 | Section预选择、动态隐藏工具、按证据增益停止 | 质量不降时主请求、工具和非缓存token下降 |
| sensory为空仍调用recall | AC40 4题5个空step | 自动路径关闭但工具schema仍可见 | sensory/bank为空时不暴露工具，或显式availability | 空recall=0，低压组成本不高于A |
| 跨题/跨session污染 | 早期global index风险 | 感知索引进程全局、scope未清理 | `indexScope=session`、独立store、题后cleanup | 第二题prompt中第一题ID=0，scope/handle清零 |
| Sidecar私有提交膨胀 | 长复用曾约65.9GiB；batch4无改善 | PyTorch CPU allocator保留，不是batch大小问题 | C每题重启Sidecar；DSH最多10题；前置10GiB门 | memory-lifecycle无单调增长，停止后可用内存恢复 |
| Judge漏识别弃答 | `no mention`等曾被误判 | 规则词表不完整 | 预注册弃答同义测试；A/C统一重判；发布再加盲LLM Judge | 不按题特化，旧回复冻结后统一重算 |
| 最终context短但总成本高 | Terminal最终-70.81%，Provider却+18.39% | planner/再读取与cache破坏抵消压缩 | 分离final/peak/provider/cache/reacquisition四种口径 | C任务成功不降，非缓存token与再获取成本过门 |

### 黑盒实验如何设计

#### 推荐组别

| 组 | 定义 | 作用 |
|---|---|---|
| A：短窗口原生组 | DSH原生compaction，无持久/感知记忆 | 产品基线 |
| B：完整轨迹 ceiling | 足够长窗口或oracle保留完整轨迹 | 判断失败是否由上下文管理造成，不作为低成本产品方案 |
| C：短窗口插件组 | 与A相同窗口、模型和工具，启用当前Layered Memory | 目标方案 |
| D：Section Whole Unit | 相同任务、完整transaction一次性query-aware选择 | 低成本控制面基线 |
| E：内部消融 | no-recall、no-E5、无图/无planner等 | 白盒归因，不与主黑盒总效果混报 |

#### 必须冻结的边界

1. **模型**：provider、model、reasoning effort、system、tools、温度和max output完全一致。
2. **真实容量**：不仅写`contextWindow`，还要验证每次Provider实际input；强制出现至少一次、压缩算法实验最好两次真实边界。
3. **任务环境**：每题独立Git状态、cwd、DSH_HOME、workspace、session、storeDir和index scope。
4. **插件环境**：固定bundle、配置、E5 model/revision/dimensions/normalize；`vectorRequired`异常即退出正式分数。
5. **执行顺序**：A/B/C逐题配对、平衡或交错运行；不让一组全部冷启动、另一组全部热缓存。
6. **状态清理**：题后等待idle、dispose handle、dropSession、清scope并记录cleanup；正常3080不承载正式实验。
7. **预算与停止**：固定token、工具回合、墙钟、最低内存和总成本；到门即停，不临场加预算救某一组。
8. **裁判**：优先官方verifier/测试/环境状态；诊断Judge与盲LLM Judge分栏，方案标签对Judge隐藏。
9. **证据**：保存prompt trace、Provider usage/cache、memory transition、selected sourceRefs、最终动作和环境状态。
10. **污染**：任意题序下前题专有ID不进入后题prompt；共享只读模型缓存与可变任务记忆分离。

#### 黑盒实验的判定顺序

先看结构和污染门，再看任务成功；任务不退化后，才比较visible context、Provider非缓存token、再获取成本、延迟和内存。C若只把最终prompt缩短，却增加总非缓存token、工具回合或错误来源，就不能判为整体收益。B ceiling用于判断“理论上保留完整历史能否解决”，D Section用于判断“是否需要复杂在线工具链”，E消融用于解释哪一机制有效。

### 下一轮最小可执行协议

1. 从公开或已冻结任务中选能产生170K–250K实际Provider输入、且有后续依赖的development小样本。
2. 每题构造A/B/C/D，保持模型、工具、输出、环境和Judge完全一致；`seedFinalize=false`。
3. 强制至少两次真实边界，记录每次边界前后的Next-Action Preservation、事实覆盖和未settled transition。
4. 主门：任务/测试成功、最终环境状态、source entailment、污染0；成本门：visible context至少下降40%，非缓存Provider token不得高于A超过10%。
5. 记录再获取：额外open/read/search、planner、recall/open、重读token和墙钟；不能只记录最终context。
6. development只用于修复一个最大Badcase；新held-out打开后冻结，失败即保留，不在同一集合继续调参。
7. 通过小样本结构与压力门后，再扩MemGym多预算；随后接MemoryArena跨session行为、AgentLongBench极长轨迹和Mem2ActBench工具参数回归。

### 当前结论的严格边界

- LongMemEval 9→21→26和Section27是固定40题内部诊断，不是500题官方效果。
- sensory 27对OpenViking21是新版外部同协议对照，不能覆盖旧版内部消融。
- NoLiMa支持“E5在低词面重合场景有增量”，不支持“所有任务必须启用E5”。
- MemGym held-out总门失败，256K单档正增益不能包装成全档位提升。
- AC40 33对33是低压非劣，迁移0，不能证明压缩。
- Terminal最终context下降70.81%同时Provider token增加18.39%，必须同时报告。
- Terminal-Bench 2/2只证明公开任务兼容；单turn、目录0，不证明长期记忆。
- MemoryArena、AgentLongBench、LongMemEval-V2和Mem2ActBench是已完成选型，不是已运行效果。

## 本工作区 Benchmark 面试官连续拷问

### 第一组：为什么有这么多 Benchmark

#### 1. 为什么一个记忆插件需要这么多 benchmark，做一个 LongMemEval 不够吗？

**回答主干：** 因为项目同时改变上下文生命周期、检索、工具协议和资源进程。LongMemEval能测历史问答，却不测工具参数、最终环境状态、真实compaction、跨边界稳定性和内存泄漏。内部消融回答机制归因，Terminal回答真实压力，MemGym回答多预算，OpenViking回答外部竞争，官方benchmark回答可比性，资源测试回答能否长跑。

#### 2. 你怎样给这些 benchmark 分层？

**回答主干：** 分为结构门、组件归因、任务质量、真实压力/连续任务、外部公开可比性五层。前一层失败时，后一层分数不进入结论；例如Provider实际输入没过压力门时，A/C持平只能算低压回归，不能算压缩效果。

#### 3. 这个项目最核心的对照组是什么？

**回答主干：** A是相同短窗口下的DSH原生compaction，B是完整轨迹或oracle ceiling，C是相同短窗口加插件。A回答相对产品基线，B判断问题是否真由上下文丢失造成，C是目标方案。Section Whole Unit是低成本控制面，no-E5/no-recall属于白盒消融。

#### 4. 为什么不能只比较A和C？

**回答主干：** A/C都失败时，不知道是任务本身太难、模型能力不足，还是上下文管理失败。B完整轨迹能给出可达到上限；若B成功而A失败、C成功，才能更有力地把收益归因到上下文管理。

#### 5. Benchmark 的第一完成门为什么不是准确率？

**回答主干：** 如果两组题目、模型、Provider输入、session隔离、工具结构或Judge不一致，准确率差没有因果意义。先要求结构错误0、污染0、未settled transition0、硬cap违规0、cleanup完成，再看任务分数。

### 第二组：LongMemEval、NoLiMa 与内部消融

#### 6. LongMemEval 的五类能力分别是什么？

**回答主干：** information extraction、multi-session、knowledge update、temporal和abstention。它们分别测单事实、跨会话组合、新事实覆盖旧事实、时间顺序以及历史无答案时克制。

#### 7. H0为什么只有9/40？

**回答主干：** H0使用DSH统一摘要，主prompt短、工具为0，但低频事实和细粒度关系容易从summary中丢失。这个结果说明“压得短”不等于“保留查询所需证据”。

#### 8. 仅压缩为什么能到21/40？

**回答主干：** 它保留压力卸载和可恢复完整Parent，但移除recall/open。相对H0的提升主要证明结构化保留完整transaction比统一有损摘要更可靠，不是工具召回的贡献。

#### 9. no-E5 25/40、完整26/40说明E5没用吗？

**回答主干：** 在LongMemEval词面线索较强时，E5只增加1题，说明边际收益小；NoLiMa中no-E5为4/40、完整为12/40，配对9胜1负、p=0.0215，说明E5的价值集中在低词面重合语义召回。不能只用一个数据集判断。

#### 10. 为什么21、25、26不能画成逐组件累加？

**回答主干：** 仅压缩分支保留E5但删除recall/open；no-E5分支保留recall/open但删除E5。它们不是在同一基线顺序加组件，因而只能分别回答工具召回和向量召回的贡献。

#### 11. Section Whole Unit 27/40为什么是重要反向结论？

**回答主干：** 它不做summary、不拆transaction，只在固定预算内一次性选择完整单元，27/40且Provider token 663,700、主请求40。它说明复杂在线memory工具未必是第一选择；更合理的控制面可能是先做一次query-aware完整单元选择，证据不足时再开放工具。

#### 12. LongLLMLingua 10/40说明什么？

**回答主干：** 当前llmlingua 0.2.2加GPT-2的配置与多session对话结构匹配较弱。它不能说明LongLLMLingua普遍无效，只说明通用token压缩器仍要对本项目的transaction、工具结构和语言分布做适配验证。

#### 13. 固定40题够不够？

**回答主干：** 它适合作为中间效果门和Badcase回归，不足以支撑发布级统计。正式对外需要冻结500题官方协议或独立held-out，并保留官方evaluator/盲Judge；当前40题数字必须带样本与Judge边界。

### 第三组：OpenViking 外部对照与成本

#### 14. sensory 27/40对OpenViking 21/40可以怎样讲？

**回答主干：** 在相同DSH原生压缩、DeepSeek模型、32K上限和40题下，当前sensory多答对6题，主要领先知识更新和弃答；同时可见token峰值均值低20.1%，回答链Provider token低26.6%。这是外部同协议黑盒对照，不是内部消融。

#### 15. 这个外部对照哪里仍不完全对称？

**回答主干：** OpenViking有独立VLM/embedding记忆构建链，约20.78M VLM token；sensory使用本地E5。回答链DeepSeek token可直接并列，记忆构建成本需要分模型、分阶段报告，不能隐藏，也不能简单相加后假装同价。

#### 16. sensory主要赢在哪些能力，输在哪里？

**回答主干：** 知识更新7/8对3/8、弃答4/8对0/8；OpenViking在multi-session和temporal各多答对1题。这决定下一轮Badcase应优先检查跨会话证据覆盖和时态替代，而不是只继续优化总体分。

#### 17. 为什么主请求从191降到102很重要？

**回答主干：** 旧版完整方法靠大量recall/open得到26/40，但主请求191、工具263。新版102个主请求、90次记忆工具，说明工具链已收敛；不过距离一题一次请求仍远，因此Section预选择和动态工具可见性仍是下一步。

#### 18. 如何同时比较质量、回答链成本和记忆构建成本？

**回答主干：** 至少分三栏：最终任务质量；主模型回答链input/output/cache；记忆构建的VLM/embedding/本地CPU时间和内存。还要报告主请求数、工具调用和延迟，避免某组靠多轮查询换分却只展示最终答案token。

### 第四组：真实压力、Terminal 与多预算

#### 19. 256K AC40为什么33/40对33/40却不是压缩成功？

**回答主干：** 最大实际输入116,542，低于插件约169K压力阈值，working→sensory、catalog、planner全为0。结果只能证明低压旁路总体非劣；contextWindow写256K不表示请求真的经历压缩。

#### 20. 怎样避免“标称32K/256K，实际没压到窗口”的假实验？

**回答主干：** 记录每个Provider请求的真实input+cache、输出reserve和硬门；冻结seedFinalize=false；要求观察到阈值越过、迁移、surface replacement、catalog/selected Parent。没有这些事件就降级为结构或低压回归门。

#### 21. 为什么 `seedFinalize=true` 会造成方法学偏差？

**回答主干：** 它在真实压力未到时强制把seed历史降级为sensory，等于人为制造插件工作。正式压力测试必须由真实token meter触发，否则不能判断系统是否在正确时机迁移。

#### 22. Terminal 256K最重要的正面结果是什么？

**回答主干：** A/C七阶段都完成，C发生3次working→sensory，最终上下文从193,102降到56,359，减少70.81%，tool-call/result无孤立，最终词项保持。这是目标机制真实运行的结构和有限上下文证据。

#### 23. Terminal结果里最重要的负面结果是什么？

**回答主干：** C最终prompt虽短，但Provider input+output比A高18.39%；两次planner还选错了与query不蕴含的技术说明chunk。短上下文不自动等于低总成本或正确来源。

#### 24. 为什么source validation仍不够？

**回答主干：** 当前门能证明selected chunk确实来自原始source且内容一致，却不能证明它回答resolvedQuery。需要增加query-evidence entailment、目标实体/字段覆盖和冲突检查。

#### 25. temporal supersession出了什么问题？

**回答主干：** 技术讲解里的“更新为/改为”触发了3次误替代，真正8421→8521的业务更新没有正确进入最终目录。下一版要同时匹配实体、字段、时间、来源类型和新旧值。

#### 26. MemGym-DR为什么比单一LongMemEval更适合归因？

**回答主干：** 它固定reasoner和环境，把memory manager做成可替换接口，并能控制8K、16K、32K、256K以及多跳深度。这样能看到策略在哪个预算有帮助、在哪个预算反而干扰。

#### 27. MemGym held-out结果应该怎样讲？

**回答主干：** C−A在8K为+0.1083、16K为-0.0583、32K为-0.0083、256K为+0.0333；fact recall0.9444低于0.95，完整held-out门失败。只能说256K有小幅平均增益，不能说所有档位提升。

#### 28. 为什么宽上下文反而可能让插件收益下降？

**回答主干：** A本身已能看到更多事实，C额外Parent可能造成证据竞争、重复或生成方差；16K/32K负值说明收益不是单调函数。需要画预算—fact recall—任务分—token曲线，而不是只扩大窗口。

#### 29. 把selected Parent固定压到2个为什么失败？

**回答主干：** fact recall从0.9208降到0.7375，多跳题需要多个支持事实。正确做法是按新增coverage边际停止，而不是用固定小数量追求漂亮token。

#### 30. dense top-8全是distractor时怎么修？

**回答主干：** 保留词法guarantee，让包含明确query词的supporting Parent进入候选；再做混合rerank、source gate和coverage。修复必须同时检查各预算任务分、fact recall、4-hop和selected上限。

### 第五组：Badcase、隔离、Judge 与资源

#### 31. 当前Badcase优先级怎样排？

**回答主干：** 第一是真压力与来源正确性；第二是multi-session/temporal和多预算回退；第三是recall/open过度调用与总Provider成本；第四是跨题污染、Judge和内存生命周期；最后才是加入更复杂模型或长期bank。

#### 32. sensory为空还调用recall暴露了什么？

**回答主干：** AC40有4题、5个空step，说明自动召回关闭但工具schema仍可见，模型会无效探索。应在sensory/bank为空时动态隐藏recall/open或显式告诉可用状态，目标是低压空recall为0。

#### 33. 为什么session scope是硬门？

**回答主干：** 进程全局索引会把前题通用词、调试文本和答案带入后题，直接破坏benchmark因果性。每题必须独立DSH_HOME、workspace、session、store/index scope，题后cleanup并验证前题ID在后题prompt为0。

#### 34. cleanup具体要清什么？

**回答主干：** Bridge ownedHandles、Agent handle/session maps、session envelope和purposes；插件lastEvidence、transitions、auxiliary purposes、frozen session、workspaceTurns、lastPreStep及session sensory。只删磁盘目录而不dispose进程引用仍会泄漏。

#### 35. E5 Sidecar的内存问题是什么？

**回答主干：** PyTorch CPU allocator长复用时私有提交曾到约65.9GiB，batch从32降到4没有改善。当前有效缓解是每个C题重启Sidecar、DSH最多10题、题前至少10GiB可用内存；这是进程隔离，不是根因修复。

#### 36. Node插件本身重吗？

**回答主干：** 空载差分均值约6.61MiB，稳定样本约2.60MiB，Node侧是个位数MiB；完整资源主要由E5热态约0.8GiB工作集决定。因此公开beta应提供轻量词法/Section默认和E5增强preset。

#### 37. Judge为什么也要做benchmark？

**回答主干：** 初版漏识别`no mention`等弃答表达，导致假回退。Judge必须有独立同义表达回归、对A/C统一重判、不能按具体题加特判；对外发布再加方案标签盲化的统一LLM Judge。

#### 38. 为什么只看最终答案关键词不够？

**回答主干：** Terminal中最终词项正确，但来源依靠assistant后续重复，planner没召回原始事实；关键词Judge看不出证据链错误。必须检查selected source、最终工具参数、环境状态和query-evidence entailment。

#### 39. prefix cache为什么要单列？

**回答主干：** 动态目录、planner和多步工具可能降低cache hit。Terminal里C的cache hit低于A，虽然保守总token下降，非缓存Provider token却上升。input、cacheRead、output和辅助模型token必须分开。

#### 40. 跨题污染为0怎样证明？

**回答主干：** 不依赖目录名推断；直接检查后题最终prompt、catalog和selected source中前题专有ID出现0次，cleanup scope/handle归零，并在不同题序复验结果签名。

### 第六组：黑盒实验与下一轮

#### 41. 这个项目的黑盒实验“黑”在哪里？

**回答主干：** 执行Agent只看到相同任务和工具合同，不知道当前是A、B、C或D；裁判只读取官方测试、最终环境、回复和资源记录。内部Parent、权重和索引实现不向Judge暴露；机制归因另做E消融。

#### 42. 黑盒最少需要冻结哪些变量？

**回答主干：** provider/model/effort/system/tools、context与output、任务与Gold、Git/环境、DSH_HOME/workspace/session/store、插件bundle/E5合同、题序、预算、缓存状态、停止条件和Judge。任一漂移都可能伪造差异。

#### 43. 为什么正常3080不用于正式实验？

**回答主干：** 正常实例含真实会话、索引和用户状态，切profile会造成污染和数据风险。正式组使用独立端口、DSH_HOME和workspace；正常3080只做健康检查并保持消息数不变。

#### 44. A/B/C应该怎样交错执行？

**回答主干：** 以题为配对单元，用平衡顺序交错，避免A全冷启、C全热缓存；每题各自独立状态。内存限制下可以单组串行，但必须保留相同题序、主机条件和逐题checkpoint。

#### 45. 真实压力门怎样定义？

**回答主干：** Provider实际输入必须越过插件65%门且低于硬cap，并观察working→sensory、surface replacement、catalog/selected Parent。压缩算法实验最好强制至少两次边界，检验连续稳定性。

#### 46. 再获取成本具体包括什么？

**回答主干：** recall/open/planner次数、额外open/read/search、重读token、辅助模型token、工具回合、墙钟和cache损失。它与最终visible context是两条指标，不能相互替代。

#### 47. 怎样判定C真正优于A？

**回答主干：** 先要求结构、污染和来源门通过；在依赖记忆的任务上C成功率不低于A，再要求visible context显著下降，且非缓存Provider token、再获取和延迟不过预注册成本门。只短不对、只对但极贵都不算完整收益。

#### 48. 公开benchmark下一步怎样接？

**回答主干：** LongMemEval-V1继续做稳定QA回归；MemGym做memory manager主工程归因；MemoryArena测跨session因果行为；AgentLongBench测32K–4M动态轨迹压力；Mem2ActBench做记忆到工具参数快速门。它们当前是选型，不是已跑结果。

#### 49. 如果只能做一个下一迭代，选什么？

**回答主干：** 选170K–250K真实Provider输入的development小样本，做A原生、B完整轨迹、C插件、D Section，强制两次边界；补query-evidence entailment和动态工具可见性，统一统计任务成功、非缓存token、再获取、污染和内存。

#### 50. 面试时怎样一句话说明项目仍未完成的部分？

**回答主干：** 已证明压力卸载和Parent/Child在若干场景能保留更多事实并显著缩短最终上下文，也完成外部系统对照；但多预算held-out未全过、真压力下Provider总成本和来源蕴含仍有缺口，跨session长期晋升与公开大样本效果仍待闭环。

## 系统设计加压题

### 如果任务持续数百轮，checkpoint和catalog会不会自己膨胀？

会。Terminal和公开LongMem smoke都发现数百个checkpoint仍可能常驻prompt。下一步需要层级折叠或按需目录化：surface只保留稳定短索引，catalog按query和预算生成，原始Parent继续保存在可回查存储；同时把catalog token计入真实Provider输入门。

### 如果E5不可用怎么办？

正式向量实验使用`vectorRequired=true`，合同异常退出评分；普通产品环境可以显式进入lexical-only。不能用feature hash或零向量冒充E5，也不能把降级结果混进正式E5分数。

### 如果多个Agent并发使用同一workspace怎么办？

sensory保持session scope；可共享的semi/bank使用显式workspace记录、来源和并发控制。benchmark每题仍隔离store和session，不能为模拟产品共享而牺牲实验因果性。

### 如果模型不主动调用recall/open怎么办？

首先用确定性catalog/Section把高质量候选放到当前user之前；工具只作为证据不足时的第二阶段。评测要记录工具可见但未调用、调用为空、调用后是否新增有效coverage，不能把“有工具”当作“工具发挥作用”。

### 如果C准确率提高但成本翻倍，是否上线？

按预注册效用决定。默认门是任务不退化后比较成本；若非缓存Provider token高于A超过10%，作为独立成本失败。可以提供E5增强preset，但轻量默认应优先Section/词法路径，并向用户公开资源和延迟。

## 个人贡献与第三方边界

### 可以表述的个人贡献

- 设计压力驱动的working/sensory/semi/bank层级与DSH hook生命周期；
- 实现完整transaction封存、Parent/Child、surface replacement、Layer Ledger和session cleanup；
- 设计词法/E5混合召回、source/coverage选择、时态和弃答边界；
- 建立A/B/C、内部消融、外部OpenViking、MemGym多预算、Terminal真实压力和内存安全benchmark；
- 将Provider prompt trace、tool结构、memory transition、token/cache、污染和回滚纳入验收；
- 主动保留held-out失败、低压非劣、来源蕴含、temporal和Sidecar内存等负面结果。

### 必须明确的第三方能力

- DSH提供event log、surface、hook、token meter和原生compaction；
- E5提供预训练文本向量能力，PyTorch/Sidecar提供运行时；
- LongMemEval、NoLiMa、MemGym、Terminal-Bench提供数据或任务协议；
- OpenViking是外部记忆系统对照；
- McNemar、bootstrap等是通用统计方法。

个人贡献是架构组合、DSH适配、确定性边界、工程实现、实验协议和证据链，不表述为从零训练E5、发明LongMemEval或实现DSH核心。

## 简历与口述模板

### 三条式项目描述

1. 为DSH实现外部压力驱动上下文管理插件，在65%上下文压力后将完整对话事务切分为Parent/Child并从surface卸载到session sensory，通过词法/E5与source/coverage恢复原始证据，不修改DSH核心。
2. 建立LongMemEval、NoLiMa、MemGym-DR、256K Terminal、OpenViking外部对照和内存生命周期组合评测；旧版内部归因从原生摘要9/40提升至完整方法26/40，新版同协议sensory为27/40、OpenViking为21/40，sensory回答链Provider token低26.6%。
3. 用真实prompt trace验证compaction、working→sensory、tool-call/result、污染和token/cache；发现多预算held-out未全过、Terminal最终上下文虽降70.81%但Provider token增18.39%，据此推进来源蕴含、动态工具可见性和再获取成本优化。

### 数字使用规则

- 9/21/25/26/27属于旧版内部40题不同分支，不能与新版O/C当作单一时间序列；
- sensory27对OpenViking21必须同时说同协议、40题和VLM成本分栏；
- 70.81%是Terminal最终请求上下文减少，同时报告Provider token+18.39%；
- 33对33必须说低压、迁移0、只证明非劣；
- MemGym必须说held-out总门失败和各预算正负值；
- 公开Terminal 2/2是兼容smoke，不是长期记忆效果。

## 面试前自检

- 能解释每个benchmark对应哪一机制，不能用一个总分覆盖全部问题；
- 能画出A/B/C/D/E组及其因果角色；
- 能说明实际Provider输入与标称contextWindow的区别；
- 能同时报告任务分、最终context、非缓存Provider token、cache和再获取；
- 能解释LongMemEval、NoLiMa、MemGym和Terminal为什么不能互相替代；
- 能主动说出AC40低压、MemGym held-out失败、来源蕴含和temporal误替代；
- 能解释session隔离、cleanup、Sidecar逐题重启和10GiB内存门；
- 能区分已运行结果与MemoryArena/AgentLongBench等后续选型；
- 能给出下一轮170K–250K、两次真实边界的最小协议。

## 证据导航

- 本工作区主报告：`E:\deepseek_memory\knowledge-bases\sensory-memory-plugin\human\analysis\DSH Layered Memory：秋招面试拷问准备手册.md`
- 当前状态：`E:\deepseek_memory\research\41-notice-for-codex.md`
- 连续任务benchmark选型：`E:\deepseek_memory\research\49-agent-context-continuity-benchmarks.md`
- 256K AC40低压回归：`E:\deepseek_memory\results\important-tests\longmemeval-s-256k-ac40-hardcap-20260827-01\final-report.md`
- Terminal 256K：`E:\deepseek_memory\results\important-tests\terminal-256k-chunk-vector-20260824-01\03-important-benchmark-report.md`
- Parent/Child多预算：`E:\deepseek_memory\results\important-tests\parent-child-rerank-256k-complete-20260825-01\03-final-report.md`
- 压力驱动上下文：`E:\deepseek_memory\results\important-tests\context-pressure-agent-v1-20260825-01\03-final-report.md`
- 公开benchmark正式smoke：`E:\deepseek_memory\results\important-tests\official-benchmarks-formal-20260826-01\03-formal-test-report.md`

## 相关知识页

- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[render_integration 与 _looks_windows 的协作实现]]
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]]
- [[deploy 的协作边界]]
- [[build 的协作边界]]
- [[ingest_event 与 default_registry_path 的协作实现]]
- [[finalize 与 _replace_output_prefix 的协作实现]]
- [[load_page_config 与 _merge_known 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1715`
- [打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-536`
- [打开源码：scripts/ckb_core/obsidian_plugin.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian_plugin.py:1:1)  `scripts/ckb_core/obsidian_plugin.py:1-262`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1665`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3482`
- [打开源码：scripts/ckb_core/page_config.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/page_config.py:1:1)  `scripts/ckb_core/page_config.py:1-244`
