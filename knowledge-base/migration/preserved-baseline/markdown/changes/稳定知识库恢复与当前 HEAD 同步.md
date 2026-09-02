# 稳定知识库恢复与当前 HEAD 同步

标签：#类型/变更

稳定知识库已经从固定源码基线迁移到 integration branch 的当前提交 `150a1ce`。迁移先在独立 staging 中重建源码事实、关系、中文页面、FTS5 索引和兼容 Agent 索引，再经过状态、检索、双 SQLite、镜像、人类可读性、研究缺口、Agent Policy 与 `maintain` 门后切换。

迁移保留了原有 50 条工作记录、1 个已审阅 reference、3 个开放 research gap，以及 `2026-08-29.md` 和 `2026-08-30.md` 两份学习笔记的原始字节。为满足双层镜像要求，两份学习笔记在 `human` 与 `markdown` 中使用相同内容；研究缺口引用的历史检索包也按原始字节保留。

审计发现三份故意不完整的 C++ 失败夹具以 `.cpp` 后缀进入了全量源码解析，导致固定图谱语法门失败。集成修正仅把这些失败夹具改为 `.cpp.txt`，测试仍通过显式 `language=cpp` 读取相同字节，因此负例行为保持不变，而知识库只解析语法有效的源码文件。

旧知识页在新导航计划中降为 appendix 时，迁移将两条历史 Wiki 链接重定向到新的所属页面。该修正同步更新 human、markdown 和工作记录元数据，并重新构建两个 SQLite 索引。

切换前已在隔离副本中执行真实目录切换与回滚探针，确认新 staging 能被提升，旧知识库能够按完整树清单恢复。正式切换仍保留原目录备份、额外完整基线副本、Agent Policy 文件备份和可直接运行的 PowerShell 回滚入口。

## 相关知识页

- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]]
- [[serve_stdio 与 _write_line 的协作实现]]
- [[start_session 与 _session_directory 的协作实现]]
- [[_Transport.close 与 _StartGate 的协作实现]]
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]
- [[parse_file 与 _language 的协作实现]]
- [[maintenance_check 与 capability_matrix 的协作实现]]
- [[audit_migration 与 _entity_key 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/knowledge_batch_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_batch_migration.py:1:1)  `scripts/ckb_core/knowledge_batch_migration.py:1-2076`
- [打开源码：scripts/ckb_core/stdio_server.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/stdio_server.py:1:1)  `scripts/ckb_core/stdio_server.py:1-392`
- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
- [打开源码：scripts/ckb_core/session_stdio.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/session_stdio.py:1:1)  `scripts/ckb_core/session_stdio.py:1-1459`
- [打开源码：scripts/ckb_core/keyword_fallback.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/keyword_fallback.py:1:1)  `scripts/ckb_core/keyword_fallback.py:1-633`
- [打开源码：scripts/ckb_core/parsers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/parsers.py:1:1)  `scripts/ckb_core/parsers.py:1-538`
- [打开源码：scripts/ckb_core/llm_wiki_capabilities.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/llm_wiki_capabilities.py:1:1)  `scripts/ckb_core/llm_wiki_capabilities.py:1-459`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-604`
