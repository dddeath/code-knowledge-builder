# Code Knowledge Builder 5.3.0

本版在既有纯确定性检索、双层知识库、跨 Harness Hook 与 Obsidian 工作流上，增加经过 Agent 逐来源审阅的本地 Markdown/TXT 资料吸收。

## 主要变化

- 新增 `reference ingest/review-template/review/audit/list/rollback`。
- 资料先按原始字节保存，未审阅时保持 `pending-agent-review`，不会生成完成标记。
- 审阅主张必须绑定原文行范围，`source_text` 与保存原文逐字一致。
- 每个来源最多生成一个中文摘要页，机器层使用 SQLite FTS 分段检索。
- 支持显式修订、旧版本 supersede、恢复上一版本和首版本完整回滚。
- Agent 协议升级到 1.4.0，维护门纳入资料层审计。

## 自身知识库边界

仓库中的当前知识库复用既有固定源码图，并追加了迁移后的人类页面、机器索引、工作记录、参考资料和 5.3.0 维护记录。固定图并非针对 5.3.0 重新全量扫描；该边界同时记录在知识库和发布清单中。

## 发行资产

- `code-knowledge-builder-lite-5.3.0.zip`
- `code-knowledge-builder-full-win-x64-5.3.0.zip`
- `code-knowledge-builder-5.3.0-reference-ingest.patch`
- `verification-record-5.3.0.json`
- `rollback-code-knowledge-builder-5.3.0.ps1`

精确大小和 SHA-256 见 `delivery/package-verification-5.3.0.json`。
