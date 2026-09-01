# LLM Wiki 快速检索性能验证（5.1.3）

标签：#类型/分析

## 结论

在不改变冻结查询、预算、重复次数和验收阈值的前提下，5.1.3 的 `machine-fast` 已通过全部七项预设门。十二个修改定位问题的目标源码 Recall@8 为 100%，高于 Markdown 宽扫描代理的 91.67%；九次重复的结果签名完全一致，且没有触发源码宽搜回退。待办 2 因此可从“首轮结果 mixed”更新为“确定性优化与原协议复测完成”。

## 本次实现

检索器在排序后只物化固定 overscan 窗口：`fast` 为 32 个候选，`precise` 为 64 个候选。实体上下文改为两次批量 SQL 读取；同一机器库的不可变实体元数据、章节、关系图和源码链接渲染器按数据库与打开器修改时间缓存。源码链接对同一路径只做一次边界处理。

每个最终目标都会获得紧凑区块，章节超过剩余预算时截断章节而不是跳过目标。中文查询增加三元词项；文件名、限定名和已审阅中文职责参与固定权重匹配；没有测试意图的问题对测试实体施加固定折扣。所有顺序、权重、上限、缓存失效条件和同分规则均由脚本确定，不引入向量模型、随机采样或隐藏模型排序。

## 冻结协议结果

| 路径 | 中位延迟 | P95 延迟 | 目标源码 Recall@8 | 可见上下文中位数 | 回退率 | 确定性 |
|---|---:|---:|---:|---:|---:|---:|
| Markdown 宽扫描代理 | 27.19 ms | 42.41 ms | 91.67% | 10,049 tokens | 0% | 100% |
| 旧页面级 SQLite | 37.45 ms | 62.17 ms | 50% | 2,370 tokens | 0% | 100% |
| 5.1.3 machine-fast | 25.29 ms | 45.36 ms | 100% | 2,283 tokens | 0% | 100% |

相对 Markdown 宽扫描代理，机器检索的 Agent 可见上下文减少 77.28%，中位延迟加速 1.075 倍，P95 低于冻结的 200 ms 上限。目标源码召回、不得低于人工宽扫、零回退、完全确定性、上下文减少、绝对 P95 和相对中位加速七项门全部通过。

## 边界

辅助统计中的目标符号召回为 8.33%，该指标没有被列入本轮冻结完成门；本轮确认的是“以最少上下文稳定定位应修改源码路径”的能力，不把它外推为精确符号检索已经最优。后续若把符号级命中设为产品目标，应单独冻结查询、同名符号处理和下游修改成功率门。向量检索仍留在后续 benchmark 阶段。

## 验证与可复现位置

- 冻结协议：`E:\knowledge_builder\self-workspace\work\retrieval-optimization-5.1.3\benchmark\protocol.json`
- 324 条正式测量：`E:\knowledge_builder\self-workspace\work\retrieval-optimization-5.1.3\benchmark\raw-results.json`
- 七门汇总：`E:\knowledge_builder\self-workspace\work\retrieval-optimization-5.1.3\benchmark\summary.json`
- 逐实体源码重开记录：`E:\knowledge_builder\self-workspace\work\retrieval-optimization-5.1.3\source-range-review.json`
- 回归结果：`test_ckb.py` 18 项、`test_automation.py` 18 项、`test_migration.py` 1 项全部通过。

## 相关知识页

- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[package_showcase 与 _parse_sample 的协作实现]]
- [[audit_global 与 _replace_output_prefix 的协作实现]]
- [[audit_migration 与 _entity_key 的协作实现]]
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]
- [[MigrationTest 等测试场景]]
- [[audit_obsidian 与 prepare_vault 的协作实现]]
- [[retrieve]]

## 源码入口

- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/showcase.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/showcase.py:1:1)  `scripts/ckb_core/showcase.py:1-173`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3242`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
- [打开源码：tests/test_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:1:1)  `tests/test_migration.py:1-181`
- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`
- [打开源码：scripts/ckb_core/agent_index.py 第 440 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:440:1)  `scripts/ckb_core/agent_index.py:440-568`
