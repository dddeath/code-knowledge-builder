# Obsidian 多 Harness 选区学习插件

标签：#类型/变更

## 当前能力

项目新增桌面端 Obsidian 学习伴侣。插件直接复用 Claudian 的 provider-neutral 会话和执行架构，保留 Claude Code、Codex、OpenCode、Pi 与 Grok 的 CLI/SDK 发现、认证环境、模型设置、会话生命周期和流式执行，不再为每个 Harness 编写独立客户端。

## 选区学习流程

用户在 Markdown 页面选择文本后，可以输入自己的问题或使用默认概念解释问题。插件通过当前启用 provider 的只读 inline execution 获取简体中文解释，不替换原文；随后把来源页面双链、选区行范围、执行器、问题、原文和解释追加到 `学习笔记/YYYY-MM-DD.md`。同一天所有解释写入同一页面，并通过串行写入队列避免并发覆盖。

## 来源和许可

Claudian 固定到已记录的上游提交，MIT 许可证、版权说明和构建锁随插件交付。LLM Wiki Skill 只用于研究选区捕获与持久记录的交互形式；参考仓库当前没有附带可确认的许可证文件，因此交付没有复制或重新分发其源码。

## 验证结果

Linux Node 24.16.0 环境中的 typecheck、lint、三项新增功能测试、生产构建和从干净 Claudian 提交开始的可复现构建全部通过；两次产出的 `main.js` 与 `styles.css` 字节一致。CKB 核心、自动化和迁移共四十三项回归测试全部通过。可安装 ZIP 已验证包含编译脚本、插件清单、样式、MIT 许可证、来源说明和构建记录。

## 当前边界

交互式 provider 与固定 Claudian 上游保持一致。DSH、Gemini CLI、GitHub Copilot 和 Cursor 继续通过 CKB Hook 记录会话和修改事件，本版没有把它们声明为 Obsidian 内的交互式 provider。

## 插件源码入口

- [打开插件使用说明](vscode://file/E:/knowledge_builder/self-workspace/source/plugins/obsidian-code-knowledge-builder/README.md:1:1)  `plugins/obsidian-code-knowledge-builder/README.md`
- [打开选区提问服务](vscode://file/E:/knowledge_builder/self-workspace/source/plugins/obsidian-code-knowledge-builder/overlay/src/features/selection-learning/SelectionLearningService.ts:1:1)  `SelectionLearningService.ts`
- [打开每日学习页生成器](vscode://file/E:/knowledge_builder/self-workspace/source/plugins/obsidian-code-knowledge-builder/overlay/src/features/selection-learning/LearningNoteDocument.ts:1:1)  `LearningNoteDocument.ts`

## 相关知识页

- [[prepare_vault 与 install_obsidian 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`

## 后续补充

## 右键 GUI 入口

插件 0.2.0 已在 Markdown 编辑器右键菜单加入“使用知识库解释选中文本”。右键入口和原有命令入口共同调用 `promptAndExplain`，因此问题输入框、选区范围、解释格式、每日学习页路径和串行写入行为保持一致；用户不再需要打开命令面板。

## 知识库工作流约束

解释请求会要求当前 Claudian provider 显式应用 `code-knowledge-builder`，按“开放反馈 → `retrieve --profile fast` → Agent pack → 中文解释 → 当日唯一 `record` 分析记录 → `feedback audit` → `agent-policy check`”顺序执行。返回值必须带有检索、生成、审计和整体工作流四项通过标记以及正式记录路径；任一凭据缺失时，确定性解析器不更新每日学习页。

## 本机部署

插件已部署到当前打开的 `E:\knowledge_builder\self-workspace\knowledge-base\human` vault，`community-plugins.json` 已登记插件 ID。Obsidian 1.13.7 完成平滑重启，实际编辑器右键菜单显示新入口，选择该入口后已打开原有“询问选中文本”问题弹窗。

## 验证结果

固定 Claudian 提交上的 typecheck、lint、生产构建和五项聚焦测试通过；独立快速构建与干净重建的脚本和样式产物一致。CKB 核心回归二十四项通过，Skill 结构验证通过，源码、安装 Skill 副本和 vault 部署文件逐字节一致。

## 后续补充

## 常驻 stdio 初始化

插件 0.3.0 在加载时从当前 vault 或父目录发现 `machine/knowledge.sqlite`，并从受管 `AGENTS.md` 解析 Python 与 `ckb.py`。插件以无 shell 子进程启动 `ckb.py serve --out OUTPUT --stdio`，通过 JSONL `ping` 核对 `ckb-stdio-retrieval` 协议；右键解释复用同一进程发送 `retrieve`，卸载时发送 `shutdown`。

## 确定性完成门

插件持有实际 stdio 请求 ID、Agent pack 路径和 OUTPUT 根。Agent 必须回传相同请求与 pack，并提供当日正式分析记录、`feedback-audit.json`、`agent-protocol-audit.json` 的绝对路径。插件重新打开这些文件，核对同一知识库边界、`passed` 状态以及覆盖当前请求的修改时间；凭据缺失或过期时，每日学习页保持原样。

## 本机生命周期验证

Obsidian 1.13.7 重启后只存在一个 `python.exe ... ckb.py serve --out E:\knowledge_builder\self-workspace\knowledge-base --stdio` 子进程。再次平滑关闭 Obsidian 后旧 stdio PID 已退出，重启后生成一个新的唯一 stdio PID，证明初始化与卸载清理均进入真实桌面生命周期。

## 验证结果

固定 Claudian 提交上的 typecheck、lint、七项聚焦测试、生产构建和干净重建通过；测试覆盖 Windows AGENTS 绑定解析、stdio 证据注入、真实 pack/记录/审计文件重开和缺失凭据门。CKB 二十四项核心回归通过，0.3.0 发布包与本机 vault 部署已更新。

## 后续补充

## 编辑与阅览模式统一入口

插件 0.4.0 的作者字段为 `DDDeath`。编辑模式继续通过 `editor-menu` 获取选中文本和精确行范围；阅览模式在 `.markdown-preview-view` 内读取用户实际选中的可见文本和当前页面，不再反推渲染文本对应的 Markdown 行号。阅览模式学习记录明确标注“阅览模式选中文本”。

## 快速检索与页面生成

两种模式最终都进入同一个 `SelectionLearningService`：先复用插件启动时建立的 CKB stdio 进程生成预算化 Agent pack，再由当前 Claudian provider 基于 pack 生成解释和当日唯一正式分析记录，最后执行反馈与 Agent Policy 审计。插件核对真实 stdio 请求、pack、记录和审计文件后才追加每日学习页。

## 验证结果

用户已在本机 Obsidian 现场看到右键菜单。固定 Claudian 提交上的 typecheck、lint、八项聚焦测试、生产构建和干净重建通过；测试新增阅览模式无虚构行号检查。CKB 二十四项核心回归通过，最终插件已部署并平滑重启，唯一 stdio 子进程重新建立。

## 后续补充

## 选区 Unicode 修复

插件 0.4.1 修复了剪贴板或 DOM 选区中孤立 UTF-16 surrogate 导致的 `utf-8 codec can't encode character`。`utf8SafeText` 保留合法 emoji 代理对，只把孤立高/低代理字符替换为 `�`；选中文本、问题和 stdio 查询都经过该门。

## stdio 传输加固

CKB `stdio_server` 在调用检索器前重复执行 surrogate 规范化，并把 JSONL 响应改为 ASCII 转义输出，避免 Windows GBK 控制台对 `�` 的二次编码错误。其他 Harness 直接调用 stdio 时也获得相同边界。

## 验证结果

九项插件聚焦测试通过，新增合法 emoji 保留与孤立 surrogate 替换测试；CKB stdio 协议测试和二十四项核心回归通过。真实 Windows stdio 探针发送 `截图异常\udca6文本` 后返回 `截图异常�文本`、生成 Agent pack 并以退出码零关闭。最终 0.4.1 已部署，作者保持 `DDDeath`，Obsidian 重启后唯一 stdio 子进程运行。
