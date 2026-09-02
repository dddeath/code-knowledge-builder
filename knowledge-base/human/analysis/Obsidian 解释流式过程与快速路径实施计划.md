# Obsidian 解释流式过程与快速路径实施计划

标签：#类型/分析

## 目标行为

右侧 `CKB 解释` 视图流式显示可审计的执行过程和解释正文，但不显示、请求或保存模型隐藏思维链。可见过程包括 CKB 检索请求、Agent pack、确定性路由结果、Provider/模型、显式 reasoning summary、工具名称和目标、审计阶段、答案增量、落库状态与错误。简单问题走确定性快速路径，复杂或不确定问题继续走完整 Agent、record 和审计路径。

## 完成契约

- 所有问题先执行 CKB stdio `retrieve --profile fast`，快速路径不能绕过知识库。
- 路由由纯确定性脚本判别，Agent 不能自行决定是否跳过完整路径。
- 分类缺字段、冲突、低置信度、`needs-source-read`、开放反馈或复杂意图时一律进入完整路径。
- 侧栏只展示显式过程事件、Provider 提供的 reasoning summary 和最终答案增量，不展示隐藏 chain-of-thought。
- 快速路径仍须验证同一 request ID、Agent pack、中文正文和来源；落库失败时回答可以留在侧栏，但必须标为“未写入知识库”，不得显示完成。
- 完整路径继续要求 `record`、`feedback audit`、`agent-policy check` 和 human/markdown/SQLite 一致。

## 路由模型

新增 `SelectionLearningRoute`，输出 `fast | full`、规则版本、命中条件和回退原因。快速路径只在以下条件全部满足时成立：问题和选区低于固定长度上限；意图是单概念、单段解释或局部定义；没有修改、调试、架构、调用链、多文件比较、安全审计或实验请求；CKB 返回确定性、来源完整、无开放反馈、无 `needs-source-read`；候选页数和 pack token 数低于固定上限。阈值和关键词集合写入版本化常量及测试夹具，不由模型修改。

## 快速路径

1. 插件执行 CKB stdio 检索并显示 request、pack 和路由证据。
2. 把预算化 pack 内容直接交给只读 auxiliary execution；禁用 shell、grep 和源码工具。
3. 使用当前默认 Provider/模型的低延迟配置，流式返回结构化简体中文解释。
4. 新增受限 stdio `record-explanation` 方法：验证 request/pack 新鲜度和同库边界，创建或追加正式分析记录，执行反馈与 Agent Policy 审计并返回凭据；不启动第二个写工具 Agent。
5. 凭据通过后追加当天学习笔记；失败时侧栏保留答案并标记未落库，可一键升级到完整路径。

## 完整路径

保留当前 `SelectionLearningService` 的 Provider 工具执行、`record`、两项审计和证据重开逻辑。新增统一事件适配器，将 CKB 检索、Provider 启动、显式 reasoning summary、工具开始/结束、record、审计、写入和错误转换成同一 `SelectionLearningProgressEvent`，由右侧视图消费。答案正文继续从协议标记中增量提取。

## 流式事件与界面

事件类型固定为 `route.selected`、`retrieval.started/completed`、`provider.started`、`reasoning_summary.delta`、`answer.delta`、`tool.started/completed`、`record.started/completed`、`audit.started/completed`、`persist.completed`、`failed/cancelled`。界面增加“快速/完整”徽标、路由原因、可折叠过程、流式解释、停止按钮、升级完整分析按钮和最终落库状态。UI 以 80 至 120 毫秒批量刷新，防止每个 token 重绘 Markdown。

## 分阶段实施

### Phase 0：协议与冻结样例

冻结简单、复杂、边界和故障问题集；定义可见事件 Schema、隐藏思维链边界、路由规则版本和完成状态。当前所有请求仍走完整路径。

### Phase 1：统一流式事件

扩展 `AuxiliarySessionController`、`InlineEditService` 和 Provider 事件适配器，把 text delta、显式 reasoning summary 和工具生命周期传给 `SelectionLearningViewController`。只改变可见性，不改变路由和落库行为。

### Phase 2：确定性分类器影子运行

实现 `SelectionLearningRoute.ts` 和 CKB `routing_signals` 响应。分类器只记录建议路径，实际仍走完整路径。用冻结样例计算复杂问题误入快速路径的数量，要求为零后才启用。

### Phase 3：快速回答与确定性落库

实现只读快速生成、`record-explanation` stdio 方法、同 request/pack 验证、中文与来源检查和审计。快速失败或信号漂移时自动升级完整路径，使用幂等 request key 防止重复记录。

### Phase 4：设置与恢复

设置面板新增“自动路由”和“始终完整”两项，默认自动；不提供无条件强制快速。加入取消、超时、Provider 断线、stdio 重启、落库失败和重复点击恢复测试。

### Phase 5：真实验收与发行

在 Codex、Claude Code 和至少一个其他已启用 Provider 上验证流式事件；比较完整基线与快速路径的首 token、答案完成和落库耗时；验证答案来源、request/pack、镜像、SQLite 和无 grep 路径；更新独立 Obsidian 插件版本和 ZIP，不改 lite/full 成员边界。

## 主要修改入口

- `src/features/selection-learning/SelectionLearningService.ts`：路由编排、快速/完整分支、完成门。
- `SelectionLearningProgress.ts`：类型化事件和增量正文解析。
- `SelectionLearningView.ts`：过程流、路由徽标、停止与升级按钮。
- `InlineEditService.ts`、`AuxiliarySessionController.ts`：Provider 事件观察器。
- Provider execution adapter：显式 reasoning summary、工具事件和 answer delta 的统一映射。
- `scripts/ckb_core/stdio_server.py`：`routing_signals` 与 `record-explanation`。
- `agent_index.py`、`machine_knowledge.py`：确定性路由信号。
- `workspace_notes.py`：快速路径正式记录和幂等写入。
- 插件设置、单元测试、真实 Obsidian E2E 和发行文档。

## 验收门

- 冻结复杂问题进入快速路径的数量为零。
- 每次快速回答都具有真实 CKB request、pack 和来源；Provider 会话中没有 grep/rg 或项目源码读取。
- 流式过程不含隐藏 chain-of-thought、密钥、原始环境变量或未脱敏工具输出。
- 快速回答首个正文增量时间不高于同问题完整路径基线的 25%，最终落库时间不高于基线的 50%；绝对延迟只在真实 Provider benchmark 后确定。
- 完整路径现有完成门和 31 项插件测试无回归；新增路由、流式、幂等、恢复和多 Provider 测试全部通过。
- 未通过 record/audit 的快速回答明确显示“未写入知识库”，不生成成功标记。

## 相关知识页

- [[audit_obsidian 与 prepare_vault 的协作实现]]
- [[retrieve]]
- [[start_session 与 _session_directory 的协作实现]]
- [[retrieve_machine]]
- [[module_name 与 estimated_tokens 的协作实现]]
- [[record_note]]
- [[audit_global 与 _replace_output_prefix 的协作实现]]
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`
- [打开源码：scripts/ckb_core/agent_index.py 第 440 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:440:1)  `scripts/ckb_core/agent_index.py:440-568`
- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 942 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:942:1)  `scripts/ckb_core/machine_knowledge.py:942-1315`
- [打开源码：scripts/ckb_core/navigation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/navigation.py:1:1)  `scripts/ckb_core/navigation.py:1-456`
- [打开源码：scripts/ckb_core/workspace_notes.py 第 106 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/workspace_notes.py:106:1)  `scripts/ckb_core/workspace_notes.py:106-183`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
