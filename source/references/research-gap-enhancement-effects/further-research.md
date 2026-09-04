# 进一步研究结果与最小决策

## 本地已完成研究

### 原生 PDF 冻结效果对照

协议：`tests/fixtures/research-gap-enhancement-effects/pdf-native-v1.json`。

运行入口：`tests/benchmark_reference_pdf_effect.py`。

```text
C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe -X utf8 tests\benchmark_reference_pdf_effect.py --protocol tests\fixtures\research-gap-enhancement-effects\pdf-native-v1.json --raw references\research-gap-enhancement-effects\pdf-native-v1\raw-results.json --report references\research-gap-enhancement-effects\pdf-native-v1\report.json --git "C:\Program Files\Git\cmd\git.exe"
```

退出状态为 0，报告 `status=passed`。旧基线 `8ac58b9` 不含页级 PDF 模块；当前实现 blob 与 `bdd4a667` 完全一致。benchmark 从实际运行模块和 distribution metadata 读取到 `pypdf/6.16.2`，raw/report 同时保存冻结 expected、运行时 actual、提取 manifest 和匹配结果；`parser_identity_matches_protocol=true` 是完成门。固定原生样例的页码定位、中文行、代码行、四空格代码缩进、表格行和 7 类诊断准确率均为 `1.0`。原始逐项结果位于 [`pdf-native-v1/raw-results.json`](pdf-native-v1/raw-results.json)，聚合报告位于 [`pdf-native-v1/report.json`](pdf-native-v1/report.json)。

固定负例 `tests/fixtures/research-gap-enhancement-effects/pdf-native-v1-parser-drift.json` 把期望版本设为 `6.16.2-drift`。实际 runtime 仍返回 `6.16.2` 时，唯一失败门为 `parser_identity_matches_protocol`，入口退出状态为 1、`written=false`，既有 raw/report 字节保持不变。

这项结果把原生 PDF 子项判为“已证实增强”，但不改变组合 gap：真实 OCR 调用为 0，Web 抓取调用为 0。

### QMD 2.8.3 可运行性准备

已确认：

- npm 包 `@tobilu/qmd@2.8.3`，MIT，要求 Node `>=22.0.0`；本机 Node 为 `24.19.0`。
- tag `v2.8.3` 指向提交 `facd35e01359e59d938bc9418e93fb9318addee3`。
- 当前 PATH 没有 `qmd`；没有 QMD 模型缓存用于本实验。
- 隔离 `npm exec` smoke 在超过 180 秒且无 stdout/stderr 后人工中止，退出状态 130；临时 HOME 与 npm cache 均已清理，残留进程为 0。

因此当前只确认版本、许可证、Node 前置条件和可执行命令形状，QMD 引擎可用性与检索效果仍是“证据不足”。没有下载默认约 300 MB 的向量模型，也没有把 FastEmbed/BGE 结果归给 QMD。

建议固定命令形状：

```text
npm exec --yes --package=@tobilu/qmd@2.8.3 -- qmd collection add ENTITY_MARKDOWN_ROOT --name ckb-gap-vector-v1
npm exec --yes --package=@tobilu/qmd@2.8.3 -- qmd embed -c ckb-gap-vector-v1
npm exec --yes --package=@tobilu/qmd@2.8.3 -- qmd vsearch --json -n 8 -c ckb-gap-vector-v1 "QUESTION"
npm exec --yes --package=@tobilu/qmd@2.8.3 -- qmd query --no-rerank --json -n 8 -c ckb-gap-vector-v1 "QUESTION"
```

运行前需确定临时软件/模型缓存目录、下载字节上限和最长索引时间。语料必须由现有向量实验的 1,937 个实体文本确定性投影，问题与相关性标签复用现有 12 题，避免把 Markdown 页面粒度变化混进引擎比较。

## 需要最小外部输入的研究

### 真实 LLM 关键词固定任务集

已有一题真实 benchmark，基线与慢路径质量都为 `1.0`，冷调用约 `54.3 s`；它只证明这一题无增益。继续运行前需要三个值：

1. `MAX_REAL_CALLS`：允许的真实冷调用上限，建议 12；
2. `MAX_COST_USD`：硬费用上限；
3. `TELEMETRY_PROVIDER`：能返回 input/output token 和费用的 Provider/旁路，不能继续把未报告的 0 当作零消耗。

输入确定后复用现有 12 题、相关性标签和当前确定性基线；逐题保存质量、冷/热延迟、token、费用、失败类型与缓存命中。

### 真实 OCR 与 Web

真实 OCR 需要固定 `OCR_ENGINE`、`OCR_MODEL_OR_LANGUAGE_PACK`、版本、许可证和下载上限。最小样例应包含：四空格与八空格代码、空行、等宽/比例字体、中文注释、表格、低分辨率与旋转页；指标至少包括字符错误率、行召回、缩进深度准确率、表格行准确率、页码定位和失败诊断。

Web 需要一组许可明确、响应体哈希固定的 HTML/PDF 静态快照，以及隔离适配器实现。必须记录 requested/final URL、状态码、media type、响应大小和 SHA-256；不以实时网页变化作为同一冻结实验输入。

### 真实 Obsidian Tag

开始真实 vault 对照前需要三个互斥决策：

- tag 命名空间：建议只使用 `#导航/...`，不复用 `#类型/...`；
- Agent/来源身份：确定何种身份算独立 Agent、何种文件或提交算独立来源；
- 投影所有权：生成器只读导出，或允许人类编辑后回收差异。

确定后把稳定人类 vault 复制到一次性测试 vault，固定 Obsidian 版本；稳定知识库保持只读。沿用现有 6 题可做首轮兼容验证，但关闭 gap 需要真实人类的无 tag/tag 交叉对照。

### 真实 Obsidian Canvas

现有 12 题协议、四种 assignment、指标和门均已冻结。最小输入是实际 `OBSIDIAN_VERSION` 和参与 session。正式汇总要求：两个 sequence 每个至少 2 个独立 session、每个 assignment 至少 2 个 block；同一参与者重复时相隔至少 24 小时，不同参与者可免除等待。仓库内示例 summary 只用于 schema，不能进入效果矩阵。

## 本轮停止点

原生 PDF 是唯一同时满足“缺少效果数据、无需新增外部依赖、可在本地完成”的子项，已经完成测量。其余项目分别卡在模型下载、真实调用预算/费用 telemetry、真实 OCR 引擎或人类 Obsidian session；继续自动执行会改变成本或比较对象，因此停在以上已冻结输入和最小决策处。
