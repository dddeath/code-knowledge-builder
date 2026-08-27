# 跨 Harness 会话与修改自动同步实现

标签：#类型/变更

## 修改内容

- 新增项目级显式注册表，把 Codex、Claude Code、OpenCode、OpenCode V2、DeepSeek Harness 和通用 Harness 的事件归一为九类会话、轮次、工具、文件、压缩与结束事件。
- 新增原子写前队列和 `machine/automation.sqlite`，对事件、轮次、修改路径和待审阅记录进行确定性去重；中断后可继续排空，失败事件可显式重试。
- Git 状态采集固定使用注册项目子树，并把外层 Git 返回的路径前缀转为项目相对路径；缓存、虚拟环境、`node_modules` 与 C# `bin/obj` 由确定性规则过滤。
- 新增递归脱敏与字段限长，对敏感键、授权头、凭据赋值、私钥文本和项目自定义模式先处理再落盘。
- 每轮停止只产生机器层 `pending-agent-review`。Agent 重新打开全部变化路径，提交简体中文正文、来源核对说明和精确路径集合后，才会生成一页人类变更记录。
- 机器检索和变更查询已经接入待审阅自动化记录；原始或近原始对话不会直接扩张 Markdown 页面。
- 为六种 Harness 生成隔离适配包；Codex companion plugin 已安装并启用，其他 Harness 可按项目复制对应配置。

## 修改原因

过去的会话页与修改页依赖 Agent 主动调用记录命令，容易遗漏，也缺少跨 Harness 的统一幂等、恢复和隐私边界。本次把 Harness 限定为事件来源，把项目启用、脱敏、持久化、分类和审阅统一放进确定性核心，从而兼顾自动化、可恢复性、人类可读性与较低上下文成本。

## 验证结果

- 全量源码回归共三十项测试通过，其中自动化专项十二项全部通过。
- Windows canary 覆盖六种 Harness；Codex、Claude Code 与 DSH 的生成命令链实际执行通过，OpenCode 稳定版、OpenCode V2 与通用协议 canary 通过。
- 并发、事件重放、未登记项目、已脏文件继续变化、脱敏、失败队列重试、机器检索和 Agent 审阅晋升均有自动化用例。
- 自动化专项在最终安装版连续运行三轮均全部通过；自身源码位于外层 Git 的未跟踪子目录时，状态 canary 在一秒内返回六百余条项目相对路径，前缀路径和缓存路径均为零。
- Windows canary 最终记录十三个事件、六个会话，队列无待处理或失败项，SQLite 完整性检查为正常，测试凭据未出现在持久化结果中。
- lite、full-win-x64 与六 Harness 集成包均已重新打包并通过归档完整性检查；Codex 与 DSH 安装版均通过结构校验、doctor 和专项测试。
- 安装回滚已在隔离副本中执行，能够恢复各自原版本并逐字节匹配保存的基线。

## Harness 接入边界

- Codex 使用 companion plugin 的生命周期 Hook；新任务需在 `/hooks` 中核对并信任定义。
- Claude Code 使用项目级 `.claude/settings.json` Hook。
- OpenCode 使用 `.opencode/plugins/` 中的稳定版或 V2 插件文件，两种 API 不混用。
- DSH 使用官方 Codex 方言桥接器支持的四类事件，并以每轮 Stop 作为主要持久化点。
- 其他 Harness 按通用 JSON Schema 至少发送会话开始、用户请求、工具结果和轮次停止。

## 新增源码入口

- [打开源码：自动化核心](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py`
- [打开源码：Harness 适配器](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py`
- [打开源码：CLI 自动化路由](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb.py:226:1)  `scripts/ckb.py:226-269`
- [打开源码：机器检索接入](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/machine_knowledge.py:734:1)  `scripts/ckb_core/machine_knowledge.py:734-980`
- [打开源码：自动化专项测试](vscode://file/E:/knowledge_builder/code-knowledge-builder/tests/test_automation.py:1:1)  `tests/test_automation.py`

## 相关知识页

- [[record_note]]
- [[retrieve_machine]]
- [[start_session]]

## 源码入口

- [打开源码：scripts/ckb_core/workspace_notes.py 第 106 行](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/workspace_notes.py:106:1)  `scripts/ckb_core/workspace_notes.py:106-183`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 734 行](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/machine_knowledge.py:734:1)  `scripts/ckb_core/machine_knowledge.py:734-936`
- [打开源码：scripts/ckb_core/agent_maintenance.py 第 70 行](vscode://file/E:/knowledge_builder/code-knowledge-builder/scripts/ckb_core/agent_maintenance.py:70:1)  `scripts/ckb_core/agent_maintenance.py:70-142`
