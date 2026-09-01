# Lite、Full 与 Obsidian 插件发行边界

标签：#类型/变更

## 修改内容

发行体系固定为三个独立类别。`lite` 保留完整核心功能，包括源码扫描、分段恢复、局部范围、机器 SQLite、人类 Markdown/Obsidian vault、Logseq 投影、确定性检索、Agent 审阅、审计、迁移和自动化适配，但不携带离线运行时和 `plugins/`。`full-win-x64` 与 lite 使用相同的核心版本，并且文件集合严格等于 lite 加 `assets/runtime/win-x64/`；任何其他增量或 `plugins/` 成员都会使打包失败。`obsidian-plugin` 使用插件 `manifest.json` 中的独立版本，只包含六个 Obsidian 安装文件，不包含核心 Skill 或离线运行时。

`scripts/package_release.py` 新增 `obsidian-plugin` 和 `all` 类型；`both` 仍只生成 lite 与 full。核心 manifest 写入功能矩阵、禁止前缀和 full 的唯一增量前缀，插件 manifest 写入独立版本、核心知识库依赖和固定 Claudian 上游提交。`references/distributions.md` 记录发行矩阵、版本关系、安装位置和命令。

## 修改原因

原打包器遍历源码根目录时会把 `plugins/` 同时纳入 lite 和 full，导致核心 Skill、离线运行时和 Obsidian GUI 插件的版本及安装边界混在一起。Lite 也缺少可机检的能力声明，无法明确表达“功能完整但不捆绑运行时”。

## 验证结果

新增三项发行边界单元测试全部通过。实际生成 `code-knowledge-builder-lite-5.2.4.zip`、`code-knowledge-builder-full-win-x64-5.2.4.zip` 和 `code-knowledge-builder-obsidian-0.6.0.zip`。ZIP CRC 全部通过；lite 和 full 都没有 `plugins/`；lite 没有 runtime；full 严格包含 lite，唯一差集为 `code-knowledge-builder/assets/runtime/win-x64/payload.zip`；插件 ZIP 精确包含 `main.js`、`manifest.json`、`styles.css`、`LICENSE`、`NOTICE.md` 和 `build-record.json`，没有 `SKILL.md`、`scripts/ckb.py` 或 `toolchain.lock.json`。源码与已安装 Skill 的结构校验通过，安装版 lite canary 也确认不含插件和 runtime。任务 patch 的正向与反向重放、隔离回滚探针均通过。

## 相关知识页

- [[source_files 与 sha256 的协作实现]]
- [[audit_obsidian 与 prepare_vault 的协作实现]]
- [[deployment_plan 与 skill_root 的协作实现]]
- [[package_showcase]]
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[main 与 sha256 的协作实现]]
- [[ingest_event 与 default_registry_path 的协作实现]]

## 源码入口

- [打开源码：scripts/package_release.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/package_release.py:1:1)  `scripts/package_release.py:1-142`
- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`
- [打开源码：scripts/ckb_core/runtime.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/runtime.py:1:1)  `scripts/ckb_core/runtime.py:1-153`
- [打开源码：scripts/ckb_core/showcase.py 第 66 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/showcase.py:66:1)  `scripts/ckb_core/showcase.py:66-172`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/build_runtime_payload.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/build_runtime_payload.py:1:1)  `scripts/build_runtime_payload.py:1-117`
- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1632`
