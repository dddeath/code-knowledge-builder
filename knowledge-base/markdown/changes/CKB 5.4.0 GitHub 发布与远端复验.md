# CKB 5.4.0 GitHub 发布与远端复验

标签：#类型/变更

CKB 5.4.0 的可验证交付已发布到 GitHub 分支 [`codex/release-5.4.0-stable-knowledge`](https://github.com/dddeath/code-knowledge-builder/tree/codex/release-5.4.0-stable-knowledge)。该分支同时提供源码、稳定知识库和发布校验工具；远端 `main` 未被本次发布改动。

## 发布内容

- `source/`：与本次 integration 基线逐文件一致的 CKB 5.4.0 源码。
- `knowledge-base/`：绑定同一源码基线的事实层、双 SQLite、人类与 Markdown 镜像、工作记录、reference、research gap、操作日志和两份学习笔记。
- `delivery/`：源码与知识库清单、只读校验程序、校验结果、Git LFS 检查结果和回滚脚本。
- `publication-manifest.json`：发布范围、排除项、知识库状态和校验入口。

## 获取与验证

```powershell
git clone --branch codex/release-5.4.0-stable-knowledge --single-branch https://github.com/dddeath/code-knowledge-builder.git
Set-Location .\code-knowledge-builder
git lfs pull
python .\delivery\verify-publication.py --root . --write .\delivery\verification.json
git lfs fsck
```

校验程序会逐文件核对 `source/` 与 `knowledge-base/`，并检查完成标记、双 SQLite 完整性、human/markdown 镜像、readability、工作记录、reference、research gap、学习笔记原始字节和 Git LFS 对象。发布后从 GitHub 新克隆的副本已通过全部 12 项只读检查，`git lfs fsck` 也已通过。

## 使用边界

发布知识库可直接用于阅读、检索结果复核和发布完整性检查。它保留了构建时固定源码快照及其本机绑定路径；如果要在另一台机器上继续执行 `ckb status`、`ckb maintain` 或追加记录，应先按迁移流程把知识库重新绑定到当地的源码仓库与 Agent Policy，不应直接把发布副本当作已迁移的活动知识库。

大体积 ZIP 和 SQLite 文件由 Git LFS 管理。未执行 `git lfs pull` 时，工作树中可能只有指针文件，此时发布校验不会通过。

## 回滚

远端回滚脚本位于 `delivery/rollback-github-release-5.4.0.ps1`。具备目标分支推送权限的维护者可在发布仓库中运行该脚本；它会创建新的 revert commit 并推送，不执行 force push，也不改写公开历史。

## 相关知识页

- [[preflight]]

## 源码入口

- [打开源码：scripts/ckb_core/gitrepo.py 第 194 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:194:1)  `scripts/ckb_core/gitrepo.py:194-217`
