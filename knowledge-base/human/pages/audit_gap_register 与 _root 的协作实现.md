# audit_gap_register 与 _root 的协作实现

标签：#类型/代码

> `scripts/ckb_core/research_gaps.py` 是 `scripts/ckb_core/research_gaps.py` 中负责汇总并提供研究缺口的确定性登记、状态转换、聚合与审计的文件入口。 它按源码所示的参数、条件分支和数据结构完成汇总并提供研究缺口的确定性登记、状态转换、聚合与审计，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当研究缺口的确定性登记、状态转换、聚合与审计的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/research_gaps.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/research_gaps.py:1:1)  `scripts/ckb_core/research_gaps.py:1-273`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 主要代码单元是 [[audit_gap_register]]。
- 实现时会用到 [[audit_work_record_index 与 _contains_chinese 的协作实现]]。
- 实现时会用到 [[retrieve 与 _tokens 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[ScopeExtensionTest]] 会使用这里提供的行为。
- [[audit_gap_register]] 会使用这里提供的行为。
- [[audit_work_record_index 与 _contains_chinese 的协作实现]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanPageAuthoringValidationFailureTests]]
- [[HumanPageTemplateRegistryTests 等测试场景]]
- [[MigrationTest]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 15 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_root` | 处理 `root` 对应的数据与约束。 |
| `_records_root` | 处理 `root` 对应的数据与约束。 |
| `_narrative` | 处理 `narrative` 对应的数据与约束。 |
| `_evidence` | 处理 `evidence` 对应的数据与约束。 |
| `_record_path` | 记录 `path` 对应的数据与约束。 |
| `gap_records` | 处理 `records` 对应的数据与约束。 |
| `_index_value` | 处理 `value` 对应的数据与约束。 |
| `_write_index` | 写入 `index` 对应的数据与约束。 |
| `gap_navigation_counts` | 汇总 `gap_navigation_counts` 状态与计数。 |
| `_sync_indexes` | 同步 `indexes` 对应的数据与约束。 |
| `create_gap` | `create_gap` 是第 123-149 行的函数，供所属页面定位实现。 |
| `resolve_gap` | 解析并确定 `gap` 对应的数据与约束。 |
| `list_gaps` | 列出 `gaps` 对应的数据与约束。 |
| `gap_machine_records` | 处理 `machine_records` 对应的数据与约束。 |
| `_record_errors` | 记录 `errors` 对应的数据与约束。 |

</details>
