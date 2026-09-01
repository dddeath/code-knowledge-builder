# 修复 Codex commandWindows 在 WSL 中二次启动失败

标签：#类型/变更

## 修改内容

- 为当前已信任的 `code-knowledge-builder-sync` Plugin 增加 WSL 命令兼容入口，使 Codex 把 Windows `commandWindows` 交给 `/bin/sh` 时仍能启动既定的 Windows Python Hook；没有修改当前 Hook 定义，因此不会触发新的信任确认。
- 将自动化集成版本提升为 `1.2.2`。新生成的 Codex Plugin 不再把裸盘符命令直接放入 `commandWindows`，而是生成 `hooks/ckb-hook.cmd`，并通过跨 Windows/WSL 均可解析的 `cmd.exe` 调用。
- 把本轮在修复前漏掉的 `UserPromptSubmit` 按原 session、turn 与 workspace 补入机器自动化数据库。

## 修改原因

上一轮只修复了 POSIX `command` 的 Python 启动路径和 Hook 事件中的 WSL `cwd`。进一步的原样复现确认：Codex Desktop 仍可能按 Windows 桌面宿主选择 `commandWindows`，再由 WSL `/bin/sh` 执行。盘符路径中的反斜杠被 Shell 当作转义符删除，实际命令名变成 `C:Users19739...pythonpython.exe`，因此仍返回 127。Stop Ladder 的 Node 启动在上一轮已经恢复；界面保留的两个 `PreToolUse` 失败卡片是长任务中修复前失败的累计结果。

## 验证结果

- 旧 `commandWindows` 经 `/bin/sh` 原样执行返回 127，错误命令与界面一致。
- 当前兼容入口下执行同一未改动 Hook 定义退出 0；补录当前 `UserPromptSubmit` 后，事件数从 15 增至 16、轮次数从 3 增至 4，workspace 归一化为 `E:\knowledge_builder`，spool 无待处理或失败项。
- `1.2.2` 渲染出的 `commandWindows` 为 `cmd.exe /d /s /c .../hooks/ckb-hook.cmd`，在 WSL `/bin/sh` 中实际启动退出 0。
- Windows 运行时自动化测试共 22 项通过，包括 commandWindows bridge、WSL 路径、显式 Skill 门、并发、幂等和审阅投影。
- Stop Ladder 的当前原生 `PreToolUse` 日志持续写入 `allow` 决策，使用 Codex `app-server` 实际 PATH 执行退出 0；旧失败卡片不会在同一长任务中改写为成功。

## 相关知识页

- [[render_integration 与 _looks_windows 的协作实现]]
- [[keyword_provider_config 与 parser 的协作实现]]
- [[ingest_event 与 default_registry_path 的协作实现]]
- [[audit_migration 与 _entity_key 的协作实现]]
- [[CkbError 与 DependencyError 的协作实现]]
- [[source_files]]
- [[AutomationTest.register 等测试场景]]
- [[MigrationTest 等测试场景]]

## 源码入口

- [打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-502`
- [打开源码：scripts/ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:1:1)  `scripts/ckb.py:1-495`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1632`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-158`
- [打开源码：scripts/package_release.py 第 27 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/package_release.py:27:1)  `scripts/package_release.py:27-38`
- [打开源码：tests/test_automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:1:1)  `tests/test_automation.py:1-801`
- [打开源码：tests/test_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:1:1)  `tests/test_migration.py:1-194`
