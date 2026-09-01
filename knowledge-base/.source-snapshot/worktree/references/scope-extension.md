# 既有知识库追加中心

`scope extend` 在同一固定 Git 快照上把一个或多个新中心加入已完成知识库。目标中心集合始终是旧 `entries` 与新增 `entries` 的并集；接口不提供隐式删除。所有构建、审阅和审计先发生在独立 staging，生产 OUTPUT 在 `cutover` 前保持原字节不变。

## 启动和审阅

每个新增中心必须使用完整的 `LANGUAGE:PATH#QUALIFIED_NAME`，并且在受支持、已跟踪的固定源码中唯一解析。零解析、多解析、不支持语言、未跟踪路径、重复输入和已经存在的中心均使用固定错误分类退出。

```powershell
& PYTHON scripts\ckb.py scope extend start `
  --from-out "OLD_OUTPUT" `
  --repo "CLEAN_FIXED_REPOSITORY" `
  --staging "STAGING_OUTPUT" `
  --entry "python:src/service.py#Service.run" `
  --expand-depth 1 `
  --expand-direction both

& PYTHON scripts\ckb.py scope extend status --out "STAGING_OUTPUT"
```

`scope-extension/plan.json` 固定记录绝对绑定、旧/新增/目标 entries，以及 entries、paths、entities、relations、pages 五个维度的 retained/added/removed 集合。正常追加的所有 removed 集合必须为空。重复执行完全相同的 `start` 会读取同一 `operation_id` 和现有计划，不重建 staging；不同请求不能复用已有 staging。

未变化的路径、语言、Git blob 和已通过 parse 精确复用。实体审阅还要求源码键、审阅状态和叙述字段形状兼容。新实体及新增关系的旧端点进入 `delta-*` review pack；其余实体进入自动重放普通源码门的 `migrated-*` pack。Agent 只提交 `delta-*`：

```powershell
& PYTHON scripts\ckb.py review-pack --out "STAGING_OUTPUT" --pack "DELTA_PACK" --review "REVIEW.json"
& PYTHON scripts\ckb.py scope extend audit --out "STAGING_OUTPUT"
```

`audit` 重新计算精确 reuse/delta 集合，核对旧 OUTPUT 和目标 commit 未漂移，验证工作记录、reference、gap、feedback、operation journal、Agent Protocol 和生成器未拥有的用户文件均有不可变基线，并执行普通 `finalize`、全局审计、双 SQLite `integrity_check`/foreign key、镜像、中文、来源、页面配额、readability 和 `maintain`。只有全部门通过时，状态才变为 `ready`。

## 切换和回滚

```powershell
& PYTHON scripts\ckb.py scope extend cutover --out "STAGING_OUTPUT"
& PYTHON scripts\ckb.py scope extend status --out "OLD_OUTPUT"
& PYTHON scripts\ckb.py scope extend rollback --out "OLD_OUTPUT"
```

`cutover` 在同一父目录内先把旧 OUTPUT 改名为 operation 专属备份，逐文件核对预先冻结的 SHA-256 树清单，再把 staging 改名为正式 OUTPUT。随后执行完成态路径重定位和双 SQLite 探针。任一步失败时，命令把目录改名顺序反向执行，并再次核对旧 OUTPUT 的完整树清单；复制开始或首次改名不等于切换成功。

切换控制记录保存在 OUTPUT 的同级隐藏 JSON 中，字段为固定 schema/version、绝对路径、commit、旧/新树清单和 SQLite 结果，不包含 Prompt、secret、命令输出或无界日志。`rollback` 先验证当前新 OUTPUT 未漂移和备份仍等于切换前清单，再把新 OUTPUT 移入 operation 专属隔离目录并恢复旧目录。恢复后逐文件清单必须完全相等，双 SQLite 和自动化数据库必须通过完整性与外键探针；失败会反向恢复切换后的状态，不触碰同工作区其他知识库。

同一 OUTPUT 可以顺序追加多个中心。每次成功 cutover 保存 `parent_operation_id` 和从 1 开始的 `chain_depth`；旧 schema-1 记录缺少这两个字段时，只在唯一旧 `modified_manifest` 等于新操作 `origin_manifest` 时推导父操作。`status` 以当前 OUTPUT 全树清单唯一匹配 `cutover-complete.modified_manifest`，不按 operation ID 或文件名字典序选择。多条记录同时匹配、父链缺失、深度漂移或循环均以固定控制记录错误退出。

`rollback` 每次只撤销当前链顶端：恢复后的全树等于父操作 `modified_manifest` 时，父操作重新成为 active；再次 rollback 继续撤销父操作。根操作回滚后没有 active cutover，此时同一根 rollback 再次调用返回幂等 `rolled-back`。历史 JSON、失败尝试、已回滚记录和隔离后的新 OUTPUT 均保留，不通过删除历史来消除二义性。
