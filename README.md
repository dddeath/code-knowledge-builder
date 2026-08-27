# Code Knowledge Builder 5.1.3

这是 `code-knowledge-builder` 的私有可审计发布快照，包含当前源码、由该源码为自身构建的简体中文知识库，以及补丁、验证和回滚交付。

## 本版更新

5.1.3 在纯确定性检索边界内加入固定 overscan、两次批量 SQL、源码路径与静态检索上下文缓存、紧凑目标保留、中文三元词项、元数据固定加权和测试实体折扣。原冻结协议的十二个问题、三种路径、2400 token、一次预热、九次重复和七项阈值保持不变；目标源码 Recall@8 从 50% 提升到 100%，P95 从 2,270.19 ms 降至 45.36 ms，可见上下文减少 77.28%，七门全部通过。

增量迁移新增完成态目录提升后的受验证路径重定位：只有旧快照路径消失、当前输出内固定快照存在且 commit/tree/clean 检查通过时才重写输出自有 JSON 路径；不可变迁移基线和固定源码保持原字节。

## 内容

- `source/`：Skill 源码，提交为 `abeac3eb116552d5c223503205625e9fafefa2e0`。
- `knowledge-base/`：5.1.3 自身知识库；全局审计、增量迁移、机器层和人类层均为 `passed`。
- `knowledge-base/human/`：面向人的简体中文 Markdown/Obsidian 知识库。
- `knowledge-base/machine/knowledge.sqlite`：面向 Agent 的完整 SQLite/FTS 知识库。
- `delivery/`：从空基线补丁、5.1.2→5.1.3 文本补丁、统一验证记录、安装记录和已执行的回滚脚本。

当前图谱包含 31 个源码文件、483 个实体、1,985 条关系、495 份机器文档和 1,639 个检索段。发布前 Hook canary 完成真实 `SessionStart → Prompt → PostToolUse → Stop → Agent review → SessionEnd`，自动化数据库为 10 个事件、1 个会话、2 个轮次、2 个已审阅记录、0 个待审阅项，SQLite 完整性为 `ok`。

## Hook 边界

会话与修改同步同时要求项目登记和当前 Harness 会话明确应用 `code-knowledge-builder`。普通文本提及不激活；事件先进入脱敏、幂等机器层，Stop 生成待审阅记录，只有中文说明和来源核对通过后才进入人类知识库。

## 大文件与发行包

仓库使用 Git LFS 保存 `*.zip` 与 `*.sqlite`。5.1.3 的 lite/full 包位于本地 `E:\knowledge_builder\dist`；精确大小和 SHA-256 见 `delivery/package-verification-5.1.3.json`。克隆本仓库前先安装 Git LFS。

## 快速验证

```powershell
$py = 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.0.0\python\python.exe'
& $py -X utf8 .\source\scripts\ckb.py doctor --json
& $py -X utf8 .\source\scripts\ckb.py migrate status --out .\knowledge-base
& $py -X utf8 .\source\scripts\ckb.py automation status --out .\knowledge-base
```

知识库的 `.complete`、`.machine.complete` 与 `.human.complete` 只在相应审计门通过后存在。知识库保存本机来源与固定快照证据；在另一台机器重新运行源码定位命令前，需要重建或显式重定位本地仓库与输出路径。
