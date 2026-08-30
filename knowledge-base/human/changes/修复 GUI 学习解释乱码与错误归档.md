# 修复 GUI 学习解释乱码与错误归档

标签：#类型/变更

## 修改结果

Obsidian Companion 0.7.2 将 Node 启动的 Python 环境固定为 `PYTHONUTF8=1` 和 `PYTHONIOENCODING=utf-8`，CKB stdio 服务端同时把默认 stdin/stdout 重配为严格 UTF-8。这样 Windows 本地代码页不再把“学习解释”解码为错误字符序列。

`record-explanation` 不再调用 `record_note(kind=analysis)`。它只在 `workspace-meta/stdio/explanations/` 写入机器审计证据并执行反馈与 Agent-policy 审计；插件通过证据门后，唯一人类输出追加到 `学习笔记/YYYY-MM-DD.md`。因此以后不会再生成 `human/analysis/GUI 学习解释 *.md` 或兼容镜像。

## 现有数据修复

原有三份 GUI analysis 页面及其 metadata、索引项和临时请求正文已清理。2026-08-29 的解释已经存在于当日学习笔记，因此只去除重复 analysis 页面。2026-08-30 中仅存在于 analysis 的四条解释已迁移到 `human/学习笔记/2026-08-30.md`；其中两条代码页乱码根据可恢复文本和原始上下文重建为简体中文。修复后学习笔记没有 Unicode replacement character，`RECORDS.md` 也不再列出 GUI 学习解释分析项。

## 验证

真实 Windows stdio canary 在没有外部 UTF-8 环境注入的情况下完整传输中文问题、选中文本和解释，进程退出状态为 0、stderr 为空；机器证据保持正确中文，学习笔记和 analysis 集合在 server 审计阶段均未变化。插件聚焦测试覆盖机器证据路径、学习笔记唯一输出和 UTF-8 子进程环境。

## 相关知识页

- [[record_note]]
- [[sync_human_layer 与 _source_manifest 的协作实现]]
- [[start_session 与 _session_directory 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[audit_migration 与 _entity_key 的协作实现]]
- [[query_graph 与 _networkx_modules 的协作实现]]
- [[AutomationTest.event 等测试场景]]
- [[retrieve 与 _tokens 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/workspace_notes.py 第 106 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/workspace_notes.py:106:1)  `scripts/ckb_core/workspace_notes.py:106-183`
- [打开源码：scripts/ckb_core/knowledge_layers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:1:1)  `scripts/ckb_core/knowledge_layers.py:1-239`
- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：scripts/ckb_core/graphify_core.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/graphify_core.py:1:1)  `scripts/ckb_core/graphify_core.py:1-676`
- [打开源码：tests/test_automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:1:1)  `tests/test_automation.py:1-801`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
