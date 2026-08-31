# Agent 确定性检索

在读取大范围源码或执行全仓 grep 前，先使用本页接口。

## 主索引

每种输出格式都生成 `OUTPUT/machine/knowledge.sqlite`。它不是页面缓存，而是 Agent 专用完整知识库，包含全部实体、范围、关系、来源证据、审阅说明、固定快照源码、职责群、人类页映射、Agent 记录和工作树覆盖层。`OUTPUT/agent-index.sqlite` 只保留旧接口兼容能力。

```powershell
& PYTHON scripts\ckb.py reindex --out OUTPUT
& PYTHON scripts\ckb.py coverage --out OUTPUT
```

`reindex` 同时重建机器库和兼容索引。`coverage` 必须报告所有实体均为 `agent-reviewed`、中文叙述覆盖率为 `1.0`，并通过 SQLite 完整性和外键检查。

## 查询档位

```powershell
& PYTHON scripts\ckb.py brief --out OUTPUT `
  "修改订单失败后的库存回滚" --budget 1800 --max-pages 8 --profile fast

& PYTHON scripts\ckb.py retrieve --out OUTPUT `
  "修改订单失败后的库存回滚" --budget 1800 --max-pages 8 --profile fast

& PYTHON scripts\ckb.py retrieve --out OUTPUT `
  "跨模块失败恢复与持久化边界" --budget 3000 --max-pages 12 --profile precise
```

Agent 的首轮入口使用 `brief`。它执行完全相同的确定性检索并生成同一形状的 Agent pack/JSON record，但命令响应只保留 pack、record、开放反馈数、固定阅读入口和源码回退判断；`terms`、`selected_entities`、得分分解和关系文档继续保存在 record 中，不占用首轮 Harness 上下文。需要调试排序或 benchmark 时才直接使用完整 `retrieve` 输出。

两种档位均为纯确定性：

- `fast`：精确锚点、词项、实体/章节 FTS5，加固定权重的两跳图传播；
- `precise`：增加固定源码 FTS，并使用固定 24 轮、固定重启率的加权 PageRank。

5.1.3 的 `fast` 渲染阶段只物化排序后的前 32 个候选，以源码路径去重后选择预算允许的结果；实体与章节使用两次批量 SQL 读取，源码 URI 由单个已验证 renderer 按路径缓存。每个入选目标都获得紧凑区块，完整章节超过剩余预算时截断该章节而不是跳过目标。实现定位问题还会对文件名、限定名和已审阅中文职责执行固定权重匹配，并在问题没有测试意图时对测试实体施加固定折扣。结果中的 `retrieval_stats` 公开 overscan、物化候选、预算实体上限、源码路径数、批量查询数和链接缓存数，便于回归检查。

同分按稳定实体 ID 排序。同一机器库和查询重复执行时，实体顺序、得分与得分分解必须一致。本版没有向量模型、embedding、外部模型调用或随机采样。

## 中文与标识符词项

`scripts/ckb_core/query_terms.py` 统一机器检索和兼容索引的词项规则。输入先执行 NFKC 规范化，再按固定优先级生成词项：

1. 完整代码 run 和完整中文连续段；
2. 路径/API 分段、CamelCase 分段，以及固定语法连接字符之间的中文内容段；
3. 内容段内的中文三元组；
4. 内容段内的中文二元组。

同一词项只保留最高优先级，随后按优先级、长度降序和字典序排序。查询最多保留 64 项；建库使用相同排序规则但不应用查询上限，避免较长职责说明在索引阶段丢词。机器 FTS 只接收前 16 个长度至少为 3 的词项，兼容页面索引保留原有前 12 项上限，与 SQLite FTS5 `trigram` 的最小长度一致。

完整中文段始终保留，但滑动二元组、三元组不跨越固定语法连接字符。因此“打包不满足”“是否会回”“回的检索”仍保留完整短语，而“包不满”“否会回”“回的检”不再成为独立词项或独立 FTS 子句。路径、API、数字和 CamelCase 继续保留完整 run 与分段；空输入和纯标点返回空词项，单汉字可作为精确词项但不进入 trigram FTS。规则不扩写同义词，也不读取网络、模型或知识库外用户文本。

## 冻结十二问验收

固定协议位于 `tests/fixtures/chinese-retrieval-protocol.json`，使用 12 个问题、2400 token、最多 8 个结果、1 次预热和 9 次正式重复。`tests/benchmark_chinese_retrieval.py` 在调用方指定的隔离输出目录复制语料，按冻结顺序执行 Markdown 宽扫描、兼容页面索引和 `machine-fast`，并可比较两个独立进程的结果签名。

2026-09-01 的两个独立进程各完成 324 条正式测量，七项门全部通过：

| 指标 | 进程 1 | 进程 2 |
|---|---:|---:|
| `machine-fast` 中位延迟 | 47.17 ms | 48.69 ms |
| `machine-fast` P95 | 66.94 ms | 68.49 ms |
| 目标源码 Recall@8 | 100% | 100% |
| 回退率 | 0% | 0% |
| 进程内确定性 | 100% | 100% |
| Agent 可见上下文中位数 | 2392 tokens | 2392 tokens |
| 相对 Markdown 宽扫的上下文减少 | 79.96% | 79.96% |
| 相对 Markdown 宽扫的中位加速 | 1.147× | 1.128× |
| 查询词项中位数 | 20.0 | 20.0 |
| FTS 子句中位数 | 11.5 | 11.5 |
| FTS MATCH UTF-8 字节中位数 | 193.5 | 193.5 |
| 物化候选中位数 | 32.0 | 32.0 |
| 静态缓存冷/热中位延迟 | 107.09 / 47.82 ms | 105.00 / 50.64 ms |

相同冻结语料的旧规则基线为中位 23.5 个查询词项、195.0 个 FTS MATCH UTF-8 字节和 32.0 个物化候选；新规则把查询词项中位数减少 14.89%，同时保持 Recall@8 与候选上限。冷/热延迟只在同一进程内解释，跨轮绝对值不用于替代七门中的同轮宽扫对照。

在完整知识库副本上执行 `reindex` 后，机器索引从 23,900,160 字节、38,829 条词项变为 22,552,576 字节、29,055 条词项；兼容索引从 4,325,376 字节、6,920 条词项变为 4,898,816 字节、10,988 条词项。兼容索引增加是因为旧路径原先只有中文二元组，新路径同步保留高信号三元组和代码分段；两个索引合计减少 774,144 字节。重建前后两库的 `PRAGMA integrity_check` 均为 `ok`。

结果会生成预算内 `machine/agent-packs/*.md` 和 JSON 记录。先打开阅读包，再按需使用下列窄接口：

```powershell
& PYTHON scripts\ckb.py entity --out OUTPUT "OrderService"
& PYTHON scripts\ckb.py neighbors --out OUTPUT "OrderService" --depth 2
& PYTHON scripts\ckb.py source --out OUTPUT "OrderService" --context-lines 3
& PYTHON scripts\ckb.py changes --out OUTPUT --kind analysis
```

## 常驻 stdio 检索

同一 Agent 会话需要连续检索时，可启动一个本地、单线程、无网络端口的 JSONL 进程，复用 Python 模块和进程内静态检索缓存：

```powershell
& PYTHON scripts\ckb.py serve --stdio --out OUTPUT
```

每行输入一个 JSON 对象，每个响应也严格占一行。`id` 必须是字符串或整数；服务支持 `ping`、`retrieve` 和 `shutdown`：

```json
{"id":"ready","method":"ping"}
{"id":"q1","method":"retrieve","question":"修改订单失败后的库存回滚","budget":1800,"max_pages":8,"profile":"fast"}
{"id":"stop","method":"shutdown"}
```

`retrieve` 与一次性 CLI 使用同一个 `retrieve_machine`，仍会生成 Markdown/JSON Agent pack，排序、预算、来源和审计契约不变。单个请求的参数或 JSON 错误只返回 `ok:false`，不会终止服务；EOF 或 `shutdown` 结束进程。数据库或 `local-openers.json` 被原子替换后，已有修改时间失效键会在下一次请求重建静态缓存。

进程启动与第一次 `retrieve` 的缓存未命中成本应单独计量；后续请求的 `retrieval_stats.static_cache_hit` 应为 `true`。响应中的 `elapsed_ms` 是服务端请求时间，Harness 从写入一行到读回一行的时间才是用户可见往返延迟。

`passed` 结果已经给出来源绑定候选，不再加载完整图。`needs-source-read` 表示索引中没有可信候选，此时只按返回路径、词项和已知范围继续读取源码。

## 分节与上下文

机器库把每个实体拆成含义、职责、修改时机、来源说明和有界源码片段等章节；人类笔记按 Markdown 标题拆分。FTS 先命中章节，再把得分归属到来源实体，因此 Agent 可以读取少量相关章节而不是整页或整文件。文件实体不复制整个文件到实体章节；固定源码只在 `files/source_fts` 保存一次。

## 完成门

- `PRAGMA integrity_check` 返回 `ok`，外键检查为空；
- 文件、实体、源码范围、关系、审阅和人类归属计数与事实图一致；
- 所有要求叙述的字段含中文内容；
- 成功阅读包不超过请求预算，并带有可点击源码位置；
- `fast` 与 `precise` 重复查询结果稳定；
- 机器库缺少来源绑定候选时明确返回 `needs-source-read`，不生成猜测结果。
- `brief` 的首轮 JSON 不含候选实体、词项和得分大字段，所指 pack 与完整 record 均可重开。
