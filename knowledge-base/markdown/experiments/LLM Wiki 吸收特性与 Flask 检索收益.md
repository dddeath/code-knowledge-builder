# LLM Wiki 吸收特性与 Flask 检索收益

标签：#类型/实验

## 结论

Code Knowledge Builder 吸收了 LLM Wiki 的“先编译知识、再检索知识、把回答回写到 Wiki、持续审计图谱健康”方法，但没有直接复制其页面结构或非确定性 Agent 行为。CKB 将这些方法改造成来源绑定的代码知识系统：完整事实进入机器 SQLite，保守中文页面供人阅读，查询通过分节 FTS5、确定性词项和有界图扩展生成 token 预算内的 Agent pack，分析和实验再通过 `record` 回链知识页。

这些特性对速度的作用需要分开判断。FTS5、批量物化、缓存和预算裁剪直接缩短检索时间；双知识库、Obsidian、持久记录和可读性审计主要改善上下文成本、维护一致性与任务完成能力，不应被写成纯延迟优化。常驻 stdio 也不是 LLM Wiki 原始特性，它是让已经优化的确定性检索引擎在真实 Harness 会话中避开 Python 冷启动的 CKB 运行时扩展。

## 归因边界

### 从 LLM Wiki 吸收的方法

- 把原始事实编译成可查询 Wiki，而不是让 Agent 每次重新阅读全部材料；
- 以查询为入口，按问题选择少量高相关页面或章节；
- 用双链、反向链接和索引维持 Wiki 导航；
- 把回答、实验和人工反馈写回知识库；
- 对悬空链接、孤立页面、覆盖缺口和页面形状执行持续审计；
- 将 Markdown/Obsidian 作为人类可直接浏览和修订的知识界面。

### CKB 的来源约束扩展

- 固定 Git commit、blob、路径和源码范围；
- Tree-sitter 与语言服务器构建代码实体和语义证据；
- 全事实机器库与保守中文人类库分离；
- 页面数量、附录、关系和 token 预算由确定性脚本控制；
- Agent 逐实体重开源码范围并审阅中文说明；
- 分段构建、迁移复用和三重完成标记。

### 不归因于 LLM Wiki 的独立能力

- Graphify 的职责群和图聚类；
- C/C++、C#、JavaScript、Python 的 Tree-sitter/LSP 适配；
- Git 固定快照、分段恢复和语义完成门；
- 跨 Harness Hook 协议；
- 常驻 JSONL stdio 进程。

## 已吸收特性清单

| 特性 | CKB 中的落地 | 对检索或任务的作用 |
|---|---|---|
| 编译式知识库 | `facts`、`machine/knowledge.sqlite`、`human` 三层 | 查询读取已编译事实，避免重复扫描全部源码和 Markdown |
| 查询优先入口 | `retrieve --profile fast|precise` | 先按任务缩小到少量实体、页面和源码范围 |
| 分节全文索引 | `entity_fts`、`section_fts`、`source_fts` | 直接命中职责、修改时机、来源说明和源码片段 |
| 确定性词项 | `terms` 表、中文三元词、标识符锚点 | 不依赖向量模型，重复查询保持相同排序 |
| 有界图扩展 | fast 两跳传播、precise 固定轮次 PageRank | 从词法种子补充调用、引用和测试邻居 |
| 预算化阅读包 | `machine/agent-packs` | 将可见上下文限制在任务预算内，并保留可复查证据 |
| 批量物化和缓存 | 固定 overscan、两次批量 SQL、静态实体/章节/关系缓存 | 消除 N+1 SQL 和重复 Windows 路径解析 |
| 双知识库 | 完整机器 SQLite 与保守中文 Markdown/Obsidian | Agent 保留完整召回，人类避免实体页面爆炸 |
| Wiki 双链与源码链接 | 双链、反向链接、`vscode://file` | 人可以从职责页跳到关联页和精确源码位置 |
| 持久回答与反馈 | `record` 的 analysis/change/pitfall/experiment/session | 查询后的结论回链知识页并进入两个 SQLite 索引 |
| 图谱与页面健康审计 | 链接、孤立页、中文、标签、来源、镜像和可读性门 | 防止页面存在但不可发现、不可理解或不可追溯 |
| 增量维护 | exact-blob 迁移复用、保留用户笔记、重建索引 | 代码升级时复用可信事实和说明，避免从零重建全部人类知识 |
| 持久 Agent 协议 | `AGENTS.md`、Claude/Gemini/Copilot/Cursor 指令 | 让进入项目的 Agent 先检索再读源码，并通过 `record` 维护知识 |

## 关键特性的详细作用

### 编译式机器知识库

LLM Wiki 的核心方法是把材料预先编译成可查询的知识结构。CKB 将代码事实写入 `machine/knowledge.sqlite`，其中包含实体、源码范围、关系、审阅说明、章节、固定源码、人类页归属和持久记录。查询不需要重新解析源码，也不需要宽扫整个 Markdown vault。

这项能力主要减少重复读取和上下文，而构建成本在 `finalize` 前支付。它适合多次查询同一仓库，不应把一次性构建成本隐藏在查询指标之外。

### 分节 FTS5 与确定性词项

每个实体被拆分为中文含义、职责、修改时机、来源说明和有界源码片段；人类笔记按 Markdown 标题拆分。`entity_fts` 检索实体叙述，`section_fts` 检索高相关章节，`source_fts` 只在 precise 档位补充固定源码全文。

标识符、限定名、路径和中文词项同时进入固定权重排序。同分使用稳定 ID，fast 和 precise 的传播轮数、上限、折扣与同分规则全部固定，因此不存在隐藏模型调用或随机排序。

### Agent pack 与上下文预算

检索器先限制候选 overscan 窗口，再批量读取实体和章节，只为最终结果生成源码链接。每个结果获得固定预算；章节过长时截断章节而不是跳过高分实体。这样既保留目标文件，又避免把整页或整文件装入 Agent 上下文。

### 双知识库与 Obsidian

机器层保留全部实体和关系；人类层只生成类、函数或职责聚合页，并把访问器、局部辅助函数和薄包装收进附录。Markdown 页面使用少量类型标签、自然标题、双链、反向链接和可点击源码位置，`markdown` 与 `human` 保持镜像。

这项特性主要降低人的认知负担，不直接承诺毫秒级加速。其效果需要通过导航任务、跳转次数、目标页面命中和验证入口命中来评价。

### 持久回答、反馈与审计

分析、修改、踩坑、实验和会话通过 `record` 写入，必须使用简体中文并回链至少一个知识页。写入后同时刷新兼容 Agent 索引和机器知识索引。页面、元数据、双层镜像、SQLite 完整性和链接都进入审计。

这形成“查询—分析—记录—再检索”的闭环，使知识库能积累经过来源核验的工程结论，而不是只保存一次性聊天内容。

### 批量物化与静态缓存

5.1.2 的首轮实现存在逐候选 SQL、重复路径解析和预算耗尽后仍继续渲染的问题。后续吸收快速 Wiki 查询思路，把 fast 候选限制为固定窗口，实体与章节改为两次批量 SQL，源码链接按路径缓存，并复用实体元数据、章节和关系图。

在原自身知识库冻结十二题上，machine-fast 中位延迟从 5.1.2 的 1,783.6 ms 降到 5.1.3 的 25.3 ms，目标源码 Recall@8 从 50% 提升到 100%。这组数据反映检索器改造本身，但语料不是 Flask，因此不用于 Flask 速度结论。

## Flask 3.1.3 的同轮量化结果

为隔离主机负载差异，常驻 stdio 与 `git grep` 在同一轮、相同十题、相同执行顺序规则下交错测量。stdio 接收中文自然语言任务；grep 使用每题四组预先冻结的人工关键词。两者输入能力不同，因此速度和上下文可比较，符号召回只用于说明边界。

| 指标 | 常驻 stdio + 机器知识库 | `git grep` |
|---|---:|---:|
| 正式请求数 | 70 | 70 |
| 中位延迟 | 24.9 ms | 73.2 ms |
| P95 延迟 | 47.6 ms | 86.3 ms |
| 目标文件 Recall@8 | 100% | 100% |
| 精确目标符号召回 | 40% | 100% |
| 确定性 | 100% | 100% |
| 回退率 | 0% | 0% |
| 可见上下文中位数 | 2,294 tokens | 11,228 tokens |

在这组 Flask 数据上：

- 常驻机器检索中位速度是 grep 的 2.94 倍；
- 中位延迟减少 65.9%；
- P95 减少 44.8%；
- Agent 可见上下文减少 79.6%；
- 目标文件 Recall@8 保持 100%；
- 精确符号召回仍低于人工关键词 grep，因此知识库适合先定位文件、职责和相邻关系，再用窄范围符号查询落到具体函数。

### stdio 在结果中的作用

一次性 `ckb.py retrieve` 会为每个请求重新启动 Python。在同一 Flask 十题复测中，一次性 CLI 中位往返为 321.6 ms，而常驻 stdio 为 23.5 ms，速度提升 13.71 倍。stdio 不改变 LLM Wiki 检索算法，只消除重复进程启动并让静态知识缓存持续命中。

因此，对 Flask 的速度结论应拆成两层：FTS5、词项、批量物化和图扩展构成约 25 ms 的确定性检索引擎；常驻 stdio 让 Harness 能直接使用这个引擎速度，而不是每次支付完整 CLI 冷启动成本。

## 完成判据

“吸收 LLM Wiki”不能以功能名称存在为完成。每项能力至少需要满足：

1. 有明确源码实现和用户入口；
2. 有固定输入、输出和失效边界；
3. 有确定性测试或审计门；
4. 对速度、上下文、可读性或维护性的作用分别测量；
5. 负面结果和未覆盖指标继续保留；
6. 页面和记录能从两个 SQLite 索引再次检索；
7. 变更具备可执行回滚。

## 当前边界

- Flask 速度提升是在本机、固定知识库和冻结十题内确认，不外推为所有仓库的统一倍数。
- grep 使用人工关键词，机器知识库使用自然语言任务；符号召回差异不能只归因于索引算法。
- stdio 当前未自动绑定 Harness SessionStart/SessionEnd，调用方仍需管理进程。
- 人类可读性、任务完成率和真实代码修改成功率需要独立任务集，不由延迟数据替代。
- Tree-sitter/LSP、Graphify、Git 来源门和 stdio 是 CKB 的独立扩展，不写成 LLM Wiki 原生特性。

## 可复查证据

- Flask 同轮 stdio/grep 协议：`E:\knowledge_builder\evaluations\llm-wiki-absorbed-features-20260829\flask-speed\protocol.json`
- Flask 同轮结果：`E:\knowledge_builder\evaluations\llm-wiki-absorbed-features-20260829\flask-speed\summary.json`
- Flask 正式记录：`E:\knowledge_builder\evaluations\llm-wiki-absorbed-features-20260829\flask-speed\formal-records.jsonl`
- 常驻 stdio 复测：`E:\knowledge_builder\evaluations\flask-3.1.3-stdio-benchmark\summary.json`
- 5.1.2 首轮基准：`E:\knowledge_builder\self-workspace\work\llm-wiki-retrieval-benchmark\summary.json`
- 5.1.3 优化复测：`E:\knowledge_builder\self-workspace\work\retrieval-optimization-5.1.3\benchmark\summary.json`
- 5.1.4 独立进程复验：`E:\knowledge_builder\self-workspace\work\llm-wiki-retrieval-revalidation-5.1.4\verification.json`

## 延伸阅读

- [[常驻 stdio 检索性能复测（Flask 3.1.3）]]
- [[Flask 3.1.3 知识库与 grep 对比测试（秋招版）]]
- [[LLM Wiki 快速检索性能复验（5.1.4）]]
- [[知识库人类可读性与任务完成标准]]

## 相关知识页

- [[audit_obsidian 与 prepare_vault 的协作实现]]
- [[audit_migration 与 _entity_key 的协作实现]]
- [[package_showcase 与 _parse_sample 的协作实现]]
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]
- [[initialize 与 _replace_output_prefix 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[query_graph 与 _networkx_modules 的协作实现]]
- [[record_note]]
- [[keyword_provider_config 与 parser 的协作实现]]
- [[sync_human_layer]]
- [[module_name 与 estimated_tokens 的协作实现]]
- [[MigrationTest 等测试场景]]

## 源码入口

- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：scripts/ckb_core/showcase.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/showcase.py:1:1)  `scripts/ckb_core/showcase.py:1-173`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/graphify_core.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/graphify_core.py:1:1)  `scripts/ckb_core/graphify_core.py:1-676`
- [打开源码：scripts/ckb_core/workspace_notes.py 第 106 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/workspace_notes.py:106:1)  `scripts/ckb_core/workspace_notes.py:106-183`
- [打开源码：scripts/ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:1:1)  `scripts/ckb.py:1-495`
- [打开源码：scripts/ckb_core/knowledge_layers.py 第 126 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:126:1)  `scripts/ckb_core/knowledge_layers.py:126-181`
- [打开源码：scripts/ckb_core/navigation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/navigation.py:1:1)  `scripts/ckb_core/navigation.py:1-456`
- [打开源码：tests/test_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:1:1)  `tests/test_migration.py:1-194`
