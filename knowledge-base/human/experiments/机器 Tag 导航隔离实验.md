# 机器 Tag 导航隔离实验

标签：#类型/实验

## 实验问题

能否把 tag 事实先保存在机器层，让 Agent 只提交支持票、反对票或撤销，再由确定性审计决定哪些 tag 值得进入人类导航，从而减少查找步骤而不增加页面。

## 固定范围

实验只在独立原型中运行，不接入生产 CKB、稳定人类页面或 Obsidian 插件。机器记录包含结构化来源、固定提交、时间、Agent 身份类别和幂等键，不保存对话原文、Prompt、凭据或自由文本证据。

## 实验方法

审计把 tag 分为候选、已确认、争议和废弃四态，同时检查支持票数、独立 Agent、独立来源、反对比例、证据时效和提交漂移。同一 Agent 的重复投票只保留最后一票。只有已确认 tag 进入独立导航 JSON，每页最多三个，超额项保留在机器审计中。

## 实验结果

固定样例写入 25 条唯一事件并忽略 1 条幂等重复，得到 1 个候选、5 个已确认、1 个争议和 3 个废弃 tag。六个隔离导航任务的总步骤从 `19` 降到 `7`，误导链接从 `5` 降到 `1`，两组页面数都为 `11`，没有新增页面或 tag 冲突。

## 如何解释

结果说明“机器 assertion、确定性审计、人类层只投影已确认 tag”在固定样例中具有导航信号，同时保持页面数量不变。它不等同于真实人类在 Obsidian 中的使用效果，也没有证明当前阈值适合生产知识库。

## 适用边界

生产接入保持关闭。原型只读取本地 JSONL、SQLite 和 JSON；Properties 与 Canvas 仅作为对照能力，没有被写入稳定页面。回滚路径对工作区外目标、目标漂移、manifest 写入失败和恢复失败均有保护，恢复失败时保留 baseline 备份。

## 下一步决定

进入生产前仍需确定三个问题：使用独立 `#导航/...` 还是与 `#类型/...` 并存；如何登记独立 Agent 与独立来源；tag 投影由生成器管理、允许人类编辑，还是只读导出。真实 Obsidian 人工对照应在这些边界确定后进行。

## 相关知识页

- [[ingest 与 connect 的协作实现]]
- [[state_machine 的协作边界]]

## 源码入口

- [打开源码：prototypes/ckb-tag-navigation/ckb_tag_navigation/store.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/prototypes/ckb-tag-navigation/ckb_tag_navigation/store.py:1:1)  `prototypes/ckb-tag-navigation/ckb_tag_navigation/store.py:1-269`
