# Code Knowledge Builder 5.4.0

Code Knowledge Builder（CKB）把一个干净的 Git 提交转换为可供 Agent 检索、也可供人类阅读的项目知识库。人类从任务入口、职责页面和历史记录理解项目；Agent 从机器索引定位相关源码范围。

## 先选择你要完成的任务

| 你现在需要什么 | 继续阅读 | 完成后得到什么 |
|---|---|---|
| 先看懂下载内容和知识库入口 | [了解本项目知识库结构](#了解本项目知识库结构) | 知道各目录保存什么，并能从人类入口开始阅读 |
| 尚未安装 Code Knowledge Builder | [让 Agent 安装本项目](#让-agent-安装本项目) | 项目、Git LFS 内容、Skill 和运行环境均通过安装验收 |
| 已经安装，想了解自己的代码仓库 | [让 Agent 解释自己的项目](#让-agent-解释自己的项目) | 为目标仓库建立或接管知识库，并得到带源码依据的回答 |

## 了解本项目知识库结构

下载本项目后，首先会看到四个入口：

```text
code-knowledge-builder/
├─ README.md                  当前使用入口
├─ source/                    Code Knowledge Builder 源码与协议
├─ knowledge-base/            与当前发布版本配套的稳定知识库
├─ delivery/                  发布校验结果与回滚工具
└─ publication-manifest.json  发布范围、固定版本与文件清单
```

其中，`knowledge-base/` 同时服务于人类阅读和 Agent 检索：

```text
knowledge-base/
├─ human/
│  ├─ INDEX.md          按当前任务选择阅读入口
│  ├─ WIKI.md           了解页面怎样组织
│  ├─ RECORDS.md        查找分析、修改、实验和会话记录
│  ├─ REFERENCES.md     查找已审阅的外部资料
│  ├─ pages/            阅读当前源码职责
│  └─ changes/          阅读已经成立的项目变化
├─ markdown/            与 human 对应的 Obsidian 兼容镜像
├─ machine/             Agent 使用的检索数据库与来源证据
└─ AGENTS.md            Agent 自动发现的知识库使用规则
```

人类从 `knowledge-base/human/INDEX.md` 开始即可。想了解某项功能现在如何工作时进入职责页；想了解为什么发生变化时进入工作记录；想核对外部资料时进入 reference。`machine/` 由 Agent 使用。

## 让 Agent 安装本项目

下面的 Prompt 负责下载并安装 Code Knowledge Builder。安装位置可以省略，由 Agent 使用当前 Harness 的标准位置。

<details>
<summary>复制给 Agent：安装 Code Knowledge Builder</summary>

```text
请安装 Code Knowledge Builder 项目及其 code-knowledge-builder Skill。

项目来源：https://github.com/dddeath/code-knowledge-builder
发布分支：codex/release-5.4.0-stable-knowledge
安装位置：<可省略；默认使用当前 Harness 的标准项目与 Skill 目录>

请按固定顺序完成：
1. 下载指定发布分支及其 Git LFS 内容；
2. 核对 publication-manifest.json，并运行发布包自带的完整性校验；
3. 从该发布包安装 code-knowledge-builder Skill 和配套运行环境；
4. 验证当前 Harness 能发现并调用该 Skill，检查 Python、解析器、SQLite 和本地依赖；
5. 执行一个不修改业务仓库的最小检索探针；
6. 返回安装验收摘要：项目位置、发布分支与提交、Skill 位置、运行环境、Git LFS、发布校验、检索探针和卸载或回滚入口。

本次只完成 Code Knowledge Builder 安装。不要为其他仓库建立知识库，也不要开始解释业务代码。
```

</details>

## 让 Agent 解释自己的项目

完成安装后，把下面的 Prompt 交给位于目标仓库中的 Agent。只需说明仓库和问题；仓库留空时，Agent 使用当前工作区内唯一的 Git 仓库。

<details>
<summary>复制给 Agent：为自己的仓库建库并解释项目</summary>

```text
请使用已安装的 $code-knowledge-builder 为我的代码仓库建立或接管知识库，然后回答问题。

repository=<本地 Git 仓库或 Git URL；留空时使用当前工作区内唯一的 Git 仓库>
question=<我想了解的项目问题>

可选参数：
knowledge_base=<知识库位置；省略时使用源码仓库同级的 knowledge-base>
scope=<目录或入口符号；省略时覆盖整个仓库>

请按固定顺序完成：
1. 确认 repository、当前 Git 提交、工作树状态和知识库输出边界；Git URL 先下载到独立目录；
2. 查找与该仓库绑定的现有知识库；没有时从当前干净提交建立，有时先核对固定源码版本和当前状态，再选择直接使用、迁移或局部更新；
3. 新建时固定源码快照，按 review pack 完成源码审阅，生成人类页面、机器索引和 Obsidian 镜像；
4. 安装并核对项目级 Agent 使用规则，使后续 Agent 先检索知识库，再按返回范围窄读源码；
5. 使用 brief 获取紧凑阅读包，按阅读包回答 question，并区分已确认事实、推断和待核验内容；
6. 运行知识库维护门和一个与 question 对应的真实检索验证；
7. 返回交付摘要：固定源码版本、知识库位置、人类入口、覆盖范围、待审阅项、双 SQLite、镜像、检索验证、feedback、research gap、维护结果、回答依据和回滚入口。

本次从已经安装的 Skill 开始，不重复安装 Code Knowledge Builder。
```

</details>

`Skill` 是 Agent 可发现并按约定调用的一组本地说明、脚本和资源。`Git LFS`（Git Large File Storage）用于把大型二进制文件作为独立对象下载，避免仓库只留下指针文本。`Harness` 是承载 Agent 会话、工具和生命周期事件的宿主，例如 Codex、Claude Code 或 OpenCode。

### 安装后的解释与使用

完成安装 Prompt 后，人类可以直接使用前面的解释 Prompt；只有需要核对安装、复现检索或控制高级行为时，才使用下面的命令行入口。

#### 复核发布包和运行环境

先进入安装得到的项目目录，再核对发布分支、Git LFS 对象、发布清单和运行依赖：

```powershell
$ProjectRoot = 'E:\path\to\code-knowledge-builder'
Set-Location $ProjectRoot

git branch --show-current
git rev-parse HEAD
git lfs fsck

$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$Python = 'python'  # 也可以换成已安装 CKB Skill 使用的 Python
$Ckb = (Resolve-Path '.\source\scripts\ckb.py').Path
$PublishedOut = (Resolve-Path '.\knowledge-base').Path

& $Python '.\delivery\verify-publication.py' `
  --root . `
  --write '.\delivery\verification.json'
if ($LASTEXITCODE -ne 0) { throw '发布内容校验失败。' }

& $Python $Ckb doctor --json
if ($LASTEXITCODE -ne 0) { throw 'CKB 运行环境校验失败。' }
```

`publication-manifest.json` 把本发布版本标记为 `5.4.0`，固定源码提交为 `150a1ce8ea3fca0f7ce2f56c731d42a9973ee0e3`。`verify-publication.py` 会检查 `source/`、`knowledge-base/`、完成标记、双 SQLite、human/markdown 镜像、工作记录、reference、research gap、学习笔记和 Git LFS 对象；`doctor` 再检查当前机器的 Python、解析器、SQLite 和本地工具。`doctor` 退出状态 `3` 表示仍有依赖或完整运行环境需要部署。

稳定发布中的 `knowledge-base/` 可直接阅读和检索。若希望发布分支工作树保持干净，应在隔离副本中执行会写入 Agent pack 或操作证据的查询。生成器管理的 `human/pages`、`markdown/pages`、`INDEX.md`、`WIKI.md`、`RECORDS.md`、`REFERENCES.md`、投影清单和 SQLite 不直接编辑。

#### 先检索知识库，再窄读源码

`brief` 是 Agent 的紧凑首轮入口。它返回预算内的 Markdown 阅读包和完整 JSON 检索记录，但不把候选实体、词项和得分展开到首轮上下文：

```powershell
$Out = $PublishedOut  # 对自己的项目提问时改为该项目的活动知识库

$Brief = & $Python $Ckb brief `
  --out $Out `
  '当前项目如何维护稳定知识库' `
  --budget 1800 `
  --max-pages 8 `
  --profile fast | ConvertFrom-Json

Get-Content $Brief.pack -Raw

if ($Brief.open_feedback -gt 0) {
  & $Python $Ckb feedback list --out $Out --status open
}
```

`$Brief.pack` 指向先读的 Markdown 阅读包；`$Brief.record` 指向完整 JSON 记录，供 `record --from-pack` 回链。不要把 Markdown pack 路径传给 `--from-pack`。

阅读包给出精确符号或源码范围后，再缩小查询：

```powershell
& $Python $Ckb entity --out $Out 'serve_stdio'
& $Python $Ckb neighbors --out $Out 'serve_stdio' --depth 2
& $Python $Ckb source --out $Out 'serve_stdio' --context-lines 3
& $Python $Ckb changes --out $Out --kind change --limit 10
```

推荐顺序固定为 `brief --profile fast` → 打开 Agent pack → `entity`、`neighbors`、`source` 或 `changes` → 按返回范围窄读源码。只有结果标记 `needs-source-read`，或已经返回精确路径和行范围时，才补充源码读取；`grep` 不替代首轮 SQLite 检索。复杂跨模块关系可使用 `--profile precise`。两种档位默认都不调用模型；只有显式提供关键词 fallback 选项和完整 Provider 配置时才进入备选慢路径。

#### 建立或接管目标仓库的知识库

目标源码必须是具有提交的干净 Git 工作树，知识库输出目录不得与源码仓库重叠。输出格式包括 `markdown`、`logseq-db` 和 `both`；通常先使用 `markdown`，同时得到人类 Markdown/Obsidian 投影和机器层：

```powershell
$Repo = 'E:\project\source'
$NewOut = 'E:\project\knowledge-base'

& $Python $Ckb doctor --json
& $Python $Ckb run `
  --repo $Repo `
  --out $NewOut `
  --format markdown
```

初次 `run` 会建立脱离活动工作树的固定源码快照。遇到下一个 Agent review pack 时，命令以退出状态 `4` 停在人工审阅门；这表示需要继续审阅，不表示构建已经完成。没有 Git 提交的目录会收到 `--init-git` 提示，只有人类明确选择创建仓库和首个提交后才使用该选项。

重新打开 review pack 列出的每个源码范围，提交事实一致的简体中文审阅，再继续构建：

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

只有来源、简体中文、页面、镜像、Graphify 关系图、双 SQLite、Agent 审阅和所选投影格式全部通过时，`finalize` 才写入完成标记。

#### 保存分析、修改和实验记录

记录只写入已经迁移或重新构建的活动知识库，不向发布分支中的稳定副本追加。先在活动知识库执行 `brief` 并打开阅读包：

```powershell
$ActiveOut = $NewOut
$ActiveBrief = & $Python $Ckb brief `
  --out $ActiveOut `
  '当前项目如何执行首轮检索' `
  --budget 1800 `
  --max-pages 8 `
  --profile fast | ConvertFrom-Json

Get-Content $ActiveBrief.pack -Raw
```

准备只含简体中文正文的 `analysis-body.md`，再写入记录：

```powershell
& $Python $Ckb record `
  --out $ActiveOut `
  --kind analysis `
  --title 'CKB 首轮检索路径' `
  --body '.\analysis-body.md' `
  --from-pack $ActiveBrief.record
```

`analysis` 保存可复用解释和判断，`change` 保存已完成修改、原因、验证与回滚边界，`pitfall` 保存已确认的失败路线，`experiment` 保存有固定输入和测量的实验，`session` 保存完整 Agent 任务总结。非 `session` 记录必须通过 `--from-pack`、`--from-query` 或唯一 `--link` 回链知识页；同标题追加使用 `--append`。脚本会同步 human/markdown 镜像、记录元数据、`RECORDS.md` 和两个 SQLite 索引。

#### 让后续 Agent 自动遵循检索协议

Agent Policy 是投影到项目工作区的跨 Harness 规则，要求后续 Agent 先运行 `brief`、按返回范围窄读源码、通过 `record` 写入记录并在结束前运行 `maintain`：

```powershell
$Workspace = 'E:\project'

& $Python $Ckb agent-policy install `
  --out $ActiveOut `
  --workspace-root $Workspace `
  --python $Python `
  --ckb $Ckb

& $Python $Ckb agent-policy check --out $ActiveOut
```

该命令写入各 Harness 可发现的项目级规则，只更新带规范 marker 的受管区块，并保留文件中的其他项目说明。

#### 在 Agent 会话中复用常驻 stdio

`stdio` 是基于标准输入输出的一行一个 JSON 对象的本地传输。正式会话通过 Harness 自动化管理其生命周期，不需要每轮手工启动后台进程。

先登记源码仓库、活动知识库、工作区和明确启用的 Harness：

```powershell
$Registry = "$HOME\.ckb\automation-registry.json"

& $Python $Ckb automation register `
  --repo $Repo `
  --out $ActiveOut `
  --workspace-root $Workspace `
  --registry $Registry `
  --harness codex

& $Python $Ckb automation render `
  --harness codex `
  --destination 'E:\project\ckb-codex-bundle' `
  --python $Python `
  --ckb $Ckb `
  --registry $Registry
```

`automation render` 只写入指定隔离目录。检查生成内容后，按 Harness 自身的信任和配置方式安装，不使用整目录覆盖现有 Hook 或项目配置。注册本身不启动进程，也不采集其他目录的会话。

当前会话第一次精确应用 `code-knowledge-builder` Skill 时，适配器执行等价激活，并 single-flight 启动、握手和拥有一个会话级 `serve --stdio`：

```powershell
& $Python $Ckb automation activate `
  --harness codex `
  --cwd $Workspace `
  --registry $Registry

& $Python $Ckb stdio-session list --active
& $Python $Ckb stdio-session status `
  --harness codex `
  --session-id SESSION_ID `
  --out $ActiveOut

& $Python $Ckb stdio-session close `
  --harness codex `
  --session-id SESSION_ID `
  --out $ActiveOut

& $Python $Ckb stdio-session cleanup
& $Python $Ckb stdio-session audit
```

同一 `Harness + session + OUTPUT + executable/protocol` 身份的 `brief`、`retrieve`、`entity`、`neighbors`、`source` 和 `changes` 会复用同一健康 PID。`session.start` 不启动，`turn.stop` 不释放；`session.end`、显式关闭、management `unbind`、Harness unload 或可靠父 PID 死亡会执行有界关闭并等待回收。启动或握手失败时返回 `mode=cli-fallback`、`resident=false`，查询随后退回一次性 CLI。

#### 绑定管理 Agent 对话

`agent-policy` 规定项目级读写规则；`manager` 把一个具体 conversation 绑定到 workspace、源码仓库、知识库、integration branch 和绑定时 HEAD：

```powershell
$ManagerRegistry = "$HOME\.ckb\manager-registry.json"

& $Python $Ckb manager bind `
  --conversation-id CONVERSATION_ID `
  --harness codex `
  --workspace-root $Workspace `
  --repo $Repo `
  --out $ActiveOut `
  --integration-branch INTEGRATION_BRANCH `
  --registry $ManagerRegistry

& $Python $Ckb manager context `
  --conversation-id CONVERSATION_ID `
  --harness codex `
  --question '审阅当前开发分支' `
  --registry $ManagerRegistry `
  --format prompt
```

`manager context` 会重新检查 integration HEAD、工作树、`brief`、开放 feedback、research gap、双 SQLite 和 `maintain`，再生成可注入 Agent 的完整中文管理 Prompt。`manager task-create`、`manager task-review` 和 `manager task-status` 用固定 HEAD 创建并审阅独立 branch/worktree，但不执行合并；合并和活动知识库同步仍由管理 Agent 完成。

### 建库后的维护

#### 运行统一维护门

写入记录、处理 feedback、迁移、重新投影或更新索引后，运行：

```powershell
& $Python $Ckb maintain --out $ActiveOut
```

只有 Agent Policy、简体中文和页面链接、human/markdown 镜像、工作记录、reference、research gap、feedback、operation journal、`agent-index.sqlite`、`machine/knowledge.sqlite` 和人类可读性审计全部通过，才把知识库描述为维护完成。`maintain` 证明协议与索引一致，不替代源码功能测试或运行时验证；源码符号、关系或页面来源变化时，选择迁移、局部重建或 `reindex`，不因一次小修改无条件重扫整个仓库。

#### 迁移到新的源码提交

旧知识库已经完成审计、而新提交只修改部分源码时，在隔离目录启动增量迁移：

```powershell
$OldOut = $ActiveOut
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

迁移始终写入新的 staging 目录。所有门通过后，在同一卷内保留旧输出目录作为回滚基线，再通过目录改名切换，不直接覆盖旧知识库。

本发布分支的 `knowledge-base/` 保留构建机固定快照和本机绑定路径，可直接用于阅读、SQLite 检索和发布完整性复核。在另一台机器继续写入、运行 `status`、`maintain` 或定位源码前，先迁移到当地干净 Git 提交，或从该提交重新建库。

#### 使用对应的回滚入口

- 活动知识库切换：保留切换前的旧输出目录；出现问题时先停止写入，再把目录名称切回旧输出并重新运行检索与维护门。
- CKB 5.4.0 本机构建环境的稳定知识库切换：运行 `delivery/rollback-stable-kb.ps1`。该脚本使用构建机保留的基线与回滚程序。
- 已推送发布分支：运行 `delivery/rollback-github-release-5.4.0.ps1`，通过新的 revert commit 恢复发布树，不 force push，也不改写公开历史。

#### 按目的阅读实现协议

- [阅读完整建库工作流，了解输入前提与分阶段完成门](source/references/workflow.md)
- [阅读 Agent 确定性检索协议，核对档位、来源范围与完成门](source/references/agent-retrieval.md)
- [阅读固定基线与 Agent 修改会话，设计修改记录和验证边界](source/references/workspace-mode.md)
- [阅读会话、Hook 与常驻 stdio 协议，接入 Harness 生命周期](source/references/automation.md)
- [阅读增量迁移协议，把已审阅知识迁移到新提交](source/references/migration.md)
- [阅读跨 Harness Agent Policy，核对各宿主的自动发现入口](source/references/agent-policy.md)
- [阅读人类可读页面约束，核对标题、叙述、来源链接和页面完成门](source/references/human-readable-pages.md)
