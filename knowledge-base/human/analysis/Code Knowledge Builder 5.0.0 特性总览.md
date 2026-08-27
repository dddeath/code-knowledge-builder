# Code Knowledge Builder 5.0.0 特性总览

标签：#类型/分析

## 项目定位

Code Knowledge Builder 5.0.0 把固定 Git 来源中的完整代码事实、Agent 检索数据和人类阅读页面分层管理。机器层追求完整、可查询和来源可复核；人类层追求简体中文、少页面和可直接定位修改入口。

## 当前特性

1. **多语言扫描**：覆盖 C、C++、C#、标准 JavaScript 和 Python；Tree-sitter 建立语法实体，Pyright、TypeScript Language Server、clangd 与 csharp-ls 提供语义证据。
2. **固定来源边界**：以干净 Git commit、blob 和精确源码范围作为事实边界；非 Git 目录只有在用户明确选择后才建立一次初始提交。
3. **全仓与局部范围**：支持重复路径、单文件、单目录、类或函数入口、callers/callees 深度扩展和一跳边界记录。
4. **可恢复分段构建**：解析批次与 Agent 审阅包独立；语法、语义、分类和投影可按失败阶段返工，已通过批次保持复用。
5. **确定性导航压缩**：脚本独占页面分类、归属、排序、配额、关系预算和上下文预算，隔绝 Agent 的重要性判断波动。
6. **保守人类页面**：普通文件默认最多一个关键实体页；核心入口与邻近实体使用受控配额；访问器、局部辅助函数、薄包装和简单判断只进入一句中文附录。
7. **逐实体中文审阅**：Agent 必须重新打开固定源码范围，为页面实体写中文含义、职责、修改时机和来源说明，为附属实体写一句中文作用。
8. **简体中文硬门**：页面、Wiki、关系说明、阅读包、分析、修改原因、踩坑、实验和会话都使用简体中文；英文只保留专有名词和源码标识符。
9. **事实层**：`facts` 保存可重建图、逐实体来源清单、审阅清单和计数契约。
10. **机器知识库**：`machine/knowledge.sqlite` 保存全部文件、实体、范围、关系、证据、提供器、诊断、审阅、职责群、边界、人类归属、固定源码和工作记录。
11. **纯确定性检索**：`fast` 使用精确锚点、分节 FTS5 和两跳图传播；`precise` 增加源码 FTS 与固定轮次加权 PageRank，不加载向量模型。
12. **窄查询接口**：提供 `coverage`、`entity`、`neighbors`、`source` 和 `changes`，避免 Agent 装入完整图或执行无范围 grep。
13. **中文人类知识库**：`human` 只展示类、函数及职责聚合，采用自然关系句、单一类型标签、折叠附录和可点击源码位置；`markdown` 保留兼容镜像。
14. **Obsidian 与 Logseq**：人类 Markdown 保留 Obsidian 核心导航与用户文件；Logseq 模式额外导入 EDN、验证并导出 SQLite，同时在导入根提供 `logseq/config.edn`。
15. **Graphify 关系层**：完整关系图派生确定性职责群、路径查询和中文关系报告，同时保留更严格的来源与审计门。
16. **构建期间持续修改**：语义提供器读取 detached 固定快照，活动工作树变化进入独立覆盖层，不污染基线完成记录。
17. **Agent 会话与过程知识**：初始化后即可启动会话；人类投影尚未生成时先排队，完成后自动落页。分析、修改、踩坑和实验主动回链代码页。
18. **三重完成状态**：只有所有分段、中文、来源、链接、事实、机器、人类、Graphify 和请求格式门同时通过，`finalize` 才写入总完成、机器完成和人类完成标记。

## 相关知识页

- [[sync_human_layer 与 _source_manifest 的协作实现]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[retrieve 与 _tokens 的协作实现]]
- [[start_session 与 _session_directory 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/knowledge_layers.py 第 1 行](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/knowledge_layers.py:1:1)  `scripts/ckb_core/knowledge_layers.py:1-239`
- [打开源码：tests/test_ckb.py 第 1 行](vscode://file/E:/knowledge_builder/code-knowledge-builder/tests/test_ckb.py:1:1)  `tests/test_ckb.py:1-1130`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
