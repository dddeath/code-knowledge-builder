# QMD 固定三臂基准结果

## 结论

在同一 `fcad08a` 冻结语料、同一 12 题、`2400` token 预算、top 8、统一 source-path 去重/截断和同一逐题 judge 下，QMD 2.8.3 `searchVector` 的 Recall@8、MRR@8、nDCG@8 分别为 `1.000000000`、`0.875000000`、`0.907732438`。相对当前确定性 SQLite 路线，三项分别增加 `0.250000000`、`0.305555556`、`0.291666666`，因此本协议下判为“已证实提升”，并只进入后续生产实验候选；生产默认检索没有改变。

现有 FastEmbed/BGE 路线三项均低于当前确定性路线，判为“观察到回归”。本轮没有路线落入“点指标非劣但未提升”。

## 固定输入与完成门

- 语料：`machine/knowledge.sqlite` SHA-256 `7d67e4098b6f69c7315ac0acf4a8a76549a04dd91f34408f27dce8e2fd471632`；`agent-index.sqlite` SHA-256 `c047b5917167c0fc462a9e85069bee7b69debc0ffe833c6accf1110a2e780806`；共 2,090 个实体文档。
- 问题：复用 `tests/fixtures/chinese-retrieval-effects/protocol.json` 的 12 题及相关性标签，源文件 SHA-256 固定在协议中。
- 排序与截断：每臂先按本臂得分排序，再按 `entity_id` 打破同分，按 source path 去重，执行共同的 2,400-token 预算，最后保留 top 8。
- 运行：每个 arm/question 为 1 次冷查询与同进程 5 次热查询，共 216 行；三臂每题的 6 次排序签名一致，独立重算 5 项检查全部通过。
- QMD：`@tobilu/qmd@2.8.3`，build `facd35e`，Node `v24.19.0`，Vulkan；`embeddinggemma-300M-Q8_0.gguf` 为 333,590,944 bytes，SHA-256 `b5ce9d77a3fc4b3b39ccb5643c36777911cc4eb46a66962eadfa3f5f60490d63`。
- 所有报告完成门通过，网络连接记录为 0，源 SQLite 与隔离副本在运行前后均保持不变。

## 质量结果

| 路线 | Recall@8 | MRR@8 | nDCG@8 | 相对当前路线判定 |
|---|---:|---:|---:|---|
| sqlite-current | 0.750000000 | 0.569444444 | 0.616065772 | 比较基线 |
| semantic-vector | 0.583333333 | 0.221527778 | 0.307883379 | 回归 |
| qmd-vsearch | 1.000000000 | 0.875000000 | 0.907732438 | 提升 |

## 时延与资源

| 路线 | 冷查询 p50 / p95 (ms) | 热查询 p50 / p95 (ms) | 中位首包估算 token | 峰值 RSS (bytes) |
|---|---:|---:|---:|---:|
| sqlite-current | 3136.390800 / 10564.247880 | 429.308200 / 2169.216785 | 605.5 | 106786816 |
| semantic-vector | 1425.847850 / 1959.237745 | 13.834200 / 17.320725 | 644.5 | 223051776 |
| qmd-vsearch | 15924.399900 / 24178.113260 | 638.396250 / 2421.319270 | 560.5 | 795459584 |

BGE 首次索引 `683.008599` 秒、索引 `5308687` bytes；QMD 首次索引 `131.058913` 秒、数据库 `14671872` bytes。总运行时加模型为 `1481145833` bytes，测得总峰值 RSS `3098050560` bytes。

## 失败样例

- `failure-samples/missing-qmd.json`：缺少 QMD 运行时，状态为 `qmd-unavailable`，不形成效果结论。
- `failure-samples/qmd-process-failure.json`：QMD 进程退出 7，状态为 `qmd-execution-failed`。
- `failure-samples/qmd-output-drift.json`：schema/kind 漂移，状态为 `qmd-output-drift`。

逐题结果位于 `report.json`，216 行原始记录位于 `raw-results.json`，独立重算位于 `recomputed.json`，运行与重算命令分别位于 `run-command.ps1.txt` 和 `recompute-command.ps1.txt`。
