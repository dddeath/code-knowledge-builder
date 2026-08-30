# Code Knowledge Builder 5.3.0

这是 `code-knowledge-builder` 的私有可审计发布快照，包含 5.3.0 当前源码、项目自身知识库，以及补丁、验证与回滚交付。

## 本版更新

5.3.0 新增审阅式本地 Markdown/TXT 资料吸收：原文按字节保存，Agent 逐条核对中文主张、行范围与原文，单来源最多生成一个摘要页；审阅结果进入 SQLite FTS，并支持显式修订和可恢复回滚。未通过资料审计时不会生成资料完成标记。

既有确定性快速检索、双层知识库、跨 Harness 会话/修改采集和 Obsidian 配套能力保持可用。

## 内容

- `source/`：Code Knowledge Builder 5.3.0 源码。
- `knowledge-base/`：当前项目自身知识库。固定代码图仍来自既有审阅快照；人类页面、机器索引、工作记录、参考资料层和维护记录已更新到当前发布。
- `knowledge-base/human/`：面向人的简体中文 Markdown/Obsidian 知识库。
- `knowledge-base/machine/knowledge.sqlite`：面向 Agent 的 SQLite/FTS 知识库。
- `delivery/`：补丁、验证记录、知识库维护结果、包校验和回滚脚本。

当前机器层保存 31 个源码文件、483 个实体、1985 条关系、522 份文档和 2118 个检索段；工作记录 38 篇，已审阅参考来源 1 个，待审阅来源 0 个。

## 知识库真实性边界

自身知识库的固定代码图 commit 为发布清单中的 `knowledge_graph_commit`，并未为 5.3.0 重新执行全仓解析。5.3.0 新功能通过已审阅工作记录、资料页、SQLite 文档和维护门进入当前知识库。需要完整重建代码实体图时，应在目标机器上重新运行分段构建与 Agent 审阅。

## Git LFS

仓库使用 Git LFS 保存 `*.zip` 和 `*.sqlite`。克隆前请安装 Git LFS。Release 中另附 lite/full 安装包。

## 快速验证

```powershell
$py = 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.0.0\python\python.exe'
& $py -X utf8 .\source\scripts\ckb.py doctor --json
& $py -X utf8 .\source\scripts\ckb.py reference audit --out .\knowledge-base
& $py -X utf8 .\source\scripts\ckb.py maintain --out .\knowledge-base
```

知识库的 `.complete`、`.machine.complete`、`.human.complete` 和 `references/.complete` 只在相应审计门通过后存在。本地源码链接保存构建机路径；在另一台机器执行源码定位前，需要重建或显式重定位。
