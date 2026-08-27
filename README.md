# Code Knowledge Builder 5.1.2

这是 `code-knowledge-builder` 的私有可审计发布快照，包含当前源码与由该源码为自身构建的中文知识库。

## 内容

- `source/`：Skill 源码，原始源码提交为 `2711ced13be680d3737d1cce98fc0c23dc4c3365`。
- `knowledge-base/`：5.1.2 自身知识库；状态为 `complete`，全局审计与增量迁移审计均为 `passed`。
- `knowledge-base/human/`：面向人的简体中文 Markdown/Obsidian 知识库。
- `knowledge-base/machine/knowledge.sqlite`：面向 Agent 的完整机器知识库。
- `knowledge-base/agent-index.sqlite`：确定性 SQLite/FTS 检索索引。
- `delivery/`：从空基线生成的源码补丁、安装记录和可执行回滚脚本。

当前图谱包含 31 个源码文件、467 个实体、1,899 条关系、474 份机器文档和 1,546 个检索段。自动化数据库在发布时保持空闲基线：事件、会话、轮次和待审阅项均为 0。

## Hook 边界

会话/修改自动同步同时要求：

1. 项目已经登记；
2. 当前 Harness 会话明确应用 `code-knowledge-builder` Skill。

普通文本提及不会激活同步。激活按 Harness 会话隔离，另一会话需要独立激活。

## 大文件

仓库使用 Git LFS 保存 `*.zip` 与 `*.sqlite`。克隆前请安装 Git LFS，然后执行：

```powershell
git lfs install
git clone https://github.com/dddeath/code-knowledge-builder.git
```

## 快速验证

```powershell
$py = 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.0.0\python\python.exe'
& $py -X utf8 .\source\scripts\ckb.py doctor --json
& $py -X utf8 .\source\scripts\ckb.py migrate status --out .\knowledge-base
& $py -X utf8 .\source\scripts\ckb.py automation status --out .\knowledge-base
```

知识库的 `.complete`、`.machine.complete` 与 `.human.complete` 只在相应审计门通过后存在。
