# CKB Agent 方法调用防偏移机制

标签：#类型/分析

## 当前结论

CKB 通过“固定对象绑定、自动发现协议、预算化检索顺序、受控写入和结束审计”降低 Agent 调用路径偏移，并在交付前检测协议文件或知识表示漂移。它目前属于多层约束和可审计闭环，不是拦截所有工具调用的全局路由器；Harness 是否加载项目指令、Agent 是否按顺序执行，仍是需要运行时证据验证的边界。

## 第一层：固定知识库、源码和命令入口

`agent-policy install` 从知识库 `state.json` 读取固定源码仓库，把知识库输出、源码根、Python runtime 和 `ckb.py` 的绝对路径写入 `workspace-meta/agent-protocol.json`。协议命令示例全部携带精确 `--out`，避免 Agent 临时猜测知识库位置、切换到其他仓库或混用 WSL/Windows runtime。

知识图谱继续绑定固定 Git 提交和独立 source snapshot。Agent 面对 live worktree 修改时，基线代码事实保持在固定提交，工作区变化进入 overlay、change 或 session 记录；这可以区分“固定源码事实”和“当前工作树状态”。

## 第二层：让不同 Harness 自动发现同一协议

安装器把同一份协议投影到知识库根、`human`、`markdown` 和显式登记的 Harness task root，并生成：

- `AGENTS.md`：Codex、OpenCode 和通用 Agent 的主入口；
- `CLAUDE.md`：导入主协议；
- `GEMINI.md`：导入主协议；
- `.github/copilot-instructions.md`：GitHub Copilot 入口；
- `.cursor/rules/code-knowledge-builder.mdc`：Cursor 常驻规则。

工作区根中的协议使用带开始/结束标记的 managed block，安装器只维护该块，保留文件中不属于 CKB 的用户内容。内部知识库根使用精确投影，便于审计字节漂移。

## 第三层：固定读取顺序

协议把默认读取顺序固定为：

```text
brief --profile fast
→ 打开预算化 Agent pack
→ entity / neighbors / source / changes
→ 返回路径和范围的窄源码读取
→ 证据仍不足时才切换 precise 或补充宽搜索
```

`brief` 仍生成完整 JSON record，但首轮只返回 pack 路径、开放 feedback 数、固定阅读入口和是否需要源码回退。候选实体、词项、分项得分、关系和检索统计保存在 record，不预先占用对话上下文。这样既限制首轮信息量，也给后续窄读取留下可复查依据。

协议明确要求：只有 pack 返回 `needs-source-read`，或给出需要核实的精确路径和范围后，才读取源码；全仓遍历、整个 vault 加载和宽范围文本搜索不替代首轮 SQLite 检索。

## 第四层：固定写入入口

可复用分析、修改原因、踩坑、实验和会话记录只通过 `record` 写入，并使用 `--from-pack`、`--from-query` 或唯一知识页链接绑定来源。外部资料走 `reference ingest/review/audit/rollback`，证据不足或来源冲突走 `gaps create`，页面反馈走 `feedback create/locate/resolve`。

`human/pages`、`markdown/pages`、导航页、reference 投影、生成清单和 SQLite 属于生成器管理内容。Agent 不把直接编辑这些对象当成持久维护方式，从而避免 human/markdown、RECORDS 和双 SQLite 彼此漂移。

## 第五层：协议与知识表示审计

`audit_agent_protocol` 检查：

1. 协议记录存在且版本等于当前 `AGENT_PROTOCOL_VERSION`；
2. Python 与 `ckb.py` 路径真实存在；
3. output、human、markdown 三个内部根的所有适配器存在且内容精确一致；
4. 每个工作区 managed block 恰好出现一次且内容为当前版本；
5. Obsidian 忽略规则和隐藏样式存在；
6. 正式笔记、工作记录、feedback 和 output contract 通过审计。

`maintain` 再聚合 Agent Policy、工作记录、reference、research gap、operation journal、人类可读性、`agent-index.sqlite` 和 `machine/knowledge.sqlite`。因此“命令执行过”不等于维护完成；只有审计结果为 `passed` 且 `failed_checks` 为空，才能确认知识表示一致。

## 偏移仍可能从哪里发生

- Harness 若没有加载这些自动发现文件，协议文本不会进入 Agent 上下文。
- 当前协议告诉 Agent 按什么顺序调用，但没有在工具层阻止 Agent 先运行其他命令。
- 项目登记和自动化激活解决事件路由与知识库绑定，不等于每次检索都由统一会话客户端接管。
- 通用 Agent 对话目前仍以逐命令 CLI 为主；会话级 stdio 常驻、自主释放和内存治理已经登记为高优先级待办。
- “任意 Agent 对话绑定管理 Agent”仍在独立开发审计流程中，合并前不属于 integration branch 的已确认能力。

因此，当前可确认的是：CKB 已把正确路径写成跨 Harness 可发现、可审计、可重新投影的项目协议，并通过 `maintain` 检测表示漂移；更强的运行时保证需要会话绑定层实际接管检索入口，并用真实 Harness 调用轨迹证明 `brief-first`、stdio 复用、关闭释放和回退原因。

## Agent 的执行判定清单

开始任务时：

1. 从当前工作区协议读取精确 OUTPUT、repo、Python 和 CKB 路径；
2. 执行 `brief --profile fast`；
3. 若 `open_feedback` 大于零，先列开放反馈；
4. 打开 pack，按返回实体调用 `entity/neighbors/source/changes`；
5. 仅在 pack 要求时窄读源码；
6. 持久结论通过相应 CKB 命令写入；
7. 结束前执行 `maintain`；
8. 在结果中区分已确认事实、推断、待验证项和仍未通过的门。

如果 Agent 绕过上述顺序，现有审计可以发现协议文件、记录、镜像和索引不一致，但对“先运行了哪一个读取命令”的完整强制仍依赖 Harness 会话管理和调用轨迹，这也是后续管理 Agent 与会话级 stdio 任务需要补齐的运行时层。

## 相关知识页

- [[audit_agent_protocol 与 _default_python 的协作实现]]
- [[maintenance_check 与 capability_matrix 的协作实现]]
- [[audit_work_record_index 与 _contains_chinese 的协作实现]]
- [[retrieve 与 _tokens 的协作实现]]
- [[start_session 与 _session_directory 的协作实现]]
- [[serve_stdio 与 _write_line 的协作实现]]
- [[audit_agent_protocol]]

## 源码入口

- [打开源码：scripts/ckb_core/agent_protocol.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol.py:1:1)  `scripts/ckb_core/agent_protocol.py:1-507`
- [打开源码：scripts/ckb_core/llm_wiki_capabilities.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/llm_wiki_capabilities.py:1:1)  `scripts/ckb_core/llm_wiki_capabilities.py:1-453`
- [打开源码：scripts/ckb_core/work_record_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/work_record_index.py:1:1)  `scripts/ckb_core/work_record_index.py:1-242`
- [打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-569`
- [打开源码：scripts/ckb_core/agent_maintenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:1:1)  `scripts/ckb_core/agent_maintenance.py:1-255`
- [打开源码：scripts/ckb_core/stdio_server.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/stdio_server.py:1:1)  `scripts/ckb_core/stdio_server.py:1-283`
- [打开源码：scripts/ckb_core/agent_protocol.py 第 420 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol.py:420:1)  `scripts/ckb_core/agent_protocol.py:420-496`
