# 真实 LLM 关键词慢路径 12 用例结果

## 结论

在冻结的 12 个 CKB 检索问题和同一份语料副本上，显式 `force` 的 `codex-cli / gpt-5.6-luna / real-12case-v1` 慢路径完成 12 次真实冷调用。平均 `Recall@8` 从 `0.75` 提高到 `1.00`，增量为 `+0.25`；q02、q06、q12 从未召回变为召回，12 题没有 Recall 退化。因此，本协议下的召回改善已测得。

排序结果不是全题单调改善：平均 `MRR@8` 从 `0.611111111` 提高到 `0.649404762`，平均 `nDCG@8` 从 `0.646821626` 提高到 `0.733297918`，但 q11 的目标仍在 Top 8 内且名次下降，`MRR@8` 单题增量为 `-0.857142857`。结论限定为“提高本冻结任务集的召回”，不扩展为“每题排序都改善”。

## 调用条件

| 模式 | 已测行为 |
| --- | --- |
| 默认路径 | 不传 fallback 选项时，12 题 Provider 启动数为 0。 |
| `allow` + 确定性结果 `passed` | 不启动 Provider，记录 `skipped`。 |
| `allow` + 确定性结果 `needs-source-read` | 启动一次 Provider，触发原因为 `needs-source-read`。 |
| `force` | 12 题各启动一次真实 Provider，共 12 次；热运行全部读取已校验缓存，没有再次启动 Provider。 |

默认 `fast` / `precise` 行为和启用策略没有改变。

## 质量、时延与用量

| 指标 | 确定性基线 | 真实慢路径 | 差值或状态 |
| --- | ---: | ---: | ---: |
| `Recall@8` | 0.750000000 | 1.000000000 | +0.250000000 |
| `MRR@8` | 0.611111111 | 0.649404762 | +0.038293651 |
| `nDCG@8` | 0.646821626 | 0.733297918 | +0.086476292 |
| Recall 提升题数 | - | 3 | q02、q06、q12 |
| Recall 退化题数 | - | 0 | 无 |
| MRR 退化题数 | - | 1 | q11 |
| Provider 时延 P50 / P95 | - | 20,451.893050 / 22,569.100855 ms | 真实冷调用 |
| 端到端额外时延 P50 / P95 | - | 20,405.490500 / 22,919.513580 ms | 慢路径减基线 |
| 输入 / 输出 token | - | 176,041 / 2,714 | 来自 `turn.completed` |
| 费用 | - | 未报告 | CLI 没有账单金额字段，`cost_usd` 记为 `null` |

逐题的确定性输入词项、Provider 原始 `keywords` / `anchors` / `rewrites`、校验后词项、最终排序、召回变化和时延均在 [`report.json`](report.json)；包含完整逐题对象及语料哈希的记录在 [`raw-results.json`](raw-results.json)。

## 失败和无关输出

| 样例 | 结构化结果 | 检索结果 |
| --- | --- | --- |
| 超时 | `timeout`，Adapter `attempts=1` | 原状态、原排序和原 Recall 保持 |
| 非 JSON | `invalid-json` | 原状态、原排序和原 Recall 保持 |
| 空词项 | `invalid-output` | 原状态、原排序和原 Recall 保持 |
| 17 个越界词项 | `invalid-output` | 原状态、原排序和原 Recall 保持 |
| 凭据缺失 | `missing-credentials`，`attempts=0` | 不启动 Adapter；原状态、原排序和原 Recall 保持 |
| schema 合法但语义无关 | Provider 输出被接收 | 检索未阻塞，`Recall@8` 未下降 |

超时进程可能在 fixture marker 写入前结束，因此是否发起调用以核心返回的 `attempts` 判定；marker 仅作为已落盘进程证据。六个探针的逐项检查见 [`report.json`](report.json)。

## 未配置行为

未传入真实 Provider 可执行文件时，运行器返回 `status=not-executed`、`actual_calls=0`、`quality_claim=not-executed`，不借用 fixture 或回放结果形成效果结论。固定样例见 [`not-configured-report.json`](not-configured-report.json)。
