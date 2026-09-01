# 发行包边界

Code Knowledge Builder 使用三个彼此独立的发行类别。核心 Skill 与 Obsidian 插件分别版本化；插件不会隐式进入 lite 或 full。

## 发行矩阵

| 发行类别 | 当前版本来源 | 包含内容 | 不包含内容 |
|---|---|---|---|
| `lite` | `scripts/package_release.py` 的核心版本 | 完整扫描器、语言解析、分段构建、机器 SQLite、确定性检索、人类 Markdown/Obsidian vault、Logseq 投影、Agent 审阅、审计、局部扫描、迁移和自动化适配代码 | 离线运行时、`plugins/`、Obsidian 伴侣插件 |
| `full-win-x64` | 与 lite 相同的核心版本 | lite 的完整成员集合，加 `assets/runtime/win-x64/` 中由 `toolchain.lock.json` 固定的离线运行时载荷 | `plugins/`、Obsidian 伴侣插件、任何非运行时增量 |
| `obsidian-plugin` | `plugins/obsidian-code-knowledge-builder/dist/manifest.json` 的插件版本 | `main.js`、`manifest.json`、`styles.css`、许可证、来源说明、通过的构建记录和独立 Agent 部署脚本 `deploy.py` | 核心 Skill 源码、扫描器、离线运行时载荷 |

## Lite 的基本功能

Lite 不是演示版或阉割版。只要宿主已经具备锁定版本兼容的 Python、Tree-sitter、语言服务器和格式工具，它可以执行核心知识库流程，包括全仓或局部扫描、分段恢复、机器知识库、人类知识库、Markdown/Logseq 投影、确定性检索、记录和审计。Lite 缺少的只有随包离线部署的第三方运行时。

Lite 完成门固定检查以下基础入口仍在包内：

```text
SKILL.md
agents/openai.yaml
scripts/ckb.py
scripts/ckb_core/__init__.py
references/workflow.md
references/runtime.md
toolchain.lock.json
THIRD_PARTY_NOTICES.md
```

## Full 只增加离线运行时

`full-win-x64` 的核心成员集合必须完整包含 lite，二者差集中的每个成员都必须位于：

```text
assets/runtime/win-x64/
```

打包器检测到 full 增加其他源码、文档或插件文件时直接失败。运行时 payload 的文件大小、SHA-256 和必要成员继续由 `toolchain.lock.json` 验证。

## Obsidian 插件独立发行

插件包名使用插件自己的版本：

```text
code-knowledge-builder-obsidian-PLUGIN_VERSION.zip
```

插件要求用户已经拥有一个 CKB 知识库。插件包不复制核心 Skill，也不携带 full 的离线 payload；随包 `deploy.py` 把已验证插件文件部署到指定 vault，并根据显式参数或已有 `AGENTS.md` 生成 `.ckb/output-contract.json`。插件构建必须先通过自己的 `build-record.json`，打包器随后逐文件复核大小、SHA-256 和 ZIP 字节。

源码仓库可以保留 `plugins/` 作为独立开发工程，但核心 ZIP 永远排除该目录。升级已安装的核心 Skill 时应先替换目标目录，而不是把新 ZIP 叠加到旧目录；这样旧版本遗留的 `plugins/` 不会被误认为 full 的正式成员。Agent 可直接运行 ZIP 内 `deploy.py`，也可用核心命令 `obsidian-plugin register` 后对既有 OUTPUT 执行 `obsidian-plugin deploy`。登记包存在时，后续 CKB 人类 vault 投影会自动部署当前版本。

## 打包命令

只生成 lite：

```powershell
python scripts/package_release.py --kind lite --dist DIST
```

只生成 full：

```powershell
python scripts/package_release.py --kind full-win-x64 --dist DIST
```

只生成 Obsidian 插件：

```powershell
python scripts/package_release.py --kind obsidian-plugin --dist DIST
```

生成两个核心包，不生成插件：

```powershell
python scripts/package_release.py --kind both --dist DIST
```

显式生成全部三类：

```powershell
python scripts/package_release.py --kind all --dist DIST
```

每个 ZIP 都有同名 `.manifest.json`。核心 manifest 声明功能矩阵、禁止前缀和 full 的唯一增量前缀；插件 manifest 声明独立版本、核心依赖和固定上游提交。
