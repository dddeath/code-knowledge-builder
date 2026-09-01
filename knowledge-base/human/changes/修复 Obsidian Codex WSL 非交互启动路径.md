# 修复 Obsidian Codex WSL 非交互启动路径

标签：#类型/变更

## 修改结果

Obsidian Companion 的 Codex Provider 继续使用默认 WSL 发行版 Ubuntu。模型发现失败的直接原因不是 Codex 缺失，而是 Codex Desktop 只把 WSL 启动器目录临时注入当前任务的 PATH；Obsidian 启动的独立 `bash -lc` 没有这段临时路径，所以返回 `codex: command not found`。

在 Ubuntu 用户目录安装了稳定入口 `/home/radar/.local/bin/codex`。该目录已经由登录 Shell 放在 PATH 首位。入口不会复制或重新安装 Codex，而是从当前用户受控的 `/mnt/c/Users/19739/.codex/bin/wsl/*/codex` 中选择修改时间最新的可执行 WSL launcher，并原样转发全部参数。Codex Desktop 更新 launcher 哈希目录后，入口仍能自动选择新版本。

## 验证

默认 Ubuntu 非交互登录 Shell 现在把 `codex` 解析为 `/home/radar/.local/bin/codex`，`codex --version` 返回 `codex-cli 0.150.0-alpha.12.2`，`codex app-server --help` 返回 app-server 帮助。额外在清空继承环境、只保留系统 PATH 的条件下重新执行 `bash -lc`，登录配置仍自动加入 `~/.local/bin`，同样完成命令解析和版本输出。

截图中的 WSL localhost/NAT 诊断仍可能以乱码形式出现在 stderr，但它与命令发现无关；决定性的 `codex: command not found` 已消失。Obsidian 重新加载插件后会使用这个稳定入口重新进行模型发现。

## 相关知识页

- [[doctor_report 与 _version_matches 的协作实现]]
- [[audit_obsidian 与 prepare_vault 的协作实现]]
- [[render_integration 与 _looks_windows 的协作实现]]
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/providers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/providers.py:1:1)  `scripts/ckb_core/providers.py:1-596`
- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`
- [打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-502`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
