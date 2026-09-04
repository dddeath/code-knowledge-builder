# start_scope_extension 与 _error 的协作实现

标签：#类型/代码

> `scripts/ckb_core/scope_extension.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责实现 `scope_extension.py` 中由固定源码定义的命令或知识库处理步骤。

## 什么时候需要修改

当 `scripts/ckb_core/scope_extension.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/scope_extension.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/scope_extension.py:1:1)  `scripts/ckb_core/scope_extension.py:1-1314`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[ScopeExtensionOfferTests.retrieval]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[finalize]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[maintenance_check]]。
- 实现时会用到 [[preflight]]。
- 主要代码单元是 [[start_scope_extension]]。
- 实现时会用到 [[validate]]。

## 谁会来到这里

- [[ScopeExtensionOfferTests.retrieval 等测试场景]] 会使用这里提供的行为。
- [[ScopeExtensionTest]] 会使用这里提供的行为。
- [[_Transport.close 与 _StartGate 的协作实现]] 会使用这里提供的行为。
- [[audit_agent_protocol 与 _default_python 的协作实现]] 会使用这里提供的行为。
- [[command 等测试场景]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 会使用这里提供的行为。
- [[keyword_provider_config 与 parser 的协作实现]] 会使用这里提供的行为。
- [[query_graph]] 会使用这里提供的行为。
- [[refresh]] 会使用这里提供的行为。
- [[refresh 等测试场景]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[serve_stdio]] 会使用这里提供的行为。
- [[start_scope_extension]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[AgentProtocolBatchApplyTests 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[ChineseRetrievalEffectRetestFixtureTests]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 35 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_error` | `_error` 是第 34-35 行的函数，供所属页面定位实现。 |
| `_canonical_entry` | `_canonical_entry` 是第 38-54 行的函数，供所属页面定位实现。 |
| `_scope_offer_diagnostic` | `_scope_offer_diagnostic` 生成有界的扩库未建议诊断，保存固定分类、中文说明和最多八个候选。 |
| `_explicit_scope_candidates` | `_explicit_scope_candidates` 只从用户问题中提取显式源码路径或完整 entry selector，并保持首次出现顺序去重。 |
| `_canonical_candidate_path` | `_canonical_candidate_path` 把候选转换为仓库相对 POSIX 路径，并拒绝绝对路径、父目录跳转和非规范片段。 |
| `_catalog_file_records` | `_catalog_file_records` 从固定 catalog 中提取带路径的源码文件记录，供扩库候选核对 Git blob 和中心归属。 |
| `_resolve_scope_offer_selector` | 该函数为范围外源码确认提供候选解析、证据判定或有界诊断。 |
| `_candidate_warning_evidence` | `_candidate_warning_evidence` 只收集明确命中候选路径或实体且禁止缺失推断的 warning，忽略其他语言和其他路径的警告。 |
| `_candidate_warning_evidence.normalized_path` | 该函数为范围外源码确认提供候选解析、证据判定或有界诊断。 |
| `_candidate_warning_evidence.add_if_relevant` | 该函数为范围外源码确认提供候选解析、证据判定或有界诊断。 |
| `attach_scope_extension_offer` | 该函数为范围外源码确认提供候选解析、证据判定或有界诊断。 |
| `_tree_manifest` | `_tree_manifest` 是第 57-72 行的函数，供所属页面定位实现。 |
| `_same_manifest` | `_same_manifest` 是第 75-76 行的函数，供所属页面定位实现。 |
| `_sqlite_checks` | `_sqlite_checks` 是第 79-100 行的函数，供所属页面定位实现。 |
| `_release_audit_handles` | `_release_audit_handles` 是第 103-107 行的函数，供所属页面定位实现。 |
| `_candidate_graph` | `_candidate_graph` 是第 110-118 行的函数，供所属页面定位实现。 |
| `_dimension` | `_dimension` 是第 121-131 行的函数，供所属页面定位实现。 |
| `_page_ids` | `_page_ids` 是第 134-135 行的函数，供所属页面定位实现。 |
| `_replace_prefix` | `_replace_prefix` 是第 138-145 行的函数，供所属页面定位实现。 |
| `_rebind_preserved_json` | `_rebind_preserved_json` 是第 148-167 行的函数，供所属页面定位实现。 |
| `_layer_inventory` | `_layer_inventory` 是第 170-195 行的函数，供所属页面定位实现。 |
| `_preservation_errors` | `_preservation_errors` 是第 198-216 行的函数，供所属页面定位实现。 |
| `_recomputed_review_sets` | `_recomputed_review_sets` 是第 219-246 行的函数，供所属页面定位实现。 |
| `_load_extension_state` | `_load_extension_state` 是第 249-258 行的函数，供所属页面定位实现。 |
| `_control_records` | `_control_records` 是第 454-521 行的函数，供所属页面定位实现。 |
| `_control_records.depth` | `_control_records.depth` 是第 504-517 行的函数，供所属页面定位实现。 |
| `_control_selection` | `_control_selection` 是第 524-548 行的函数，供所属页面定位实现。 |
| `_public_control` | `_public_control` 是第 551-552 行的函数，供所属页面定位实现。 |
| `extension_status` | `extension_status` 是第 555-595 行的函数，供所属页面定位实现。 |
| `audit_scope_extension` | `audit_scope_extension` 是第 598-692 行的函数，供所属页面定位实现。 |
| `audit_scope_extension.check` | `audit_scope_extension...` 是第 604-605 行的函数，供所属页面定位实现。 |
| `_control_path` | `_control_path` 是第 695-696 行的函数，供所属页面定位实现。 |
| `cutover_scope_extension` | `cutover_scope_extension` 是第 699-804 行的函数，供所属页面定位实现。 |
| `_active_control` | `_active_control` 是第 807-818 行的函数，供所属页面定位实现。 |
| `rollback_scope_extension` | `rollback_scope_extension` 是第 821-908 行的函数，供所属页面定位实现。 |

</details>
