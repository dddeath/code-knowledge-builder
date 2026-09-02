# 修复 Codex WSL Hook 启动路径并重新安装 Plugin

标签：#类型/变更

## 修改内容

- 将 Codex 自动化集成版本从 `1.2.0` 提升到 `1.2.1`。
- 在 `automation_integrations.py` 增加 `_wsl_launch_path`：当 Python 是 Windows 盘符路径时，POSIX Hook 的可执行文件转换为 WSL `/mnt/<drive>/...` 路径；传给 Windows Python 的 `ckb.py` 与注册表参数继续保留 Windows 路径。
- 在 `test_automation.py` 增加混合宿主路径断言，并让 render 回归真实启动生成的 POSIX handler。
- 同步更新已安装的 `code-knowledge-builder` Skill 生成器，重新生成、校验并通过个人 marketplace 重装 `code-knowledge-builder-sync` Plugin。安装版本为 `1.2.1+codex.20260829092900`。

## 修改原因

Codex App 当前把 `app-server` 运行在 WSL，而旧 Plugin 的 POSIX `command` 直接使用 `C:\...\python.exe`。该命令在 CKB 进程启动前以退出码 127 结束，导致原生会话事件、Stop 待审阅记录与后续知识页投影全部缺失。

## 验证结果

- 语法检查通过。
- 新增的 2 项混合宿主测试通过。
- `tests.test_automation` 共 19 项全部通过。
- 修复后生成的 production 与 canary Plugin 均为 `1.2.1`，Plugin 校验通过。
- 生成的 POSIX handler 可执行文件为 `/mnt/c/.../python.exe`，空事件启动退出状态为 0。
- 隔离事件链实际写入 2 个事件、1 个 turn，`Stop` 生成 1 条 `pending-agent-review`；pending spool 与 failed spool 均为 0，SQLite 完整性为 `ok`。
- cachebuster、Plugin 源校验和 CLI 重装均返回 0；Plugin 清单显示 `installed, enabled`，版本为 `1.2.1+codex.20260829092900`。
- Plugin 源与安装缓存的 manifest、Hook 和 integration 文件逐字节一致；缓存中的生成 handler 在 WSL 启动退出状态为 0。

## 相关知识页

- [[audit_migration 与 _entity_key 的协作实现]]
- [[ingest_event 与 default_registry_path 的协作实现]]
- [[keyword_provider_config 与 parser 的协作实现]]
- [[render_integration 与 _looks_windows 的协作实现]]
- [[record_note 与 page_tag 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]
- [[start_session 与 _session_directory 的协作实现]]
- [[CkbError 与 DependencyError 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1632`
- [打开源码：scripts/ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:1:1)  `scripts/ckb.py:1-495`
- [打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-502`
- [打开源码：scripts/ckb_core/workspace_notes.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/workspace_notes.py:1:1)  `scripts/ckb_core/workspace_notes.py:1-374`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
- [打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-158`
