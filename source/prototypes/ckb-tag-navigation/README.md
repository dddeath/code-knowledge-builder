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

## 接近真实规模的三臂隔离实验

`study` 从已完成知识库的 `human` vault 复制三份隔离样本，只读打开 `machine/knowledge.sqlite`，并在复制品中比较：

1. `no_tag`：不增加实验 tag；
2. `machine_tag`：投影所有机器候选 tag；
3. `confirmed_tag`：只投影通过支持/不支持票阈值的 tag。

协议固定任务顺序、两跳预算、候选排序、证据时点和判定规则。运行器记录可发现性、点击或跳转步数、错误导航、`pages/` 孤立页、tag 数量与确定性审计工作量。结果字段 `effect_claim=system-navigation-proxy-only`，没有真实人类任务记录时，`human_result` 固定为 `pending-human-validation`。

隔离副本会删除指向稳定知识库的 `.ckb/output-contract.json` 与 companion 插件目录，并禁用 community plugin，避免打开实验 vault 时连接生产输出。稳定来源在运行前后都重新计算 vault、完成标记和机器 SQLite 的 SHA-256；发生漂移时整次运行失败。

```powershell
$Python = 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe'
$Cli = 'prototypes\ckb-tag-navigation\scripts\ckb_tag_navigation.py'
$Protocol = 'tests\fixtures\tag-navigation-real-vault\protocol.json'
$Policy = 'tests\fixtures\tag-navigation\policy.json'
$Run = 'prototypes\ckb-tag-navigation\.real-vault-run'

& $Python -X utf8 $Cli study `
  --source-output 'E:\knowledge_builder\self-workspace\knowledge-base' `
  --protocol $Protocol --policy $Policy --out $Run `
  --workspace-root 'prototypes\ckb-tag-navigation'
```

整个隔离运行目录的可执行回滚：

```powershell
& $Python -X utf8 $Cli study-rollback `
  --manifest "$Run\study.rollback.json" `
  --workspace-root 'prototypes\ckb-tag-navigation'
```

回滚会重算目录摘要；实验结果已有任何漂移时返回 `ROLLBACK_DRIFT` 并保留现场。
