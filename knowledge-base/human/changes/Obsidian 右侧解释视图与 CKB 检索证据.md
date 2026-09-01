# Obsidian 右侧解释视图与 CKB 检索证据

标签：#类型/变更

## 修改内容

Obsidian 伴侣插件新增独立的右侧 `CKB 解释` ItemView。右键解释在问题弹窗出现前创建或复用该视图，随后持续显示等待提问、CKB stdio 检索、Provider 初始化、Agent 生成、凭据验证、学习笔记写入、完成、失败或取消状态。模型输出进入 `CKB_EXPLANATION` 区段后，侧栏渐进渲染解释正文；完成后保留完整解释以及“打开学习笔记”和“打开来源页面”按钮，过程和结果不写入 Claudian 聊天栏。

侧栏新增“知识库检索证据”，显示固定路径 `CKB stdio · retrieve --profile fast`、实际 request ID 和 Agent pack 路径。Agent 提示明确禁止把 grep、ripgrep 或全仓文本搜索作为首要检索入口；只有 Agent pack 返回 `needs-source-read` 时才允许对指定路径进行窄范围源码阅读。插件继续要求 Agent 回传同一 stdio request 与 pack，并在写入学习页前重新验证它们。

## 修改原因

原 0.5.1 只有短暂 Notice 和最终学习页，没有独立的持久过程视图。用户在右键提交后看不到请求是否进入检索、Provider 是否运行、审计是否执行，也无法直接确认 Agent 使用了 CKB 检索路径，因此容易被判断为“无反应、无更新”。

## 验证结果

固定 Claudian 提交上的干净构建通过 typecheck、lint、5 个测试套件、31 项测试和生产构建。真实 Obsidian 1.13.7 端到端请求 `obsidian-1788008712015-1` 创建了一个右侧 `ckb-selection-learning-view`，中间状态实际显示 `CKB stdio · retrieve --profile fast` 与 `E:\knowledge_builder\self-workspace\knowledge-base\machine\agent-packs\pack-20260829-130512-394410-01.md`，最终在 21:08:18 写入 `学习笔记/2026-08-29.md`。`feedback-audit.json` 与 `agent-protocol-audit.json` 均为 `passed` 且错误数为零，human/markdown 正式分析记录逐字节一致。0.6.0 ZIP 与构建 dist 逐字节一致，0.5.1 回滚脚本已在隔离目录执行并通过。

## 相关知识页

- [[audit_obsidian 与 prepare_vault 的协作实现]]
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]
- [[ingest_event 与 default_registry_path 的协作实现]]
- [[CkbError 与 DependencyError 的协作实现]]
- [[audit_migration 与 _entity_key 的协作实现]]
- [[initialize 与 _replace_output_prefix 的协作实现]]
- [[start_session 与 _session_directory 的协作实现]]
- [[module_name 与 estimated_tokens 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1632`
- [打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-158`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
- [打开源码：scripts/ckb_core/navigation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/navigation.py:1:1)  `scripts/ckb_core/navigation.py:1-456`
