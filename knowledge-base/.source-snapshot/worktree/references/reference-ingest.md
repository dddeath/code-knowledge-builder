# 审阅文本参考资料层

## 目标与边界

参考资料层把用户主动提供的本地 UTF-8 Markdown/TXT 纳入独立来源、审阅、摘要和机器检索流程。它复用 CKB 的 human/markdown 镜像、SQLite FTS、Agent pack、中文门和维护审计，但不会把外部资料写入代码 `files`、`entities` 或 `source_ranges`。

第一版固定边界：

- 只接收本地 `.md` 和 `.txt`；
- 单文件上限 2 MiB；
- 必须提供标题、来源和明确许可证；
- 原文字节归档后保持不变；
- Agent 必须逐项核实精确行范围和原文；
- 每个活动来源最多一个人类摘要页；
- 不抓网页，不解析 PDF，不执行 OCR；
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

首次返回退出码 `4` 和 `pending-agent-review`。命令会写入：

```text
OUTPUT/references/raw/
OUTPUT/references/manifests/
OUTPUT/references/review-templates/
OUTPUT/references/transactions/
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

摘要页不显示 reference ID、摘要哈希或内部状态。每项关键结论提供可点击的归档原文行范围。

## 许可与来源

`--license` 必须是明确 SPDX 标识或具体用户许可声明。`unknown`、`none`、`待定` 等值保持输入失败。第一版归档全文，因此导入者必须确认具有本地保存全文和生成摘要的权限。

机器 manifest 保留原文字节摘要以检查来源漂移；人类页面只显示资料来源、作者或组织、许可证和原文入口。

## 幂等与修订

相同标题、来源、许可证和原文字节重复导入时返回原记录，不创建新文件或页面。

同一标题与来源的原文发生变化时，使用：

```powershell
& PYTHON scripts\ckb.py reference ingest ... --revision-of PREVIOUS_REFERENCE_ID
```

新修订在审阅前不替换旧摘要。新修订通过后，旧 manifest 变为 `superseded`，人类层仍只有一个活动摘要页。回滚新修订会恢复旧摘要。

## 检索与维护

参考资料写入 `machine/knowledge.sqlite` 的 `reference_sources`、`documents`、`sections` 和 `section_fts`。`brief`/`retrieve` 可以在没有代码实体命中的情况下直接返回已审阅资料，并在 Agent pack 中标记“已审阅参考资料”和归档原文范围。

```powershell
& PYTHON scripts\ckb.py brief --out OUTPUT "资料中的稳定关键词" --budget 1800 --profile fast
& PYTHON scripts\ckb.py reference list --out OUTPUT --status all
& PYTHON scripts\ckb.py reference audit --out OUTPUT
& PYTHON scripts\ckb.py maintain --out OUTPUT
```

`maintain` 把参考资料门纳入聚合结果。存在待审阅、原文漂移、许可缺失、引用范围不符、镜像差异、页面配额超限或 SQLite 计数漂移时，维护状态不会为 `passed`。

## 回滚

```powershell
& PYTHON scripts\ckb.py reference rollback --out OUTPUT --reference REFERENCE_ID
```

回滚删除该修订的归档副本、manifest、审阅模板、审阅记录和事务记录，重新生成参考资料导览、摘要页与两个 SQLite 索引。若该修订替代上一版，则恢复上一版；其他代码知识、Agent 笔记、Obsidian 设置和插件目录保持不变。

## 完成门

- 原文是 1..2 MiB 的有效 UTF-8 Markdown/TXT；
- 标题、来源和许可证明确；
- 原文字节与 manifest 一致；
- `summary_zh`、`claim_zh` 和 `evidence_note` 使用简体中文；
- 每项 `source_text` 精确等于对应行范围；
- 每个活动来源恰好一个摘要页；
- human/markdown 摘要与 `REFERENCES.md` 字节一致；
- 人类页不暴露机器 ID 或长哈希；
- `reference_sources` 数量等于 manifest 数量；
- `documents(kind='reference')` 数量等于活动来源数量；
- `section_fts` 与原文章节一致；
- 重复导入幂等，修订替换和回滚可验证；
- `reference audit` 与 `maintain` 均通过。
