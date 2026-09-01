# Obsidian 多 Harness 学习伴侣

## 交付目标

`plugins/obsidian-code-knowledge-builder` 是桌面端 Obsidian 插件。它直接复用 Claudian 的 provider-neutral 会话和执行架构，保留 Claude Code、Codex、OpenCode、Pi 与 Grok 的设置、CLI/SDK 发现、认证环境、会话生命周期、流式输出和取消行为。每个实际安装本插件的 vault 都由核心投影一个 `.ckb/output-contract.json`；未安装插件的 vault 不生成该文件，审计也不要求它存在。

CKB 只新增三项职责：

1. 在 Markdown 编辑模式或阅览模式中选择文本，通过右键菜单输入问题；
2. 由常驻 stdio 进程先执行 CKB 检索并把 Agent pack 正文直接交给 Provider，Provider 不再通过工具重新读取知识库；
3. 只把通过凭据齐全的只读解释追加到当天唯一的 `学习笔记/YYYY-MM-DD.md`。

## 为什么复用 Claudian

交互式 Harness 连接涉及 CLI 定位、认证环境、模型配置、会话恢复、流式协议、取消、工具权限和 provider 差异。插件固定 Claudian 上游提交，并通过其 `ProviderRegistry`、`ProviderWorkspaceRegistry` 和 `InlineEditService` 执行解释，避免为每个 Harness 再写一套客户端。

当前交互式 provider 与固定 Claudian 上游一致：Claude Code、Codex、OpenCode、Pi、Grok。CKB 的 DSH、Gemini CLI、GitHub Copilot 和 Cursor Hook 继续负责会话/修改事件同步；它们不是本插件内的交互式 provider。

## 右键 GUI 解释流程

在选中文本上点击右键，选择“使用知识库解释选中文本”：

1. 从活动 Markdown 编辑器读取选中文本、文件路径和行范围；
2. 打开问题输入框，默认问题要求解释核心概念、作用、上下文和边界；
3. 读取可视设置“右键解释 provider”；默认值 `follow-default` 使用 `lastSelectedChatModel` 同时解析 Provider 与模型，固定选项则使用指定 Provider 及其已保存模型；
4. 常驻 stdio 进程执行 `retrieve`，返回真实 request ID、pack 路径和 pack 正文；
5. 以独立 auxiliary execution 调用当前设置的 Provider/模型，把 pack 正文直接放入提示词，并使用 `passive` 工具策略；Provider 不调用 Shell、grep、文件读取、Skill 或子 Agent，只根据 pack 生成简体中文解释；
6. 同一 stdio 进程执行 `record-explanation`，验证 retrieval request、pack 路径、检索记录和幂等键后，把机器证据写入 `workspace-meta/stdio/explanations/`；它不创建 analysis 页面；
7. `record-explanation` 在同一调用中执行反馈审计与 Agent-policy 审计，并返回机器证据与审计文件；
8. 插件验证返回凭据，再将问题、原文、解释、来源双链、行范围和执行器追加到唯一的人类输出 `学习笔记/YYYY-MM-DD.md`；
9. 打开当天学习页。

首次解释通过后，右侧 `CKB 解释` 视图显示“继续追问”输入框。提交追问时复用同一 Provider 会话以保留上下文，但不会复用上一轮检索结果：插件为追问重新执行 `retrieve`，把新的 Agent pack、承接问题和上一轮解释一起交给 Provider；随后为追问单独执行 `record-explanation` 和两项审计。通过后，以“追问”条目追加到同一天学习笔记，记录承接问题与本轮追问，不重复整段选中文本。失败、取消或 Provider 连续会话失效时不写学习笔记，用户重新选择文本发起新解释。

执行开始后，插件立即打开独立的右侧 `CKB 解释` 视图。该视图持续显示等待提问、检索知识库、初始化模型、生成解释、确定性记录与审计、写入学习笔记，并在模型输出进入正文标记后显示生成中的解释。“知识库检索证据”固定展示 `CKB stdio · retrieve --profile fast`、真实 request ID 和 Agent pack 路径；成功门要求 `record-explanation` 绑定同一 request 与 pack，因此可以确定解释经过 CKB 检索路径。成功后保留完整解释和学习笔记入口；失败或取消时保留准确终态。辅助 Notice 仍显示当前阶段，模型执行超过 5 分钟时自动取消并显示超时原因。

## 在哪里查看解释

通过全部完成门后，面向用户的解释追加到当前 vault：

```text
学习笔记/YYYY-MM-DD.md
```

插件会自动用新标签页打开该文件。右侧 `CKB 解释` 视图中的“打开学习笔记”与“打开来源页面”也提供固定入口。机器审计证据位于：

```text
workspace-meta/stdio/explanations/REQUEST.json
```

该 JSON 只用于确定性核验，不进入 Obsidian 人类导航。右键解释不再生成 `human/analysis/GUI 学习解释 *.md` 或 `markdown/analysis/GUI 学习解释 *.md`。右侧 Claudian 聊天栏只承载普通交互会话；右键解释使用独立执行器和独立 `CKB 解释` ItemView，不把过程或结果写入聊天栏。若失败，学习笔记保持不变，侧栏保留检索、Provider、凭据或超时错误。

同一天所有解释进入同一文件，并通过串行写入队列避免并发覆盖。原有命令入口保留，与右键菜单共用 `promptAndExplain`，不形成第二套解释逻辑。

追问直接在右侧视图输入，点击“追问并记录”或按 `Ctrl/Cmd + Enter` 提交。追问生成过程复用同一套进度、流式正文、知识库检索证据和学习笔记入口；每次成功后仍可继续下一轮追问。

编辑模式从 `Editor` 取得选区与精确行范围。阅览模式在 `.markdown-preview-view` 内监听 `contextmenu`，仅读取 `window.getSelection()` 返回的可见文本和当前页面。阅览模式记录不填写行号，但与编辑模式共用同一 `SelectionLearningService`、stdio 进程、`record` 生成和审计完成门。

## Provider 与默认模型

0.5.0 起，右键解释不再从 `settingsProvider` 推断执行器。设置面板“常规 → 知识库选区解释 → 右键解释 provider”提供：

- `跟随默认模型（当前 Provider / Model）`：默认选项；每次执行时读取聊天模型选择器持久化的 `lastSelectedChatModel`，用户切换默认模型后下一次右键解释立即切换 Provider；
- `固定使用 Provider`：为每个已启用 Provider 生成一个选项，使用该 Provider 保存的模型，模型失效时确定性回退到其当前默认模型。

`SelectionLearningService` 在创建选区学习专用执行器后显式调用 `setModelOverride`，所以 Provider 与模型一起切换，不依赖设置页当前打开的是哪一个 Provider tab。Notice 与学习笔记中的“执行器”同时显示 Provider 和模型，便于核对实际路由。

0.5.1 起，WSL Provider 会把设置中的 `CODEX_HOME`、`OPENAI_API_KEY` 等自定义环境变量加入 `WSLENV`。POSIX 绝对路径不会套用 Windows 路径转换标志，Windows 路径则保留 `/p`；因此 Obsidian 启动的 WSL `codex app-server` 与直接 CLI 使用同一认证环境。

## stdio 生命周期

`CkbStdioClient` 在插件加载时执行以下确定性发现：

1. 从 `FileSystemAdapter.getBasePath()` 取得当前 vault 本地路径；
2. 优先读取 vault 内的 `.ckb/output-contract.json`，核对 contract 类型、vault 绝对路径、OUTPUT、stdio protocol v2、方法集合、Python 与 `ckb.py`；
3. 只有旧知识库没有输出契约时，才在 vault、父目录或 `CKB_OUTPUT` 中验证 `machine/knowledge.sqlite`，并从受管 `AGENTS.md` 或 `CKB_PYTHON`/`CKB_SCRIPT` 解析绑定；
4. 用 `spawn`直接启动 `ckb.py serve --out OUTPUT --stdio`，不经过 shell；
5. 发送 `ping`，验证 `ckb-stdio-retrieval` 版本；
6. 右键解释通过同一进程发送 JSONL `retrieve` 并直接读取返回的 Agent pack；
7. Provider 生成解释后，通过同一进程发送 JSONL `record-explanation`，完成来源绑定、幂等记录和两项审计；
8. 插件卸载时先发送 `shutdown`，超时后再结束子进程。

stdio 检索请求 ID、pack 路径和 OUTPUT 根作为插件持有的机器证据。Provider 只返回生成通过标记和解释正文；核心 `record-explanation` 依据当前进程保存的 retrieval request 验证 pack 与检索记录，不依赖模型复述路径。解释证据、pack 和两个审计 JSON 必须属于同一 OUTPUT。相同幂等键重试只返回原结果，不重复追加学习内容。

Obsidian 选区、问题和 stdio `question` 都经过 UTF-8 安全规范化。插件启动 Python 时固定 `PYTHONUTF8=1` 与 `PYTHONIOENCODING=utf-8`；Python `stdio_server` 还把默认 stdin/stdout 重配为严格 UTF-8。合法代理对保留，孤立 UTF-16 surrogate 替换为 `�`。这避免 Windows 本地代码页把“学习解释”写成“瀛︿範瑙ｉ噴”。

## Agent 部署与自动覆盖

0.7.0 起，插件 ZIP 自带 `deploy.py`，核心 Skill 同时提供 `obsidian-plugin` 命令。0.7.1 起，部署动作必须同时生成机器可读输出契约。Agent 可以直接完成部署，不再要求用户手工复制目录或让插件从说明文字猜测路径。

仅使用插件包时：

```powershell
python deploy.py deploy --vault 'VAULT' --output 'OUTPUT' --python 'PYTHON' --ckb 'CKB.py'
python deploy.py status --vault 'VAULT'
```

已安装核心 Skill 时，先登记通过发布校验的包，再部署到已有知识库：

```powershell
& PYTHON scripts\ckb.py obsidian-plugin register --package 'code-knowledge-builder-obsidian-0.8.0.zip'
& PYTHON scripts\ckb.py obsidian-plugin deploy --out 'OUTPUT'
& PYTHON scripts\ckb.py obsidian-plugin status --out 'OUTPUT'
```

登记记录与不可变载荷位于当前用户的 `%USERPROFILE%\.ckb\`。登记成功后，CKB 每次初始化或重新投影插件 vault 都自动部署当前登记版本、启用固定插件 ID，并写入 `.ckb/output-contract.json`；因此之后由本项目创建且实际安装插件的 Obsidian 知识库都会携带准确绑定。已有知识库不会因登记动作被隐式遍历，Agent 应对自动化注册表中的每个既有 `knowledge_output` 显式执行一次 `deploy --out`。未安装插件的 vault 不投影输出契约，也不会因为用户级登记文件存在而被审计判错。

部署结果位于：

```text
VAULT/.obsidian/plugins/code-knowledge-builder-companion/
```

并写入 `OUTPUT/workspace-meta/obsidian-plugin.json`。`remove --out OUTPUT` 只删除指定 vault 的插件目录、启用项和部署记录，不删除全局登记包。Obsidian 已运行时需要重新加载应用或关闭后重新打开，才能载入刚替换的 `main.js`。

## 构建与来源

`upstream.lock.json` 固定 Claudian 提交。`patches/claudian-base.patch` 包含入口、设置模型、可视设置、选区学习实现、样式与测试；构建前必须在干净上游副本中完整重放。`scripts/build.py` 随后执行：

```text
npm ci
npm run typecheck
npm run lint
selection-learning 聚焦测试
npm run build
```

Claudian 源码按 MIT 许可证复用，许可证和来源说明随插件发布。LLM Wiki Skill 仅用于研究选区捕获与持久记录的交互形式；由于参考仓库当前没有附带可确认的许可证文件，插件没有复制或重新分发其源码。

## 完成门

- 固定 Claudian 提交与锁文件一致；
- 插件启动后 stdio protocol v2 `ping` 通过，真实 `retrieve` 返回 pack，`record-explanation` 通过且幂等重试不重复写入，卸载后子进程退出；
- 安装插件的 vault 必须存在通过审计的 `.ckb/output-contract.json`；插件缺席时契约状态固定为 `not-required`；
- 补丁可以在干净上游副本应用；
- typecheck、lint、聚焦测试和生产构建通过；
- 编译产物包含 `editor-menu`、`.markdown-preview-view` 阅览选区、右键菜单标题、两个原有命令、Agent pack 注入、被动工具策略、`record-explanation` 和学习笔记写入逻辑；
- 右键动作在问题弹窗出现前创建或复用右侧 `CKB 解释` ItemView；取消、失败和完成状态都必须保留在该视图，不依赖聊天栏或短暂 Notice；
- 聚焦测试覆盖默认模型在 Codex/Claude 间切换、固定 Provider、禁用 Provider 回退、可视下拉选项、model override、WSL 自定义环境传递、AGENTS 绑定解析、stdio pack 注入、确定性记录与审计凭据、幂等重试和缺失凭据时保持学习页不变；
- 真实 Obsidian 声明式设置渲染器必须生成“右键解释 provider”，并显示 `follow-default`、当前 Provider/Model 与已启用 Provider 固定选项；
- `main.js`、`manifest.json`、`styles.css`、MIT `LICENSE`、`NOTICE.md`、`build-record.json` 和 `deploy.py` 齐全；
- 可复现构建产物与交付字节一致；
- 安装与回滚只影响指定 vault 的插件目录。
