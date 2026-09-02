# LLM Wiki 快速检索性能复验（5.1.4）

标签：#类型/分析

## 结论

当前 `machine-fast` 在两个独立进程、每轮 324 条正式测量中均通过原冻结协议的七项门。目标源码 Recall@8 为 100%，零回退且跨进程结果签名完全一致；相对 Markdown 宽扫描，Agent 可见上下文减少 80.43%，中位延迟加速范围为 1.124–1.160 倍。

## 结果

| 指标 | 独立运行 1 | 独立运行 2 |
|---|---:|---:|
| machine-fast 中位延迟 | 20.85 ms | 21.20 ms |
| machine-fast P95 | 31.86 ms | 29.70 ms |
| Markdown 宽扫中位延迟 | 23.44 ms | 24.60 ms |
| machine-fast Recall@8 | 100% | 100% |
| Markdown 宽扫 Recall@8 | 100.00% | 100.00% |
| machine-fast 可见上下文中位数 | 2336 tokens | 2336 tokens |
| Markdown 宽扫可见上下文中位数 | 11935 tokens | 11935 tokens |
| 上下文减少 | 80.43% | 80.43% |
| 相对宽扫加速 | 1.124× | 1.160× |

## 七项门

- Recall@8 不低于 90%：通过。
- Recall 不低于 Markdown 宽扫：通过。
- 回退率为 0：通过。
- 重复结果完全确定：通过。
- 可见上下文至少减少 40%：通过。
- P95 不超过 200 ms：通过。
- 中位延迟不慢于 Markdown 宽扫：通过。

## 边界

辅助符号召回为 16.67%，没有纳入原冻结完成门。本轮确认的是检索器以较少上下文定位目标源码路径的效果，不等同于真实模型已经完成代码修改；后者需要单独的下游 Agent 任务 benchmark。

## 可复现证据

- 冻结协议：`E:\knowledge_builder\self-workspace\work\llm-wiki-retrieval-revalidation-5.1.4\protocol.json`
- 两轮原始结果：`formal-run-1/raw-results.json`、`formal-run-2/raw-results.json`
- 跨进程审计：`verification.json`

## 相关知识页

- [[package_showcase 与 _parse_sample 的协作实现]]
- [[audit_global 与 _replace_output_prefix 的协作实现]]
- [[audit_migration 与 _entity_key 的协作实现]]
- [[MigrationTest 等测试场景]]
- [[audit_obsidian 与 prepare_vault 的协作实现]]
- [[AutomationTest.register 等测试场景]]
- [[query_graph 与 _networkx_modules 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/showcase.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/showcase.py:1:1)  `scripts/ckb_core/showcase.py:1-173`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：tests/test_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:1:1)  `tests/test_migration.py:1-194`
- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`
- [打开源码：tests/test_automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:1:1)  `tests/test_automation.py:1-801`
- [打开源码：scripts/ckb_core/graphify_core.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/graphify_core.py:1:1)  `scripts/ckb_core/graphify_core.py:1-676`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`

## 后续补充

## 待办关联

- [[自动同步与 LLM Wiki 后续待办]]
