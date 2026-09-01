# LLM Wiki 定位式反馈闭环

标签：#类型/变更

## 当前能力

知识库现在具备定位式人工反馈闭环：人类可以针对具体知识页的行范围提交中文反馈，脚本自动保存原文与前后文本窗口；后续 Agent 按原行范围、全文唯一原文、文本窗口消歧的固定顺序重新定位，并把处理结果归入开放或已归档状态。

## 使用方式

`feedback create` 创建反馈，`feedback list` 按严重程度列出待办，`feedback locate` 检查锚点，`feedback resolve` 记录采纳、部分采纳、不采纳或暂缓决议，`feedback audit` 验证目标、锚点、中文内容、镜像和落实记录。采纳或部分采纳必须链接知识输出内已存在的修改或分析记录；已处理反馈只归档，不删除。

## 检索与 Agent 约束

确定性检索能够直接返回开放或已解决反馈；项目级 Agent 协议要求进入知识库时先检查开放反馈，涉及目标页时优先处理错误和警告，再执行 SQLite 检索。反馈可见页在 `human` 与 `markdown` 中逐字一致，并保持无 frontmatter、单一反馈标签和中文叙述。

## 验证结果

核心、自动化与迁移共四十一项回归测试全部通过。已安装 Skill 的独立 canary 完成创建、列出、定位、归档和反馈审计，锚点定位、状态迁移与双镜像一致性均通过。

## 保留边界

任意网页、PDF 和文章不会进入固定 Git 源码事实层；本地 Web 查看器与 Obsidian 插件只复用统一反馈命令和字段契约，本版不复制独立渲染器或第二套锚点算法。

## 相关知识页

- [[audit_obsidian 与 prepare_vault 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]
- [[query_graph 与 _networkx_modules 的协作实现]]
- [[audit_migration]]
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]
- [[CkbError 与 DependencyError 的协作实现]]
- [[package_showcase 与 _parse_sample 的协作实现]]
- [[record_note 与 page_tag 的协作实现]]
- [[sync_human_layer 与 _source_manifest 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
- [打开源码：scripts/ckb_core/graphify_core.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/graphify_core.py:1:1)  `scripts/ckb_core/graphify_core.py:1-676`
- [打开源码：scripts/ckb_core/migration.py 第 353 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:353:1)  `scripts/ckb_core/migration.py:353-460`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
- [打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-158`
- [打开源码：scripts/ckb_core/showcase.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/showcase.py:1:1)  `scripts/ckb_core/showcase.py:1-173`
- [打开源码：scripts/ckb_core/workspace_notes.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/workspace_notes.py:1:1)  `scripts/ckb_core/workspace_notes.py:1-374`
- [打开源码：scripts/ckb_core/knowledge_layers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:1:1)  `scripts/ckb_core/knowledge_layers.py:1-239`
