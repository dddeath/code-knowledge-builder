# 跨 Harness Agent 检索与维护协议

## 目标

知识库不能依赖用户在每轮任务中重复点名 Skill。`agent-policy` 把必要约束投影为各 Harness 会自动发现的项目级指令，同时用确定性审计检查写入结果。

## 安装

在知识库已经完成 machine、human 与 markdown 投影后运行：

```powershell
& PYTHON scripts\ckb.py agent-policy install `
  --out OUTPUT `
  --workspace-root TASK_ROOT
```

`TASK_ROOT` 是 Agent 实际启动任务的目录，可以与 Git 仓库根目录分离。命令始终在以下知识库根写入精确生成的适配文件：

- `OUTPUT`
- `OUTPUT/human`
- `OUTPUT/markdown`

并在每个显式 `--workspace-root` 写入或更新一个带边界标记的受管区块，保留文件中原有的其他项目说明。重复安装只替换该区块，不重复追加。

## Harness 发现文件

| Harness | 入口 |
|---|---|
| Codex | `AGENTS.md` |
| OpenCode | `AGENTS.md` |
| Claude Code | `CLAUDE.md`，导入同目录 `AGENTS.md` |
| Gemini CLI | `GEMINI.md`，导入同目录 `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Cursor | `.cursor/rules/code-knowledge-builder.mdc`，`alwaysApply: true` |
| 其他 Harness | 启动时显式读取 `AGENTS.md` |

人类 Obsidian vault 通过忽略规则和本地 CSS 隐藏根目录的三个适配 Markdown 文件，避免把工作协议混入普通知识页导航。

## 项目指令、Skill 与运行时来源矩阵

“自动注入项目指令”只表示 Harness 在文件存在且当前 surface 支持时把对应文件加入上下文；它不等于 `manager context` 自动注入，也不证明 `code-knowledge-builder` Skill 正文已经加载。当前所有生成适配器的 `manager_prompt.automatic_injection` 均为 `false`，完整管理 Prompt 仍由 `manager context --format prompt` 显式取得。

| Harness | 项目指令自动来源 | Skill 精确加载 | 激活／注册 | OUTPUT 发现来源 |
|---|---|---|---|---|
| Codex | `AGENTS.md`；文件存在时按项目层级加载 | `$code-knowledge-builder` | 项目一次 `automation register`；原生精确 Skill 证据或 `automation activate` | 当前任务显式绑定 → `AGENTS.md` → `manager context` → `automation registry` |
| Claude Code | `CLAUDE.md` 自动加载并 `@./AGENTS.md` | `/code-knowledge-builder` | 同上；Skill/Hook 元数据不可见时使用 `automation activate` | 当前任务显式绑定 → `CLAUDE.md`/`AGENTS.md` → manager → registry |
| OpenCode | `AGENTS.md` | `skill(name=code-knowledge-builder)` | 同上；生成 Plugin 的精确 command 事件可发送 `skill.applied` | 当前任务显式绑定 → `AGENTS.md` → manager → registry |
| Gemini CLI | `GEMINI.md` 自动加载并 `@./AGENTS.md` | `activate_skill(name=code-knowledge-builder)` | 生命周期 Hook 不冒充 Skill 激活；使用 canonical `skill.applied` 或 `automation activate` | 当前任务显式绑定 → `GEMINI.md`/`AGENTS.md` → manager → registry |
| GitHub Copilot | `.github/copilot-instructions.md`；具体 surface 以官方支持矩阵为准 | `/code-knowledge-builder` 或 Agent 对同名 Skill 的精确加载 | 生命周期 Hook 不冒充 Skill 激活；使用 canonical `skill.applied` 或 `automation activate` | 当前任务显式绑定 → Copilot instructions → manager → registry |
| Cursor | `.cursor/rules/code-knowledge-builder.mdc`，`alwaysApply: true` | `/code-knowledge-builder`，按消息附加或作为 active mode | 生命周期 Hook 不冒充 Skill 激活；使用 canonical `skill.applied` 或 `automation activate` | 当前任务显式绑定 → always-on rule → manager → registry |
| 通用 Harness | 不自动读取；调用方显式加载项目 `AGENTS.md` | 调用方加载精确 `SKILL.md` 正文 | 提交 canonical `skill.applied`，或调用 `automation activate` | 当前任务显式绑定 → manager → registry；不扫描目录猜测 |

宿主发现行为依据各自一手资料：[Codex `AGENTS.md`](https://developers.openai.com/codex/guides/agents-md) 与 [Codex Skills](https://developers.openai.com/codex/skills)、[Claude Code memory](https://docs.anthropic.com/en/docs/claude-code/memory) 与 [Claude Code Skills](https://code.claude.com/docs/en/slash-commands)、[OpenCode instructions](https://opencode.ai/docs/rules/) 与 [OpenCode Skills](https://opencode.ai/docs/skills/)、[Gemini CLI `GEMINI.md`](https://google-gemini.github.io/gemini-cli/docs/cli/gemini-md.html) 与 [Gemini CLI Skills](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md)、[GitHub Copilot instructions support](https://docs.github.com/en/copilot/reference/custom-instructions-support) 与 [Copilot Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)、[Cursor Rules](https://docs.cursor.com/context/rules-for-ai) 与 [Cursor Agent Skills](https://prod.cursor.com/docs/skills)。这些资料证明宿主发现入口；`integration.json.retrieval_contract` 证明 CKB 生成器实际声明；`tests/harness_retrieval_contract_probe.py` 证明 CKB 运行时实际执行，三者不互相替代。

## 强制读路径

1. `brief --profile fast`；
2. 读取返回的预算化 Agent pack；
3. 用 `entity`、`neighbors`、`source`、`changes` 缩小范围；
4. 仅在 `needs-source-read` 或已得到精确路径/行范围后读取源码；
5. `grep` 只补充精确范围，不替代机器库首轮检索。

这个顺序同时减少上下文消耗，并让每次结论带有可复查的实体、关系和源码范围。

## 强制写路径

- 生成器管理的代码页、索引页、投影清单和 SQLite 文件不直接编辑；
- 分析、修改、踩坑、实验和会话页使用 `record`；
- 非会话页必须通过 `--from-pack`、`--from-query` 或唯一 `--link` 连接已有知识页；
- 正文使用简体中文；
- 更新已有人工笔记使用同标题和 `--append`；
- Hook 只负责事件采集和审核后新建记录，更新其他已有页面使用显式命令，不按每轮对话扩散。

## 确定性审计

```powershell
& PYTHON scripts\ckb.py agent-policy check --out OUTPUT
```

检查内容包括：

1. 各 Harness 指令文件与当前协议完全一致；
2. workspace 受管区块存在且只有一份；
3. 人工笔记符合中文、标签和双链规则；
4. `human` 与 `markdown` 笔记集合和字节一致；
5. 每篇人工笔记都有 `workspace-meta/notes` 审阅元数据；
6. `agent-index.sqlite` 和 `machine/knowledge.sqlite` 中的笔记标题、路径、类型和正文与文件一致；
7. 两个 SQLite 数据库完整性检查通过。

任何检查失败时，本轮只能报告具体失败项；修复后重新运行本命令。

## 低版本协议批量升级

批量接口只处理 Agent Protocol 管理层，不重新扫描 Git，不重建实体、关系、人类代码页、`machine/knowledge.sqlite` 或 `agent-index.sqlite`。支持的确定性路径固定为：

| 源版本 | 目标版本 | 路径 |
|---|---|---|
| `1.0.0` | `1.5.0` | `1.0.0 → 1.3.0 → 1.4.0 → 1.5.0` |
| `1.3.0` | `1.5.0` | `1.3.0 → 1.4.0 → 1.5.0` |
| `1.4.0` | `1.5.0` | `1.4.0 → 1.5.0` |
| `1.5.0` | `1.5.0` | 审计后幂等跳过 |

未知版本、反向迁移和矩阵中没有连续边的路径均按单库失败，不推测协议内容。manifest 只接受固定字段；`OUTPUT` 只能位于显式 `allowed_roots` 内，多个 `OUTPUT` 不得重复或互相嵌套：

```json
{
  "schema_version": 1,
  "allowed_roots": ["E:\\CKB-projects"],
  "projects": [
    {
      "project_id": "project-a",
      "output": "E:\\CKB-projects\\project-a\\knowledge-base",
      "workspace_roots": ["E:\\CKB-projects\\project-a"],
      "source_version": "1.3.0",
      "target_version": "1.5.0",
      "harnesses": ["codex", "claude", "gemini", "copilot", "cursor"],
      "python": "C:\\CKB-runtime\\python.exe",
      "ckb": "C:\\CKB-skill\\scripts\\ckb.py",
      "expected_digest": "AGENT_PROTOCOL_JSON_SHA256"
    }
  ]
}
```

`expected_digest` 是计划时 `OUTPUT/workspace-meta/agent-protocol.json` 的小写 SHA-256。计划还会计算全部协议受管文件的 `observed_digest`；`apply` 同时核对 plan 自身摘要和逐库 `observed_digest`，因此 plan 后发生的任何受管字节漂移都会阻止该库写入。

```powershell
& PYTHON scripts\ckb.py agent-policy batch plan `
  --manifest MANIFEST.json --write PLAN.json

& PYTHON scripts\ckb.py agent-policy batch apply `
  --plan PLAN.json --state BATCH-STATE.json

& PYTHON scripts\ckb.py agent-policy batch status `
  --state BATCH-STATE.json

& PYTHON scripts\ckb.py agent-policy batch audit `
  --state BATCH-STATE.json

& PYTHON scripts\ckb.py agent-policy batch rollback `
  --state BATCH-STATE.json --project project-a
```

省略 `plan --write` 时只向标准输出返回稳定 JSON，目标知识库零写入。`BATCH-STATE.json` 必须位于所有目标 `OUTPUT` 之外；每个项目使用独立 OUTPUT 锁、备份和原子替换。单库审计失败时立即恢复该库的原始受管字节，其他库继续执行。再次运行同一 `apply` 时，已成功且摘要一致的项目返回 `skipped`，中断在 `applying` 的项目先核对当前文件只包含 baseline 或本批 desired 字节，再恢复 baseline 并续跑。

OUTPUT 锁使用 schema 1 有界 JSON，记录 owner PID、owner token、进程启动标识、主机名和创建时间，并在持有期保留操作系统级 descriptor lock。超过 stale 阈值本身不触发回收：活 owner 始终返回 busy；PID 无法核验或跨主机时保持 busy；只有旧锁超过阈值且已确认 owner 死亡、PID 已复用，或损坏记录满足 stale 恢复条件时才在已获取 descriptor lock 后原位接管。释放时再次核对文件身份和 owner token，token 漂移或文件被替换时保留对方锁并返回固定失败分类。旧版 PID-only 锁仍会先核验 PID；活 PID 不因旧 mtime 被接管。

workspace 指令文件必须含一对规范 marker。重复 marker、破损 marker、声明旧版本与管理区内容不一致，以及管理区中混入用户文本都会在 plan 阶段失败。升级只替换 marker 内的 CKB 管理区；marker 外 UTF-8/BOM、中文、空行、前后章节和换行字节保持不变，文件权限保持原值。内部生成适配器、Obsidian 忽略规则、隐藏 CSS 和插件存在时的 `.ckb/output-contract.json` 与目标协议一起更新。

`rollback` 默认选择所有已完成项目，也可重复给出 `--project` 只恢复子集。它先要求当前受管摘要仍等于本批次 `applied_digest`；批次后的用户修改会返回 `rollback-external-drift`，不会被覆盖。成功回滚从已核验备份恢复原始存在性、字节和权限。批次 state 和 operation journal 只保存固定 ID、版本、摘要、状态、失败类别与证据路径；不保存 prompt、secret、token、transcript 或用户文档正文。

## conversation 级管理身份

项目级 `agent-policy` 说明知识库对所有 Agent 的固定读取和写入规则；conversation 级 `manager` 绑定在此基础上增加当前任务的 workspace、repo、knowledge base、integration branch 和 bound HEAD。它不替换 `AGENTS.md`，也不把对话正文写入项目指令。

```powershell
& PYTHON scripts\ckb.py manager bind `
  --conversation-id CONVERSATION_ID --harness HARNESS `
  --workspace-root WORKSPACE --repo REPO --out OUTPUT `
  --integration-branch INTEGRATION_BRANCH --registry MANAGER_REGISTRY

& PYTHON scripts\ckb.py manager context `
  --conversation-id CONVERSATION_ID --harness HARNESS `
  --question "QUESTION" --registry MANAGER_REGISTRY --format prompt
```

绑定前必须满足：workspace、repo 与 output 存在；repo 是所给 Git worktree 的根；当前分支就是 integration branch；该分支有 HEAD。工作树存在未提交修改时仍可登记管理身份，绑定结果会返回 `clean=false` 和有限的 `dirty_paths`；后续状态保持 `blocked`，直到工作树恢复干净，因此不会绕过任务派发与合并前的干净工作树要求。相同 Harness + conversation + project 重复绑定返回同一个 `binding_id`；同一身份指向另一项目时结构化失败。解绑只停止后续管理上下文获取，保留绑定和审计历史。

完整管理 Prompt 会列出 `brief`、feedback、gaps、reference、record、maintain 的精确入口，并重新报告 HEAD drift、dirty tree、开放 error feedback、两个 SQLite 完整性和 maintain 失败项。Prompt 审计缺少任一固定职责或命令时，context 增加 `management-prompt-audit-failed` 阻断项。
