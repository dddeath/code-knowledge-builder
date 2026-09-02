# Git 驱动的源码事实新鲜度合同

本合同在固定源码事实层之上增加一个机器侧状态机。它只比较当前 Git 仓库、知识库绑定提交和隔离迁移 staging，不改写既有事实、审阅、人类页面或远端历史。

## 状态与优先级

| 对外状态 | 判定 | 稳定事实用途 | 允许写入 |
|---|---|---|---|
| `current` | 当前 `HEAD` 等于知识库绑定提交，绑定元数据有效且工作树干净 | 可作为当前固定事实 | 机器新鲜度状态、事件与会话缓存 |
| `stale-committed` | 当前 `HEAD` 已提交到另一提交，稳定库仍绑定旧提交，工作树干净 | 只可作为旧基线，不得形成当前确定性结论 | 机器漂移摘要和 staging 下一动作 |
| `provisional-dirty` | 工作树存在暂存、未暂存或未跟踪变化 | 固定事实按 `stable_state` 解释；临时变化只进入 overlay | 可丢弃 overlay；不得写入固定事实和人类结论 |
| `migration-pending` | 已为当前提交建立隔离迁移计划，但 staging 尚未通过完成门 | 旧稳定库仍不可冒充当前事实 | 机器迁移计划与状态 |
| `migration-ready` | staging 绑定当前提交，完成标记、全局审计和迁移审计均通过 | staging 可进入显式切换；旧稳定库仍保持旧基线 | 机器就绪证据；不得自动切换目录 |
| `unavailable` | Git、绑定提交、输出状态或必要对象不足 | 不对当前事实作确定性声明 | 机器失败摘要、最后一次已确认状态和重试入口 |

`provisional-dirty` 的优先级最高，但结果必须保留底层 `stable_state`。例如新提交上又有未提交修改时，对外状态为 `provisional-dirty`，底层稳定状态为 `stale-committed` 或 `migration-pending`。清理脏树后恢复底层状态，不把 overlay 晋升为固定事实。

## 触发、缓存和有界读取

- 首次 Skill 应用、首次会话查询和管理 Agent 状态读取执行新鲜度检查。
- 成功的 `git commit`、`git merge`、`git pull`、`git switch` 和 `git checkout` 工具事件触发强制检查；事件只排队或更新机器状态。
- 每次检查只运行有超时的 Git 元数据命令。相同会话、相同 `HEAD`、相同工作树指纹复用变化摘要，不重建知识库。
- 变化摘要最多保留固定数量的路径和计数。完整命令输出、补丁正文和源码内容不进入新鲜度记录。

## 临时 overlay

overlay 只保存来源会话、触发事件、`HEAD`、工作树指纹、有限路径、创建时间、失效时间和删除入口。删除 overlay 只删除机器侧临时记录，不执行 `git reset`、`git clean` 或文件回写。工作树内容继续由 Git 和用户控制。

## 迁移、失败恢复和并发

- `stale-committed` 只生成建议 staging 路径与 `migrate start` 参数；显式计划后进入 `migration-pending`。
- staging 必须位于稳定输出之外。只有 staging 的 `state.status=complete`、绑定提交等于检查时当前 `HEAD`、`.complete` 存在、`audit/global.json` 与 `migration/audit.json` 均为 `passed`，状态才进入 `migration-ready`。
- Git 或 JSON 读取失败返回 `unavailable`，保留 `last_confirmed`，下一次检查重新探测并可恢复。
- 单输出文件锁串行更新状态、overlay、计划、协作记录和事件。死亡进程或超时锁可由后续调用接管；释放锁时核对 owner token，避免删除其他写入者的锁。
- 机器事件日志、会话缓存、overlay 和协作记录均有固定上限，不启动后台轮询。

## 远程协作记录与重复实现候选

机器协作记录按 `branch`、`commit`、`task`、功能标识和 `implemented`、`planned`、`superseded` 状态查询。重复实现检测只比较显式功能词项和受控路径交集，返回 `candidate-only`、匹配证据与记录标识；它不自动判定两项实现重复，也不修改分支、提交或任务状态。

管理 Agent 创建任务时记录 `planned`，审阅通过时记录 `implemented`。方案被替代通过显式记录写入 `superseded` 关系。人类输出只显示当前状态、影响范围和可执行入口；提交列表、工作树指纹、迁移门和协作候选证据留在机器层。

## 回滚

代码回滚使用逐提交 `git revert`。运行时状态回滚只删除或恢复 `workspace-meta/freshness/`，不会触碰 `facts/`、`machine/knowledge.sqlite`、`human/`、`markdown/`、Git 工作树或远端引用。执行恢复前必须先核对目标机器状态文件的当前哈希，避免覆盖后续会话写入。
