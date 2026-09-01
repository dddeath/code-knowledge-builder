# 常驻 stdio 检索性能复测（Flask 3.1.3）

标签：#类型/实验

## 结论

Code Knowledge Builder 现提供本地常驻 JSONL stdio 检索命令。它在一个 Agent 会话内复用 Windows Python 进程、SQLite 数据和静态检索缓存，不打开网络端口，也不改变现有排序、token 预算、来源链接或 Agent pack 契约。

在 Flask 3.1.3 的冻结十题上，常驻请求中位往返延迟为 23.5 ms，P95 为 45.1 ms；同轮一次性 CLI 分别为 321.6 ms 和 361.2 ms。常驻模式的中位速度提升为 13.71 倍，结果签名与一次性 CLI 完全一致。收益成立于进程已驻留的会话内检索，不代表精确符号召回已经改善。

## 使用方式

启动服务：

```powershell
& 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.0.0\python\python.exe' -X utf8 `
  'C:\Users\19739\.codex\skills\code-knowledge-builder\scripts\ckb.py' `
  serve --stdio --out 'KNOWLEDGE_BASE'
```

调用方通过 stdin 每次写入一个 JSON 对象，并从 stdout 读取一行响应：

```json
{"id":"ready","method":"ping"}
{"id":"q1","method":"retrieve","question":"修改订单失败后的库存回滚","budget":1800,"max_pages":8,"profile":"fast"}
{"id":"stop","method":"shutdown"}
```

服务支持 `ping`、`retrieve` 和 `shutdown`。请求与响应严格各占一行。格式错误、未知方法或无效参数只返回 `ok:false`，不会终止服务；EOF 或 `shutdown` 会结束进程。

## 冻结测试协议

- 仓库：Flask 3.1.3。
- 问题：10 个真实修改意图。
- 方法：一次性 `ckb.py retrieve` 与常驻 `ckb.py serve --stdio`。
- 档位：`fast`。
- 预算：2,400 tokens。
- 最大结果：8。
- 每种方法每题预热 1 次，正式重复 7 次。
- 正式记录共 140 条，两种方法按题号轮换执行顺序。
- 常驻进程启动到第一次 `ping` 单独计量，不混入正式稳态请求延迟。

只有结果签名、文件召回、符号召回、确定性、回退率、缓存命中、P95、速度、错误隔离和干净关闭全部通过，才确认会话内延迟收益。

## 正式结果

| 指标 | 一次性 CLI | 常驻 stdio |
|---|---:|---:|
| 正式请求数 | 70 | 70 |
| 请求往返中位数 | 321.6 ms | 23.5 ms |
| 请求往返 P95 | 361.2 ms | 45.1 ms |
| 服务端检索中位数 | 不适用 | 23.1 ms |
| 目标文件 Recall@8 | 100% | 100% |
| 精确目标符号召回 | 40% | 40% |
| 结果签名一致率 | 不适用 | 100% |
| 确定性 | 100% | 100% |
| 回退率 | 0% | 0% |
| 正式请求缓存命中率 | 0% | 100% |
| 可见上下文中位数 | 2,294 tokens | 2,294 tokens |

常驻模式中位延迟减少 92.7%。70 次正式请求的累计时间从约 22.64 秒降到约 2.18 秒，后者已包含一次进程启动，累计减少约 90.4%。JSONL 管道中位开销约为 0.33 ms，剩余时间主要来自 SQLite 查询、确定性评分和 Agent pack 生成。

## 首次请求成本

十个独立新会话的中位结果为：

| 阶段 | 中位时间 |
|---|---:|
| 启动到 `ping` 返回 | 201.9 ms |
| 第一次 `retrieve`，缓存未命中 | 79.2 ms |
| 启动加第一次检索 | 281.1 ms |
| 第二次相同检索，缓存命中 | 39.1 ms |
| 一次性 CLI | 321.6 ms |

本机样本中，启动服务后只查询一次的总时间仍低于一次性 CLI，因此摊销拐点为 1 个请求。第一次请求的 `retrieval_stats.static_cache_hit` 为 `false`，后续请求为 `true`。

## 当前实现

- `scripts/ckb_core/stdio_server.py`：JSONL 协议、参数校验、错误隔离和关闭逻辑。
- `scripts/ckb.py`：新增 `serve --stdio --out OUTPUT` 命令。
- `tests/test_ckb.py`：验证单行协议、错误后继续服务和关闭边界。
- `references/agent-retrieval.md`：记录启动方式、请求格式、缓存与延迟口径。

源码与 `C:\Users\19739\.codex\skills\code-knowledge-builder` 中的已安装文件已经验证一致。完整测试套件 40 项通过，已安装版真实进程 canary、Skill 结构校验、SQLite 完整性和隔离回滚探针均通过。

## 边界

- 服务只使用本地 stdin/stdout，不提供网络或 MCP 端口。
- 当前单线程串行执行，每次处理一个请求。
- `retrieve` 仍生成 Markdown 和 JSON Agent pack。
- 数据库或 `local-openers.json` 被原子替换后，下一次请求会通过修改时间失效键重建缓存。
- 当前没有接入 Codex、Claude、OpenCode 等 Harness 的 SessionStart/SessionEnd 自动拉起和关闭。
- 没有实现进程池、并发请求或多知识库调度。
- 精确目标符号召回仍为 40%，常驻模式只解决延迟，不改变检索质量。
- 当前没有重新打包发行 ZIP，也没有自动创建 Git commit。

## 验证证据

- 冻结协议：`E:\knowledge_builder\evaluations\flask-3.1.3-stdio-benchmark\protocol.json`
- 复测摘要：`E:\knowledge_builder\evaluations\flask-3.1.3-stdio-benchmark\summary.json`
- 140 条正式记录：`E:\knowledge_builder\evaluations\flask-3.1.3-stdio-benchmark\formal-records.jsonl`
- 新会话启动探针：`E:\knowledge_builder\evaluations\flask-3.1.3-stdio-benchmark\startup-probe.json`
- 已安装版 canary：`E:\knowledge_builder\evaluations\flask-3.1.3-stdio-benchmark\installed-canary.json`
- 总验证记录：`E:\knowledge_builder\evaluations\flask-3.1.3-stdio-benchmark\verification-record.json`
- 源码 patch：`E:\knowledge_builder\evaluations\flask-3.1.3-stdio-benchmark\delivery\stdio-server.patch`
- 可执行回滚：`E:\knowledge_builder\evaluations\flask-3.1.3-stdio-benchmark\delivery\rollback.ps1`

## 延伸阅读

- [[Flask 3.1.3 知识库与 grep 对比测试（秋招版）]]
- [[LLM Wiki 快速检索性能复验（5.1.4）]]

## 相关知识页

- [[LspClient.start 与 _version_matches 的协作实现]]
- [[audit_global 与 _replace_output_prefix 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[CodeKnowledgeBuilderTests]]
- [[CkbError 与 DependencyError 的协作实现]]
- [[parse_file 与 _language 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/providers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/providers.py:1:1)  `scripts/ckb_core/providers.py:1-596`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：tests/test_ckb.py 第 171 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb.py:171:1)  `tests/test_ckb.py:171-1147`
- [打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-158`
- [打开源码：scripts/ckb_core/parsers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/parsers.py:1:1)  `scripts/ckb_core/parsers.py:1-437`
