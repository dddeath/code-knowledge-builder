# CKB 5.3.0 审阅文本资料吸收

标签：#类型/变更

## 修改结果

CKB 5.3.0 新增经过 Agent 逐项审阅的本地文本参考资料层。用户提供的 UTF-8 Markdown/TXT 先归档到独立 references 层，必须填写标题、来源和明确许可证；导入后停在待审阅状态，不生成摘要页。Agent 重新打开归档原文，提交简体中文摘要以及逐项主张、精确行范围、精确原文和中文来源核对，全部通过后才进入人类页面与机器检索。

每个活动来源最多生成一个 带资料类型标签的摘要页，并共享一个 `REFERENCES.md` 导览。摘要页只展示中文摘要、关键结论、来源、许可证和可点击原文行范围，不显示机器 ID、内容摘要值或内部审阅状态。参考资料与代码事实保持不同类型，不写入代码 files、entities 或 source_ranges，也不自动扩散概念页。

## 查询与维护

机器知识库 Schema 增加 reference_sources，并把活动资料写入 documents、sections 和 section_fts。`brief` 与完整 `retrieve` 在没有代码实体命中时也可以直接返回“已审阅参考资料”，Agent pack 同时给出摘要页和归档原文范围。聚合 `maintain` 新增参考资料门，检查原文、许可证、逐项引用、中文、单来源页面配额、human/markdown 镜像和 SQLite 计数。

相同标题、来源、许可证和原文字节重复导入保持幂等。内容变化要求显式指定上一修订；新修订审阅通过前保留旧摘要，通过后旧记录进入 superseded。回滚新修订会恢复上一版，回滚首版会移除原文副本、审阅、摘要页、导览入口和 SQLite 记录，同时保留代码知识、正式笔记与 Obsidian 配置。

## Git 版本管理

源码在 `codex/reference-ingest-v1` 分支上维护，先提交 5.2.9 可验证基线，再提交参考资料功能，最后单独提交 reference-aware Agent 协议版本。当前工作树保持干净，使代码回退、功能比较和发行包来源都对应明确 Git 节点。

## 验证

端到端测试覆盖待审阅门、无许可和错误文件类型、错误行引用、正确审阅、单摘要页、SQLite FTS、brief 检索、重复导入、显式修订、旧版恢复和完全回滚。真实自身知识库已导入一份 CC0 中文演示资料，生成一页摘要和四个原文入口；机器库中存在一个来源、一个参考文档和四个原文章节，SQLite 完整性检查为 ok，参考资料审计和聚合维护门均通过。

## 相关知识页

- [[retrieve 与 _tokens 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[ingest_event 与 default_registry_path 的协作实现]]
- [[audit_migration]]
- [[finalize 与 _replace_output_prefix 的协作实现]]
- [[AutomationTest.register 等测试场景]]
- [[MigrationTest 等测试场景]]

## 源码入口

- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1632`
- [打开源码：scripts/ckb_core/migration.py 第 353 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:353:1)  `scripts/ckb_core/migration.py:353-460`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：tests/test_automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:1:1)  `tests/test_automation.py:1-801`
- [打开源码：tests/test_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:1:1)  `tests/test_migration.py:1-194`
