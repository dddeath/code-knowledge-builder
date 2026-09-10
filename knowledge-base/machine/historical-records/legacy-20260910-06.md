# 自动同步与 LLM Wiki 后续待办

标签：#类型/分析

## 状态

待办 1 已在 5.1.0 完成；待办 2 已在 5.1.3 完成确定性优化并通过原冻结协议全部七项门；待办 3 仍处于后续工作范围。

## 待办事项

1. **会话与修改自动化更新（已完成）**
   - 为已登记项目接入会话生命周期与代码修改事件，使会话开始、每轮结论、修改内容、修改原因、验证结果和踩坑记录能够自动进入机器知识库。
   - 自动记录先进入可去重、可恢复的机器层队列；经过中文说明与来源审阅后，再提炼到人类知识库，避免把原始逐轮对话直接扩张为大量 Markdown 页面。
   - 验收重点包括项目级启用、轮次幂等、敏感信息过滤、中断恢复、索引更新和人类投影审计。

2. **验证已合并的 LLM Wiki 快速检索对性能的提升**
   - 为已经吸收的快速检索能力建立固定基线和可重复 benchmark，对比合并前路径、当前确定性 SQLite 检索以及宽范围文本搜索。
   - 同时测量检索延迟、读取页面数、上下文 token、目标页面与源码定位召回、重复读取成本，以及实际分析或修改任务的成功率。
   - 只有可重复验证记录达到预先冻结的质量与成本门槛后，才把性能提升写成已确认结论。

3. **继续吸收剩余的 LLM Wiki 功能**
   - 建立“已吸收、待吸收、明确排除、需要 benchmark”功能矩阵，逐项核对编译、查询、反馈审计、知识维护和阅读入口等能力。
   - 每项候选功能先封闭输入、输出、依赖、许可证、数据边界和完成门，再按小批次整合，并为人类可读性、机器检索、中文叙述及回滚补齐测试。
   - 优先吸收能降低 Agent 检索成本、改善知识维护闭环且不会显著增加页面数量的能力；其余能力保留为有证据的后续候选。

## 相关知识页

- [[start_session]]
- [[retrieve_machine]]
- [[record_note]]

## 源码入口

- [打开 `retrieve_machine`](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:942:1)  `scripts/ckb_core/machine_knowledge.py:942-1315`
- [打开源码链接缓存](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:17:1)  `scripts/ckb_core/source_links.py:17-81`
- [打开 Agent 笔记维护](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:70:1)  `scripts/ckb_core/agent_maintenance.py:70-142`

## 后续补充

### 待办 1：已完成

会话与修改自动化更新已在 `code-knowledge-builder` 5.1.0 中落地。实现采用项目显式启用、统一事件协议、递归脱敏、原子写前队列、SQLite 幂等归并、修改路径核对和 Agent 中文审阅后晋升；未审阅的逐轮对话只保留在机器层。

兼容范围已覆盖 Codex、Claude Code、OpenCode 稳定版、OpenCode V2、DeepSeek Harness 和通用 Harness。六种适配器均完成静态校验与 Windows canary，外层 Git 中的未跟踪项目也已通过有界子树状态测试，Codex companion plugin 已安装启用；后续新任务在 Harness 信任配置生效后自动进入机器层队列。

验收证据包括三十项完整回归、十二项自动化专项测试、并发与重放测试、敏感信息脱敏、失败队列恢复、机器检索、人类投影审阅、发行包完整性、真实安装和隔离回滚。详细设计与结果见 [[跨 Harness 会话与修改自动同步实现]]。

### 待办 2：已完成首轮验证，整体性能门未通过

已在 5.1.2 自身知识库上冻结十二个修改定位问题、三种检索路径、2400 token 预算、一次预热和九次重复，共执行三百二十四条正式测量。当前 `machine-fast` 相比 Markdown 宽扫描代理减少 76.67% 的 Agent 可见上下文，并保持零回退和完全确定性；目标源码 Recall@8 为 50%，中位延迟为 1,783.58 ms，召回和延迟门未通过。

性能剖析显示，候选渲染阶段重复生成源码链接和解析 Windows 路径，单次查询触发 376 次源码链接生成、1,883 次路径解析和 877 次 SQLite 执行。后续先实施固定 overscan、源码 URI 缓存、批量章节查询和紧凑目标保留，再复用完全相同的协议与阈值重测。详细协议、结果和决策见 [[LLM Wiki 快速检索性能验证（5.1.2）]]。

## 后续补充

### 待办 2：确定性优化与原协议复测已完成

5.1.3 保持原先十二个问题、三种路径、2400 token 预算、一次预热、九次重复和七项阈值不变。`machine-fast` 的目标源码 Recall@8 达到 100%，可见上下文相对 Markdown 宽扫描减少 77.28%，中位延迟为 25.29 ms，P95 为 45.36 ms，零回退且九次重复完全确定；相对人工宽扫中位延迟加速 1.075 倍。七项冻结门全部通过，待办 2 现已完成。

实现采用固定 overscan、批量 SQL、源码路径与静态检索上下文缓存、紧凑目标保留、中文三元词项、元数据固定加权和无测试意图时的测试实体折扣。所有判别均由确定性脚本执行，向量模型继续留在后续独立 benchmark。详细结果见 [[LLM Wiki 快速检索性能验证（5.1.3）]]。

## 后续补充

### 待办 2：5.1.4 独立复验通过

在当前 5.1.4 Skill 与现有完成态知识库上，沿用原十二个问题、三条检索路径、2400 token 预算、一次预热、九次重复和七项阈值，执行了两个独立进程、共 648 条正式测量。`machine-fast` 两轮目标源码 Recall@8 均为 100%，Agent 可见上下文相对 Markdown 宽扫描减少 80.43%，中位延迟为 20.85–21.20 ms，P95 为 29.70–31.86 ms，相对宽扫描加速 1.124–1.160 倍；零回退且跨进程结果签名完全一致。

七项冻结门两轮全部通过，确认当前确定性快速检索在目标源码定位、上下文成本和引擎延迟三个维度均优于宽范围 Markdown 扫描。辅助符号召回为 16.67%，且本轮没有执行真实模型代码修改任务，因此结论不外推为符号检索最优或下游修改成功率已经提高。详细结果见 [[LLM Wiki 快速检索性能复验（5.1.4）]]。

## 后续补充

## 剩余 LLM Wiki 功能的完成判断

待办三已按代码知识库边界完成。`compile` 已对应固定快照分段构建和双投影，`query` 已对应 SQLite 检索、常驻 stdio 与分析回链，`lint` 已覆盖来源、实体、链接、中文、镜像、索引、协议和反馈审计，`audit` 已加入定位式反馈、严重程度、四类决议、开放列表和不可删除的归档历史。

通用 `raw ingest` 不进入源码事实层，因为它不具备固定 Git blob 与源码范围证据；本地 Web 查看器和 Obsidian 反馈入口保持接口兼容，统一调用反馈命令，不在核心 Skill 内维护另一套渲染、存储或锚点判别逻辑。该边界避免页面膨胀、来源混淆和重复实现。

## 后续补充

## 检索词项改进待办（2026-09-01）

- [ ] **改进中文检索词项。** 当前 `search_terms` 对连续中文保留整段并机械生成二元组、三元组，能提供确定性子串召回，但会产生“包不满”“回的检”一类不自然片段。后续实现应保留可复现和可审计特性，建立固定中文问题集，对比分词前后的实体命中率、首屏相关性、误召回、延迟与索引增量；没有通过对照门前，不替换当前默认路径。
- [ ] **加入 LLM 关键词备选慢路径。** 仅在确定性 `fast`、`precise` 与窄图检索证据不足时显式启用，由 LLM 输出结构化关键词、显式代码锚点和查询改写，并把输入问题哈希、模型配置、关键词结果、耗时、成本和回退原因写入机器验证记录。默认路径保持离线确定性；慢路径必须具有超时、失败回落、隐私边界、缓存和固定问题集质量/成本验收，不能把模型生成词项写成源码事实。

## 后续补充

## 三项并行待执行队列（2026-09-01）

本队列并行度固定为 3，三个任务均从 integration branch `codex/reference-ingest-v1` 的提交 `2d1ddc4…` 创建独立分支和 worktree。用户已授权：开发任务完成后由知识库管理 Agent读取完整 diff、结构化交接和真实测试，独立复查全部合并门；通过后按固定顺序自动合并，并在合并后重新运行受影响完整测试、最小同步稳定知识库和执行 `maintain`。开发任务自身不合并，也不修改稳定知识库。完整任务标识保存在机器队列验证记录中，不进入人类知识页。

1. **中文检索词项改进**：分支 `codex/chinese-retrieval-tokenizer`，worktree `E:\knowledge_builder\self-workspace\worktrees\chinese-retrieval-tokenizer`。状态：运行中。
2. **LLM 关键词备选慢路径**：分支 `codex/llm-keyword-slowpath`，worktree `E:\knowledge_builder\self-workspace\worktrees\llm-keyword-slowpath`。状态：运行中。
3. **LLM Wiki 剩余 benchmark 特性吸收**：分支 `codex/llm-wiki-remaining-absorption`，worktree `E:\knowledge_builder\self-workspace\worktrees\llm-wiki-remaining-absorption`。处理 `semantic-vector-retrieval`、`pdf-web-ocr-extraction`、`automatic-page-fanout` 三个候选；三个长期明确排除项保持不变。状态：运行中。启动时两次 Windows 输出编码解析失败，第三次按实际编码读取后继续，已判定为临时问题。

自动合并顺序固定为：中文检索词项 → LLM 关键词慢路径 → LLM Wiki 通过 benchmark 的特性。每次合并前重新确认 integration tree 干净、分支来源明确、开发 worktree 干净、小批次 commit、无无关文件、正负例和完整回归真实通过；每次合并后重新测试。三个分支结束后，根据最终源码变化选择最小 reindex、migrate、局部重建或 record，同步稳定知识库并通过全部维护门。

阻塞判定规则：文件锁、超时、rate limit、测试偶发、进程残留、暂时服务或下载不可用属于临时问题，保留同一分支和 worktree并续跑；缺少用户凭据或政策选择、许可证不明确、固定验收门冲突、不可接受的数据边界，或连续三次同一阻塞且没有新进展，属于永久问题。永久问题通过工作记录和 research gap 留下证据，清除半成品生产代码，暂时关闭并归档对应 Codex 任务，保留分支/worktree等待用户决策。

## 后续补充

## 自动管理范围扩展为五项（2026-09-01）

此前独立派发的 **C++ pinned parser 与 SCons 修复**、**任意 Agent 对话绑定管理 Agent** 两项任务现纳入同一自动监控、阻塞分类、独立审计、自动合并和稳定知识库同步队列。队列管理对象由三项扩展为五项；原三项开发波次的并行度仍为 3，不为满足该数字而暂停已经运行的既有任务。

C++ parser/SCons 分支已完成开发并保持干净，当前状态为等待管理 Agent独立审计；管理 Agent将重新读取完整 diff、commit、真实 clangd exact/bounded/fatal-negative 和完整回归证据，独立复验通过后才合并。对话绑定管理 Agent分支仍在运行，已报告管理专项、自动化、核心和发行共七十三项回归通过，正在隔离 fixture 上执行 bind、context、status、task create/review/status、unbind 和 audit 的真实端到端验证。

自动合并顺序更新为：C++ parser/SCons → 对话绑定管理 Agent → 中文检索词项 → LLM 关键词慢路径 → LLM Wiki benchmark 吸收。五项任务共用既有临时续跑与永久关闭规则；任一任务永久暂停时保留分支和 worktree等待用户决策，其余独立任务继续审计。五项全部达到已合并或永久暂停后，才进入最终稳定知识库 staging、切换和回滚验证。

## 后续补充

## 高优先级待办：Agent 会话级 stdio 常驻与自主释放（2026-09-01）

**优先级：高。状态：已登记，等待方案确认；尚未创建开发分支、worktree 或 Codex 任务。**

当前 `serve --stdio` 已提供可常驻的本地 JSONL 服务，但通用 Agent 对话没有会话级进程所有者。Agent 直接执行 `brief`、`retrieve` 等命令时，每次仍启动独立 Python 进程，只有 Obsidian companion 等已实现生命周期接管的宿主能实际复用常驻 stdio。因此，本待办的目标不是再增加一个 stdio 服务，而是让 Harness 会话在激活 CKB 后自主创建、复用并释放一个属于该会话和知识库输出的 stdio 子进程。

验收范围：

1. 会话激活并绑定知识库时，Harness 只创建一个 `ckb.py serve --out OUTPUT --stdio` 子进程；同一会话后续 `brief`、`retrieve`、`record` 和窄读取请求复用该进程，不再为每次检索启动 Python。
2. 会话关闭、显式解绑、Harness 正常关闭、父进程终止、stdin EOF 和服务致命错误均进入确定性释放路径；先发送 `shutdown` 并等待固定期限，超时后终止子进程，最终核验 PID、管道、计时器和待决请求已经清除。
3. 进程所有权按“Agent 会话 + 知识库输出”隔离；不同会话不共享可变检索状态，不把某次 `record-explanation` 的 retrieval ID 暴露给其他会话。
4. 当前 `serve_stdio` 的 `retrievals` 会随检索请求持续保留。本任务必须引入有界容量和生存期，并在解释记录成功、请求失效或会话结束时释放；同时清空客户端 pending map、缓存引用、stderr 缓冲和事件监听器。
5. 建立重复会话和长会话压力测试，记录 RSS、私有字节、句柄数、子进程数、缓存项和 pending 请求数；冻结允许波动阈值，验证高水位后回落且不存在随轮次单调增长、孤儿进程或僵尸进程。
6. 启动、握手或传输失败时允许显式退回现有逐命令 CLI 路径，但必须返回回退原因和计数，不能把高延迟回退伪装成 stdio 命中。
7. 验收必须包含真实 Harness 生命周期：同一对话至少连续执行多次检索并证明 PID 不变，随后关闭对话或 Harness 并证明 PID 退出；单元测试、直接调用 `serve_stdio` 或静态进程检查不能替代该证据。
8. 回滚入口应关闭会话级 stdio 接管、释放仍存活的子进程并恢复逐命令 CLI 路径，不改变知识库数据、Agent Protocol 或既有 Obsidian stdio 生命周期。

该任务依赖“任意 Agent 对话绑定管理 Agent”的会话所有权和解绑语义。进入开发时应以该依赖通过管理审计后的 integration HEAD 为基线，并优先占用下一可用开发槽；现有运行任务不在本次登记中被中断。

## 后续补充

## Tag 导航与 Agent 证据治理调研待办（2026-09-01）

**优先级：普通。状态：已进入研究待办队列；先完成现状审计、数据模型和固定 benchmark，再决定开发范围。尚未创建开发分支、worktree 或 Codex 任务。**

### 当前事实和设计边界

当前人类知识库的 tag 只承担页面类型：代码、职责、边界、分析、变更、实验、会话、学习、资料和导览。代码页、职责页、边界页及正式记录均要求恰好一个 `#类型/...`；readability、全局审计和工作记录审计会拒绝缺失、重复或类型错误的页面。机器知识库 `documents.tag` 也只保存一个类型字符串，当前没有独立 tag 注册表、候选状态、页面多标签关系、Agent 支持/反对证据或 tag 生命周期。

新研究不得削弱“每页恰好一个类型 tag”契约。建议把语义导航放入独立命名空间，例如 `#主题/...` 或 `#导航/...`：`#类型/...` 继续由生成器唯一决定，语义 tag 可以有多个，但只有通过机器层审计并进入 `confirmed` 状态的 tag 才投影到 human/markdown。候选、争议、已拒绝和已废弃 tag 保持机器可查，不进入普通页面正文。

### 研究目标

1. 评估从实体、关系、模块、工作记录主题和阅读路径中确定性生成候选 tag，并在机器层建立 tag 到 entity、document、section、page 的多对多映射。
2. 评估 Agent 阅读文档后通过受控命令提出新 tag、支持已有 tag或反对已有 tag；Agent 只提交结构化建议和来源证据，不直接编辑生成页面。
3. 设计由自动化脚本执行的 tag 状态机：`proposed → collecting → confirmed | rejected | deprecated | superseded`。
4. 以固定导航问题集比较“现有 INDEX/WIKI/双链入口”和“加入确认 tag 后的过滤/聚合入口”，测量首个相关页面耗时、打开页面数、Recall、Precision、重复浏览、tag fanout 和人类主观负担。
5. 限制可见 tag 数量、层级深度和页面 fanout，避免把机器分类全部下沉为人类标签，形成另一套实体清单。

### 机器层候选模型

调研至少比较以下机器对象：

- `tag_definitions`：稳定 tag ID、规范名称、命名空间、说明、父 tag、状态和版本；
- `tag_assignments`：tag 与 entity、document、section、human page 的候选或确认关系；
- `tag_evidence`：源码范围、章节、关系或正式记录中的来源证据；
- `tag_votes`：Agent、会话、目标文档、`support`/`oppose` 决策、中文理由、证据范围和时间；
- `tag_audit_runs`：阈值配置、输入集合、计数、状态迁移、投影变化和回滚信息；
- `tag_aliases`：同义名、重命名和 superseded 关系，避免平行拼写形成重复导航入口。

投票需要按 Agent 会话、目标文档和证据范围去重，同一会话重复提交不累计支持数。支持和反对都必须包含可重新打开的章节或源码证据；只提交 tag 名称不进入有效计数。

### 自动确认、拒绝和废弃规则的调研要求

阈值由固定 benchmark 冻结，不在调研前凭直觉写死。自动脚本至少同时考虑：

1. 独立支持会话数和独立目标文档数；
2. 反对数量、反对比例和是否存在来源冲突；
3. tag 覆盖页面数、命中精度和最大 fanout；
4. tag 是否与现有类型、标题、模块名或其他 tag 重复；
5. 加入 tag 后导航 benchmark 是否改善；
6. 连续多个审计周期没有有效分配、没有导航命中或收益退化；
7. 页面或来源变化后原证据是否仍可定位。

状态相等、证据不足或支持/反对冲突时保持 `collecting`，不由脚本随机选择。`confirmed` 需要满足最小独立证据、覆盖和导航收益门；`rejected` 需要明确反对证据或确定性重复；`deprecated` 适用于曾经确认但连续审计失去覆盖或收益的 tag；`superseded` 用于已由规范 tag 或父子结构替代的名称。

### Agent 接口与投影边界

候选命令形态纳入调研，不作为本轮已确认 CLI：

```text
tags propose
tags vote --decision support|oppose
tags list --status proposed|collecting|confirmed|rejected|deprecated
tags audit
tags project
tags rollback
```

`tags propose` 和 `tags vote` 写入机器层并返回证据 ID；`tags audit` 只按冻结配置计算状态迁移；`tags project` 只投影 confirmed 集合，并保持 human/markdown 字节一致；`tags rollback` 按一次审计批次撤回 tag 定义、分配和投影。Agent 对生成器页面的直接改写不作为接口。

### 验收门

- 现有 `#类型/...` 唯一性、页面数量和人类可读性门保持通过；
- candidate/rejected/deprecated tag 不出现在普通人类页面；
- confirmed tag 的 human/markdown 集合与机器 `tag_assignments` 完全一致；
- 同一会话重复投票、缺证据投票和过期来源证据具有失败样例；
- 设计固定的最小支持/反对条件、冲突保持规则和状态迁移测试；
- tag 确认与废弃全部写入 operation journal，并提供按审计批次执行的回滚；
- 固定 benchmark 证明导航效率改善，同时满足页面 tag 上限、全局 tag 上限和 fanout 上限；
- 新接口进入 `brief/retrieve`，使 Agent 能按 confirmed tag 检索，但默认代码实体、章节和源码检索结果不退化；
- 最终运行 Agent Policy、中文、链接、镜像、工作记录、reference、gap、operation journal、双 SQLite、readability 和 `maintain`。

### 队列关系

本项先作为研究/设计待办，不占用当前三个开发槽，也不改变现有五项自动合并顺序。实现阶段与 `llm-wiki-remaining-absorption` 中的页面 fanout 和人类导航规则存在交叉，因此应在该分支完成管理审计后，以最新 integration HEAD 重新冻结设计和允许修改路径。若研究发现 tag 改善没有达到固定导航收益门，则保留机器层候选和审计证据，关闭人类投影部分。

## 后续补充

## 追加中心与低版本双层批量迁移加入八项队列（2026-09-01）

用户已确认低版本知识库升级同时覆盖两层：一项只升级 Agent Protocol、Harness 适配器、managed block 和 output contract；另一项迁移完整知识库 state、facts、graph、双 SQLite、人类镜像及全部可变知识层。两层拆成独立任务，避免协议投影更新与源码图谱重建形成同一大批次。

用户同时确认“向既有知识库追加新中心”作为独立任务加入原五项自动管理队列。队列由五项扩展为八项，开发并行度仍为 3，原五项合并顺序和已运行任务保持不变；三个新增任务在原五项达到 merged 或 paused-permanent 后，从当时最新 integration HEAD 创建分支、独立 worktree 和正式交接 Prompt。

### 任务六：既有知识库追加新中心

目标是提供正式的中心扩展接口，在隔离 staging 中计算“旧 entries 与新增 entries 的并集”，默认保留全部旧中心，复用未变化 blob 和兼容审阅，只为新增范围生成 delta review。任务必须输出 retained、added、removed 的 entry、源码路径、实体、关系和页面差异；正常追加时 removed 集合为空。工作记录、reference、research gap、学习笔记、feedback、automation、Agent Protocol 和用户 Obsidian 状态全部进入保留门。

失败样例覆盖中心零匹配或多匹配、重复新增、未跟踪源码、范围重叠、旧中心丢失、页面配额退化、staging/cutover/rollback 失败。同一输入重复运行必须幂等；原中心和新中心检索、双 SQLite、human/markdown、readability、status、maintain 与回滚探针全部通过后才具备合并资格。

### 任务七：低版本 Agent Protocol 批量升级

目标是通过显式 manifest 或项目登记表批量升级多个知识库的协议层，不重建固定源码图谱。接口覆盖 plan、dry-run、apply、status、audit 和 rollback，识别源/目标协议版本、OUTPUT、workspace roots、Python 与 CKB 路径，并为每个知识库提供独立结果和恢复入口。

升级只修改 CKB 管理的协议记录、内部适配器、workspace managed block 和 output contract，保留用户自有内容。必须包含未知旧版本、重复 managed block、路径越界、部分批次失败、并发升级、幂等和回滚后的失败样例；每项最终通过 `agent-policy check` 和 `maintain`。

### 任务八：低版本完整知识库批量迁移

目标是批量迁移 state、facts、graph、review、human、markdown、Agent Protocol、reference、research gap、operation journal、`agent-index.sqlite` 和 `machine/knowledge.sqlite`。迁移由显式 manifest 驱动，为旧 Schema/CKB 版本建立支持矩阵和版本链；不兼容跨度进入 delta review、冷构建或待用户决策，不放宽来源与完整性审计。

每个知识库保留独立基线并在隔离 staging 中执行 plan、apply、resume、status、audit、cutover 和 rollback。一个输出失败不覆盖其他输出；最终逐库验证完成标记、检索、双 SQLite、human/markdown、readability、reference、gap、operation journal、Agent Policy、maintain 和回滚。该任务复用协议批量任务的 manifest 和批次状态骨架，但保持独立命令与验收。

### 自动管理顺序

自动合并顺序扩展为：C++ parser/SCons → 对话绑定管理 Agent → 中文检索词项 → LLM 关键词慢路径 → LLM Wiki benchmark 吸收 → 追加新中心 → Agent Protocol 批量升级 → 完整知识库批量迁移。前项永久暂停时按既有规则保留证据并允许独立后项继续；新增任务同样执行临时续跑、连续三次同阻塞转永久暂停、独立 diff/测试审计、普通 merge、合并后完整复测和最终稳定知识库 staging 同步。

高优先级 stdio 生命周期待办和 Tag 导航研究待办保持独立 backlog，不因八项队列扩展而改变状态。本轮只完成队列、任务合同、自动化范围和知识记录更新，尚未为三个新增任务创建分支、worktree 或 Codex 任务。

## 后续补充

## 三项 LLM Wiki benchmark 审计结论

管理任务已独立审阅 `codex/llm-wiki-remaining-absorption` 的三个分离提交、30 个变更路径、固定报告、依赖与许可锁、生产接线边界和回滚证据，并使用锁定 Windows runtime 重跑三个门控专项、核心、Harness、迁移和发行测试。

三项候选均保持“需要 benchmark”，本分支暂时关闭且不合并：

- `semantic-vector-retrieval`：30 分钟固定时间内本地索引没有完成，索引期间人类 Markdown 语料发生变化，部分索引质量比较无效；完整索引、同一冻结语料、质量/上下文和成本门失败。
- `pdf-web-ocr-extraction`：PDF 与网页来源、页码、字符范围、表格和代码保真通过；OCR 普通文本字符错误率为零，但代码缩进保真为零，因此统一保真门失败。
- `automatic-page-fanout`：扩散前后六项查找成功率均为 100%，导航步数和可见上下文没有改善，页面增加 3 个，因此人类查找收益门失败。

开发分支只保留隔离 benchmark 模块、fixture、锁文件、报告和负例测试。`scripts/ckb.py`、默认机器检索、reference ingest、导航、pipeline、功能矩阵和发行入口均未修改，三项 `production_wiring` 均为 `absent`。三项现有 research gap 继续保持 open，不将固定门失败解释为生产能力完成。

管理复验字面结果为：三个专项各 `Ran 2 tests ... OK`，核心 `Ran 33 tests ... OK`，Harness `Ran 22 tests ... OK`，迁移 `Ran 1 test ... OK`，发行 `Ran 3 tests ... OK`。页面扩散 benchmark 已完整重跑并再次只失败人类查找收益门。OCR 隔离依赖在开发任务完成后按清理清单删除；管理任务重新打开已提交报告、原始命令、许可与哈希锁、fixture 摘要和事务回滚结果，没有重新下载已清理依赖或重复执行长时间向量索引。

完整审计位于 `E:\knowledge_builder\artifacts\verification\llm-wiki-remaining-absorption\management-audit.json`。分支和 worktree 作为可复查证据保留，等待用户以后决定是否以新的冻结语料、OCR 代码布局策略或更困难的人类查找任务重新 benchmark。

## 后续补充

## 第二开发波次已派发

前五项队列现为 4 项已合并、1 项因三个固定 benchmark 门失败而暂时关闭；满足后续派发条件。管理任务从当时最新且干净的 integration HEAD 创建两个独立分支和 worktree，并以并行度 2 启动两个同项目 Codex 任务：

- `codex/knowledge-scope-center-extension`：实现既有知识库追加新中心，要求旧中心保留、新中心唯一解析、scope 并集、精确 blob 与审阅复用、delta review、双 SQLite/镜像、真实 cutover 和并发安全回滚。
- `codex/agent-protocol-batch-upgrade`：实现低版本 Agent Protocol 批量升级，要求显式 manifest、多旧版本矩阵、managed block 用户内容保护、多库部分失败、幂等续跑、逐库审计和字节级回滚。

两个任务都已绑定独立 worktree、完整交接 Prompt、允许/禁止路径、失败样例、锁定 Windows runtime 测试和“禁止自行合并或同步稳定知识库”边界。管理任务保留最终独立审计与自动 merge 责任。`knowledge-base-batch-migration` 继续等待这两个前置任务均完成或永久留痕后再派发。

## 后续补充

## 第三开发波次已派发

“既有知识库追加新中心”和“低版本 Agent Protocol 批量升级”已完成管理任务独立审计、审计缺口修复、合并后完整回归和知识库留痕。前者关闭顺序 cutover 控制链二义性，后者关闭活 owner stale lock 抢占；两个分支均以普通 merge 保留独立 commits。

依赖门满足后，管理任务从最新且干净的 integration HEAD 创建 `codex/knowledge-base-batch-migration` 和独立 worktree，并启动“低版本完整知识库批量迁移”同项目 Codex 任务。交接 Prompt 已固定显式 manifest、真实历史版本矩阵、兼容迁移/delta review/cold build 三路径、多库部分失败与续跑、48 条工作记录、1 个 reference、3 个 open gap、两份学习笔记保留、三类完成标记、检索、双 SQLite、镜像、readability、Agent Policy、maintain、逐库 cutover 和链式 rollback 门。

该开发任务不得自行合并、删除 branch/worktree 或同步稳定知识库。完成后仍由管理任务独立复查和自动 merge；只有第八项完成或永久留痕后，才对最终 integration HEAD 执行稳定知识库 staging 同步与切换。

## 后续补充

## 高优先级 stdio 生命周期已确认并派发（2026-09-01）

用户已确认该能力进入正式开发队列。固定语义是：普通会话不启动 CKB stdio；同一 Harness 会话第一次真实调用 `code-knowledge-builder` Skill 并发出首个 CKB 请求时，才惰性创建 `serve --stdio`，后续同会话与同一知识库输出复用一个健康进程；一轮 `turn.stop` 不结束生命周期。

任务或会话结束、显式终止或取消、management unbind、Harness 正常关闭或 Harness 父进程死亡时，生命周期所有者必须确定性释放子进程、读写管道、pending 请求、reader、timer、listener、会话映射和缓存引用。关闭使用有界的 `shutdown -> terminate -> kill` 升级并等待回收；失败时显式回退逐命令 CLI，不把回退报告为常驻成功。验收还要求并发首调 single-flight、真实 PID 复用与父死亡探针、50 次会话循环的 RSS/句柄压力门、安装包 canary 和隔离回滚。

该项已作为九项队列的第九项派发：基线 `d0ca8704…`，分支 `codex/agent-session-stdio-lifecycle`，独立 worktree `E:\knowledge_builder\self-workspace\worktrees\agent-session-stdio-lifecycle`，并已创建专用 Codex 开发任务。其依赖的 conversation management Agent 已合并并通过管理审计。当前状态仅为开发中；实现、压力门、审计、合并和最终稳定知识库同步尚待实际证据。

## 后续补充

## 最终源码与知识库 GitHub 推送门（2026-09-01）

用户已确认：九项开发任务完成管理审计与实际合并、合并后回归通过，并且最终稳定知识库在隔离 staging 完成同步、切换和回滚探针后，把最终 integration 源码与切换后的稳定知识库一并推送到 GitHub。该动作是队列终态发布阶段，不提前推送开发中分支或未通过维护门的知识库。

发布沿用既有“同一私有 GitHub 仓库”边界，SQLite 与 ZIP 使用 Git LFS。稳定知识库的发布范围包含 human/markdown 镜像、facts、机器 SQLite、兼容 SQLite、工作记录、reference、research gap、operation journal 和审计元数据；排除其他 worktree、构建下载缓存、临时 migration/publish staging、活动锁、运行时进程状态、原始敏感事件和凭据。

当前本地事实是：integration 源码仓库没有 Git remote，也没有 tracking branch；稳定知识库不是独立 Git 仓库；工作区顶层是无提交且包含大量无关未跟踪开发数据的 Git 初始化目录。因此最终发布必须从 final integration commit 创建隔离 allowlist staging，再加入已通过全部门的稳定知识库，不在工作区顶层执行整树暂存。

终态推送前仍需唯一确定 GitHub `owner/repository` 和目标分支。远端未配置不影响当前开发、审计、合并和知识库同步，只阻塞最终 push。推送门还要求敏感信息扫描、LFS 指针与对象、非 fast-forward 风险、远端旧 tip、非强制推送和推送后 fresh clone 复核；远程回滚使用新 revert commit 或恢复分支，不重写公开历史。

## 后续补充

## stdio 生命周期首轮管理审计退回修复（2026-09-01）

开发任务已提交六个独立 commit、结构化交接、锁定 Windows runtime 测试、压力探针和回滚证据，但管理任务没有直接采用其完成结论。独立复查确认变更路径和提交边界正确、交接时工作树干净、普通首次激活可以创建并复用 stdio，所有本轮执行过的关闭探针最终活动进程和对象计数均为零；同时发现三个尚未通过的门，因此当前不允许合并。

第一，同一 `harness + session_id + OUTPUT` 执行 `activate -> close -> 立即 activate` 时，第二轮可能先读到上一代 `lease.json` 的 closed 状态，把旧 `close_reason` 误判为本次启动失败并返回逐命令 CLI fallback。该行为违反“相同外部会话标识的新生命周期必须在首次精确 Skill 调用直接常驻，且不复用旧 PID 或缓存”的固定边界。

第二，`_write_lease` 的临时文件名叠加 PID、线程 ID 和完整 UUID，会放大 Windows 生命周期根路径；在项目内较长但有效的管理验证路径中，controller 因临时路径创建失败而退出，常驻能力只能安全降级。需要缩短原子写临时名或固定并测试精确路径预算。

第三，开发任务原 E2E 把 `brief-1` 计入 PID 复用证据，但该请求实际因不完整 fixture 的 `local-openers.json` 缺失而返回 `ok=false`。需要使用有效 schema 1 opener 重新执行普通 `brief` CLI 的会话自动路由，并把业务请求真实通过纳入断言，不能用“同 PID 但请求失败”代替检索通过。

上述问题属于可在原任务、原分支和原 worktree 修复的审计缺口。管理任务已把完整复现证据和修复门发回原 Codex 任务，状态恢复为 active；要求增加同一外部 ID 连续重建、长根、有效 brief/entity/turn.stop/session.end 正例，重跑完整 suite、50 次压力、父死亡、打包副本和隔离回滚。批量知识库迁移任务继续并行，不受该退回影响。

## 后续补充

## 完整知识库批量迁移首轮管理审计退回修复（2026-09-01）

开发任务已提交七个独立 commit，并自报完整专项、双历史版本 E2E、回归、patch 重放、归档复开和 rollback 检查通过。管理任务重新核对分支来源、变更路径、交接时干净状态和验证记录后，使用锁定 Windows runtime 构造畸形 manifest，发现两个会使已接受计划突破边界或失去回滚能力的缺口，因此当前不允许合并，也不使用该分支迁移稳定知识库。

第一，`origin.records` 当前只检查是否包含固定八项，却允许额外键。管理探针加入 `../outside-secret.txt` 及其真实 SHA-256 后，`plan` 仍返回 ready，并实际把 OUTPUT 外文件纳入 origin record 摘要。这违反“固定八个关键记录”和 OUTPUT 读取边界。运行时验证和 JSON Schema 必须要求键集合与固定八项完全相等，并在读取或哈希前拒绝额外键、绝对路径、`.`、`..` 和非规范路径。

第二，manifest 允许 `backup_root` 与 `quarantine_root` 完全相同。cutover 和 rollback 对同一 operation/project 使用相同叶名；成功 cutover 后旧 OUTPUT 已占用该目标，rollback 的 quarantine 目标随即冲突。因此当前 plan 可以接受一个无法执行回滚的恢复拓扑。只读 plan 阶段必须拒绝同项目恢复目标冲突、恢复根与任何生产 OUTPUT/staging 的包含关系，以及会覆盖其他项目生产或迁移路径的跨项目组合。

两个缺口均已由管理探针以 exit 5 复现，完整结果写入独立审计记录。问题可在原任务、原分支和原 worktree 修复；管理任务已把精确证据和新增失败样例要求发回原 Codex 任务，状态恢复为 active。修复后必须重跑完整专项、真实双历史 E2E、scope extension、Agent Protocol batch、CKB core、automation、incremental migration、package release、patch replay、归档复开和 rollback check。stdio 生命周期审计修复任务继续并行。

## 后续补充

## stdio 生命周期管理审计缺口已闭合并等待合并（2026-09-01）

原任务已在同一分支新增独立修复 commit。管理任务没有直接采用自报结果，而是在锁定 Windows runtime 下重新执行失败探针和完整回归，确认首轮审计的三个问题均已闭合。

同一 `harness + session_id + OUTPUT` 现在使用逐次唯一 generation 绑定启动结果，不再把上一代 closed lease 误判为新启动失败。管理复测在同一外部会话标识和较长项目内路径上连续完成十轮 `activate -> 真实 brief -> close -> 立即 activate`：十轮 activation 和 brief 全部常驻通过，无 fallback，server PID 与 generation 每轮唯一，最终活动进程和全部对象计数为零。

Windows lease 原子写临时名已缩短，并增加明确目录路径预算。此前触发临时文件创建失败的管理路径现已通过十轮真实生命周期。超过预算时返回结构化 fallback，不在 controller 中留下进程或半写 lease。

管理任务还使用当前 Codex 会话环境变量重新验证普通 CLI 自动路由：第一次精确 activation 后，普通 `brief`、`entity`、`turn.stop` 后的第二次 `brief` 均实际 `status=passed` 并复用同一 server PID；`session.end` 后 PID 退出，audit 的 active 和所有对象计数为零。旧 E2E 中请求失败但计入 PID 的证据已被有效 schema 1 opener 的新证据替代。

独立重跑结果为：stdio 生命周期 12 项、CKB core 37 项、automation 22 项、management Agent 18 项、package release 3 项全部通过；50 次压力、父死亡、lite 包 canary 和隔离回滚证据重新打开通过。该分支现为 `completed-awaiting-merge`，仍按队列顺序等待完整知识库批量迁移先通过审计和合并；当前尚未修改 integration 源码或同步稳定知识库。

## 后续补充

## 完整知识库批量迁移合并后布局回归退回修复（2026-09-01）

首轮 manifest 缺口修复经管理探针验证后，管理任务按队列顺序执行普通 merge并保留开发 commits。合并后的真实 integration HEAD 随即运行完整回归；真实双历史版本 E2E 在启动阶段失败，因此该 merge 尚未被标记通过，也没有开始稳定知识库迁移或同步。

失败不是迁移数据门本身，而是测试入口硬编码了独立 worktree 的父目录布局。`tests/e2e_knowledge_batch_migration.py` 和版本矩阵测试把 Git common dir 固定计算为 `ROOT.parents[1] / source / .git`；在独立 worktree 中该路径恰好存在，但在 integration checkout 中解析到错误的 `E:\knowledge_builder\source\.git`，`git archive` 返回“not a git repository”。这证明开发分支测试启动成功不能替代合并后运行。

管理任务已把 integration 失败命令、exit status 和完整 stderr 发回原 Codex 任务，要求使用 `git -C ROOT rev-parse --git-common-dir` 或等价确定性方法同时兼容普通 checkout 与 Git worktree，并在两种布局中重跑版本矩阵和双历史 E2E。当前 integration 保留已合入 commits 以便继续执行其他只读回归，但任务状态恢复为 active；只有新 fix commit 合入且全部 post-merge suites 通过后，才把第八项标记 merged并继续第九项合并。

## 后续补充

## 检索契约与增强效果待办（2026 年 9 月 4 日）

以下四项已进入待执行队列，本次仅登记，不启动开发或扩展建库范围。

### 无自动协议注入时的契约完整性

检查 Harness 不自动注入 `AGENTS.md`、但加载了 CKB Skill 时，是否仍能确定知识库位置、先检索再读源码，并正确处理反馈、来源新鲜度和证据不足。对照 Skill、参考文档与实际调用结果，区分约定存在和约定生效；另列 Skill 也未加载的入口缺口。

### 范围外检索的扩库确认

检索未取得足够证据，且明确证据表明目标位于尚未展开的源码范围时，向人类说明拟追加范围并询问是否扩展知识库。零命中、运行错误或索引过期不直接触发扩库；人类确认后复用已有追加中心流程，不影响已覆盖范围的正常读取。

### 研究缺口汇总与证据对账

当前登记共七项研究缺口，其中五项开放、两项已关闭。开放项涉及向量检索相对收益、真实 LLM 关键词调用效果、真实环境的 Tag 导航、PDF／网页／OCR 提取，以及 Canvas 可视化收益。逐项对照后续实现和实验，确认哪些仍缺证据、哪些已有结果待更新、哪些需要人类决定。

### 新增特性的增强效果

清点当前已合并特性，明确各自相对哪种旧实现或无特性路径进行比较，复用已有实验，只补测缺少的证据。分别评价功能收益、任务质量、检索与导航效率、延迟和资源成本；真实模型调用与固定回放、隔离样例与实际使用分开。最终逐项说明已证实增强、仅功能可用、无增益或退化、证据不足，不把功能测试通过等同于效果提升。
