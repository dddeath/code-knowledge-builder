# 当前 Codex Hook 触发流程核对

标签：#类型/分析


## 当前生效入口

Codex 中启用并已信任的 `code-knowledge-builder-sync@personal` Plugin 监听 `SessionStart`、`UserPromptSubmit`、`PostToolUse`、`Stop`、`PreCompact`、`PostCompact` 和 `SessionEnd`。其中 `PostToolUse` 只匹配 `Bash|apply_patch|Edit|Write`，压缩事件只匹配 `manual|auto`。已安装 Hook 与 5.1.2 新渲染 Hook 的命令、事件和 matcher 一致，差异仅是描述文字；命令实际调用已安装的 5.1.2 `ckb.py`，因此运行时执行新的显式 Skill 激活门。

## 持久化门

Hook 命令被 Codex 调用后，CKB 先把 Harness 事件归一化，再按事件 `cwd` 匹配注册表。只有命中已登记仓库或 workspace、Harness 已启用，并且同一个 `Harness + session_id + repo_root + code-knowledge-builder` 已明确激活，事件才继续写入。普通文字提及名称不构成激活；精确 `$code-knowledge-builder`、`/code-knowledge-builder`、原生 Skill 事件或 `automation activate` 才构成激活证据。

当前注册表只将 `E:\knowledge_builder\self-workspace\source` 及 workspace 根 `E:\knowledge_builder\self-workspace` 映射到正式知识库。当前 Codex 任务根是 `E:\knowledge_builder`。使用当前任务根重放 `UserPromptSubmit` 得到 `status=ignored`、`reason=project-not-registered-for-harness`；事件、turn、spool 和待审阅计数均未增加。因此当前任务中 Hook 入口会运行，但这条任务的事件不会进入该知识库。

## 激活后的机器流程

注册和会话激活同时满足后，事件内容先递归脱敏并执行字段长度限制，然后原子写入 `workspace-meta/automation/spool/pending`。单仓库 drain 锁与 SQLite `BEGIN IMMEDIATE` 事务将事件写入 `machine/automation.sqlite`；稳定事件 ID 用于幂等去重，处理成功后移入 `processed`，异常事件移入 `failed`，可用 `drain` 或 `retry` 恢复。

`SessionStart` 建立或恢复会话并记录 Git 工作树基线；`UserPromptSubmit` 建立或复用活动轮次；`PostToolUse` 保存工具结果和仓库内修改路径；`PreCompact`、`PostCompact` 保存压缩检查点；`Stop` 保存最终回答、完成轮次、重新计算相对会话基线的仓库内变化，并生成一条 `pending-agent-review`；`SessionEnd` 关闭会话，若仍有活动轮次则先生成待审阅记录。

## 人类知识库边界

`Stop` 或 `SessionEnd` 只产生机器层待审阅记录，不直接写入已审阅的人类页面。Agent 需要重新打开所有变化路径，提交简体中文正文、中文 `evidence_note` 和与变化路径完全一致的 `source_checks`，通过 `automation review` 后才投影到 `human` 与 `markdown`。该流程不会自动重建固定源码图谱、解析 transcript、发布 GitHub，Hook 故障也不会阻断 Harness 的代码操作。

## 当前状态

核对时 `automation.sqlite` 为 `integrity_check=ok`，队列中 `pending_spool=0`、`failed_spool=0`、`pending_reviews=0`。数据库已有另一个会话的 2 个事件和 1 个活动 turn；本次当前任务根的忽略探针没有改变这些计数。

## 相关知识页

- [[MigrationTest]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]

## 源码入口

- [打开源码：tests/test_migration.py 第 57 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:57:1)  `tests/test_migration.py:57-176`
- [打开源码：tests/test_automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:1:1)  `tests/test_automation.py:1-801`
- [打开源码：tests/test_ckb.py 第 170 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb.py:170:1)  `tests/test_ckb.py:170-1132`
