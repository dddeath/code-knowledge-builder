# Code Knowledge Builder 5.4.0 使用教程

Code Knowledge Builder（CKB）把一个干净 Git 提交固定为不可漂移的源码快照，并生成两套互相校验的知识层：Agent 使用 SQLite 和预算化阅读包定位实体、关系与源码范围；人类使用简体中文 Markdown 页面、工作记录、reference 和 research gap 理解项目。默认检索不调用向量模型或外部 LLM。

本分支同时提供 CKB 源码、当前稳定知识库和可独立运行的发布校验工具。第一次使用时先完成下面的五分钟流程；需要为自己的代码仓库建库时，再继续阅读“构建新的知识库”。

## 五分钟开始

### 1. 克隆并展开 Git LFS

```powershell
git lfs install
git clone --branch codex/release-5.4.0-stable-knowledge --single-branch https://github.com/dddeath/code-knowledge-builder.git
Set-Location .\code-knowledge-builder
git lfs pull
git lfs fsck
```

仓库使用 Git LFS 保存 `*.sqlite` 和 `*.zip`。如果没有执行 `git lfs pull`，工作树中可能只有指针文件，知识库和发布校验都不会得到完整输入。

### 2. 验证发布内容

```powershell
python .\delivery\verify-publication.py `
  --root . `
  --write .\delivery\verification.json
```

校验程序会逐文件检查 `source/` 与 `knowledge-base/`，并验证完成标记、双 SQLite、human/markdown 镜像、readability、工作记录、reference、research gap、两份学习笔记原始字节和 Git LFS 对象。

### 3. 设置本轮命令变量

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$Python = 'python'  # 也可以换成已安装 CKB Skill 使用的 Python
$Ckb = (Resolve-Path '.\source\scripts\ckb.py').Path
$PublishedOut = (Resolve-Path '.\knowledge-base').Path
$Out = $PublishedOut

& $Python $Ckb doctor --json
```

`doctor` 用于确认 Python、解析器、SQLite 和本地工具是否满足当前命令。退出状态 `3` 表示缺少依赖或完整 runtime 尚未部署，应先按返回项补齐运行环境。

## 发布目录分别保存什么

- `source/`：CKB 5.4.0 源码和正式协议文档。
- `knowledge-base/`：绑定固定源码快照的完整稳定知识库，包括事实层、机器 SQLite、兼容 SQLite、human/markdown 镜像、工作记录、reference、research gap、操作日志和学习笔记。
- `delivery/`：发布清单、只读校验程序、测试证据和回滚脚本。
- `publication-manifest.json`：发布范围、排除项、Git LFS 文件和验证状态的机器清单。

`knowledge-base/.source-snapshot/worktree` 保存建库时的固定源码字节。发布仓库不会在该目录中嵌套 `.git` 管理文件。

## 阅读现有知识库

不运行任何 CKB 命令也可以直接阅读以下入口：

| 目标 | 入口 |
|---|---|
| 按任务选择阅读路径 | `knowledge-base/human/INDEX.md` |
| 了解页面结构和阅读规则 | `knowledge-base/human/WIKI.md` |
| 查找 analysis、change、pitfall、experiment 和 session | `knowledge-base/human/RECORDS.md` |
| 查找已审阅的外部资料 | `knowledge-base/human/REFERENCES.md` |
| 浏览人类知识页 | `knowledge-base/human/pages/` |
| 使用 Obsidian 兼容镜像 | `knowledge-base/markdown/` |

`human/` 与 `markdown/` 中对应知识页应逐字节一致。`human/pages`、`markdown/pages`、`INDEX.md`、`WIKI.md`、`RECORDS.md`、`REFERENCES.md`、投影清单和 SQLite 都由生成器管理，不直接编辑。

## 让 Agent 先检索再读源码

`brief`、`retrieve` 等查询会在知识库中保存 Agent pack 和操作证据。如果需要保持发布分支工作树完全干净，应在隔离副本中查询；完成迁移或重新建库后，把 `$Out` 改为活动知识库路径。

### 1. 使用紧凑首轮入口

```powershell
$Brief = & $Python $Ckb brief `
  --out $Out `
  '当前项目如何维护稳定知识库' `
  --budget 1800 `
  --max-pages 8 `
  --profile fast | ConvertFrom-Json

Get-Content $Brief.pack -Raw
```

`brief` 返回两个不同文件：

- `pack`：预算内的 Markdown 阅读包，先打开它；
- `record`：完整 JSON 检索记录，供 `record --from-pack` 回链和排序调试使用。

不要把 Markdown `pack` 路径传给 `record --from-pack`；该参数使用 `$Brief.record` 指向的 JSON 文件。

若 `$Brief.open_feedback` 大于零，先读取开放反馈：

```powershell
& $Python $Ckb feedback list --out $Out --status open
```

### 2. 按检索结果窄读

```powershell
& $Python $Ckb entity --out $Out 'serve_stdio'
& $Python $Ckb neighbors --out $Out 'serve_stdio' --depth 2
& $Python $Ckb source --out $Out 'serve_stdio' --context-lines 3
& $Python $Ckb changes --out $Out --kind change --limit 10
```

推荐顺序固定为：

1. `brief --profile fast`；
2. 打开返回的 Agent pack；
3. 使用 `entity`、`neighbors`、`source`、`changes` 缩小范围；
4. 只有返回 `needs-source-read`，或已经给出精确路径和行范围时，才窄读源码；
5. `grep` 只用于补充已经确定的范围，不替代首轮 SQLite 检索。

普通实现定位使用 `fast`。复杂跨模块关系可以改用 `--profile precise`；它会增加固定源码 FTS 和确定性 PageRank，但仍不调用模型。LLM 关键词扩展属于显式备选慢路径，只有调用方提供 `--allow-keyword-fallback` 或 `--force-keyword-fallback` 以及完整 Provider 配置时才会启动。

## 保存分析、修改和实验记录

本节只用于已经迁移或重新构建的活动知识库，不向发布分支中的原始副本追加记录。先对活动知识库执行 `brief` 并审阅阅读包：

```powershell
$ActiveOut = 'E:\project\knowledge-base'
$ActiveBrief = & $Python $Ckb brief `
  --out $ActiveOut `
  '当前项目如何执行首轮检索' `
  --budget 1800 `
  --max-pages 8 `
  --profile fast | ConvertFrom-Json

Get-Content $ActiveBrief.pack -Raw
```

再准备只含正文的简体中文文件。例如 `analysis-body.md`：

```markdown
当前检索首先使用机器 SQLite 的实体与章节 FTS，再按固定权重扩展相邻关系。只有机器索引缺少来源绑定候选时，结果才标记为需要继续窄读源码。
```

写入一条 analysis：

```powershell
& $Python $Ckb record `
  --out $ActiveOut `
  --kind analysis `
  --title 'CKB 首轮检索路径' `
  --body '.\analysis-body.md' `
  --from-pack $ActiveBrief.record
```

可用类型：

| 类型 | 用途 |
|---|---|
| `analysis` | 可复用的实现解释和设计判断 |
| `change` | 已完成修改、原因、验证和回滚边界 |
| `pitfall` | 已确认的失败路线与避免方法 |
| `experiment` | 有固定输入、测量和结论的实验 |
| `session` | 一项完整 Agent 任务的总结 |

非 session 记录必须通过 `--from-pack`、`--from-query` 或唯一 `--link` 回链至少一个知识页。脚本会同时更新 human/markdown 镜像、记录元数据、`RECORDS.md` 和两个 SQLite 索引。更新同标题人工记录时使用 `--append`；正文不要重复生成器负责添加的一级标题。

## 构建新的知识库

### 1. 准备固定源码边界

目标源码必须是具有提交的干净 Git 工作树，知识库输出目录不得与源码仓库重叠。先选择输出格式：

- `markdown`：人类 Markdown/Obsidian 投影和机器层；
- `logseq-db`：增加 Logseq DB 投影；
- `both`：同时生成并验证两种投影。

```powershell
$Repo = 'E:\project\source'
$NewOut = 'E:\project\knowledge-base'

& $Python $Ckb doctor --json
& $Python $Ckb run `
  --repo $Repo `
  --out $NewOut `
  --format markdown
```

初次 `run` 会立即建立脱离活动工作树的固定源码快照。命令在遇到下一个 Agent review pack 时以退出状态 `4` 停下，这是正常审阅检查点，不表示构建失败。

如果输入目录还没有 Git 提交，CKB 会退出并提示 `--init-git`。该选项只在用户明确选择后使用；它最多创建一个初始提交，不会把已有 Git 仓库的脏工作树重新提交。

### 2. 审阅并继续构建

重新打开 review pack 中列出的每个源码范围，为页面、附录和边界写入事实一致的简体中文说明，然后提交审阅 JSON：

```powershell
& $Python $Ckb review-pack `
  --out $NewOut `
  --pack PACK_ID `
  --review '.\review.json'

& $Python $Ckb run --out $NewOut --resume
```

重复“打开源码范围 → 填写审阅 → `review-pack` → `run --resume`”，直到没有待处理 batch 或 review pack，再执行：

```powershell
& $Python $Ckb finalize --out $NewOut
& $Python $Ckb status --out $NewOut --json
```

只有来源、中文、页面、镜像、Graphify、双 SQLite、Agent 审阅和所选投影格式全部通过时，`finalize` 才写入完成标记。

## 让任意 Agent 自动遵循同一检索协议

知识库完成后，把“先 brief、后窄读、记录通过 record、结束前 maintain”的规则安装到 Agent 实际启动任务的工作区：

```powershell
$Workspace = 'E:\project'

& $Python $Ckb agent-policy install `
  --out $NewOut `
  --workspace-root $Workspace `
  --python $Python `
  --ckb $Ckb

& $Python $Ckb agent-policy check --out $NewOut
```

该命令为 Codex、OpenCode、Claude Code、Gemini CLI、GitHub Copilot 和 Cursor 写入各自可发现的项目级规则。它只更新带规范 marker 的受管区块，保留文件中的其他项目说明。

## 在 Agent 会话中复用常驻 stdio

推荐通过 Harness 自动化注册和适配包管理会话生命周期，而不是让每轮对话手工启动后台进程。

### 1. 注册仓库与知识库

```powershell
$Registry = "$HOME\.ckb\automation-registry.json"

& $Python $Ckb automation register `
  --repo $Repo `
  --out $NewOut `
  --workspace-root $Workspace `
  --registry $Registry `
  --harness codex
```

注册只声明该项目允许使用自动化，不会单独启动 stdio，也不会采集其他目录的会话。

### 2. 生成并安装 Harness 适配包

```powershell
& $Python $Ckb automation render `
  --harness codex `
  --destination 'E:\project\ckb-codex-bundle' `
  --python $Python `
  --ckb $Ckb `
  --registry $Registry
```

`automation render` 只写入指定的隔离目录。检查生成内容后，再按 Harness 的正常信任和配置流程安装；不要用整目录覆盖已有 Hook 或项目配置。

### 3. 激活、检查和释放会话

当前会话第一次精确应用 `code-knowledge-builder` Skill 时，适配器会执行等价的激活：

```powershell
& $Python $Ckb automation activate `
  --harness codex `
  --cwd $Workspace `
  --registry $Registry
```

激活会 single-flight 启动并握手一个会话级 `serve --stdio`。同一 `Harness + session + OUTPUT + executable/protocol` 身份下的 `brief`、`retrieve`、`entity`、`neighbors`、`source` 和 `changes` 自动复用同一健康 PID。

```powershell
& $Python $Ckb stdio-session list --active
& $Python $Ckb stdio-session status `
  --harness codex `
  --session-id SESSION_ID `
  --out $NewOut

& $Python $Ckb stdio-session close `
  --harness codex `
  --session-id SESSION_ID `
  --out $NewOut

& $Python $Ckb stdio-session cleanup
& $Python $Ckb stdio-session audit
```

`session.start` 不启动常驻进程，`turn.stop` 也不释放它。`session.end`、显式 `close`、`terminate`、`cancel`、management `unbind`、Harness unload 或可靠父 PID 死亡会按 `shutdown → terminate → kill` 的有界顺序关闭并等待回收。启动或握手失败时状态会明确返回 `mode=cli-fallback`、`resident=false`，随后查询退回一次性 CLI。

底层 `serve --stdio --out OUTPUT` 只用于 transport 调试；正式 Agent 会话优先使用上述 session supervisor。

## 绑定管理 Agent 对话

`agent-policy` 规定所有 Agent 的项目级读取和写入规则；`manager` 再为一个具体 conversation 绑定 workspace、源码仓库、知识库、integration branch 和绑定时 HEAD。

```powershell
$ManagerRegistry = "$HOME\.ckb\manager-registry.json"

& $Python $Ckb manager bind `
  --conversation-id CONVERSATION_ID `
  --harness codex `
  --workspace-root $Workspace `
  --repo $Repo `
  --out $NewOut `
  --integration-branch INTEGRATION_BRANCH `
  --registry $ManagerRegistry

& $Python $Ckb manager context `
  --conversation-id CONVERSATION_ID `
  --harness codex `
  --question '审阅当前开发分支' `
  --registry $ManagerRegistry `
  --format prompt
```

`manager context` 每次重新检查 integration HEAD、工作树、`brief`、开放 feedback、research gap、双 SQLite 和 `maintain`，再返回可注入当前 Agent 的完整中文管理 Prompt。绑定记录只保存不透明 conversation ID、路径、分支、HEAD、生命周期和能力声明，不保存对话正文、凭据或 transcript。

需要派发开发任务时使用 `manager task-create` 创建固定 HEAD 的独立 branch/worktree，再由 `manager task-review` 和 `manager task-status` 运行派发时冻结的测试门。这些命令只生成和审阅任务，不执行合并；合并与稳定知识库同步仍由管理 Agent 负责。

## 维护活动知识库

写入记录、处理 feedback、迁移、重新投影或更新索引后执行：

```powershell
& $Python $Ckb maintain --out $NewOut
```

只有以下项目同时通过，才把知识库描述为维护完成：

- Agent Policy；
- 简体中文和页面链接；
- human/markdown 镜像；
- 工作记录和记录元数据；
- reference；
- research gap；
- feedback；
- operation journal；
- `agent-index.sqlite`；
- `machine/knowledge.sqlite`；
- 人类可读性审计。

源码符号、关系或页面来源发生变化时，使用迁移、局部重建或 `reindex`；不要因为一次小修改无条件重扫整个仓库。`maintain` 通过只证明知识库协议与索引一致，不替代功能测试或源码运行时验证。

## 把知识库迁移到新的源码提交

旧知识库已经完成审计、而新提交只修改部分源码时，优先使用隔离增量迁移：

```powershell
$OldOut = 'E:\project\knowledge-base'
$NewRepo = 'E:\project\source-next'
$StagingOut = 'E:\project\knowledge-base-staging'

& $Python $Ckb migrate start `
  --from-out $OldOut `
  --repo $NewRepo `
  --out $StagingOut

& $Python $Ckb migrate status --out $StagingOut
```

迁移只复用相对路径、语言、Git blob 和旧解析状态全部一致的语法事实；修改、新增、删除或分类形状变化的实体进入独立 delta review pack。完成 delta 审阅后执行：

```powershell
& $Python $Ckb merge --out $StagingOut
& $Python $Ckb migrate audit --out $StagingOut
& $Python $Ckb finalize --out $StagingOut
& $Python $Ckb maintain --out $StagingOut
```

迁移始终写入新的 staging 目录。所有门通过后，在同一卷内保留旧输出目录作为回滚基线，再用目录改名切换；不要直接在旧知识库上覆盖重建。

本发布分支中的 `knowledge-base/` 仍保留构建机的固定快照和本机绑定路径。它可以直接用于阅读、SQLite 检索和发布完整性复核；在另一台机器上继续执行写入、`status`、`maintain` 或源码定位前，应先按上述迁移流程重新绑定，或从当地干净 Git 提交重新建库。

## 发布回滚

- 本机构建与稳定知识库切换回滚：`delivery/rollback-stable-kb.ps1`
- 已推送发布分支回滚：`delivery/rollback-github-release-5.4.0.ps1`

远端回滚通过新的 revert commit 恢复发布树，不执行 force push，也不改写公开历史。

## 进一步阅读

- [完整建库工作流](source/references/workflow.md)
- [Agent 确定性检索](source/references/agent-retrieval.md)
- [固定基线与 Agent 修改会话](source/references/workspace-mode.md)
- [会话、Hook 与常驻 stdio](source/references/automation.md)
- [增量迁移](source/references/migration.md)
- [跨 Harness Agent Policy](source/references/agent-policy.md)
- [人类可读页面约束](source/references/human-readable-pages.md)
