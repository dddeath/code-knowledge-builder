# Agent 会话级 stdio 生命周期合并审计

标签：#类型/变更

## 修改内容

integration branch 已普通合并 Agent 会话级 CKB stdio 生命周期，保留七个独立开发 commit。第一次精确 `skill.applied`、`automation activate` 或等价原生 Skill 调用会立即创建并握手会话监督器与 `serve --stdio`；同一会话和 OUTPUT 的普通 `brief`、`retrieve`、`entity`、`neighbors`、`source`、`changes` 复用同一健康 PID。

`turn.stop` 保留生命周期；`session.end`、terminate、cancel、management unbind、Harness unload 和可靠父 PID 死亡执行有界 `shutdown -> terminate -> kill -> wait/reap`。关闭后 lease、进程、pending、reader、timer、listener、pipe、session mapping 和 cache reference 计数归零。启动或传输失败明确标为 `resident=false` 并回退逐命令 CLI。

## 修改原因

原 `serve --stdio` 只有服务端循环，没有 Agent/Harness 会话所有者；每次 Agent 检索仍可能重复启动 Python 与 SQLite 初始化。首轮管理审计发现相同外部会话标识立即重建会误读上一代 lease、长 Windows root 的临时文件名放大路径，以及旧 E2E 把失败 brief 计入通过证据。修复引入逐启动 generation、紧凑原子临时名和固定路径预算，并以实际业务状态替换仅 PID 证据。

## 验证结果

管理任务在锁定 Windows runtime 下独立执行同一外部会话十轮 `activate -> 真实 brief -> close -> 立即 activate`，十轮均常驻通过、PID 与 generation 每轮唯一、无 fallback，较长项目路径同样通过。当前 Codex 会话普通 CLI canary 验证 `brief -> entity -> turn.stop -> brief -> session.end` 全部 exit 0 且复用同一 server PID，结束后活动进程和对象计数为零。

合并后从真实 integration HEAD运行 stdio 生命周期 12 项、CKB core 37 项、automation 22 项、management Agent 18 项、package release 3 项和完整知识库批量迁移 14 项，全部通过。50 次压力结果为 RSS 不增长、handle 增量为零；父死亡、lite 包和隔离回滚证据通过。完整 post-merge 记录位于 `E:\knowledge_builder\artifacts\verification\agent-session-stdio-lifecycle\post-merge-verification.json`。源码合并已完成，稳定知识库尚待最终隔离同步与切换。

## 相关知识页

- [[start_session 与 _session_directory 的协作实现]]
- [[audit_agent_protocol 与 _default_python 的协作实现]]
- [[serve_stdio 与 _write_line 的协作实现]]
- [[ingest_event 与 default_registry_path 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]
- [[render_integration]]
- [[doctor_report 与 _version_matches 的协作实现]]
- [[record_note 与 page_tag 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
- [打开源码：scripts/ckb_core/agent_protocol.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol.py:1:1)  `scripts/ckb_core/agent_protocol.py:1-507`
- [打开源码：scripts/ckb_core/stdio_server.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/stdio_server.py:1:1)  `scripts/ckb_core/stdio_server.py:1-283`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1665`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
- [打开源码：scripts/ckb_core/automation_integrations.py 第 422 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:422:1)  `scripts/ckb_core/automation_integrations.py:422-535`
- [打开源码：scripts/ckb_core/providers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/providers.py:1:1)  `scripts/ckb_core/providers.py:1-611`
- [打开源码：scripts/ckb_core/workspace_notes.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/workspace_notes.py:1:1)  `scripts/ckb_core/workspace_notes.py:1-376`
