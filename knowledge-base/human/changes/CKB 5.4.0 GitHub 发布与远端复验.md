# CKB 5.4.0 GitHub 发布与远端复验

标签：#类型/变更

GitHub 发布分支 `codex/release-5.4.0-stable-knowledge` 已创建并完成第一次远端发布。发布合并提交为 `bb33098`，第一父提交是远端 `main` 的 `917c790`，第二父历史是 integration 历史的 LFS 等价副本 `ca38aeb`；发布树中的 `source/` 仍逐文件等于原 integration 提交 `150a1ce`。

第一次推送尝试被 GitHub 拒绝，原因是原 integration 历史可达对象中包含未使用 LFS 的大体积 `assets/runtime/win-x64/payload.zip`。审计确认只有这一项超过远端普通 Git 限制。发布过程在隔离仓库中保留 77 个提交的顺序、作者、时间、标题和父节点数量，只把该文件替换为指向相同 SHA-256 与大小的 Git LFS 指针；原 integration branch 和提交均未改写。

修正后的非强制推送成功，远端 `main` 保持不变。随后从 GitHub 新克隆目标分支并展开 Git LFS 对象，逐文件核对 `source/` 与 `knowledge-base/`，双 SQLite、human/markdown 镜像、readability、51 条发布前工作记录、1 个 reference、3 个 research gap、两份学习笔记原始字节、无 SQLite WAL/SHM 与 LFS 对象均通过，共 12 个只读检查；`git lfs fsck` 也通过。

远端发布回滚使用目标分支中的 PowerShell 脚本创建新的 revert commit，不使用 force push。当前这条记录是发布完成后新增的第 52 条本地工作记录，下一次对同一发布分支的普通 fast-forward 提交会把它和更新后的索引一并纳入远端知识库。

## 相关知识页

- [[render_integration 与 _looks_windows 的协作实现]]
- [[preflight 与 git 的协作实现]]
- [[bind_conversation 与 default_management_registry_path 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[execute 等测试场景]]
- [[keyword_provider_config 与 parser 的协作实现]]
- [[ingest_event 与 default_registry_path 的协作实现]]
- [[main 相关实现]]

## 源码入口

- [打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-575`
- [打开源码：scripts/ckb_core/gitrepo.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:1:1)  `scripts/ckb_core/gitrepo.py:1-419`
- [打开源码：scripts/ckb_core/management_agent.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/management_agent.py:1:1)  `scripts/ckb_core/management_agent.py:1-1337`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1852`
- [打开源码：tests/provider_integration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/provider_integration.py:1:1)  `tests/provider_integration.py:1-325`
- [打开源码：scripts/ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:1:1)  `scripts/ckb.py:1-1405`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1744`
- [打开源码：scripts/make_source_patch.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/make_source_patch.py:1:1)  `scripts/make_source_patch.py:1-47`
