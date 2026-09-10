# LLM Wiki 快速检索性能验证（5.1.3）

标签：#类型/分析

## 结论

历史固定查询实验表明，5.1.3 的机器检索可以用更少上下文稳定定位目标源码路径；这不是精确符号检索已经最优的证明，也不是对当前版本的重新测量。

## 实现变化

检索器只读取排序后有限数量的候选，批量读取实体上下文，并缓存不可变的元数据和源码链接。长章节按预算截断，避免整个目标被跳过；中文词项及同分排序使用确定性规则，不调用模型。

## 已测量的效果

在当时冻结的十二个修改定位问题上，目标源码 Recall@8 为 100%，Markdown 宽扫描代理为 91.67%。九次重复结果一致，没有发生源码宽搜回退。

| 路径 | 中位延迟 | P95 延迟 | 目标源码 Recall@8 | 可见上下文中位数 |
| --- | ---: | ---: | ---: | ---: |
| Markdown 宽扫描代理 | 27.19 ms | 42.41 ms | 91.67% | 10,049 tokens |
| 旧页面级 SQLite | 37.45 ms | 62.17 ms | 50% | 2,370 tokens |
| 5.1.3 机器检索 | 25.29 ms | 45.36 ms | 100% | 2,283 tokens |

相对宽扫描代理，可见上下文减少 77.28%；中位延迟较低，但 P95 略高。结果仅适用于该固定实验，不代表所有仓库和查询都更快。

## 适用边界

当时辅助统计的目标符号召回只有 8.33%。若需要准确定位具体符号，还需单独验证同名符号消歧和下游修改成功率。该实验没有证明向量检索的收益，也没有改变生产检索默认方式。

## 原始记录

[核对历史测量、冻结协议与完整复现位置](../../machine/historical-records/legacy-retrieval-5-1-3.md)。

## 相关知识页

- [[build_machine_knowledge 与 estimated_tokens 的协作实现]]
- [[package_showcase 与 _parse_sample 的协作实现]]
- [[audit_global 与 _replace_output_prefix 的协作实现]]
- [[migrate_output 与 _entity_key 的协作实现]]
- [[ensure_local_openers 与 SourceLinkRenderer 的协作实现]]
- [[git 等测试场景（test_migration 测试）]]
- [[audit_obsidian 与 prepare_vault 的协作实现]]
- [[build_agent_index 与 _tokens 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1995`
- [打开源码：scripts/ckb_core/showcase.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/showcase.py:1:1)  `scripts/ckb_core/showcase.py:1-173`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3637`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-894`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
- [打开源码：tests/test_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:1:1)  `tests/test_migration.py:1-250`
- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-166`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-555`
