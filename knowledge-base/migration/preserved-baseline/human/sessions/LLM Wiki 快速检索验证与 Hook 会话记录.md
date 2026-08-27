# LLM Wiki 快速检索验证与 Hook 会话记录

标签：#类型/会话

## 用户请求

验证已合并的 LLM Wiki 快速检索是否带来性能提升，并通过本轮 `SessionStart`、用户提示、工具结果和 `Stop` 事件测试会话级 Hook。

## 核验过程

本轮先固定十二个修改定位问题、三种检索路径、2400 token 预算、一次预热和九次重复，再运行 324 条正式测量。机器库和页面索引均来自 Code Knowledge Builder 5.1.2 完成态自身知识库。性能剖析重新打开了 `retrieve_machine`、源码链接生成和兼容页面检索实现，并核对了冻结协议、原始结果、汇总和 SQLite 完整性。

## 检索验证结果

当前 `machine-fast` 相对 Markdown 宽扫描代理把 Agent 可见上下文从中位 10,049 tokens 降到 2,344.5 tokens，减少 76.67%，同时保持零回退和完全确定性。目标源码 Recall@8 为 50%，中位延迟为 1,783.58 ms，P95 为 2,270.19 ms；召回和延迟门均未通过，因此整体性能提升结论保持待验证。详细结果见 [[LLM Wiki 快速检索性能验证（5.1.2）]]。

## Hook 验证结果

当前 Codex 会话已先通过显式会话激活，再依次写入 `SessionStart`、`UserPromptSubmit`、`PostToolUse` 和 `Stop`。停止事件形成一条机器层 `pending-agent-review`，本次来源审阅后晋升为当前会话页面。数据库同时记录到 `activation_source=agent-skill-start` 的原生 Codex Skill 启动信号，说明显式 CLI 路径和当前 Harness 原生激活路径均已产生可检查记录。

## 修改范围

本轮没有修改固定源码仓库。基准程序、协议、原始数据和剖析文件保存在 `E:\knowledge_builder\self-workspace\work\llm-wiki-retrieval-benchmark`，分析页面作为知识库可变层记录。

## 后续动作

先限制渲染 overscan、缓存源码 URI、批量读取实体章节，并改进紧凑目标保留和测试实体折扣；随后原样复用本轮协议重测。只有七项固定门全部通过，才把 [[自动同步与 LLM Wiki 后续待办]] 中的待办 2 标记完成。

## 会话关联

- [[LLM Wiki 快速检索性能验证（5.1.2）]]
- [[retrieve_machine]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]
- [[自动同步与 LLM Wiki 后续待办]]

## 相关知识页

- [[retrieve_machine]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/machine_knowledge.py 第 734 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:734:1)  `scripts/ckb_core/machine_knowledge.py:734-1008`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1151`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
