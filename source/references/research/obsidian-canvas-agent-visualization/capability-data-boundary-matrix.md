# Obsidian MCP、companion 与 Skill 能力和数据边界

核对日期：2026-09-02。候选范围选择了一个 Obsidian 内嵌 MCP、两个通用外置 MCP、一个专用 JSON Canvas MCP、一个直接 Canvas 实现排除样本、一个独立 JSON Canvas Skill，以及当前宿主可视化能力。它覆盖主要集成形态，不声称穷尽 GitHub 上所有同名仓库。

## MCP 候选矩阵

| 候选 | 精确版本或提交 | 运行位置与传输 | 授权与权限边界 | 读能力 | 写能力 | Canvas 边界 | 维护与许可证 | 证据状态 |
|---|---|---|---|---|---|---|---|---|
| `coddingtonbear/obsidian-local-rest-api` | release/manifest `5.1.0`；HEAD `209eff08` | Obsidian desktop community plugin 内；Streamable HTTP `127.0.0.1` | Bearer API key；MCP 暴露当前 vault；源码没有独立的 CKB path allowlist | 文件、二进制、活动文件、搜索、标签、文档 map、UI 打开 | 整文件写入、追加、结构化 patch、删除、移动、复制、命令执行 | 可把 `.canvas` 当 UTF-8 vault 文件完整读写；没有 JSON Canvas schema、布局预算或 CKB 回链验证 | 2026-08-31 HEAD；MIT | 工具、认证和集成测试为来源确认；Canvas 适配待原型验证 |
| `cyanheads/obsidian-mcp-server` | `3.5.0` / `030e7b9b` | 独立本地 Node/Bun；`stdio` 或 Streamable HTTP；上游依赖 Local REST API | Bearer API key；`OBSIDIAN_READ_PATHS`、`OBSIDIAN_WRITE_PATHS`、`OBSIDIAN_READ_ONLY`；命令执行默认关闭；HTTP 对外暴露还需 MCP auth | 笔记、目录、标签、搜索、frontmatter、文档 map、UI 打开 | 创建/覆盖、append、patch、replace、标签/frontmatter、确认后删除 | `contentType=json` 与任意 vault-relative path 使整文件 `.canvas` 写入在类型上可行；没有 Canvas 专用工具或仓库 Canvas 测试 | release 2026-08-22；Apache-2.0 | 权限和 note 工具为源码/测试确认；Canvas 为合理推断、待原型验证 |
| `MarkusPfundstein/mcp-obsidian` | package `0.2.2` / `5ee0b84f` | 独立本地 Python `stdio`；上游依赖 Local REST API | `OBSIDIAN_API_KEY` 环境变量；默认整个 vault；没有 path allowlist 或全局 read-only；删除要求输入 `confirm=true` | 文件/目录、单/批量内容、简单与复杂搜索、frontmatter、周期笔记 | 完整覆盖、追加、Markdown section patch、确认后删除 | 可通过通用 `put_content` 完整覆盖 `.canvas`，但没有 schema、ID/边校验、布局或 CKB 来源门 | HEAD 2026-08-31；无 release；MIT | 工具注册和 handler 测试为来源确认；Canvas 为合理推断、待原型验证 |
| `Cam10001110101/obsidian-jsoncanvas` | package `0.2.0` / `687b8a1e` | 独立 Python；默认 `stdio`，可 Streamable HTTP；不要求 Obsidian 运行 | `OUTPUT_PATH` 目录边界；文件名去目录并限制在该目录；HTTP 无应用层认证，默认只绑定 localhost | list/read/search/validate Canvas；可返回结构化 JSON；可导出 Markdown/SVG | create/edit Canvas；先在内存验证，再直接覆盖目标文件 | JSON Canvas 1.0 专用；校验节点、ID 和边；不验证 CKB 人类页/来源是否存在；生成文件自动加日期前缀且不能指定子目录 | 2026-05-21 HEAD 内容；无 release；MIT | 工具和仓库测试为源码确认；未在本任务运行；MCP Apps UI 取决于宿主 |
| `bazylhorsey/obsidian-mcp-server` | package `1.0.0` / `ba06b167` | 独立 Node；直接文件系统或远端 vault 配置 | README 描述本地目录/远端 API；没有本研究可确认的细粒度 path policy | note、graph、Canvas、模板等多域能力 | 直接 Canvas node/edge 增删和整文件覆盖 | `CanvasService` 直接 `readFile`/`writeFile`，没有 Canvas 专用测试文件，也没有写前备份或 CKB 回链门 | 最后提交 2025-10-16；package 声称 MIT，但仓库无 LICENSE 且 GitHub SPDX 为空 | 源码确认直接写入；许可不完整，排除 |

### 候选证据说明

1. `coddingtonbear/obsidian-local-rest-api` 的 MCP 是目前最靠近 Obsidian 运行时的候选，能读取活动文件并调用 UI；它的权限面也是整个 vault 文件 API，仍需要 CKB 自己收窄目标和回滚。
2. `cyanheads/obsidian-mcp-server` 的 read/write allowlist 和 read-only 开关优于通用整库权限，但其核心对象是 note。把 JSON Canvas 写成一个 JSON 文件不等于有 Canvas 语义验证。
3. `MarkusPfundstein/mcp-obsidian` 体量小、使用广，但写入默认覆盖面更宽，缺少 CKB 所需的 deterministic budget、来源回链和隔离 rollback。
4. `Cam10001110101/obsidian-jsoncanvas` 证明专用 Canvas MCP 可以提供结构化输入输出和验证；其路径/命名合同、HTTP 授权和 CKB 数据边界不适合作为 CKB 第一原型的直接依赖。
5. `bazylhorsey/obsidian-mcp-server` 的 README 功能较多，但许可证文件缺失、Canvas 测试缺失、维护时间弱于其他候选，不能进入下一阶段依赖集。

候选源码和固定提交 URL 见 [`sources.json`](sources.json)。

## Agent 与 Skill 候选矩阵

| 候选 | 输出结构 | 权限和生命周期 | 属于宿主的能力 | CKB 可拥有的能力 | 结论 |
|---|---|---|---|---|---|
| `kepano/obsidian-skills` 的 `json-canvas` | 指导 Agent 创建/编辑 JSON Canvas 1.0，校验唯一 ID 与悬空边 | 指令型 Skill；文件权限继承 Agent 宿主；只在触发时运行 | Skill 发现、模型执行、文件写权限 | 冻结输入、确定性选择、预算、链接验证、布局、回滚 | 适合作为结构参考，不直接等同 CKB Skill；进入设计输入 |
| OpenAI `visualize` 1.0.23 | 静态关系可输出 Mermaid；交互解释可输出宿主 HTML fragment | ChatGPT/Codex 宿主插件生命周期；本机插件为 Proprietary | HTML/交互渲染、`window.openai`、会话内展示 | 只提供经过来源门的数据，不应依赖宿主状态保存 CKB 知识 | 只作会话解释/设计预览，不作 Obsidian Canvas 持久层 |
| CKB 当前 companion | 选区问题、Agent pack、机器审计、`学习笔记` | Obsidian 插件加载/卸载；vault output contract；本地 stdio | Obsidian UI、Provider 会话、编辑器选区 | CKB 检索、来源绑定、审计凭据 | 当前没有 Canvas 合同；后续可作为打开/刷新入口，不作为第一原型生成器 |
| 拟议的 CKB 独立 Canvas Skill | 冻结 JSON 输入、`.canvas`、验证 manifest、rollback manifest | 按任务触发；宿主只授予 staging 与一个目标文件；无需 Obsidian 运行 | Skill 调用与文件权限 | 所有选择、预算、回链、验证和回滚由确定性脚本拥有 | 推荐进入独立设计与最小原型 |

## 三种集成位置比较

| 决策项 | MCP server | Obsidian companion | 独立 CKB Skill |
|---|---|---|---|
| 最小权限 | 取决于 server；通用 Obsidian MCP 常得到 vault 级 token，只有部分实现提供 path allowlist | 可只注册一个 CKB 命令，但插件本身运行在 vault 内并可访问 Obsidian API | 可把读范围固定到一个 Agent pack/record，把写范围固定到 staging 和一个目标 `.canvas` |
| 生命周期 | `stdio` 由宿主拉起；HTTP 独立常驻；还需协议协商、授权和进程恢复 | 随 Obsidian load/unload；升级需插件部署和应用重载 | 仅在请求时运行；无后台服务；失败后重新执行同一冻结输入 |
| 数据流 | 结构化 tool call，易跨宿主；也易把更宽 vault 数据暴露给通用 Agent | 原生掌握活动文件、选区和打开页面；最贴近人类交互 | 直接消费已预算化 CKB 产物；无需再次查询全部 vault 或 SQLite |
| 写入边界 | 由 server 决定；很多实现是覆盖或增量 patch，不带 CKB baseline hash | 可用 Obsidian Vault API 写入，但要处理用户同时编辑和插件重载 | 先写隔离副本，验证后 hash-guarded promotion；rollback 可独立执行 |
| 错误恢复 | JSON-RPC 错误、进程/HTTP 重连、token/协议/上游插件错误并存 | UI 可展示错误；插件异常可能影响当前 Obsidian 会话 | 固定失败码，无部分目标写入；失败保留 staging 和验证报告 |
| 宿主依赖 | MCP client 必须兼容相应协议与可选 UI | 必须安装并运行 Obsidian companion | 只需可执行 Skill/脚本；生成后由任何 JSON Canvas 1.0 应用打开 |
| 维护成本 | 需要跟踪 MCP、SDK、认证、server 与上游 REST 插件 | 需要跟踪 Obsidian API、插件打包、provider 与 UI | 只跟踪 JSON Canvas 1.0、CKB pack/record schema 与 Skill 合同 |
| 第一原型适配 | 中；结构化但权限和依赖偏重 | 中；人机体验最好但会扩大现有插件范围 | 高；边界最窄、最容易与 Markdown 基线公平比较 |

## CKB 数据边界

### 可以进入人类 Canvas

只允许进入已经面向人类或已经有精确来源入口的数据：

- 冻结任务标题与不含内部查询词表的简短说明；
- Agent pack 中入选且存在 `human_page_file` 的知识页/记录页路径；
- 已审阅参考资料页和它的精确归档范围；
- pack 已给出的源码路径、起止行和已验证 editor URI；
- “检索命中”“来源核对”“相关记录”这类由输入字段直接证明的有限边标签；
- 面向人类的状态：`已审阅`、`待验证`。其中 `待验证` 必须有可点击 gap/来源入口，否则整个生成失败。

### 继续留在机器层

- `entity_id`、`document_id`、SQLite row ID、内部 gap ID；
- 检索词项、seed、得分、score breakdown、图传播和 `retrieval_stats`；
- 未审阅的源码摘要、自动推断关系、隐藏机器实体全集；
- pack/record 的绝对机器路径、内部 cache、凭据、环境变量和 MCP token；
- 没有人类页或精确来源范围的候选；
- 为填满画布而新增的实体、标签、状态或关系。

### 离机与离开索引不是一回事

第一原型仍应完全本地运行。“进入 Canvas”表示从机器索引投影到人类可见文件，不表示允许上传到第三方服务。若将来使用远端 MCP、Hosted Plugin 或云端模型展示 Canvas，必须单独定义允许离机的字段，本研究不作该授权。

## 推荐与排除

### 推荐进入下一阶段

设计一个 **独立 CKB Canvas Skill**，其中 Skill 只编排，确定性脚本负责选择、排序、预算、布局、链接核对、写入和回滚。第一原型消费冻结 Agent pack/record，在隔离目录生成一个 JSON Canvas 1.0 文件；Obsidian companion 只作为以后可选的“打开/刷新”入口。

选择依据：

1. 不引入 vault 级 API token、HTTP 服务或 Obsidian 插件升级；
2. 可以用与 Markdown baseline 相同的 Agent pack 和知识页，隔离可视布局变量；
3. 所有选择和预算可由脚本判定，避免模型把机器图展开成人类实体墙；
4. 生成文件、验证报告和 rollback manifest 可独立测试；
5. 通过 benchmark 后仍可把同一核心封装成 MCP tool 或 companion command，无需重做数据合同。

### 排除方案

- **排除把通用 Obsidian MCP 作为第一原型必需依赖**：权限和生命周期比生成一个受控 `.canvas` 文件更宽，而且候选没有 CKB 回链、预算和 rollback 合同。
- **排除 `bazylhorsey/obsidian-mcp-server`**：缺少仓库 LICENSE、Canvas 专用测试和近期维护证据，不满足依赖门。
- **排除把 OpenAI Visualize 当作 Canvas 持久层**：输出与渲染依赖宿主，官方文档也明确 Codex CLI/IDE 不渲染 Visualizations；它不产生 Obsidian JSON Canvas 合同。
- **排除直接把机器知识图全量投影**：会暴露内部 ID/得分、超出人类注意力预算，并改变 CKB “机器完整、人类保守”边界。

### 待用户决策

- benchmark 通过后，最终 Canvas 应进入 `OUTPUT/human` 受管投影、进入用户自有文件区，还是只保留导出目录；
- 是否在第二阶段增加 companion 的“打开/刷新 Canvas”命令；
- 是否允许 Canvas 使用 `vscode://` 等 editor URI 作为 `link` 节点，还是只通过知识页间接到达源码。
