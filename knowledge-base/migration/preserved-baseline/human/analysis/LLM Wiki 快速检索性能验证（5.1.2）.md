# LLM Wiki 快速检索性能验证（5.1.2）

标签：#类型/分析

## 结论

本轮在固定源码提交和完成态自身知识库上执行了三路径确定性 A/B/C 基准。当前 `machine-fast` 已确认具备显著的 Agent 可见上下文压缩、零回退和完全确定性，但目标源码召回与延迟门均未通过，因此本轮不把“已合并的 LLM Wiki 快速检索带来整体性能提升”写成已确认结论。待办 2 的状态应保持为“已完成首轮验证，需先优化再复测”。

## 冻结协议

基准在看到结果前固定了十二个未知修改定位问题、三种路径、2400 token 预算、最多八个结果、一次预热和九次重复，共形成 324 条正式测量。三种路径分别是：

1. `manual-wide-scan`：原 LLM Wiki 先读索引、宽扫描 Markdown、读取高分页面并跟随一跳链接的纯确定性代理；每次实际重读全部 Markdown，不计模型推理时间。
2. `legacy-page-sqlite`：兼容 `agent-index.sqlite` 的页面级 exact、terms、FTS5/trigram 和一跳图路径。
3. `machine-fast`：当前 `machine/knowledge.sqlite` 的实体与章节 FTS5、确定性词项和固定权重两跳图传播。

正式语料包含七十六个 Markdown 文件、六十七个人类页面、四百六十七个实体和一千八百九十九条关系。首轮预检发现宽扫描计时错误地复用了设置阶段缓存；该轮已经归档并标记不参与结论，查询与阈值保持不变，正式轮改为每次实际重读文件。

## 结果

| 路径 | 中位延迟 | P95 延迟 | 目标源码 Recall@8 | 符号召回 | 可见上下文中位数 | 结果数中位数 |
|---|---:|---:|---:|---:|---:|---:|
| Markdown 宽扫描代理 | 41.91 ms | 51.34 ms | 100% | 不适用 | 10,049 tokens | 8 |
| 旧页面级 SQLite | 58.38 ms | 81.38 ms | 50% | 41.67% | 2,370 tokens | 2 |
| 当前 machine-fast | 1,783.58 ms | 2,270.19 ms | 50% | 25% | 2,344.5 tokens | 3 |

当前路径相对于 Markdown 宽扫描代理减少了 76.67% 的 Agent 可见上下文，超过预先固定的 40% 门；十二个问题均未触发 grep fallback，九次重复的结果签名全部一致。但当前路径只定位到六个预设目标源码，低于 90% 召回门，也低于宽扫描代理的十二个目标；其中位延迟约为宽扫描代理的 42.56 倍，P95 也超过 200 ms 绝对门。相对于旧页面级 SQLite，当前路径的上下文只再减少约 1.08%，目标源码召回没有提高，而中位延迟约增加到 30.55 倍。

七项门中，零回退、完全确定性和上下文压缩三项通过；目标召回、不得低于宽扫描、P95 绝对延迟和相对加速四项未通过。最终状态是 `mixed`，不是整体性能提升。

## 性能剖析

对失败查询执行的 `cProfile` 显示，一次 `retrieve_machine` 调用总计约 1.792 秒：

- `source_markdown_link` 被调用 376 次，累计约 1.098 秒；
- 路径解析调用 1,883 次，累计约 0.920 秒，其中 Windows `_getfinalpathname` 约 0.806 秒；
- SQLite `execute` 被调用 877 次，累计约 0.579 秒。

主要原因不是 FTS5 本身，而是排序后渲染阶段对大量候选逐个生成源码链接、重复验证本地路径，并逐实体查询章节。阅读包达到预算后，循环仍会继续考察后续候选；许多候选在生成链接和读取章节之后才因预算不足被跳过。该路径同时存在明显的 N+1 SQL 和 Windows 路径解析放大。

召回不足与预算分配也有关。当前实现会让测试实体、相邻模块或较短实体占据有限阅读包；较长但更相关的目标实体在剩余预算不足时会被直接跳过，而不是保留紧凑摘要。例如 Hook 行为、页面索引、知识层同步、源码链接、页面配置和 Tree-sitter 解析六类任务没有把预设实现文件纳入最终阅读包。

## 后续优化顺序

1. 在进入渲染前把候选限制为固定 overscan 窗口，例如前 32 个，并对实体、来源范围和高分章节使用批量 SQL，消除逐实体查询。
2. `local-openers.json` 和仓库根路径只验证一次；对同一源码路径缓存 URI，避免每个候选重复执行 `resolve` 和 `_getfinalpathname`。
3. 为最高分目标预留紧凑区块；当完整区块超过剩余预算时保留职责、修改时机和源码位置，而不是跳过该目标。
4. 对实现定位问题增加确定性的文件名、限定名和职责词权重，并对测试实体施加固定折扣；不引入向量模型或隐藏排序调用。
5. 修复后复用本轮完全相同的协议、查询和阈值。只有七项门全部通过，才更新待办 2 为完成。

## 结论关联

- [[retrieve_machine]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]
- [[自动同步与 LLM Wiki 后续待办]]
- [[跨 Harness 会话与修改自动同步实现]]

## 性能热点源码

- [打开 `retrieve_machine`](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:734:1)  `scripts/ckb_core/machine_knowledge.py:734-936`
- [打开源码链接实现](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:89:1)  `scripts/ckb_core/source_links.py:89-142`
- [打开兼容页面检索](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:440:1)  `scripts/ckb_core/agent_index.py:440-569`

## 可复现证据

- 协议：`E:\knowledge_builder\self-workspace\work\llm-wiki-retrieval-benchmark\protocol.json`
- 原始结果：`E:\knowledge_builder\self-workspace\work\llm-wiki-retrieval-benchmark\raw-results.json`
- 汇总：`E:\knowledge_builder\self-workspace\work\llm-wiki-retrieval-benchmark\summary.json`
- 性能剖析：`E:\knowledge_builder\self-workspace\work\llm-wiki-retrieval-benchmark\machine-fast-profile.txt`
- 验证记录：`E:\knowledge_builder\self-workspace\work\llm-wiki-retrieval-benchmark\verification.json`

## 相关知识页

- [[retrieve 与 _tokens 的协作实现]]
- [[audit_migration]]
- [[package_showcase 与 _parse_sample 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
- [打开源码：scripts/ckb_core/migration.py 第 353 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:353:1)  `scripts/ckb_core/migration.py:353-460`
- [打开源码：scripts/ckb_core/showcase.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/showcase.py:1:1)  `scripts/ckb_core/showcase.py:1-173`
