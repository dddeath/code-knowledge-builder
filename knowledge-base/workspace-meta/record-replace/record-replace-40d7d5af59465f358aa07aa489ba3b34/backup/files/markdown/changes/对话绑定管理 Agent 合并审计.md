# 对话绑定管理 Agent 合并审计

标签：#类型/变更

## 合并结论

`codex/conversation-management-agent` 已通过管理 Agent 独立审计，并在 C++ parser/SCons 合并后的 integration HEAD 上以普通 merge 合入；五个开发提交全部保留。合并提交为 `190e4e4…`，稳定知识库固定源码图谱仍等待八项队列终态统一迁移。

## 已确认行为

- 以 Harness ID 与 opaque conversation ID 建立规范绑定，重复 bind 幂等，同一对话跨项目冲突失败，unbind 保留审计历史。
- status/context 每次重新检查 integration branch、HEAD、工作树、feedback、双 SQLite 和 maintain，不复用旧的 ready 结论。
- 管理注册表使用字段允许列表，Prompt、assistant 原文、secret、token 与 transcript path 不持久化；并发 bind/unbind 和审计事件保持单一规范对象。
- task-create 从绑定基线创建独立 branch/worktree 和哈希交接 Prompt；task-review 在最终 HEAD 执行字面测试，只有 verification、干净工作树和 integration 基线同时匹配才返回 merge-ready，接口本身不执行 merge。
- generic bundle提供管理绑定 Schema；各 Harness 分别声明 binding、prompt injection、event sync 和 task dispatch 能力。当前 prompt injection 明确为 false/manual-context，避免把 CLI context 描述成自动注入。

## 独立与合并后验证

合并前独立重跑 18 项管理测试、33 项核心、22 项自动化、3 项发行和 23 步 generic E2E，全部通过。合并后重跑 18 项管理测试、37 项核心、22 项自动化、3 项发行和 23 步 E2E，全部通过；E2E 覆盖 bind、context、status、task-create/review/status、unbind、audit、隐私扫描、注册表恢复和 branch/worktree 回滚，merge gate 为 ready 且 merge_performed=false。

## 回滚与边界

integration 回滚入口为撤销 merge commit `190e4e4…`；开发交付还包含逐 commit 回滚及注册表备份/恢复脚本。该功能提供 Harness-neutral 管理身份、上下文与派发准备；真实 Codex 新任务创建继续由 Codex App 的任务能力完成。完整证据位于 `E:\knowledge_builder\artifacts\verification\conversation-management-agent\management-audit.json`。

## 相关知识页

- [[ingest_event 与 default_registry_path 的协作实现]]
- [[audit_agent_protocol]]
- [[retrieve 与 _tokens 的协作实现]]
- [[finalize 与 _replace_output_prefix 的协作实现]]
- [[start_session 与 _session_directory 的协作实现]]
- [[render_integration 与 harness_retrieval_contract 的协作实现]]
- [[ingest_reference 与 _root 的协作实现]]
- [[sync_human_layer 与 _source_manifest 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1783`
- [打开源码：scripts/ckb_core/agent_protocol.py 第 420 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol.py:420:1)  `scripts/ckb_core/agent_protocol.py:420-496`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-555`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3605`
- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
- [打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-575`
- [打开源码：scripts/ckb_core/reference_documents.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_documents.py:1:1)  `scripts/ckb_core/reference_documents.py:1-903`
- [打开源码：scripts/ckb_core/knowledge_layers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:1:1)  `scripts/ckb_core/knowledge_layers.py:1-262`
