# Obsidian tag 真实规模隔离实验

## 结论

本次实验在稳定知识库 `fcad08af3dac7ecf341f2833c1bfc8f352131a3b` 的隔离副本上完成。自动导航代理在固定两跳预算内的可发现任务数为：无实验 tag `0/12`、全部机器候选 tag `7/12`、经支持/不支持票确认的 tag `12/12`。确认臂同时把错误导航从机器候选臂的 5 次降为 0 次，并把 12 个任务的总跳转从无 tag 的 36 次降为 24 次。

这些是系统代理指标，不是人类任务结果。实验没有真实人类参与，`human_result` 保持 `pending-human-validation`，生产默认和稳定知识库均未改变。

## 已确认事实

- 稳定来源：360 个文件、336 个 Markdown、251 个 `pages/` 页面，约 9.45 MB；机器层有 2,090 个实体、8,152 条关系和 246 个有机器映射的页面。
- 隔离方式：复制三份 vault；删除副本中指向稳定输出的 `.ckb/output-contract.json` 和 companion 插件目录，并禁用 community plugin。稳定来源的 vault、机器 SQLite 和 `.complete` 在运行前后哈希一致。
- 固定协议：12 个任务按 `T01` 至 `T12` 顺序执行；入口固定为 `INDEX.md`；预算固定为 2 次跳转；无 tag 臂使用有向 WikiLink 最短路径；tag 臂使用全局 tag 面板和大小写折叠后的页面路径排序。
- 机器候选：12 个目标和 6 个干扰项，共 18 个页面-tag 对。
- 投票审计：输入 53 行断言，去重后写入 52 条；包含 18 个 proposal 和 35 行 vote；最终为 12 个 `confirmed`、2 个 `candidate`、2 个 `contested`、2 个 `deprecated`。其中一行重复 vote 被忽略。
- 并列规则：1 票支持、1 票反对时，反对比例为 `0.5`，超过固定上限 `0.25`，确定性进入 `contested`。
- 证据不足：只有 1 票支持的候选同时记录票数、独立 Agent 和独立来源不足三个原因码。
- 失败样例：来源哈希漂移返回 `SOURCE_DRIFT`；`../恶意` 返回 `INVALID_TAG`；实验目录发生字节漂移时回滚返回 `ROLLBACK_DRIFT` 并保留现场。
- 确定性：第二次完整重放的 assertions、audit、projection、逐任务记录、条件指标、来源身份和三份 vault 摘要均与第一次一致。

## 三臂系统指标

| 条件 | 两跳内可发现 | 可发现率 | 总跳转 | 中位跳转 | 错误导航 | `pages/` 孤立页 | 唯一实验 tag | tag 赋值 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `no_tag` | 0/12 | 0.000000 | 36 | 3.0 | 0 | 0 | 0 | 0 |
| `machine_tag` | 7/12 | 0.583333 | 29 | 2.0 | 5 | 0 | 12 | 18 |
| `confirmed_tag` | 12/12 | 1.000000 | 24 | 2.0 | 0 | 0 | 12 | 12 |

这里的“可发现”只表示确定性代理能否在协议规定的两跳内到达目标。“错误导航”只统计 tag 候选排序中先于目标被访问的干扰页面；无 tag 臂使用最短路径，因此它的 0 次错误不表示真人不会走错。

## 对当前问题的影响

系统层证据表明，在本协议和本固定样本中，直接下沉全部机器候选会引入 6 个额外 tag 赋值，并造成 5 次干扰页面访问；确定性票审计移除这 6 个未确认页面-tag 对后，代理指标优于无 tag 和全部机器候选两臂。这个结果支持继续进行人类任务验证，但不支持宣称人类导航效率已经提高。

## 待人类验证

后续真人实验应继续使用同一批任务、任务顺序、两跳判定和页面版本，分别记录完成率、实际点击或跳转、错误页面、完成时间和主观负担。真人记录必须单独进入新结果，不与本次自动代理记录合并。

## 复验入口

```powershell
$Python = 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe'
& $Python -X utf8 .\references\research-gap-enhancement-effects\obsidian-tag-real-vault-study-v1\verify_results.py `
  --result .\references\research-gap-enhancement-effects\obsidian-tag-real-vault-study-v1 `
  --out .\references\research-gap-enhancement-effects\obsidian-tag-real-vault-study-v1\result-audit.json
```
