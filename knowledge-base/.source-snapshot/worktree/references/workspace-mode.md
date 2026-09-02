# 固定基线与 Agent 修改会话

当 Agent 需要一边构建知识库、一边修改代码时使用本模式。

## 源码模型

`init` 要求干净 Git commit，并立即创建 `OUTPUT/.source-snapshot/worktree` 脱离工作树快照。AST 和语言提供器始终读取该快照。状态出现 `source_snapshot.status=snapshot-ready` 后，用户工作树可以修改，分段知识构建不会漂移。

固定基线的完成记录始终描述初始化 commit；当前工作树变化单独写入：

```powershell
& PYTHON scripts\ckb.py workspace sync --out OUTPUT --repo REPO
& PYTHON scripts\ckb.py workspace status --out OUTPUT
```

`workspace sync` 保存已修改和未跟踪路径及可读 patch，不改写固定图。patch 会去掉 Git `index ...` 行，避免把无助于阅读的哈希加入知识笔记。

## 会话生命周期

项目初始化完成后，为每项实质任务启动一次会话，而不是为每次工具调用启动会话：

```powershell
& PYTHON scripts\ckb.py workspace session-start --out OUTPUT --repo REPO `
  --question "实现订单失败后的库存回滚" --budget 1800 --profile fast
```

- 若机器库已经完成，命令先同步工作树，再执行确定性检索，并把阅读包绑定到会话。
- 若分段构建尚未完成，命令仍会建立会话，把中文会话页放入 `workspace-meta/pending-notes`；`finalize` 在人类投影产生后自动落页。
- 会话启动不修改固定快照，也不要求暂停代码编辑。

完成任务时提交一份简体中文总结：

```markdown
## 修改内容

说明改了哪些行为和代码。

## 修改原因

说明为何采用这一实现。

## 验证结果

说明执行了什么验证及结果。
```

```powershell
& PYTHON scripts\ckb.py workspace session-finish --out OUTPUT --repo REPO `
  --session SESSION_ID --summary SUMMARY.md --title "库存回滚修改记录"
& PYTHON scripts\ckb.py workspace sessions --out OUTPUT
```

只要工作树存在文件变化，以上三个标题就是确定性输入门。完成命令再次同步工作树，将相关路径回链到检索命中的知识页；尚未完成投影时则进入待落页队列。

## 分析与经验笔记

机器阅读包产生后，用固定类型保存结论：

```powershell
& PYTHON scripts\ckb.py record --out OUTPUT --kind analysis `
  --title "订单失败路径分析" --body BODY.md --from-pack PACK.json
```

固定类型和标签：

- `analysis` → `#类型/分析`
- `change` → `#类型/变更`
- `pitfall` → `#类型/踩坑`
- `experiment` → `#类型/实验`
- `session` → `#类型/会话`

每个非会话笔记至少链接一个知识页。脚本补充 `[[页面]]` 和可点击源码入口，在 `workspace-meta/notes` 保存机器侧记录，并刷新机器库与兼容索引。人类笔记不含 frontmatter、稳定实体 ID、commit 或长哈希。

## 中文要求

会话、分析、修改、踩坑和实验正文必须使用简体中文。英文仅用于专有名词、API、代码标识符、路径、命令和必要术语。纯英文正文在写入前直接失败；重新投影和最终审计还会再次检查。

## Agent 行为

- 每个实质任务一页会话总结；原始逐轮对话保留在外部记录，不膨胀人类知识库。
- 回复实质代码解释前，先把可复用结论保存为 `analysis`。
- 一组连贯修改保存为 `change`，必须写清修改内容、原因和验证。
- 独立失败路线保存为 `pitfall`，产生可复核证据的试验保存为 `experiment`。
- 回复前重新打开新笔记、关联知识页和对应源码范围。
- 完整命令输出保存在验证侧车；人类页只保留有长期价值的中文结论。

## 自动化模式

当 Harness 能提供生命周期事件时，使用 `automation register` 与 `automation render` 代替依赖 Agent 记忆手动调用会话命令。自动化与本页手动接口共享同一知识分层，但状态互不冒充：

- Harness Hook 只写脱敏机器事件、工作树证据和 `pending-agent-review`；
- `Stop` 或等价事件结束一轮，`SessionEnd` 只关闭主会话；
- 并发 Hook 通过单输出 drain 锁和 SQLite 事务串行提交；
- Agent 重新打开变化路径并提交 `automation review` 后，人类页才出现；
- 固定快照、工作覆盖层、自动化事件和人类审阅分别保存，任一层都不覆盖另一层。

完整事件、隐私、恢复和 Harness 配置见 `automation.md`。

## 管理 Agent 派发独立开发 worktree

已绑定 conversation 只有在 integration HEAD 仍等于 bound HEAD、integration worktree 干净、machine/agent-index SQLite 完整、没有开放 error feedback 且 `maintain` 通过时，才能创建开发任务：

```powershell
& PYTHON scripts\ckb.py manager task-create `
  --conversation-id CONVERSATION_ID --harness HARNESS `
  --task-id TASK_ID --branch codex/TASK_BRANCH `
  --worktree WORKSPACE\worktrees\TASK `
  --allow-path OWNED_PATH --forbid-path FORBIDDEN_PATH `
  --test "TEST_COMMAND" --registry MANAGER_REGISTRY
```

命令使用绑定时 HEAD 创建新 branch 和独立 worktree，并在管理注册表旁生成带哈希的中文交接 Prompt。Prompt 固定包含基线、允许/禁止路径、测试、分批 commit、结构化返回格式以及“不得自行合并、不得同步稳定知识库”边界。相同 binding + task ID + 参数的并发重复调用只产生一个 worktree 和一个 `dispatch_id`；字段冲突时不覆盖旧任务。

开发 Agent 提交修改并保持 worktree 干净后，由管理 Agent 执行真实验证：

```powershell
& PYTHON scripts\ckb.py manager task-review --dispatch-id DISPATCH_ID --registry MANAGER_REGISTRY
& PYTHON scripts\ckb.py manager task-status --dispatch-id DISPATCH_ID --registry MANAGER_REGISTRY
```

`task-review` 在开发最终 HEAD 逐条运行派发时固定的测试命令，保存 literal stdout、stderr 和退出状态，再重新核对开发 HEAD、工作树、integration HEAD 与 bound HEAD。并发 review 由单任务锁串行化；已通过且未漂移的重复 review 复用同一验证记录。`task-status=merge-ready` 只表示审阅门通过，命令本身不执行 merge。

真正合并仍需用户明确指令。合并后在 integration branch 重新运行受影响测试，再执行最小知识库同步和新的 `maintain`；开发 worktree 的测试记录与合并前 maintain 状态不能复用为合并后证据。
