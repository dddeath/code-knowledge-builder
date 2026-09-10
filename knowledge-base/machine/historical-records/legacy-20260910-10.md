# Obsidian 解释快速路径与跨知识库部署

标签：#类型/变更

## 修改结果

Obsidian Companion 升级到 0.7.0。右键解释仍跟随用户选择的 Provider 和模型，但不再让 Codex、Claude Code 等 Provider 自行打开 Agent pack、调用命令并执行多轮审计。插件先通过常驻 CKB stdio 完成确定性检索，把预算化 Agent pack 正文直接放入提示词；Provider 以无工具模式只生成中文解释。解释返回后，同一 stdio 进程通过 `record-explanation` 一次完成检索证据绑定、幂等记录、索引刷新、反馈审计和 Agent-policy 审计。

这项修改把可控的本地阶段压缩为一次检索和一次记录调用。实测常驻检索约 10 毫秒；独立冷进程中的真实检索约 35 毫秒；首次确定性记录、重建索引和两项审计约 1.84 秒，幂等重试约 7 毫秒。剩余主要等待时间来自用户所选 Provider 的模型初始化、推理与网络；因此如果 Codex 仍明显慢，可在插件设置中切换较快模型，而不会绕过知识库检索与审计。

## 部署能力

插件 ZIP 新增独立 `deploy.py`，Agent 可直接对任意 vault 执行部署、状态检查和移除。核心 Skill 升级到 5.2.5，新增 `obsidian-plugin register|deploy|status|remove`。登记插件包后，后续初始化或重新投影的人类知识库会自动部署登记版本；已有知识库需要按自动化注册表逐个补部署一次。

本次已把 0.7.0 部署到当前自知识库和 `sensory-memory-plugin` 知识库，两处都已写入插件启用项与部署记录。Obsidian 当前正在运行，磁盘部署已经生效；应用重新加载或重启后载入新的 `main.js`。

## 验证边界

固定 Claudian 源码补丁通过 typecheck、lint、5 个测试套件共 31 项测试和生产构建。CKB 核心主测试 25 项、自动化测试 22 项、发行测试 3 项全部通过。独立部署器完成部署、状态、移除和再次部署探针；两个已登记知识库的插件状态均为 `deployed`、版本均为 0.7.0。未把模型端到端响应时间包装成固定收益，因为该时延会随 Provider、模型、认证状态和网络变化。

## 相关知识页

- [[audit_migration 与 _entity_key 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[deployment_plan 与 skill_root 的协作实现]]
- [[CkbError 与 DependencyError 的协作实现]]
- [[finalize 与 _replace_output_prefix 的协作实现]]
- [[preflight 与 git 的协作实现]]
- [[keyword_provider_config 与 parser 的协作实现]]
- [[query_graph 与 _networkx_modules 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/runtime.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/runtime.py:1:1)  `scripts/ckb_core/runtime.py:1-153`
- [打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-158`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：scripts/ckb_core/gitrepo.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:1:1)  `scripts/ckb_core/gitrepo.py:1-417`
- [打开源码：scripts/ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:1:1)  `scripts/ckb.py:1-495`
- [打开源码：scripts/ckb_core/graphify_core.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/graphify_core.py:1:1)  `scripts/ckb_core/graphify_core.py:1-676`

## 后续补充

## 实现入口补充

本次快速路径以常驻 `serve --stdio` 为运行入口，核心部署由 Obsidian vault 投影和独立插件登记器共同完成；正式记录继续通过统一的 `record_note` 入口写入并重建机器索引。
