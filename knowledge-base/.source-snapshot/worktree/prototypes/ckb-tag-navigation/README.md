# CKB tag 导航隔离原型

该原型把 tag assertion 写入任务自有 SQLite，重放 Agent 的 propose、vote 和 retract，按冻结阈值生成四态审计，再把 `confirmed` tag 投影为独立 JSON。它不导入 `scripts/ckb.py`，不写稳定知识库，也不修改现有 Markdown、Obsidian companion 或 Canvas 原型。

## 命令

```powershell
$Python = 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe'
$Cli = 'E:\knowledge_builder\self-workspace\worktrees\tag-navigation-research\prototypes\ckb-tag-navigation\scripts\ckb_tag_navigation.py'
$Fixture = 'E:\knowledge_builder\self-workspace\worktrees\tag-navigation-research\tests\fixtures\tag-navigation'
$Out = 'E:\knowledge_builder\self-workspace\worktrees\tag-navigation-research\artifacts\tag-navigation-run'

& $Python -X utf8 $Cli replay --input "$Fixture\assertions.jsonl" --database "$Out\tags.sqlite" --rollback-manifest "$Out\tags.rollback.json" --workspace-root $Out
& $Python -X utf8 $Cli audit --database "$Out\tags.sqlite" --policy "$Fixture\policy.json" --current-commit 19152b227ccf687e7e4d89337d421c22a4e1a75f --as-of 2026-09-03T00:00:00Z --out "$Out\audit.json" --workspace-root $Out
& $Python -X utf8 $Cli project --audit "$Out\audit.json" --policy "$Fixture\policy.json" --out "$Out\projection.json" --workspace-root $Out
& $Python -X utf8 $Cli benchmark --fixture "$Fixture\navigation-benchmark.json" --records "$Fixture\navigation-records.jsonl" --out "$Out\benchmark.json" --workspace-root $Out
```

SQLite 目标回滚：

```powershell
& $Python -X utf8 $Cli rollback --manifest "$Out\tags.rollback.json" --workspace-root $Out
```

回滚先读取并校验 manifest，再要求 manifest、target 和非空 backup 都位于 `--workspace-root`。越界返回 `ROLLBACK_PATH_OUTSIDE_WORKSPACE`；目标字节发生变化时返回 `ROLLBACK_DRIFT`。两种失败都保留当前文件。

`replay` 在 manifest 写入失败时先把 baseline 复制到独立 `.restore.tmp`，核对 hash 后再原子替换数据库。恢复成功才清理 backup 和临时文件；恢复 copy 或 hash 校验失败时返回 `REPLAY_RECOVERY_FAILED`，保留 baseline backup、当前数据库和诊断文件。

## 状态与投影

- `candidate`：已有 proposal 或未满足全部确认门的有效 support；
- `confirmed`：票数、独立 Agent、独立来源、反对比例、commit 与时效全部通过；
- `contested`：有效反对比例超过阈值；
- `deprecated`：曾有 vote，但当前没有可用 support。

人类投影只含 confirmed tag，每页使用固定配额。投影中的 `#导航/...` 只是实验显示值，不会写回人类页面。
