# audit_feedback 与 _contains_chinese 的协作实现

标签：#类型/代码

> `scripts/ckb_core/feedback.py` 是 `scripts/ckb_core/feedback.py` 中负责汇总并提供定位式人工反馈的创建、重定位、审计与归档的文件入口。 它按源码所示的参数、条件分支和数据结构完成汇总并提供定位式人工反馈的创建、重定位、审计与归档，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当定位式人工反馈的创建、重定位、审计与归档的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/feedback.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/feedback.py:1:1)  `scripts/ckb_core/feedback.py:1-595`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 主要代码单元是 [[audit_feedback]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[audit_feedback]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[KeywordFallbackRetrievalWiringTests 等测试场景]]
- [[MigrationTest]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 23 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_contains_chinese` | 判断 `contains_chinese` 所表达的条件。 |
| `prepare_feedback_store` | 准备 `feedback_store` 对应的数据与约束。 |
| `_canonical_relative_target` | 处理 `relative_target` 对应的数据与约束。 |
| `_read_chinese_body` | 读取 `chinese_body` 对应的数据与约束。 |
| `_line_selection` | 处理 `selection` 对应的数据与约束。 |
| `_next_feedback_id` | 根据固定输入计算 `next_feedback_id` 稳定标识。 |
| `_title_of` | 处理 `of` 对应的数据与约束。 |
| `_blockquote` | 处理 `blockquote` 对应的数据与约束。 |
| `_visible_feedback` | 处理 `feedback` 对应的数据与约束。 |
| `_record_path` | 记录 `path` 对应的数据与约束。 |
| `_visible_relative` | 处理 `relative` 对应的数据与约束。 |
| `_write_visible_mirrors` | 写入 `visible_mirrors` 对应的数据与约束。 |
| `create_feedback` | 创建 `feedback` 对应的数据与约束。 |
| `_load_feedback` | 加载 `feedback` 对应的数据与约束。 |
| `_all_offsets` | 处理 `offsets` 对应的数据与约束。 |
| `_offset_lines` | 处理 `lines` 对应的数据与约束。 |
| `_locate_anchor` | 定位 `anchor` 对应的数据与约束。 |
| `locate_feedback` | 定位 `feedback` 对应的数据与约束。 |
| `_canonical_applied_record` | 处理 `applied_record` 对应的数据与约束。 |
| `resolve_feedback` | 解析并确定 `feedback` 对应的数据与约束。 |
| `list_feedback` | 列出 `feedback` 对应的数据与约束。 |
| `_query_terms` | 查询 `terms` 对应的数据与约束。 |
| `search_feedback` | 处理 `feedback` 对应的数据与约束。 |

</details>
