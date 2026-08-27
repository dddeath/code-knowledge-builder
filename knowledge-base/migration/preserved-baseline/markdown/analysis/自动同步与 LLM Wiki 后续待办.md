# 自动同步与 LLM Wiki 后续待办

标签：#类型/分析

## 状态

待办 1 已在 5.1.0 完成；待办 2 和待办 3 仍处于后续工作范围，尚未把性能收益或剩余功能吸收标记为完成。

## 待办事项

1. **会话与修改自动化更新（已完成）**
   - 为已登记项目接入会话生命周期与代码修改事件，使会话开始、每轮结论、修改内容、修改原因、验证结果和踩坑记录能够自动进入机器知识库。
   - 自动记录先进入可去重、可恢复的机器层队列；经过中文说明与来源审阅后，再提炼到人类知识库，避免把原始逐轮对话直接扩张为大量 Markdown 页面。
   - 验收重点包括项目级启用、轮次幂等、敏感信息过滤、中断恢复、索引更新和人类投影审计。

2. **验证已合并的 LLM Wiki 快速检索对性能的提升**
   - 为已经吸收的快速检索能力建立固定基线和可重复 benchmark，对比合并前路径、当前确定性 SQLite 检索以及宽范围文本搜索。
   - 同时测量检索延迟、读取页面数、上下文 token、目标页面与源码定位召回、重复读取成本，以及实际分析或修改任务的成功率。
   - 只有可重复验证记录达到预先冻结的质量与成本门槛后，才把性能提升写成已确认结论。

3. **继续吸收剩余的 LLM Wiki 功能**
   - 建立“已吸收、待吸收、明确排除、需要 benchmark”功能矩阵，逐项核对编译、查询、反馈审计、知识维护和阅读入口等能力。
   - 每项候选功能先封闭输入、输出、依赖、许可证、数据边界和完成门，再按小批次整合，并为人类可读性、机器检索、中文叙述及回滚补齐测试。
   - 优先吸收能降低 Agent 检索成本、改善知识维护闭环且不会显著增加页面数量的能力；其余能力保留为有证据的后续候选。

## 相关知识页

- [[start_session]]
- [[retrieve_machine]]
- [[record_note]]

## 源码入口

- [打开源码：scripts/ckb_core/agent_maintenance.py 第 70 行](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/agent_maintenance.py:70:1)  `scripts/ckb_core/agent_maintenance.py:70-142`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 734 行](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/machine_knowledge.py:734:1)  `scripts/ckb_core/machine_knowledge.py:734-936`
- [打开源码：scripts/ckb_core/workspace_notes.py 第 106 行](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/workspace_notes.py:106:1)  `scripts/ckb_core/workspace_notes.py:106-183`

## 后续补充

### 待办 1：已完成

会话与修改自动化更新已在 `code-knowledge-builder` 5.1.0 中落地。实现采用项目显式启用、统一事件协议、递归脱敏、原子写前队列、SQLite 幂等归并、修改路径核对和 Agent 中文审阅后晋升；未审阅的逐轮对话只保留在机器层。

兼容范围已覆盖 Codex、Claude Code、OpenCode 稳定版、OpenCode V2、DeepSeek Harness 和通用 Harness。六种适配器均完成静态校验与 Windows canary，外层 Git 中的未跟踪项目也已通过有界子树状态测试，Codex companion plugin 已安装启用；后续新任务在 Harness 信任配置生效后自动进入机器层队列。

验收证据包括三十项完整回归、十二项自动化专项测试、并发与重放测试、敏感信息脱敏、失败队列恢复、机器检索、人类投影审阅、发行包完整性、真实安装和隔离回滚。详细设计与结果见 [[跨 Harness 会话与修改自动同步实现]]。
