# CKB 5.3.0 GitHub 发布边界

标签：#类型/变更

本次发布把 Code Knowledge Builder 5.3.0 源码、当前自身知识库和可验证交付放入同一个私有 GitHub 仓库，并以 `v5.3.0` Release 提供 lite/full 发行包。

源码目录对应 5.3.0 已提交功能分支，包含审阅式本地 Markdown/TXT 资料摄取、逐来源审阅、单来源单摘要页、SQLite FTS 检索、显式修订和可运行回滚。

自身知识库继续复用既有固定源码图，不重新消耗资源构建全图；当前发布保留该固定图的来源边界，同时包含迁移后的人类页面、机器 SQLite、工作记录、参考资料层、Agent 协议和 5.3.0 维护记录。发布说明不得把复用的固定图描述为针对 5.3.0 全量重扫。

GitHub 仓库继续使用 Git LFS 管理 ZIP 和 SQLite。发布前必须通过知识库维护、资料审计、SQLite 完整性、复制一致性、敏感凭据扫描、Git LFS 指针、单文件大小、补丁重放与隔离回滚探针；远程 main、标签和 Release 资产完成后还要从 GitHub API 独立复核。

## 相关知识页

- [[keyword_provider_config 与 parser 的协作实现]]
- [[preflight 与 git 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[finalize 与 _replace_output_prefix 的协作实现]]
- [[deployment_plan 与 skill_root 的协作实现]]
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]
- [[CkbError 与 DependencyError 的协作实现]]
- [[query_graph 与 _networkx_modules 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb.py 第 104 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:104:1)  `scripts/ckb.py:104-112`
- [打开源码：scripts/ckb_core/gitrepo.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:1:1)  `scripts/ckb_core/gitrepo.py:1-417`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：scripts/ckb_core/runtime.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/runtime.py:1:1)  `scripts/ckb_core/runtime.py:1-153`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
- [打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-158`
- [打开源码：scripts/ckb_core/graphify_core.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/graphify_core.py:1:1)  `scripts/ckb_core/graphify_core.py:1-676`

## 后续补充

当前 integration branch 和稳定知识库已经完成本地审计，但 GitHub 发布仍停在远端配置门。源码仓库没有 `remote` 与上游分支，工作区根目录也不是可直接承载全部内容的已提交发布仓库；本机同时缺少 `gh` 和 `git-lfs` 命令。

发布不得把工作区中的无关文件整体加入 Git。收到 GitHub 的 `OWNER/REPOSITORY` 与目标分支后，应在隔离目录中按允许清单组装源码和稳定知识库，重新核对文件集合、SQLite 完整性、学习笔记、reference、research gap、回滚入口与发布清单，再创建远端并推送。知识库 SQLite 与大体积归档仍按既定发布边界使用 Git LFS；缺少 LFS 时不把普通 Git 推送误报为完整发布。
