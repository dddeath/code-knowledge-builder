# 低版本 Agent Protocol 批量升级合并审计

标签：#类型/变更

## 合并结果

`codex/agent-protocol-batch-upgrade` 的 6 个独立提交已由管理任务以普通非 squash merge 合入 `codex/reference-ingest-v1`。新增 `agent-policy batch plan/apply/status/audit/rollback` 五命令；接口只升级 Agent Protocol、跨 Harness managed block、output contract 和机器状态，不重建固定源码图谱。

## 已确认行为

- 批次由显式 manifest 绑定 allowed roots、OUTPUT、workspace roots、源/目标协议版本、Harness、Python、CKB 和预期协议摘要；未知字段、重复或嵌套 OUTPUT、越界 workspace root、失效 runtime、未知版本和无升级路径均失败，不扫描未声明目录。
- 版本矩阵包含三个真实历史版本和当前版本。管理任务从对应 Git source commit 重新运行历史 `_protocol_text`，确认 1.0.0、1.3.0、1.4.0 的原始输出与本实现的历史重构逐字节一致，不是只比较自定义 fixture。
- `plan` 为确定性 dry-run 且零写入；`apply` 对每个 OUTPUT 建立独立备份、状态和锁。一个项目失败会恢复该项目基线，不覆盖其他已成功项目；中断后可续跑，成功项幂等跳过。
- managed block 只替换唯一 CKB 管理区，保留区外用户字节、BOM 和换行合同；重复或破损 marker、计划后漂移、部分失败、后续用户修改和子集回滚具有固定负例。
- 真实双库 E2E 覆盖部分失败、恢复、续跑、逐库 Agent Policy/output contract/maintain、单库与子集 rollback。`graph.json`、`facts/graph.json`、`machine/knowledge.sqlite` 和 `agent-index.sqlite` 的摘要在升级前后保持不变。

## 管理审计发现并关闭的问题

初版 OUTPUT 锁只根据 mtime 判断 stale。管理探针创建一个由当前存活 PID 持有、年龄 65 秒的锁，现实现会删除它并重新获取，实际结果为 `live-lock-was-stolen`；旧持有者 finally 还可能删除新持有者的锁。因此没有直接合并。

修复后，锁使用版本化有界 owner 记录、操作系统 descriptor lock、PID 启动标识、host 边界和 owner token。活 owner 不因超过 stale 阈值被删除；死亡 owner 只在确认后回收；无法确认时保持 busy；释放前重新核对 token，只删除自己的锁。管理原探针重新运行后返回 live lock preserved，专项还覆盖真实跨进程超时、死亡 owner、损坏记录、PID 复用/无法核验和释放期 token 漂移。

## 独立验证

最终开发 HEAD 和合并后 integration HEAD 均实际通过：Agent Protocol batch 专项 18 项、真实双库 E2E、核心 37 项、Harness 22 项、迁移 1 项和发行 3 项；合并后还重跑 scope extension 专项 5 项以验证两个新命令族共存。修改归档、完整 patch、验证记录和集成 rollback 均重新打开、重放或执行。完整命令、字面输出和退出状态位于 `E:\knowledge_builder\artifacts\verification\agent-protocol-batch-upgrade\management-audit.json`。

管理任务提供的集成回滚为 `E:\knowledge_builder\artifacts\verification\agent-protocol-batch-upgrade\rollback-integration-merge.sh`，已在隔离 clone 实际创建 merge revert，恢复树等于合并前集成树且工作树干净。

## 已测量边界

管理任务首次把 E2E 工作根放在较长 Windows 路径下时，备份 blob 创建触发路径长度相关 `FileNotFoundError`；批次把该项目标记失败并恢复基线。使用短绝对工作根重新运行后完整 E2E 通过。当前实现没有新增 Windows 长路径前缀或专用预检，部署 manifest 与 state/backup 根应避免接近传统 Windows 路径长度上限。

完整知识库跨版本批量迁移仍属于下一任务；本接口不会迁移固定图、源码索引、人类页面或可变知识层。

## 相关知识页

- [[audit_agent_protocol 与 _default_python 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]
- [[start_session 与 _session_directory 的协作实现]]
- [[sync_human_layer 与 _source_manifest 的协作实现]]
- [[audit_feedback 与 _contains_chinese 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[ingest_reference 与 _root 的协作实现]]
- [[finalize 与 _replace_output_prefix 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/agent_protocol.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol.py:1:1)  `scripts/ckb_core/agent_protocol.py:1-507`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
- [打开源码：scripts/ckb_core/knowledge_layers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:1:1)  `scripts/ckb_core/knowledge_layers.py:1-262`
- [打开源码：scripts/ckb_core/feedback.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/feedback.py:1:1)  `scripts/ckb_core/feedback.py:1-595`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1715`
- [打开源码：scripts/ckb_core/reference_documents.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_documents.py:1:1)  `scripts/ckb_core/reference_documents.py:1-604`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3482`
