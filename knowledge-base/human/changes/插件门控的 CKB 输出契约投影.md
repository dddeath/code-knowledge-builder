# 插件门控的 CKB 输出契约投影

标签：#类型/变更

## 修改结果

CKB 新增插件专用的机器可读输出契约 `.ckb/output-contract.json`。契约只投影到实际安装 `Code Knowledge Builder Companion` 的 vault，记录该 vault 对应的 OUTPUT、Python、`ckb.py`、stdio protocol v2、允许方法和中文输出语言；不写入 Git commit、哈希或页面属性。

Obsidian 插件启动时优先读取并校验该契约，不再把解析 `AGENTS.md` 说明文字作为首选路径。旧知识库没有契约时仍保留 `AGENTS.md`、`CKB_OUTPUT`、`CKB_PYTHON` 和 `CKB_SCRIPT` 兼容路径。契约中的 vault 必须与当前打开目录一致，OUTPUT 必须存在 `machine/knowledge.sqlite`，Python 与 `ckb.py` 必须可执行，stdio 方法必须包含 `ping`、`retrieve`、`record-explanation` 和 `shutdown`。

## 投影边界

`obsidian-plugin deploy --out OUTPUT`、登记插件后的自动 vault 投影以及 ZIP 内独立 `deploy.py` 都会在部署插件时同步生成输出契约。状态命令独立审计插件文件、启用项和契约内容。

用户级插件包登记本身不代表某个 vault 已安装插件。没有插件目录的知识库固定返回 `status: not-required`、`required: false`，不会生成契约，也不会因为全局登记存在而审计失败。移除插件时同时移除对应契约。

## 当前落地

当前自知识库与 `sensory-memory-plugin` 的人类 vault 都已升级到插件 0.7.1，并写入通过审计的输出契约。核心 Skill 升级到 5.2.6。插件仍由 DDDeath 发布，输出契约不进入普通知识页面或导航。

## 验证

Claudian 固定源码通过 typecheck、lint、5 个测试套件共 33 项测试和生产构建；CKB 核心 26 项、自动化 22 项、发行 3 项测试通过。独立插件包完成带显式 OUTPUT/runtime 参数的部署和状态探针。额外 plugin-free 实例在用户级 0.7.1 已登记的条件下仍返回 `not-required`，证明审计依据 vault 实际安装状态而不是全局登记状态。

## 相关知识页

- [[prepare_vault 与 install_obsidian 的协作实现]]
- [[status 与 _replace_output_prefix 的协作实现]]
- [[create_source_snapshot 与 git 的协作实现]]
- [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]]
- [[__init__ 实现概览]]
- [[run 与 CkbError 的协作实现]]
- [[render_integration 与 _looks_windows 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：scripts/ckb_core/gitrepo.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:1:1)  `scripts/ckb_core/gitrepo.py:1-417`
- [打开源码：scripts/ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:1:1)  `scripts/ckb.py:1-495`
- [打开源码：scripts/ckb_core/__init__.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/__init__.py:1:1)  `scripts/ckb_core/__init__.py:1-5`
- [打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-158`
- [打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-502`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
