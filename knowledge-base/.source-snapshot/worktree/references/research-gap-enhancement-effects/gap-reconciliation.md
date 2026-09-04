# Research gap 逐项对账

## 对账基线

- 源码与稳定知识库快照：`bdd4a6671df5c8f3ebd2f2980acf8e0072ce0d1d`，tree `9289ac724bfb6c1a5a76e6160fe57ba11255691e`。
- gap 索引：`2026-09-02T22:50:45Z`，共 7 项，其中 open 5 项、resolved 2 项。
- 对账日期：`2026-09-04`。
- 判定原则：后续实现、回归或审计通过只证明功能或合同可用；只有相对冻结旧基线的任务指标才能证明效果。gap 的旧 `open` 状态不用于推断后续没有实现。

## 对账结果

| Gap | 当前状态 | 后续证据与比较对象 | 对账结论 | 管理 Agent 动作 | 最小进一步研究 |
|---|---|---|---|---|---|
| `gap-00b32bb494b250ee9f73b6fdc9937f5b`：QMD/向量检索 | open | `c533dd7` 前已合并 FastEmbed 0.8.0 + `Qdrant/bge-small-zh-v1.5` 三臂实验；同一 12 题中，纯向量相对 SQLite 的 Recall@8/MRR@8/nDCG@8 分别变化 `-0.166667/-0.316667/-0.281894`，RRF 融合为 `+0.083333/-0.022817/-0.000893`，均未通过无回退门。该引擎不是 QMD。 | 保持 open。现有实验已证明当前 BGE 文本合同和融合方式退化，但没有回答 QMD 本身是否增益。 | 不执行 resolve。 | 固定 QMD `2.8.3`，把同一 1,937 个实体文本投影为隔离 Markdown 语料，复用现有 12 题、相关性标签、8 条结果和资源上限；分别测 `vsearch` 与 `query --no-rerank`，记录 Recall/MRR/nDCG、首包 token、索引大小、冷/热延迟、RSS、子进程和模型字节。运行前需允许临时安装软件并下载约 300 MB 的默认向量模型。 |
| `gap-6c6eb1a7982550999213f764e115e7ad`：真实 LLM 关键词慢路径 | open | `3cc77d4` 已合并显式慢路径。冻结 12 题的固定回放相对当前确定性检索有质量增益，但实际模型调用为 0；合并审计另有一次 `codex-cli/gpt-5.6-luna/canary-v1` 真调用，Provider 延迟 `27,643.134 ms`，只证明接线、校验、审计和回落。适配器没有账单 telemetry。 | 保持 open。真实 canary 不是固定问题集对照，也没有 token/费用证据；离线回放不得替代真实模型效果。 | 不执行 resolve。 | 在现有 12 题协议上固定 Provider/Model/Version/Prompt，执行真实慢路径与确定性基线；调用方先给出调用次数和费用上限，并使用能返回 input/output token 与费用的 Provider 或计费旁路。输出逐题质量、冷/热延迟、token、费用、失败类型和缓存命中。 |
| `gap-8c436abb192752cb90c955c0158d611e`：真实 Obsidian Tag 导航 | open | `eca7398` 已合并隔离原型。固定 6 题中，确认 tag 相对无 tag 的总导航步骤 `19→7`、中位步骤 `3→1`、误导链接 `5→1`，页面数均为 11；报告将其明确限定为 `isolated-fixture` 和 `fixture-navigation-signal-only`。 | 保持 open。隔离 fixture 已有增强信号，但未覆盖真实 vault、真实 Obsidian、人类对照、独立 Agent/来源登记、命名空间和投影所有权。 | 不执行 resolve。 | 先由用户确定 `#导航/...` 命名空间、Agent/来源身份登记和投影所有权；再复制稳定人类 vault 到一次性测试 vault，固定 Obsidian 版本和任务顺序，执行无 tag/确认 tag 交叉对照，记录完成率、步骤、错误跳转、冲突和页面增量。稳定 vault 不参与写入。 |
| `gap-9dc58ab149375bfd98332149a3ba6cb3`：PDF/Web/OCR | open | `252dbb4` 已合并页级 PDF 吸收：固定单元样例覆盖页码、中文、原生代码缩进、表格、扫描/混合页、适配器边界和失败类型。Web 只有未实现的适配协议；OCR 使用测试适配器，没有真实引擎的代码缩进/乱码率结果。 | 保持 open。PDF 功能与失败诊断可用，但组合 gap 所需的 Web、真实 OCR 与固定效果指标仍不完整。 | 不执行 resolve。 | 本地先对原生 PDF 建立冻结旧基线/当前实现对照，量化页码、字符、代码缩进、表格行和诊断准确率；真实 OCR 需先选择并固定引擎/模型，Web 需使用许可明确的静态快照并实现隔离适配器，然后使用同一指标。 |
| `gap-bb90bd3314185078a6a0a7cdb8d271e6`：Canvas/白板与解释可视化收益 | open | `62b1537/2094f90/1ca0c2c` 已形成一手来源审阅、JSON Canvas 1.0 合同和确定性原型；4 节点/3 边、路径泄漏 0、35 项专项测试和回滚探针通过。冻结 benchmark 的 `benchmark-summary.json` 明确是“真实 benchmark 必须替换”的示例。 | 保持 open。数据格式、许可证、权限边界、原型和评测合同已补齐；真实 Obsidian 中的人类可理解性与导航效率仍无结果。 | 不执行 resolve。 | 将冻结 run 中的 `OBSIDIAN_VERSION` 换成实测版本，在一次性 vault 中按两个序列收集每序列至少 2 个独立 session、每 assignment 至少 2 个 block；记录 12 题发现率、首次正确入口时间、导航次数、理解分、来源核验、无依据断言、稳定性和回滚。 |
| `gap-da2148a026de59c2b09fbf2cf3c1eb0b`：自动页面扩张 | resolved | `334cae7` 的 9 题对照中，扩张相对保守投影新增 9 页，正确率与来源蕴含率都保持 `1.0`，中位导航步骤却由 `2→3`；结论为 `retain-conservative`，回滚与字节一致重生成通过。 | 关闭结论与后续证据一致：实验得到退化结果并保留保守投影，不需要重新打开。 | 维持 resolved，不重复执行 resolve。 | 无。只有出现新的页面策略、用户任务或阈值时才另建新协议，不覆盖本次负面结果。 |
| `gap-e1a88b6c3b0e57cca58e6bc38daa47b8`：record 正文替换 | resolved | `94bf220` 已合并 `record --replace`。专项测试覆盖全角色替换、原子恢复、镜像、索引、漂移保护和幂等回滚；管理记录确认真实 staging 完成替换、回滚、再次替换，268 项完整回归通过。 | 关闭结论与实现、真实 staging 和回滚证据一致，不需要重新打开。 | 维持 resolved，不重复执行 resolve。 | 无。若将来需要跨类型移动或模糊匹配，应作为新能力另建 gap。 |

## 可执行关闭建议

本次没有新的 open gap 达到整体关闭条件。管理 Agent 只需维持两项既有 resolved 状态；五项 open 均保留，并按上表最小研究继续。尤其不能用以下证据替代缺失结论：

- 不能用 FastEmbed/BGE 的负面结果替代 QMD 实测；
- 不能用离线关键词回放或单次真实 canary 替代真实固定任务集与费用数据；
- 不能用隔离 Tag fixture 替代真实 Obsidian 人类对照；
- 不能用 PDF 单元合同替代 Web 与真实 OCR 效果；
- 不能把 Canvas 示例汇总当作真实 session 结果。

来源路径、哈希、外部版本和许可证见 [`sources.json`](sources.json)。
