# LLM Wiki 有界操作日志与研究缺口登记

标签：#类型/变更

本批次继续吸收 LLM Wiki 中不增加人类页面、可以由确定性脚本完成的知识维护能力。

有界机器操作日志现在只记录 compile、query、record、audit 和 maintenance 的固定机器字段、状态与 OUTPUT 内相对证据路径；日志按 UTC 日期分片，同日去重，限制单片记录数和字节数，并执行三十天保留。它不保存原始问题、对话、凭据、命令参数或完整输出，也不会创建每日人类页面。

研究缺口登记把证据不足、来源冲突和暂缓反馈保存为机器待验证记录。缺口进入 SQLite 全文检索时明确标记为“待验证研究缺口”，不进入固定源码事实；人类层只在 RECORDS 中保留一个汇总入口。关闭缺口必须提交中文结论和 OUTPUT 内现有证据。

功能矩阵中的默认路径候选已经全部吸收；向量检索、PDF/网页/OCR 和自动页面扩散仍保持 benchmark 状态，效果门通过前不进入默认路径。

## 相关知识页

- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]
- [[package_showcase 与 _parse_sample 的协作实现]]
- [[start_session 与 _session_directory 的协作实现]]
- [[ingest_event 与 default_registry_path 的协作实现]]
- [[audit_global 与 _replace_output_prefix 的协作实现]]
- [[audit_migration 与 _entity_key 的协作实现]]
- [[preflight 与 git 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
- [打开源码：scripts/ckb_core/showcase.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/showcase.py:1:1)  `scripts/ckb_core/showcase.py:1-173`
- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1632`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：scripts/ckb_core/gitrepo.py 第 230 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:230:1)  `scripts/ckb_core/gitrepo.py:230-257`
