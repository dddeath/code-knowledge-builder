# Obsidian Canvas 与 Agent 可视化官方来源审阅

核对日期：2026-09-02
研究基线：`150a1ce8ea3fca0f7ce2f56c731d42a9973ee0e3`
稳定知识库缺口：`gap-bb90bd3314185078a6a0a7cdb8d271e6`

## 证据状态

- **来源确认**：由官方文档、协议规范、仓库 manifest、原始源码或测试源码直接支持。
- **合理推断**：由两个以上来源边界推导，但尚未通过 CKB 原型运行。
- **待原型验证**：仓库存在实现或测试，本研究没有安装、启动或接入 CKB。
- **待用户决策**：会改变活动 vault、稳定知识库、插件部署或长期维护成本的选择。

本研究没有把 README 中的功能表等同于运行结果。候选仓库的版本、权限和工具形状由 manifest、源码与仓库测试交叉核对；仓库测试只表示项目包含相应测试，不表示本任务已执行第三方测试。

## CKB 当前边界

CKB `brief --profile fast` 已返回 `status=passed`、`open_feedback=0`、`grep_fallback_required=false`，Agent pack 为：

`E:\knowledge_builder\self-workspace\knowledge-base\machine\agent-packs\pack-20260901-175741-198169-01.md`

由该 pack 与当前基线文档确认：

1. `OUTPUT/machine/knowledge.sqlite` 是完整 Agent 检索层；Obsidian 搜索不是完整实体召回入口。
2. `OUTPUT/human` 是人类主投影，`OUTPUT/markdown` 是兼容镜像；`INDEX.md`、`WIKI.md`、`RECORDS.md`、知识页和来源链接是人类导航入口。
3. Agent pack 是预算化检索结果，完整候选、得分和检索统计留在机器 record；可视化不应重新展开全部机器实体。
4. 当前 Obsidian companion 的已验收职责是选区解释、重新检索、审计凭据和学习笔记写入；它没有 Canvas 生成合同。
5. 本研究只形成设计输入，Canvas、MCP、Skill 和 companion 扩展都不是当前 CKB 已支持能力。

本地来源：

- [`references/obsidian.md`](../../obsidian.md)
- [`references/obsidian-companion-plugin.md`](../../obsidian-companion-plugin.md)
- [`references/agent-retrieval.md`](../../agent-retrieval.md)

## JSON Canvas 公开格式

### 来源确认

- Obsidian 将 Canvas 作为 core plugin，`.canvas` 文件使用开放的 JSON Canvas 格式；画布可放置笔记、附件、网页、文本卡片并用有向线连接。文本卡片不会进入 Obsidian backlinks，文件卡片会回到 vault 文件。[Obsidian Canvas 帮助](https://obsidian.md/help/plugins/canvas)
- JSON Canvas 规范当前公开版本是 **1.0（2024-03-11）**。顶层只有可选 `nodes` 与 `edges` 数组；节点类型为 `text`、`file`、`link`、`group`。[JSON Canvas 1.0 原始规范](https://raw.githubusercontent.com/obsidianmd/jsoncanvas/main/spec/1.0.md)
- 通用节点要求 `id`、`type`、`x`、`y`、`width`、`height`；文件节点使用 `file`，可用以 `#` 开头的 `subpath` 指向标题或块；链接节点使用 `url`；组节点可带 `label`、`background`、`backgroundStyle`。
- 边要求 `id`、`fromNode`、`toNode`，可带两端方向、端点形状、颜色和标签。规范定义的默认端点为起点 `none`、终点 `arrow`。
- Obsidian API 当前 `canvas.d.ts` 仍采用同一四类节点与边结构，并允许顶层、节点和边携带任意附加键用于前向兼容。[Obsidian API `canvas.d.ts` 固定提交](https://raw.githubusercontent.com/obsidianmd/obsidian-api/cc1744324150c632416857c98964f87b1574a5fc/canvas.d.ts)

### 版本与稳定性边界

- JSON Canvas 仓库当前 HEAD 为 `456f843cb293df4f4ab1763e22ccb46a80b307c8`，2026-07-24 仍有维护活动；仓库没有 GitHub release。
- `spec/1.0.md` 最近一次提交是 `cb29ef61788cf430f3deb7ed3501110ed5bced7c`（2024-04-11），内容是补充端点默认值。自此没有对 1.0 文件的提交，可作为低漂移信号，但不是未来兼容保证。
- Obsidian API 的 Canvas 类型最近一次专门修改是 `9ad9c0b89a878a96da2a127bd35e6864f0ab87aa`（2024-09-19），把 `fromSide`/`toSide` 标为可选；当前 API HEAD 为 `cc1744324150c632416857c98964f87b1574a5fc`，对应 Obsidian 1.13.2 的 API 包。
- 因规范允许附加键，CKB 原型解析时可以忽略未知键；生成时仍应只写 JSON Canvas 1.0 标准字段，避免把 CKB 私有机器字段扩散到人类画布。

### 许可证边界

- `obsidianmd/jsoncanvas` 仓库、规范和关联资源使用 **MIT** 许可证。[JSON Canvas 仓库](https://github.com/obsidianmd/jsoncanvas)
- `obsidianmd/obsidian-api` 使用 **MIT** 许可证。
- Obsidian 应用本身是许可软件，不因 JSON Canvas 格式开放而变成 MIT 软件；本研究只依赖公开文件格式和 API 类型，不复制应用实现。[Obsidian Terms of Service](https://obsidian.md/terms)

## MCP 协议与 Codex 宿主边界

### MCP

- 当前公开 MCP 规范版本是 **2026-07-28**；协议把工具、资源、Prompt、授权和传输分开，工具输入/输出可由 JSON Schema 约束。[MCP 2026-07-28 概览](https://modelcontextprotocol.io/specification/2026-07-28/basic)
- 标准传输是本地子进程 `stdio` 与 Streamable HTTP。`stdio` 的凭据通常由环境提供；HTTP 应使用授权框架。传输只承载消息，不自动提供 vault 权限、事务或回滚。[MCP 2026-07-28 传输](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
- MCP 工具的 `readOnlyHint`、`destructiveHint` 等注解是提示，不替代服务端权限检查。结构化输出也不表示宿主一定能渲染第三方 UI。

### Codex Skills 与 Visualizations

- OpenAI 官方文档把 Skill 定义为 `SKILL.md` 加可选脚本、参考和资源；Skill 可以显式或按描述隐式触发。Skill 负责工作流，不自动获得额外文件权限。[OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills)
- Codex 可连接本地 `stdio` 或 Streamable HTTP MCP；MCP 生命周期和授权由宿主配置与服务器共同承担。[OpenAI Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- OpenAI Visualizations 是 ChatGPT 宿主中的交互解释能力；官方页面明确 Codex CLI 与 IDE extension 不渲染 Visualizations。它不是 Obsidian `.canvas` 持久化格式。[OpenAI Visualizations](https://learn.chatgpt.com/docs/visualizations)
- 当前本机缓存的 OpenAI `visualize` 插件版本为 `1.0.23`、许可证字段为 `Proprietary`。其 Skill 可输出静态 Mermaid，或把小于 1 MiB 的 HTML fragment 交给支持的会话宿主渲染；该 HTML 与 `window.openai` 交互都属于宿主能力，不属于 CKB。

本地证据：

- `C:\Users\19739\.codex\plugins\cache\openai-bundled\visualize\1.0.23\.codex-plugin\plugin.json`
- `C:\Users\19739\.codex\plugins\cache\openai-bundled\visualize\1.0.23\skills\visualize\SKILL.md`

## 来源审阅清单

| 对象 | 固定版本或提交 | 许可证 | 最近维护证据 | 本研究使用的证据 | 状态 |
|---|---|---|---|---|---|
| JSON Canvas | 规范 1.0；repo HEAD `456f843c` | MIT | repo HEAD 2026-07-24；规范文件 2024-04-11 后未改 | 规范、仓库 API、LICENSE | 来源确认 |
| Obsidian Canvas | Obsidian API HEAD `cc174432`（1.13.2 API） | 应用许可；API MIT | API HEAD 2026-07-14 | 官方帮助、`canvas.d.ts`、Terms | 来源确认 |
| MCP | 2026-07-28 | 规范页面 | 当前公开规范路径 | 概览、传输、授权边界 | 来源确认 |
| OpenAI Skill | 当前官方文档；本机 `visualize` 1.0.23 | 本机插件 Proprietary | 文档与本机 manifest 于 2026-09-02 核对 | 官方文档、本机 Skill 与 manifest | 来源确认 |
| CKB | baseline `150a1ce8` | 项目许可证边界不在本研究改动范围 | 当前 Agent pack 2026-09-01 | pack、Obsidian/companion/retrieval 文档 | 来源确认 |

精确 URL、候选提交、API 核对时间和证据状态同时保存在 [`sources.json`](sources.json)。
