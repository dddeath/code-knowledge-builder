# Flask 3.1.3 知识库与 grep 对比测试（秋招版）

标签：#类型/分析

## 一句话结论

在 Flask 3.1.3 的 24 个核心 Python 文件上，知识库检索与人工设计的 `git grep` 基线都能在前 8 个结果内定位 10/10 个目标文件；知识库把 Agent 可见上下文中位数从 11,228 tokens 降到 2,294 tokens，减少 79.6%，但命令中位延迟由 74 ms 增至 368 ms，而且自然语言 Top-8 的精确目标符号召回只有 40%。因此这次结果应表述为“显著降低未知仓库任务的上下文成本并稳定定位文件”，而不是“全面替代 grep”或“检索更快”。

## 测试对象与方法

- 对象：常见开源 Python Web 框架 Flask 3.1.3，范围固定为 `src/flask`。
- 规模：24 个源码文件、1,016 个机器实体、578 个一跳边界实体、3,425 条关系、85 个人类 Markdown 页面。
- 知识库方法：Tree-sitter 提取语法实体，Pyright 提供语义证据，Agent 逐实体复核中文说明；检索采用 SQLite FTS5、确定性加权排序和一跳图扩展，不使用向量模型。
- 对照方法：`git grep -n -I -i -E`，每题使用预先冻结的 4 组关键词，再按关键词覆盖数、命中行数和路径排序，最多展示 8 个文件。
- 协议：10 个面向真实修改任务的问题；每种方法每题预热 1 次、正式重复 7 次，共 20 次预热和 140 条正式记录；问题与验收门在知识库构建前冻结。

## 量化结果

| 指标 | 知识库检索 | grep 基线 | 解释 |
|---|---:|---:|---|
| 目标文件 Recall@8 | 100% | 100% | 两者都能找到应修改文件 |
| 精确目标符号召回 | 40% | 100% | 知识库更偏向先定位文件与相邻职责，精确函数仍需二次查询 |
| 可见上下文中位数 | 2,294 tokens | 11,228 tokens | 知识库减少 79.6% |
| 展示文件数中位数 | 5.5 | 8 | 知识库减少无关文件暴露 |
| 命令延迟中位数 | 368 ms | 74 ms | grep 约快 5 倍 |
| 命令延迟 P95 | 409 ms | 88 ms | 两者都低于交互式使用门槛，但 grep 更轻 |
| 确定性 | 100% | 100% | 同一问题的排序重复一致 |
| grep 回退率 | 0% | 不适用 | 知识库全部由 SQLite 路径完成 |

成功构建本次知识库约用 92.1 秒，其中机器构建、合并和最终审计约 20.1 秒，逐实体来源复核与审阅提交约 72.0 秒。这个一次性成本没有计入单次查询延迟，面试中应主动说明。

## 面试可讲的方法与取舍

1. **为什么做**：Agent 面对未知仓库时，直接 grep 容易返回大量词法命中，后续仍要阅读很多文件；先建立带源码位置、中文职责和关系的机器索引，可以把“找哪些文件”与“读哪些代码”分开。
2. **怎么做**：先固定源码快照，再用语法树和语言服务器收集实体与关系；人类页面限制数量，机器库保留完整事实；查询阶段先用 FTS5 找种子，再做确定性图扩展和 token 预算裁剪。
3. **效果如何**：本测试保持目标文件召回不下降，同时把可见上下文减少约八成，并在 70 次正式知识库查询中保持零回退和完全一致的排序。
4. **为什么不只用 grep**：grep 对已知精确符号最快；知识库更适合“只知道业务意图、不知道文件和类名”的任务。工程上应组合使用：先用知识库缩小到文件和职责，再用符号查询或窄范围 grep 落到具体函数。

## 踩坑与后续改进

- Pyright 对只有导入或顶层调用的模块会合法返回空 `documentSymbol`；原实现把空列表误判为提供器失败。现已改为只把真实致命诊断或协议失败计为失败。
- Python 模块级 `__getattr__` 属于访问器，原先可能被跨文件引用权重晋升成独立关键页。现已由确定性规则固定归入文件附录。
- 精确符号召回是当前主要短板。下一步应在不增加大段上下文的前提下加入“文件命中后按函数签名二次重排”，并用同一冻结题集复验；在复验前不宣称知识库替代精确符号 grep。

## 可复查证据

- 完整基准摘要：`E:\knowledge_builder\evaluations\flask-3.1.3-benchmark\summary.json`
- 冻结协议：`E:\knowledge_builder\evaluations\flask-3.1.3-benchmark\protocol.json`
- 140 条正式原始记录：`E:\knowledge_builder\evaluations\flask-3.1.3-benchmark\formal-records.jsonl`
- Flask 知识库：`E:\knowledge_builder\evaluations\flask-3.1.3-knowledge`

## 相关知识页

- [[MigrationTest 等测试场景]]
- [[audit_migration 与 _entity_key 的协作实现]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[ingest_event 与 default_registry_path 的协作实现]]
- [[retrieve]]
- [[audit_global 与 _replace_output_prefix 的协作实现]]
- [[AutomationTest.event 等测试场景]]

## 源码入口

- [打开源码：tests/test_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:1:1)  `tests/test_migration.py:1-194`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：tests/test_ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb.py:1:1)  `tests/test_ckb.py:1-1152`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1632`
- [打开源码：scripts/ckb_core/agent_index.py 第 440 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:440:1)  `scripts/ckb_core/agent_index.py:440-568`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：tests/test_automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:1:1)  `tests/test_automation.py:1-801`

## 后续补充

### 最终验收与交付补充

本轮已经把 Flask 3.1.3 知识库构建、冻结协议对照实验、构建阻塞修复、已安装 Skill 同步、完整测试、当前知识库索引刷新和隔离回滚探针全部执行完毕。综合结论仍是“有条件收益”：知识库明显降低未知仓库任务的上下文成本并稳定定位文件，但命令速度和精确符号召回仍逊于 `git grep`，因此不宣称全面替代 grep。

#### 最终量化结果

| 指标 | CKB 知识库检索 | `git grep` | 判断 |
|---|---:|---:|---|
| 目标文件 Recall@8 | 100% | 100% | 文件级导航无损 |
| 精确目标符号召回 | 40% | 100% | CKB 需要文件内二次符号重排 |
| 可见上下文中位数 | 2,294 tokens | 11,228 tokens | CKB 减少 79.6% |
| 展示文件数中位数 | 5.5 | 8 | CKB 暴露更少无关文件 |
| 命令延迟中位数 | 368 ms | 74 ms | grep 约快 5 倍 |
| 命令延迟 P95 | 409 ms | 88 ms | 两者均可交互使用，grep 更轻 |
| 确定性 | 100% | 100% | 重复排序一致 |
| grep 回退率 | 0% | 不适用 | CKB 全部使用 SQLite 检索 |

测试采用 10 个真实修改意图问题，每种方法每题预热 1 次并正式重复 7 次，共形成 20 次预热和 140 条正式记录。问题、grep 关键词、排序规则、token 预算和验收门都在知识库构建前冻结。grep 每题使用 4 组人工设计关键词，而 CKB 接收中文自然语言任务，因此结果代表“Agent 任务导航”和“工程师构造 grep”的实用对照，不是完全相同查询字符串的对称测试。

Flask 知识库最终包含 24 个核心 Python 文件、1,016 个机器实体、578 个一跳边界实体、3,425 条关系和 85 个人类 Markdown 页面。成功构建、审阅、合并和最终审计约用 92.1 秒，其中机器构建、合并与最终审计约 20.1 秒，逐实体来源复核与审阅提交约 72.0 秒。这个一次性成本没有计入单次查询延迟。

#### 本轮修复

1. **合法空 `documentSymbol` 不再被当作提供器失败。** Pyright 对只有导入或顶层调用的模块可以成功返回空符号列表。现在只有真实请求异常、致命诊断或致命 stderr 才会使 provider 失败，关键页面定义覆盖仍由独立语义门检查。
2. **Python 属性访问协议固定归入附录。** `__getattr__`、`__getattribute__`、`__setattr__` 和 `__delattr__` 由确定性规则标记为 `python-attribute-accessor`，不会再因为跨文件引用权重被晋升为独立关键页。

对应修改保留在 `main` 分支的以下三个文件中：

- `E:\knowledge_builder\self-workspace\source\scripts\ckb_core\providers.py`
- `E:\knowledge_builder\self-workspace\source\scripts\ckb_core\parsers.py`
- `E:\knowledge_builder\self-workspace\source\tests\test_ckb.py`

已安装版本位于 `C:\Users\19739\.codex\skills\code-knowledge-builder`，上述三个安装文件已经验证与源码字节一致。

#### 验收结果

- 源码 Skill 与已安装 Skill 的结构校验均返回 `Skill is valid!`。
- 完整测试套件 39 项全部通过，精确记录为 `Ran 39 tests; OK`。
- 已安装版两个新增回归测试全部通过，`doctor` 返回 `ready`。
- Flask 段内范围、语法、分类、语义、来源、中文说明和链接七个门全部为 `passed`。
- Flask 全局审计为 `passed`，机器 SQLite 的 `PRAGMA integrity_check` 为 `ok`。
- 当前知识库 human/markdown 页面字节一致，`agent-index.sqlite` 与 `machine/knowledge.sqlite` 完整性均为 `ok`。
- 报告可从两个 SQLite 索引检索，并保留知识页双链和可点击源码链接。
- 源码与安装目录回滚探针、知识库报告与索引回滚探针均已实际执行并通过。

#### 可复查交付

- Flask 知识库：`E:\knowledge_builder\evaluations\flask-3.1.3-knowledge`
- 冻结协议：`E:\knowledge_builder\evaluations\flask-3.1.3-benchmark\protocol.json`
- 基准摘要：`E:\knowledge_builder\evaluations\flask-3.1.3-benchmark\summary.json`
- 140 条正式记录：`E:\knowledge_builder\evaluations\flask-3.1.3-benchmark\formal-records.jsonl`
- 总验证记录：`E:\knowledge_builder\evaluations\flask-3.1.3-benchmark\verification-record.json`
- 源码修复 patch：`E:\knowledge_builder\evaluations\flask-3.1.3-benchmark\ckb-provider-accessor-fix.patch`
- 知识库报告 patch：`E:\knowledge_builder\evaluations\flask-3.1.3-benchmark\current-kb-report.patch`
- 源码与安装回滚：`E:\knowledge_builder\evaluations\flask-3.1.3-benchmark\rollback.ps1`
- 报告与索引回滚：`E:\knowledge_builder\evaluations\flask-3.1.3-benchmark\rollback-report.ps1`

#### 当前 Git 状态与推荐工作流

源码仓库仍在 `main`，只保留 `providers.py`、`parsers.py` 和 `test_ckb.py` 三个明确的未提交修改，没有残留 Python 缓存，也没有自动创建 commit。

推荐使用顺序是：先通过 CKB 自然语言检索定位文件、职责和相邻关系，再使用 `entity`、`source` 或窄范围符号 grep 落到具体函数。下一步应在保持 2,400-token 预算不变的前提下加入文件命中后的函数签名二次确定性重排，并用同一冻结题集复验精确符号召回。

面试时可简述为：我使用 Tree-sitter、语言服务器、SQLite FTS5 和确定性图扩展为未知代码仓库建立机器知识库与受控的人类 Markdown 知识库。在 Flask 3.1.3 的 10 个修改任务上，目标文件 Recall@8 与人工设计 grep 同为 100%，但 Agent 可见上下文中位数减少 79.6%，70 次正式知识库查询保持零回退和完全一致的排序；代价是查询约慢 5 倍且精确符号召回仍为 40%，所以工程上采用“知识库先定位文件与职责，窄范围符号检索再落函数”的组合方案。
