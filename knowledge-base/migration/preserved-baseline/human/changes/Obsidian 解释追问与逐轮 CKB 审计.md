# Obsidian 解释追问与逐轮 CKB 审计

标签：#类型/变更

## 用户可见行为

Obsidian 解释侧栏在完成一次“解释选中内容”后，会在同一位置显示“继续追问”输入框。用户输入问题并点击“追问并记录”，或按 `Ctrl+Enter` / `Cmd+Enter`，即可围绕上一轮解释继续提问。每次成功追问后，侧栏显示最新回答，并继续保留下一轮追问入口。

## 知识库检索与写入约束

追问复用同一个 Provider 会话，以保留选中文本、首次问题和前序解释的上下文；但每一轮都重新调用 CKB 的确定性 SQLite 检索，生成新的 Agent pack，并把新 pack 注入 Provider。只有返回内容包含本轮检索请求和 pack 证据、机器证据写入成功且知识库审计通过时，回答才会进入学习笔记。

追问只追加到 `学习笔记/YYYY-MM-DD.md`。条目记录承接问题、当前追问、解释内容、Provider 和新的 CKB 检索证据，不重复抄写原始选中文本，也不生成 `analysis` 页面。一次失败不会留下半成品笔记；Provider 会话失效后，用户从新的选中文本解释重新开始。

## 部署兼容

插件版本为 0.8.0，Skill 版本为 5.2.8。插件包已注册并投影到当前自知识库和 sensory-memory-plugin 知识库。部署器补充了 Windows 打开 Obsidian 时的逐文件回退路径：优先原子替换插件目录，目录句柄阻止重命名时改为复制经过校验的声明文件，并在结果中记录 `install_mode`。

## 验证结果

- Claudian 固定上游提交上的 TypeScript 类型检查、ESLint、生产构建通过。
- 插件 5 个测试套件共 35 项通过，其中覆盖首次解释、同一 Provider 会话追问、每轮重新检索、紧凑学习笔记和失败不写入。
- CKB 核心 28 项、Hook 自动化 22 项、发行边界 3 项测试通过。
- 两个已安装插件的版本均为 0.8.0，输出契约审计均为 `passed`。

## 相关知识页

- [[audit_obsidian 与 prepare_vault 的协作实现]]
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]
- [[ingest_event 与 default_registry_path 的协作实现]]
- [[audit_migration 与 _entity_key 的协作实现]]
- [[finalize 与 _replace_output_prefix 的协作实现]]
- [[CkbError 与 DependencyError 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[module_name 与 estimated_tokens 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1632`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-158`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/navigation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/navigation.py:1:1)  `scripts/ckb_core/navigation.py:1-456`
