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

同分按稳定实体 ID 排序。同一机器库和查询重复执行时，实体顺序、得分与得分分解必须一致。默认路径没有向量模型、embedding、外部模型调用或随机采样。

### 显式 LLM 关键词备选慢路径

`fast`、`precise` 和 `brief` 的默认行为保持离线确定性；未提供 `--allow-keyword-fallback` 或 `--force-keyword-fallback` 时，CKB 不构造 Provider 配置、不启动 Provider 进程，也不访问网络。`--allow-keyword-fallback` 只在原始结果为 `needs-source-read` 时尝试一次慢路径；`--force-keyword-fallback` 用于 benchmark 或明确要求扩展已经通过的查询。

```powershell
& PYTHON scripts\ckb.py retrieve --out OUTPUT "QUESTION" `
  --allow-keyword-fallback `
  --keyword-provider-command "PROVIDER_COMMAND" `
  --keyword-provider-arg "ARG_1" `
  --keyword-provider "PROVIDER" --keyword-model "MODEL" `
  --keyword-provider-version "VERSION" `
  --keyword-provider-timeout 20 --keyword-provider-retries 1 `
  --keyword-provider-require-env "CREDENTIAL_ENV_NAME"
```

Provider 是调用方显式配置的本地命令/stdio JSON 适配器。CKB 向它的 stdin 写入一个 JSON 对象，内容只有 schema、Prompt schema、`request_id`、输入哈希、当前问题和固定数量/长度上限；Provider 的 stdout 必须只返回一个 JSON 对象，并带有 `keywords`、`anchors`、`rewrites`、`provider`、`model`、`version`、`request_id` 和 `usage`。候选数量、长度、字符集、重复项、提示注入文本、凭据形态和身份字段由确定性校验器拒绝。模型不接触实体分数、图传播、预算、完成状态或人类知识页。

校验通过的候选会拆成现有 `search_terms` 可接受的附加词项，并与代码锚点、查询改写一起重新进入同一 SQLite/FTS/图检索。最终候选、排序、预算和来源门仍由确定性脚本负责。检索 record 中的 `keyword_fallback` 分开保存原始词项、模型候选、通过校验的扩展词项、Provider usage/延迟/缓存状态和最终确定性选择结果。

超时、rate limit、进程异常、非法 JSON、非法输出和无凭据都返回原始确定性结果，并写入有界失败类型；一次请求最多重试一次临时失败。缓存键包含输入哈希、Provider、Model、Version 和 Prompt schema，缓存只保存通过校验的结构化响应，不保存问题正文、命令、环境变量值、stdout 或 stderr。`maintain` 会审计 `workspace-meta/keyword-fallback/cache` 和 `workspace-meta/keyword-fallback/requests`；这些机器记录不投影为人类知识页。

固定 benchmark 同时记录定位质量、上下文、冷/热延迟、token 和费用。热缓存的本次 `usage` 为零，原始调用 usage 只放在 `cached_usage` 中。报告的 `quality_claim` 只有在固定期望实体/源码路径的平均命中提升大于零时才是 `measured-gain`，否则固定为 `not-demonstrated`。

```powershell
& PYTHON scripts\ckb.py keyword-benchmark --out OUTPUT `
  --cases tests\fixtures\keyword_benchmark.json `
  --write BENCHMARK.json `
  --keyword-provider-command "PROVIDER_COMMAND" `
  --keyword-provider "PROVIDER" --keyword-model "MODEL" `
  --keyword-provider-version "VERSION"
```

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

stdio 使用同一 canonical 配置，不另设第二套 Provider 协议。只有请求内出现 `keyword_fallback` 时才构造适配器：

```json
{"id":"q2","method":"retrieve","question":"QUESTION","profile":"fast","keyword_fallback":{"mode":"allow","command":["PROVIDER_COMMAND","ARG_1"],"provider":"PROVIDER","model":"MODEL","version":"VERSION","timeout_seconds":20,"retries":1,"required_environment":["CREDENTIAL_ENV_NAME"],"use_cache":true}}
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
