# Code Knowledge Builder Companion

这是一个以 Claudian 成熟实现为基础的桌面端 Obsidian 插件。它保留 Claudian 的聊天侧栏、会话管理和 provider 架构，并增加“选中文本后从右键菜单提问，由 Agent 通过 CKB 检索、生成和审计，再把解释写入当天学习页”的 GUI 工作流。

## 已复用的 Harness 实现

插件直接保留 Claudian 固定版本中的成熟 provider：

- Claude Code；
- Codex；
- OpenCode；
- Pi；
- Grok。

provider 选择、CLI 发现、认证环境、模型设置、会话生命周期、流式输出和取消行为仍由 Claudian 维护。选区学习功能通过同一个 `ProviderRegistry` 和专用 auxiliary execution 调用当前启用的 provider，不再实现第二套 Harness 客户端；普通 Inline Edit 仍保持只读。

右键解释默认选择“跟随默认模型”。插件在每次执行时读取 Claudian 的 `lastSelectedChatModel`，同时切换 Provider 并把该模型作为显式 model override，因此用户在聊天模型选择器中从 Claude 切换到 Codex、OpenCode、Pi 或 Grok 后，下一次右键解释会立即沿用新的默认模型。设置面板的“常规 → 知识库选区解释 → 右键解释 Provider”提供可见选项：既可跟随默认模型，也可固定使用任一已启用 Provider；当前实际 Provider/Model 会直接显示在选项说明中。

CKB 对 DSH、Gemini CLI、GitHub Copilot、Cursor 等 Harness 的 Hook 仍负责会话和修改事件同步；这些 Harness 当前没有进入本插件的交互式 provider 列表，因为固定 Claudian 上游没有对应的成熟执行适配器。

## 右键提问与每日学习页

1. 在 Markdown 编辑模式或阅览模式中选择可见文本；
2. 在选区上点击右键，选择“使用知识库解释选中文本”；
3. 插件按设置面板中的可见选项选择执行器；默认随用户最近选择的聊天模型切换，也可固定 Provider；
4. 插件立即打开独立的右侧 `CKB 解释` 视图，然后输入问题或直接使用默认的概念解释问题；
5. 插件通过常驻 CKB stdio 完成 `retrieve --profile fast`，把预算化 Agent pack 直接注入当前 Provider；Provider 以无工具模式只生成中文解释，不启动 grep、Shell、Skill、子 Agent 或第二轮记录工具；
6. 解释返回后，同一 stdio 进程确定性执行记录、索引刷新、`feedback audit` 和 `agent-policy check`；
7. 只有检索、生成和审计凭据齐全时，解释才追加到 `学习笔记/YYYY-MM-DD.md`；
8. 右侧视图持续显示检索、模型生成、审计和写入阶段；“知识库检索证据”显示真实 stdio request ID 与 Agent pack，模型输出进入解释区段后在这里渐进显示正文；
9. 插件打开当天学习页，右侧视图保留完整解释、来源页面入口和学习笔记入口。

解释成功后，右侧视图出现“继续追问”输入框。追问复用同一 Provider 会话，但每轮重新执行 CKB `retrieve` 并注入新的 Agent pack，随后独立写入机器证据、执行两项审计，再以“追问”条目追加到当天学习笔记。可以点击“追问并记录”或按 `Ctrl/Cmd + Enter` 提交；失败时不写入学习笔记。

原有命令 `Ask about selection and save to daily learning note` 保留作为键盘入口，但右键菜单是本版的主要 GUI 入口。两个入口调用同一个 `promptAndExplain` 实现，解释和学习页效果一致。命令 `Open CKB explanation view` 可以随时重新打开独立侧栏；过程与结果不进入 Claudian 聊天栏。

编辑模式使用 Obsidian `editor-menu`，学习记录保留精确起止行。阅览模式只读取浏览器选中的可见文本和当前页面，学习记录标注“阅览模式选中文本”，不反推或虚构源码行号。两种模式共用同一个 stdio 检索、页面生成和审计流程。

### 启动时常驻 stdio 检索

插件加载时优先读取当前 vault 的 `.ckb/output-contract.json`，核对 vault、OUTPUT、Python、`ckb.py`、stdio protocol v2 和方法集合。只有旧知识库没有契约时，才从当前 vault 或其父目录发现 `machine/knowledge.sqlite`，再从受管 `AGENTS.md` 解析绑定。它以无 shell 子进程启动：

```text
ckb.py serve --out OUTPUT --stdio
```

启动后先执行 JSONL `ping`，只接受带 `retrieve`、`record-explanation` 和 `shutdown` 的 `ckb-stdio-retrieval` protocol v2。每次右键解释通过同一进程发送 `retrieve`，读取实际请求 ID、Agent pack 路径和正文；Provider 返回解释后，再发送 `record-explanation` 写入机器审计证据并完成审计。唯一人类输出由插件追加到 `学习笔记/YYYY-MM-DD.md`，不再创建 analysis 页面。插件卸载时发送 `shutdown`，避免留下后台进程。

可选环境变量 `CKB_OUTPUT`、`CKB_PYTHON`、`CKB_SCRIPT` 可覆盖自动发现；默认情况下用户无需填写路径。

选区和问题在进入 JSONL/stdin 前会通过 `utf8SafeText` 规范化：合法 emoji 的 UTF-16 代理对保持原样，剪贴板或 DOM 产生的孤立代理字符替换为 `�`。插件启动 Python 时固定 `PYTHONUTF8=1` 和 `PYTHONIOENCODING=utf-8`，CKB stdio 服务端同时把默认输入输出流固定为严格 UTF-8，避免 Windows 本地代码页把中文 JSONL 解码成乱码。

每天只有一个页面，当天所有解释按时间追加。每条记录包含：

- 来源页面双链；
- 选区行范围；
- 实际执行器；
- 用户问题；
- 原始选中文本；
- 简体中文解释。

命令 `Open today's learning note` 可以直接打开当天页面。插件不预设快捷键，避免覆盖 Obsidian 或用户已有按键。

### CKB 完成门

Provider 返回内容只需包含检索通过标记、生成通过标记和独立解释区段，不允许调用工具。插件把实际 stdio request ID、pack 路径和解释提交给 `record-explanation`；服务端验证该 request 属于当前常驻进程、pack 位于当前 OUTPUT、检索记录通过且解释幂等键有效，然后在 `workspace-meta/stdio/explanations/` 写入机器证据并执行反馈审计和 Agent-policy 审计。通过后插件只更新当日学习页；缺少任一检索、生成或审计证据时，学习页保持不变，右侧 `CKB 解释` 视图持续保留失败原因。

## 安装

把 `dist` 目录中的文件复制到：

```text
VAULT/.obsidian/plugins/code-knowledge-builder-companion/
```

目录内至少包含：

```text
main.js
manifest.json
styles.css
LICENSE
NOTICE.md
```

随后在 Obsidian 的“第三方插件”中启用 `Code Knowledge Builder Companion`，再在插件设置中选择并配置 Claudian provider。

### Agent 部署

0.7.0 包内自带独立部署器。Agent 解压 ZIP 后可以直接执行：

```powershell
python deploy.py deploy --vault 'VAULT' --output 'OUTPUT' --python 'PYTHON' --ckb 'CKB.py'
python deploy.py status --vault 'VAULT'
python deploy.py remove --vault 'VAULT'
```

已安装 CKB Skill 时，也可以先注册一个插件包，再部署到现有知识库：

```powershell
& PYTHON scripts\ckb.py obsidian-plugin register --package 'code-knowledge-builder-obsidian-0.8.0.zip'
& PYTHON scripts\ckb.py obsidian-plugin deploy --out 'OUTPUT'
```

注册后，CKB 后续生成或刷新插件 vault 时会自动部署同一已注册版本并写入输出契约；核心 lite/full ZIP 仍不内嵌插件二进制，保持独立包边界。没有安装插件的 vault 不生成输出契约，也不要求通过该项审计。

## 构建

`upstream.lock.json` 固定 Claudian 与参考项目版本。构建脚本会：

1. 获取或复制固定 Claudian 源码；
2. 应用 `patches/claudian-base.patch`；
3. 执行补丁后源码门，验证默认模型路由、专用写入执行、WSL 认证环境和右侧 ItemView 没有被旧文件覆盖；
4. 执行 `npm ci`、typecheck、lint、聚焦测试和生产构建；
5. 生成可安装的 `dist/`。

```powershell
python scripts/build.py --work BUILD_DIR --out dist --node NODE_EXE --npm-cli NPM_CLI_JS
```

## 数据和边界

选中文本、问题和 provider 工具输出只在用户显式运行命令后进入当前 provider。学习页写入当前 vault，不启用额外网络服务。provider 的认证、网络目标和会话文件继续遵循 Claudian 设置。
