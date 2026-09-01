# Code Knowledge Builder 5.4.0 稳定知识发布分支

本分支发布 Code Knowledge Builder 当前 integration 源码和切换后的完整稳定知识库。它以 GitHub `main` 的 `5.3.0` 发布快照为第一父提交，并把本地 integration 历史作为第二父历史保留；发布树中的 `source/` 则按 integration 提交 `150a1ce` 的 Git 跟踪文件重新生成。

## 分支与内容

- 目标分支：`codex/release-5.4.0-stable-knowledge`
- `source/`：当前 integration 源码，不包含工作区未跟踪文件或其他 worktree。
- `knowledge-base/`：已切换并通过维护门的稳定知识库，包括事实层、机器 SQLite、兼容 SQLite、human/markdown 镜像、52 条工作记录、1 个已审阅 reference、3 个开放 research gap、操作日志和两份学习笔记原文；第 52 条记录用于保存首次 GitHub 推送与远端新克隆复验结果。
- `delivery/`：本次切换、回滚、测试、Skill 安装与 stdio 生命周期验证证据，以及独立发布校验程序。
- `publication-manifest.json`：源码、知识库、Git LFS、排除项和发布边界的机器清单。

知识库固定源码图谱指向 integration 提交 `150a1ce`。三份故意不完整的 C++ 负例夹具使用 `.cpp.txt` 保存，但测试仍通过显式 `language=cpp` 读取相同字节，因此负例行为保留，固定源码图谱不会把故意非法的测试输入当作项目源码解析。

## Git LFS

仓库继续使用 Git LFS 保存 `*.sqlite` 和 `*.zip`。首次克隆前安装 Git LFS，然后执行：

```powershell
git lfs install
git clone --branch codex/release-5.4.0-stable-knowledge https://github.com/dddeath/code-knowledge-builder.git
cd code-knowledge-builder
git lfs pull
python .\delivery\verify-publication.py --root . --write .\delivery\fresh-clone-verification.json
```

校验程序会逐文件核对 `source/` 与 `knowledge-base/`，拒绝未展开的 LFS 指针，检查双 SQLite、human/markdown 镜像、readability、工作记录、reference、research gap 和两份学习笔记原始字节。

## 固定快照边界

`knowledge-base/.source-snapshot/worktree` 作为发布内容保存固定源码字节，但不会在外层 Git 仓库中嵌套提交 `.git` 管理文件。新克隆首先使用 `delivery/verify-publication.py` 做只读发布审计；如果要在新路径继续执行 CKB `status`、`maintain` 或源码定位，应在该机器上通过现有迁移或重建流程重新绑定固定 Git 快照和 Agent Policy，不能把原构建机绝对路径当成新机器路径。

## 回滚

- 本机构建与知识库切换回滚：`delivery/rollback-stable-kb.ps1`
- 已推送分支回滚：`delivery/rollback-github-release-5.4.0.ps1`

远端回滚通过新的 revert commit 恢复第一父发布树，不执行 force push，也不重写已公开历史。
