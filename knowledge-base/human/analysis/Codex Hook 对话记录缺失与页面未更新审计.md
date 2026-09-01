# Codex Hook 对话记录缺失与页面未更新审计

标签：#类型/分析

## 结论

当前 Codex Hook 自动同步存在一个高严重度故障：Codex App 的 `app-server` 运行在 WSL，但已安装 Plugin 的 POSIX `command` 写入 Windows 盘符路径。每个生命周期 Hook 都在 CKB 进程启动前以退出码 127 结束，因此本次对话没有写入 `SessionStart`、`UserPromptSubmit`、工具结果或 `Stop`，也不会形成新的机器层待审阅记录。

## 已确认事实

- 当前 Codex `app-server` 的可执行文件位于 WSL，进程环境包含 `WSL_DISTRO_NAME=Ubuntu`，`CODEX_HOME` 指向挂载后的 Windows 用户目录。
- `code-knowledge-builder-sync@personal` 在 Plugin 清单中为 `installed, enabled`，Hook 信任状态已登记；项目注册表也正确把 `E:\knowledge_builder` 映射到源码仓库与知识库。
- 生产 `automation.sqlite` 完整性检查为 `ok`，无 pending spool 和 failed spool；但最后一批会话事件仍停留在 2026-08-27，本次 2026-08-29 会话只有显式激活记录，没有原生生命周期事件。
- 已安装 `UserPromptSubmit` 的 POSIX `command` 直接交给 `/bin/sh` 时返回 127，错误为 Windows 盘符形式的 Python 路径不存在。
- 把同一 Windows Python 解释器改成 WSL 可执行路径后，隔离注册表 canary 成功写入 2 个事件、1 个 turn，并由 `Stop` 生成 1 条 `pending-agent-review`；SQLite 完整性为 `ok`，失败队列为 0。这说明注册、核心归一化、SQLite、Stop 聚合和待审阅生成链路本身正常。

## 根因定位

`scripts/ckb_core/automation_integrations.py` 的 `_commands` 同时从同一组 `Path` 原样生成 POSIX `command` 和 Windows `commandWindows`。`render_integration` 在生成 Codex Plugin 时没有接收或推导实际 Hook 执行宿主，也没有验证两种命令能否分别启动。使用 Windows Python 运行 render 时，POSIX `command` 仍保留 `C:\...`，在 WSL Codex 中必然失效。

当前 `1.2.0` 生成器仍包含同一逻辑，所以只把已安装 Plugin 从 `1.0.0` 更新到当前版本不会消除该故障。版本漂移是部署风险，但不是本次事件缺失的直接根因。

## 页面没有更新的含义

人类知识页不在 `Stop` 时直接更新，这是当前审阅契约的预期行为。正常链路应先在机器层生成 `pending-agent-review`，再由 Agent 核对中文正文、源码与验证证据，执行 `automation review` 后投影到 `human` 和 `markdown`。本次连机器层待审阅记录都没有生成，原因是 Hook 命令未能启动；修复启动路径后，仍需完成审阅步骤，人类页面才会变化。

## 测试缺口

现有 `test_render_all_harness_integrations` 只验证生成文件、事件名和元数据字段，不执行生成后的 handler，也没有覆盖“Windows 解释器路径生成 Plugin、WSL Codex 执行 POSIX command”的混合宿主场景。因此该测试当前通过，但无法发现真实运行失败。

## 最小修复边界

1. Codex render 必须显式区分 POSIX Hook 宿主与 Windows Hook 宿主；POSIX `command` 使用宿主可启动的路径，`commandWindows` 保持 Windows 命令。
2. 新增确定性测试：分别在目标 shell 中执行每个生成 handler 的空载或隔离事件 canary，并断言进程启动成功、事件计数增长、`Stop` 生成恰好一条待审阅记录、队列无失败。
3. 重新生成并安装 Plugin 后，在新的 Codex 任务中使用显式 Skill、一次真实小修改和正常任务结束做原生验收；验收必须观察事件、turn、待审阅记录及审阅后的人类投影同时增长。

## 验证证据

隔离验证记录、失败命令、SQLite 与输入事件保存在 `E:\knowledge_builder\artifacts\codex-hook-wsl-path-audit-20260829-01`。本次检阅没有修改源码实现。

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
