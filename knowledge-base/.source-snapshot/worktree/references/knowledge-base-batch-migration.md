# 低版本完整知识库批量迁移

完整知识库批量迁移用于把多个已经完成的旧版 CKB OUTPUT 迁移到当前 CKB、Schema 和 Agent Protocol。它与只升级协议文件的 `agent-policy batch` 不同：本命令会在逐库 staging 中重建固定事实、图谱、审阅绑定、人类投影和双 SQLite，同时保留工作记录、reference、research gap、feedback、automation、operation journal、学习笔记与用户 Obsidian 文件。

## 命令

```powershell
& PYTHON scripts\ckb.py migrate batch plan `
  --manifest MANIFEST.json --write PLAN.json
& PYTHON scripts\ckb.py migrate batch apply `
  --plan PLAN.json --state BATCH-STATE.json
& PYTHON scripts\ckb.py migrate batch resume --state BATCH-STATE.json
& PYTHON scripts\ckb.py migrate batch status --state BATCH-STATE.json
& PYTHON scripts\ckb.py migrate batch audit --state BATCH-STATE.json
& PYTHON scripts\ckb.py migrate batch cutover `
  --state BATCH-STATE.json --project PROJECT_ID
& PYTHON scripts\ckb.py migrate batch rollback `
  --state BATCH-STATE.json --project PROJECT_ID
```

`--project` 可重复。省略时，`cutover` 选择全部 `ready` 项目，`rollback` 选择全部 `cutover-complete` 项目。批次按 `project_id` 排序；单库失败不会阻止其他独立项目继续。

## Manifest

Manifest schema 位于 `references/knowledge-base-batch-migration-manifest.schema.json`。每个项目必须显式绑定：

- 旧 OUTPUT、固定目标 repo 和独立 staging；
- 源/目标 CKB、Schema、Agent Protocol 与历史 release commit；
- 旧 OUTPUT 固定 commit/tree、目标 repo commit/tree、format 和完整 scope selectors；
- 锁定 Python、CKB、workspace roots 与 Harness；
- 旧 OUTPUT 全树摘要及恰好八个固定关键记录 SHA-256；`origin.records` 禁止额外键、绝对路径、反斜杠、`.`、`..` 和非规范相对路径，并在读取或哈希任何文件前完成键集检查；
- 允许的 `compatible-migration`、`delta-review`、`cold-build` 策略；
- cutover 备份根、rollback 隔离根和 Windows 路径上限。

路径和摘要必须由调用方在计划前显式生成，命令不会扫描 allowed roots 寻找项目。完整字段、必填项和禁止额外字段以 JSON Schema 为准。Runtime 还会在只读计划阶段计算每库实际 backup/quarantine 叶：同项目两个叶及跨项目所有恢复叶不得相等或嵌套；恢复根和投影叶不得等于、包含或位于任何生产 OUTPUT/staging 内。不同项目可以共享安全的 backup 父目录或 quarantine 父目录，因为各自使用不同 operation/project token 叶。

## 只读计划与版本决策

`plan` 不写目标 OUTPUT、repo 或 staging。它先核对固定八键和恢复拓扑，再核对旧 state、三个完成标记、全局审计、facts、graph、review pack、实体审阅绑定、双 SQLite integrity/foreign keys、人类/Markdown 镜像和 readability 记录；随后核对 manifest 全树与关键记录摘要、固定 repo、scope、runtime、路径边界和最长后代路径。畸形 `origin.records` 在形成外部路径或读取文件前失败，畸形恢复拓扑在写 state、staging、backup 或 control 前失败。

版本矩阵位于 `references/knowledge-base-batch-migration-versions.json`。每行绑定历史 commit，不接受只修改当前 state 版本号得到的伪旧库。当前兼容链包含 `5.1.4/Schema 4/Protocol 1.0.0`、`5.2.9/4/1.3.0`、两个有不同协议来源的 `5.3.0` 检查点和 `5.4.0/4/1.5.0`。`5.1.1` 没有 Agent Protocol，固定进入 `cold-build-required`。未知组合或缺失链进入 `awaiting-review`；目标不是当前版本、摘要漂移或缺失完成门则固定失败。

## Apply、审阅与 Resume

`apply` 只写项目 staging、批次 state 和 OUTPUT 同级的 owner-token 锁锚点。它不会覆盖生产 OUTPUT，也不会提前修改外部 workspace 指令。

- `compatible-migration` 复用路径、语言、Git blob 和旧 parse 状态完全一致的事实；审阅还要求实体键和 page/appendix 字段形状兼容。
- 目标 commit 改变、新增实体或审阅形状变化时生成 `delta-*` pack，并返回 `review-pending`。
- `cold-build` 从固定 repo/commit 和旧 scope/page config 重新构建，复用事实数和审阅数固定为零；全部实体重新进入审阅。

Agent 提交完 `delta-*` 或 cold-build review 后运行 `resume`。它重新计算精确复用/delta 集合，执行普通 `finalize`，再运行三个完成标记、双 SQLite、人类/Markdown、readability、reference、gap、operation journal、Agent Policy 和 `maintain` 门。中断在 `applying` 的 staging 只有在批次 state 与 operation ID 相符时才由 `resume` 清理并重建；不相符的既有 staging 固定失败。

## Cutover 与 Rollback

每个 OUTPUT 使用独立的、位于 OUTPUT 同级的 owner-token descriptor 锁。锁不放在待改名目录内部，因此 Windows 可以执行同卷原子目录改名；锁记录仍沿用 PID、owner token、进程启动标识、主机和 stale owner 核验合同。

`cutover` 只接受 `ready` staging。它依次重算旧 OUTPUT 与 staging 全树，备份 OUTPUT 和外部 workspace 的 Agent Protocol 管理文件，原子改名两个目录，重定位 OUTPUT 自有绝对路径并升级当前 Agent Protocol，再复查双 SQLite、Agent Policy 与 `maintain`。任一步失败只恢复当前项目；`cutover-failed-restored` 可以用同一 state 重试，失败尝试保留在控制记录中。

`rollback` 先要求当前新 OUTPUT 全树、外部协议管理摘要和旧备份都未漂移，再把新 OUTPUT 移入 operation 专属隔离目录、恢复旧完整树和协议管理文件。后续用户修改、备份变化或不是活动链顶的旧批次都会阻止覆盖。成功恢复后，旧 OUTPUT 的每个文件字节、可变层、协议记录和双 SQLite 与切换前一致；父操作的 `modified_manifest` 会重新成为活动链顶。
