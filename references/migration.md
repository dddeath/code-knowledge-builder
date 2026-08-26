# 5.x 知识库增量迁移

当旧知识库已经通过全局审计，而目标 Git commit 只修改了部分文件时，使用增量迁移。迁移复用完全相同 Git blob 的语法事实和 Agent 中文审阅；修改、新增、删除及分类形状变化的实体重新进入构建和审阅。最终结果执行与冷启动构建完全相同的当前版本审计门。

## 启动

```powershell
& PYTHON scripts\ckb.py migrate start `
  --from-out "OLD_OUTPUT" `
  --repo "NEW_CLEAN_GIT_REPOSITORY" `
  --out "STAGING_OUTPUT"
```

命令继承旧 `scope.json` 的路径、入口、扩展方向、C# 选项、格式和固定 `page-config.json`。`--format` 只在用户明确希望改变投影格式时覆盖旧值。

迁移只接受同时存在 `.complete`、`catalog.json`、`state.json` 和 `audit/global.json: passed` 的旧输出。目标仓库仍须是干净 Git commit，暂存输出与源码仓库保持不重叠。

## 精确复用规则

语法事实只在以下字段全部一致时复用：

- 相对路径；
- 语言；
- Git blob；
- 旧 parse 状态为 `passed`。

复用文件的 commit-sensitive 文件 ID、实体 ID、父实体 ID、页面所有者和关系端点全部按目标 commit 重建。旧 ID 只保存在机器迁移映射中，不进入人类页面。

Agent 审阅进一步要求实体 kind、名称、限定名、字节范围和审阅字段形状一致。`page` 与 `boundary` 共享叙述字段形状；`appendix` 只复用一句话说明。页面与附录之间发生晋升或降级时，该实体进入 delta 审阅。

## 可变知识

迁移保存生成器所有权清单之外的 Obsidian 文件、analysis/change/pitfall/experiment/session/user 页面、workspace notes、pending notes、session sidecar 和自动化数据库。SQLite 使用 backup API 复制后再执行当前 schema 初始化。目标人类标题变化时，迁移器依据相对源码路径、实体类型和限定名确定性重写保留笔记中的 Wiki 链接，并记录 `migration/note-relink.json`；正文叙述保持原样。固定源码 overlay 不从旧仓库继承，由目标仓库重新生成。

## 审阅与完成

迁移把 review pack 重分为：

- `migrated-*`：精确证据复用，脚本自动提交并重新运行普通 review-pack 源码门；
- `delta-*`：变更、新增或字段形状变化，保持 `pending-agent-review`。

```powershell
& PYTHON scripts\ckb.py migrate status --out "STAGING_OUTPUT"
& PYTHON scripts\ckb.py review-pack --out "STAGING_OUTPUT" --pack "DELTA_PACK" --review "REVIEW.json"
& PYTHON scripts\ckb.py merge --out "STAGING_OUTPUT"
& PYTHON scripts\ckb.py migrate audit --out "STAGING_OUTPUT"
& PYTHON scripts\ckb.py finalize --out "STAGING_OUTPUT"
```

普通 `finalize` 会额外执行 `incremental-migration` 门，然后继续执行全部当前版本 chunk、来源、中文、Graphify、SQLite、Markdown、Obsidian、双链、页面配额和投影一致性检查。只有所有 migrated/delta pack 和普通全局门全部通过时，才写入三项完成标记。

## 切换与回滚

迁移始终写入新的暂存目录。正式切换采用同卷目录改名：先把旧输出改为带版本的备份，再把已完成暂存目录改为正式目录。Hook 注册更新到新输出后执行真实 prompt/tool/stop canary。回滚只需要恢复旧目录名和旧注册项；旧输出在切换前保持完整可用。
