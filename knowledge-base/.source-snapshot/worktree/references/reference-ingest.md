# 审阅本地参考资料层

## 目标与边界

参考资料层把用户主动提供的本地 UTF-8 Markdown/TXT 和 PDF 纳入独立来源、审阅、摘要和机器检索流程。它复用 CKB 的 human/markdown 镜像、SQLite FTS、Agent pack、中文门和维护审计，但不会把外部资料写入代码 `files`、`entities` 或 `source_ranges`。

当前固定边界：

- 接收本地 `.md`、`.txt` 和 `.pdf`；
- Markdown/TXT 单文件上限 2 MiB，PDF 默认上限 32 MiB、400 页，并有不可越过的绝对上限；
- 必须提供标题、来源和明确许可证；
- 原文字节归档后保持不变；
- Markdown/TXT 逐项核实精确行范围；PDF 逐项核实页码、片段 ID、字符范围和原文摘录；
- 每个活动来源最多一个人类摘要页；
- PDF 首先逐页提取原生文本，只有没有达到确定性可用阈值的页面才进入显式启用的 OCR adapter；
- CKB 不内置 OCR 引擎；未配置、超时、取消、超页数或超大小的 OCR 页面保持 `pending`；
- 不抓取网页；`web-snapshot-v1` 只冻结“网络层生成不可变本地文件，再进入同一审阅流程”的 adapter 合同；
- 不自动创建概念页或实体页；
- 参考资料和代码事实在机器层保持不同类型。

## 导入与审阅

导入一个来源：

```powershell
& PYTHON scripts\ckb.py reference ingest `
  --out OUTPUT `
  --source DOCUMENT.md `
  --title "资料标题" `
  --origin "用户提供的本地资料" `
  --license "CC-BY-4.0" `
  --author "作者或组织"
```

导入 PDF 时可显式约束来源目录、输入大小和页数：

```powershell
& PYTHON scripts\ckb.py reference ingest `
  --out OUTPUT `
  --source DOCUMENT.pdf `
  --source-root LOCAL_INPUT_ROOT `
  --title "资料标题" `
  --origin "用户提供的本地 PDF" `
  --license "CC-BY-4.0" `
  --pdf-max-bytes 33554432 `
  --pdf-max-pages 400
```

原生文本不足的页面默认保持待处理。只有调用者明确传入 `--pdf-ocr` 才尝试 OCR；adapter 是本地 Python 文件，接收 `--source`、`--page`、`--output`、`--schema-version` 和可选 `--cancel-file`，并写出一页 JSON：

```powershell
& PYTHON scripts\ckb.py reference ingest `
  --out OUTPUT --source SCANNED.pdf `
  --title "扫描资料" --origin "本地扫描件" --license "CC-BY-4.0" `
  --pdf-ocr --pdf-ocr-adapter OCR_ADAPTER.py `
  --pdf-ocr-max-pages 12 `
  --pdf-ocr-timeout-seconds 30 `
  --pdf-ocr-max-input-bytes 16777216 `
  --pdf-ocr-cancel-file CANCEL.flag
```

OCR adapter 的输出合同：

```json
{
  "schema_version": 1,
  "status": "extracted",
  "page_number": 3,
  "text": "该页 OCR 得到的原始文本",
  "confidence": 0.93
}
```

同一来源已经生成 pending manifest 后，重复 `reference ingest` 仍保持幂等，不会在原记录上原地重跑 OCR。返回值中的 `next_steps` 固定为两个现有命令：先对该 reference ID 执行定向 `reference rollback`，再用相同来源、标题、来源说明、许可和修订关系执行带 `--pdf-ocr`、adapter 及新上限的 `reference ingest`。这样不会把半完成 extraction 目录原地替换，也不会影响其他 reference 来源。

首次返回退出码 `4` 和 `pending-agent-review`。命令会写入：

```text
OUTPUT/references/raw/
OUTPUT/references/manifests/
OUTPUT/references/review-templates/
OUTPUT/references/transactions/
OUTPUT/references/extractions/REFERENCE_ID/manifest.json
OUTPUT/references/extractions/REFERENCE_ID/pages/page-0001.txt
```

复制审阅模板到工作文件：

```powershell
& PYTHON scripts\ckb.py reference review-template `
  --out OUTPUT --reference REFERENCE_ID --write REVIEW.json
```

Agent 重新打开归档原文后填写：

```json
{
  "schema_version": 1,
  "reference_id": "REFERENCE_ID",
  "status": "agent-reviewed",
  "title": "资料标题",
  "source_file": "OUTPUT/references/raw/资料标题--r1.md",
  "source_sha256": "机器字段保留模板值",
  "summary_zh": "这份资料用简体中文说明一个经过原文核实的主题。",
  "claims": [
    {
      "claim_zh": "资料明确提出一项可核验结论。",
      "start_line": 3,
      "end_line": 5,
      "source_text": "归档原文第 3 至 5 行的精确文本",
      "evidence_note": "已重新打开归档原文第 3 至 5 行并核对该结论。"
    }
  ]
}
```

PDF 审阅项使用页级定位，不使用伪造的 PDF 行号：

```json
{
  "claim_zh": "资料第二页明确提出一项可核验结论。",
  "page_number": 2,
  "fragment_id": "reference-fragment-...",
  "start_offset": 120,
  "end_offset": 168,
  "source_text": "提取页文件中 120:168 的精确文本",
  "evidence_note": "已重新打开归档 PDF 第二页并核对该片段。"
}
```

提交审阅：

```powershell
& PYTHON scripts\ckb.py reference review --out OUTPUT --review REVIEW.json
```

通过后生成：

```text
OUTPUT/human/REFERENCES.md
OUTPUT/human/references/资料标题.md
OUTPUT/markdown/REFERENCES.md
OUTPUT/markdown/references/资料标题.md
OUTPUT/references/reviews/REFERENCE_ID.json
OUTPUT/references/projection.json
OUTPUT/references/audit.json
```

摘要页不显示 reference ID、摘要哈希或内部状态。每项关键结论提供可点击的归档原文行范围或 PDF 页码。标题、段落、列表、代码和表格边界由确定性规则分类；仅从版面推断的边界在机器 extraction manifest 中保留低或中置信标记，人类页不会把该标记提升为事实。

## PDF 页级 extraction manifest

PDF extraction manifest 记录解析器版本、输入哈希、页数、待处理页、上限以及逐页结果。每个片段至少包含：

- `source_id`、归档 `source_file` 和一基 `page_number`；
- `method`：`native` 或显式启用的 `ocr`；
- `confidence` 和独立的 `structure_confidence`；
- 页文本内零基、右开区间 `text_range`；
- 保持原始非空行、缩进和列间距的 `text`；
- `heading`、`paragraph`、`list`、`code`、`table` 或 `raw` 结构类型；
- 结构判断依据不足时的 `warnings`。

原生文本低于最小非空字符数、可打印字符比例或乱码阈值时不会进入已审阅索引。扫描页、混合 PDF 中的空文本页、OCR 低置信页以及未配置 OCR runtime 的页面均保留具体 `reason` 和 `pending_pages`，`reference review` 会拒绝提交仍有 pending 页的 PDF。

## 许可与来源

`--license` 必须是明确 SPDX 标识或具体用户许可声明。`unknown`、`none`、`待定` 等值保持输入失败。当前流程归档全文，因此导入者必须确认具有本地保存全文和生成摘要的权限。

机器 manifest 保留原文字节摘要以检查来源漂移；人类页面只显示资料来源、作者或组织、许可证和原文入口。

## 幂等与修订

相同标题、来源、许可证和原文字节重复导入时返回原记录，不创建新文件或页面。

同一标题与来源的原文发生变化时，使用：

```powershell
& PYTHON scripts\ckb.py reference ingest ... --revision-of PREVIOUS_REFERENCE_ID
```

新修订在审阅前不替换旧摘要。新修订通过后，旧 manifest 变为 `superseded`，人类层仍只有一个活动摘要页。回滚新修订会恢复旧摘要。

## 检索与维护

参考资料写入 `machine/knowledge.sqlite` 的 `reference_sources`、`documents`、`sections` 和 `section_fts`。PDF 的 `sections.start_line/end_line` 均保存对应页码，`source_path` 指向归档 PDF；片段正文保持在 section 与 FTS 中。`brief`/`retrieve` 可以在没有代码实体命中的情况下直接返回已审阅资料，并在 Agent pack 中标记“已审阅参考资料”和归档原文范围。

```powershell
& PYTHON scripts\ckb.py brief --out OUTPUT "资料中的稳定关键词" --budget 1800 --profile fast
& PYTHON scripts\ckb.py reference list --out OUTPUT --status all
& PYTHON scripts\ckb.py reference audit --out OUTPUT
& PYTHON scripts\ckb.py maintain --out OUTPUT
```

`maintain` 把参考资料门纳入聚合结果。存在待审阅、原文或 extraction manifest 漂移、丢页、重复页、空提取片段、路径越界、许可缺失、引用范围不符、镜像差异、页面配额超限或 SQLite 计数漂移时，维护状态不会为 `passed`。

## 回滚

```powershell
& PYTHON scripts\ckb.py reference rollback --out OUTPUT --reference REFERENCE_ID
```

回滚删除该修订的归档副本、文档 manifest、页级 extraction 目录、审阅模板、审阅记录和事务记录，重新生成参考资料导览、摘要页与两个 SQLite 索引。若该修订替代上一版，则恢复上一版；其他代码知识、Agent 笔记、Obsidian 设置和插件目录保持不变。

## 完成门

- 原文是 1..2 MiB 的有效 UTF-8 Markdown/TXT，或通过大小、页数、加密和损坏检查的 PDF；
- 标题、来源和许可证明确；
- 原文字节与 manifest 一致；
- `summary_zh`、`claim_zh` 和 `evidence_note` 使用简体中文；
- 每项 `source_text` 精确等于对应行范围，或对应 PDF 页片段内的字符范围；
- PDF 页号连续且无重复，每个页文本和片段范围均可由哈希与路径重新定位；
- 待 OCR、低置信或无文本页面不能提交为 `agent-reviewed`；
- 每个活动来源恰好一个摘要页；
- human/markdown 摘要与 `REFERENCES.md` 字节一致；
- 人类页不暴露机器 ID 或长哈希；
- `reference_sources` 数量等于 manifest 数量；
- `documents(kind='reference')` 数量等于活动来源数量；
- `section_fts` 与原文章节一致；
- 重复导入幂等，修订替换和回滚可验证；
- `reference audit` 与 `maintain` 均通过。
