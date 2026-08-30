# 修复 Codex WSL Hook 事件路径与 Node 启动

标签：#类型/变更

## 修改内容

- 在自动化事件进入注册匹配前，将 WSL 的 `/mnt/<drive>/...` 与 `file:///mnt/<drive>/...` 路径转换为 Windows 运行时可识别的盘符路径。
- 同一转换也用于工具事件携带的修改路径，确保源码变更能够归属到已登记仓库。
- 将已有的 Windows Node.js 启动包装器放入当前 Codex WSL `app-server` 的首选命令目录，使第三方 Stop Ladder Hook 能在不依赖交互式 Shell 配置的情况下解析 `node`。

## 修改原因

Codex Desktop 的 `app-server` 当前运行于 WSL，而 CKB Hook 通过 WSL interop 启动 Windows Python。Hook 命令本身能够启动，但事件中的 `/mnt/e/...` 被 Windows `pathlib` 解释成 `E:\\mnt\\e\\...`，因此注册表匹配失败。与此同时，Stop Ladder Plugin 使用裸 `node`，而 `app-server` 的实际 `PATH` 不包含用户级 Node 包装器，命令在脚本启动前返回 127。

## 验证结果

- Windows 运行时的自动化测试共 21 项通过，覆盖 WSL 路径、文件 URI、Windows 原生路径、注册匹配、分段事件和并发入库。
- 使用与已安装 Plugin 相同的 CKB Hook 命令重放 `SessionStart`、`UserPromptSubmit`、`PostToolUse` 和 `Stop`，4 个事件均退出 0。
- 自动化数据库新增 1 个会话、1 个轮次、4 个事件和 1 条修改路径；待审阅记录准确指向 `scripts/ckb_core/automation.py`，spool 无待处理或失败项，SQLite 完整性为 `ok`。
- 使用 Codex `app-server` 的实际 `PATH` 执行 Stop Ladder 命令，退出状态由 127 变为 0。
- 当前 Codex 原始会话 JSONL 持续增长且末尾记录可逐行解析；本轮看到的历史缩短来自上下文压缩记录，不是磁盘会话文件被 Hook 删除。

## 相关知识页

- [[ingest_event 与 default_registry_path 的协作实现]]
- [[ingest_event]]

## 源码入口

- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1632`
- [打开源码：scripts/ckb_core/automation.py 第 1321 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1321:1)  `scripts/ckb_core/automation.py:1321-1392`
