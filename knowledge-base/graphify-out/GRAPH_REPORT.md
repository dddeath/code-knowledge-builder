# 项目关系导览

> 这份导览把经常一起工作的类和函数聚成职责群，帮助人先理解结构，再进入具体实现。

## 建议先看的代码

- **ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append**：该局部函数为并发测试追加一条固定结构的管理审计事件。
- **CkbError**：`CkbError` 是 `scripts/ckb_core/common.py` 中负责为 CKB 输入或状态错误提供固定进程退出码的类。
- **main**：代码单元 `main`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。
- **CodeKnowledgeBuilderTests**：代码单元 `setUp`负责验证 CKB 核心构建、检索、投影、参考资料、运行时和 C++ 语法边界。
- **command**：`command` 是 `tests/e2e_knowledge_batch_migration.py` 第 42-65 行定义的函数，本页绑定该固定源码范围。
- **_Transport.close**：`_Transport.close` 是 `scripts/ckb_core/session_stdio.py` 第 457-496 行定义的函数，本页绑定该固定源码范围。
- **parser**：代码单元 `parser`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。
- **SourceLinkRenderer.uri**：`SourceLinkRenderer.uri` 将仓库内源码位置编码为编辑器可打开的 URI。
- **SessionStdioLifecycleTests**：`SessionStdioLifecycle...` 是 `tests/test_session_stdio.py` 第 77-536 行定义的类，本页绑定该固定源码范围。
- **finalize**：代码单元 `finalize`负责编排固定快照解析、Agent 审阅、页面投影、迁移、全局审计与最终生成。
- **AgentProtocolBatchApplyTests**：`AgentProtocolBatchApp...` 是 `tests/test_agent_protocol_batch.py` 第 272-685 行定义的类，本页绑定该固定源码范围。
- **TemplateProposalStoreTests**：`TemplateProposalStoreTests` 位于 `tests/test_human_page_template_proposals.py` 第 39-370 行，用于覆盖模板提议的待审、批准、退回、撤销和并发安全状态。

## 按职责群浏览

### build_case 相关职责

- **build_case**：`build_case` 位于 `tests/fixtures/obsidian-canvas-agent-visualization/runtime_builder.py` 第 101-366 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **validate**：`validate` 位于 `references/design/obsidian-canvas-agent-visualization/verification/validate_design.py` 第 31-69 行，本页用固定源码范围说明它如何校验输入、状态、证据或输出合同。
- **CanvasContractTests**：`CanvasContractTests` 位于 `tests/test_ckb_canvas_contracts.py` 第 38-146 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **CanvasGraphTests**：`CanvasGraphTests` 位于 `tests/test_ckb_canvas_graph.py` 第 23-136 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **CanvasTransactionTests**：`CanvasTransactionTests` 位于 `tests/test_ckb_canvas_transaction.py` 第 24-111 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **CanvasBenchmarkContractTests**：`CanvasBenchmarkContractTests` 位于 `tests/test_ckb_canvas_benchmark_contract.py` 第 68-204 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **CanvasPathTests**：`CanvasPathTests` 位于 `tests/test_ckb_canvas_paths.py` 第 31-150 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。
- **source_files**：`source_files` 是 `scripts/package_release.py` 第 42-63 行定义的函数，本页绑定该固定源码范围。

### AgentProtocolBatchApplyTests 相关职责

- **AgentProtocolBatchApplyTests**：`AgentProtocolBatchApp...` 是 `tests/test_agent_protocol_batch.py` 第 272-685 行定义的类，本页绑定该固定源码范围。
- **audit_agent_protocol**：`audit_agent_protocol` 是 `scripts/ckb_core/agent_protocol.py` 中负责核对各 Harness 指令文件、工作区绑定、反馈、工作记录与输出契约的函数。
- **create_batch_plan**：`create_batch_plan` 是 `scripts/ckb_core/agent_protocol_batch.py` 第 657-714 行定义的函数，本页绑定该固定源码范围。
- **run**：`run` 是 `tests/e2e_agent_protocol_batch.py` 第 147-305 行定义的函数，本页绑定该固定源码范围。
- **BatchProjectError**：`BatchProjectError` 是第 161-164 行的类，供所属页面定位实现。
- **apply_batch_plan**：`apply_batch_plan` 是第 1414-1516 行的函数，供所属页面定位实现。
- **create_protocol_fixture**：`create_protocol_fixture` 是第 47-118 行的函数，供所属页面定位实现。
- **_output_lock**：`_output_lock` 是第 1178-1256 行的函数，供所属页面定位实现。

### command 相关职责

- **command**：`command` 是 `tests/e2e_knowledge_batch_migration.py` 第 42-65 行定义的函数，本页绑定该固定源码范围。
- **validate_human_maintenance_invocation**：`validate_human_maintenance_invocation` 位于 `scripts/ckb_core/human_maintenance_prompts.py` 第 1391-1516 行，用于核对参数化维护动作的必填参数、类型、确认点和停止条件。
- **render_integration**：`render_integration` 是 `scripts/ckb_core/automation_integrations.py` 第 432-574 行定义的函数，本页绑定该固定源码范围。
- **HumanMaintenancePromptRegistryTests**：`HumanMaintenancePromptRegistryTests` 位于 `tests/test_human_maintenance_prompts.py` 第 102-184 行，用于覆盖维护 Prompt 注册表顺序、稳定序列化和管理入口复用。
- **audit_operation_journal**：`audit_operation_journal` 位于 `scripts/ckb_core/operation_journal.py` 第 385-454 行，本页用固定源码范围说明它如何校验输入、状态、证据或输出合同。
- **emit**：代码单元 `emit`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。
- **audit_human_maintenance_delivery**：`audit_human_maintenance_delivery` 用于汇总并判断受控对象是否满足当前合同。
- **record_operation**：`record_operation` 在 `operation_journal.py` 中用于完成该文件所属能力的输入、状态、输出和失败边界中的局部职责。

### CkbError 相关职责

- **CkbError**：`CkbError` 是 `scripts/ckb_core/common.py` 中负责为 CKB 输入或状态错误提供固定进程退出码的类。
- **TemplateProposalStoreTests**：`TemplateProposalStoreTests` 位于 `tests/test_human_page_template_proposals.py` 第 39-370 行，用于覆盖模板提议的待审、批准、退回、撤销和并发安全状态。
- **propose_template**：`propose_template` 位于 `scripts/ckb_core/human_page_template_proposals.py` 第 1121-1178 行，用于把通过校验的模板扩展写入待人工审阅状态，不直接激活模板。
- **load_page_config**：`load_page_config` 是源码中负责规范化并校验不可漂移的页面配置的命名代码单元。
- **stable_id**：根据固定输入计算 `stable_id` 稳定标识。
- **normalize_template_proposal**：`normalize_template_proposal` 用于规范化输入字段并拒绝未知或越界值。
- **audit_template_proposal**：`audit_template_proposal` 用于汇总并判断受控对象是否满足当前合同。
- **rollback_template_extension**：`rollback_template_extension` 用于执行范围受控的恢复或撤销。

### assertions 相关职责

- **assertions**：代码单元 `assertions`负责验证 tag assertion、策略、幂等写入和路径失败边界。
- **ingest**：代码单元 `ingest`负责以 SQLite 幂等保存 tag 事件，并为写入失败和回滚保留可恢复状态。
- **TagNavigationStateMachineTests**：代码单元 `setUp`负责验证 candidate、confirmed、contested 和 deprecated 四态及原因码。
- **TagNavigationRollbackTests**：代码单元 `test_absent_target_returns_to_absent`负责验证 tag 数据库回滚、漂移保护和恢复失败证据保留。
- **TagNavigationBenchmarkTests**：代码单元 `setUp`负责验证 tag 导航逐题记录与聚合指标可独立重算。
- **TagNavigationCanvasCompatibilityTests**：代码单元 `test_canvas_contract_remains_valid_and_byte_unchanged`负责验证 tag 实验不会改变既有 JSON Canvas 合同。
- **package_showcase**：`package_showcase` 是源码中负责构建可复现发行归档并复核成员集合的命名代码单元。
- **TagNavigationProjectionTests**：代码单元 `test_only_confirmed_tags_project_with_per_page_quota`负责验证仅确认 tag 进入配额受限的人类导航投影。

### parse_file 相关职责

- **parse_file**：代码单元 `parse_file`负责从固定源码提取结构，并把可局部归因的 C++ 语法问题降级为有边界警告。
- **doctor_report**：代码单元 `doctor_report`负责启动并约束语言服务器，收集 Python、JavaScript、C/C++ 和 C# 的语义证据。
- **deployment_plan**：`deployment_plan` 是 `scripts/ckb_core/runtime.py` 中负责根据锁定运行时清单生成所需组件、来源和部署动作的函数。
- **source_value**：代码单元 `reference-direct-init-valid.cpp`负责提供引用直接初始化的固定 C++ 解析样例。
- **CppParserAndSconsTests**：`setUp` 完成CKB 核心合同回归验证中的一个明确步骤。
- **LspClient**：`__init__` 完成语言服务器语义采集中的一个明确步骤。
- **collect_semantics**：`collect_semantics` 完成语言服务器语义采集中的一个明确步骤。
- **DependencyError**：处理 `dependencyerror` 对应的数据与约束。

### bind_conversation 相关职责

- **bind_conversation**：该函数校验项目身份后创建、重复返回或恢复一条管理对话绑定。
- **ManagementBindingLifecycleTest**：`ManagementBindingLifecycleTest` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。
- **ManagementSchemaPersistenceTest**：`ManagementSchemaPersistenceTest` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。
- **create_management_task**：只在绑定状态、知识库状态和 Git 派发条件满足时，从固定 HEAD 创建独立开发 worktree。
- **review_management_task**：执行任务约定的真实测试并把退出状态和输出摘要写入结构化复核记录。
- **binding_status**：重新读取绑定仓库的分支、HEAD、工作树和知识事实新鲜度，并据此报告 ready 或 blocked。
- **management_context**：`management_context` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。
- **unbind_conversation**：`unbind_conversation` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。

### FactFreshnessStateMachineTest 相关职责

- **FactFreshnessStateMachineTest**：代码单元 `setUp`负责验证 Git 驱动的事实新鲜度状态机、迁移计划、并发锁和协作记录。
- **check_fact_freshness**：代码单元 `check_fact_freshness`负责比较知识库固定提交与 Git 当前状态，生成事实新鲜度状态、迁移计划和协作记录。
- **_state_lock**：`_state_lock` 完成Git 源码事实新鲜度中的一个明确步骤。
- **record_collaboration**：`record_collaboration` 登记并持久化Git 源码事实新鲜度所需的数据或状态。
- **GitTriggerAndCollaborationTest**：`setUp` 完成源码事实新鲜度回归验证中的一个明确步骤。
- **create_migration_plan**：`create_migration_plan` 创建并初始化Git 源码事实新鲜度所需的数据或状态。
- **query_collaboration_records**：`query_collaboration_records` 读取并判定Git 源码事实新鲜度所需的数据或状态。
- **FactFreshnessStateMachineTest._commit**：`_commit` 完成源码事实新鲜度回归验证中的一个明确步骤。

### SessionStdioLifecycleTests 相关职责

- **SessionStdioLifecycleTests**：`SessionStdioLifecycle...` 是 `tests/test_session_stdio.py` 第 77-536 行定义的类，本页绑定该固定源码范围。
- **main**：`main` 是 `tests/session_stdio_reactivation_probe.py` 第 16-112 行定义的函数，本页绑定该固定源码范围。
- **close_session**：`close_session` 是第 1330-1389 行的函数，供所属页面定位实现。
- **request_session**：`request_session` 是第 1139-1255 行的函数，供所属页面定位实现。
- **activate_session_stdio**：`activate_session_stdio` 是第 802-887 行的函数，供所属页面定位实现。
- **cleanup_sessions**：`cleanup_sessions` 是第 1392-1431 行的函数，供所属页面定位实现。
- **audit_sessions**：`audit_sessions` 是第 1434-1458 行的函数，供所属页面定位实现。
- **controller_main**：`controller_main` 是第 518-722 行的函数，供所属页面定位实现。

### drain_automation 相关职责

- **drain_automation**：`drain_automation` 完成多 Harness 会话自动化中的一个明确步骤。
- **normalize_event**：`normalize_event` 解析并归一化多 Harness 会话自动化所需的数据或状态。
- **activate_skill_session**：`activate_skill_session` 登记并持久化多 Harness 会话自动化所需的数据或状态。
- **review_automation**：`review_automation` 完成多 Harness 会话自动化中的一个明确步骤。
- **initialize_automation_database**：`initialize_automation_database` 创建并初始化多 Harness 会话自动化所需的数据或状态。
- **_automation_root**：`_automation_root` 完成多 Harness 会话自动化中的一个明确步骤。
- **_process_event**：`_process_event` 完成多 Harness 会话自动化中的一个明确步骤。
- **_record_skill_activation**：`_record_skill_activation` 登记并持久化多 Harness 会话自动化所需的数据或状态。

### PageFanoutGeneratorTests 相关职责

- **PageFanoutGeneratorTests**：代码单元 `setUp`负责验证来源漂移、重复、配额、链接、隔离输出和守卫式回滚。
- **PageFanoutBenchmarkTests**：代码单元 `setUp`负责验证固定任务的盲化导航指标、负结果和现有投影合同兼容性。
- **PageFanoutGeneratorTests._generate**：`_generate` 生成并写入页面扩张生成测试所需的一个明确步骤。
- **PageFanoutBenchmarkTests._judge**：`_judge` 校验页面扩张基准测试所需的一个明确步骤。
- **PageFanoutGeneratorTests._write_json**：`_write_json` 生成并写入页面扩张生成测试所需的一个明确步骤。
- **PageFanoutBenchmarkTests._aggregate**：`_aggregate` 解析并归一化页面扩张基准测试所需的一个明确步骤。
- **PageFanoutBenchmarkTests.test_read_only_guard_rejects_any_snapshot_drift**：该测试验证“read only guard rejects any sna…”场景，保护页面扩张基准测试的结果与失败边界。
- **PageFanoutGeneratorTests.test_broken_link_failure_cleans_staging_and_output**：该测试验证“broken link failure cleans stag…”场景，保护页面扩张生成测试的结果与失败边界。

### ScopeExtensionTest 相关职责

- **ScopeExtensionTest**：`ScopeExtensionTest` 是 `tests/test_scope_extension.py` 第 63-418 行定义的类，本页绑定该固定源码范围。
- **start_scope_extension**：`start_scope_extension` 是 `scripts/ckb_core/scope_extension.py` 第 261-451 行定义的函数，本页绑定该固定源码范围。
- **_tree_manifest**：`_tree_manifest` 是第 57-72 行的函数，供所属页面定位实现。
- **audit_scope_extension**：`audit_scope_extension` 是第 598-692 行的函数，供所属页面定位实现。
- **cutover_scope_extension**：`cutover_scope_extension` 是第 699-804 行的函数，供所属页面定位实现。
- **ScopeExtensionTest.add_preserved_layers**：`ScopeExtensionTest.ad...` 是第 93-192 行的函数，供所属页面定位实现。
- **_sqlite_checks**：`_sqlite_checks` 是第 79-100 行的函数，供所属页面定位实现。
- **rollback_scope_extension**：`rollback_scope_extension` 是第 821-908 行的函数，供所属页面定位实现。

### _inspect_knowledge_project 相关职责

- **_inspect_knowledge_project**：`_inspect_knowledge_pr...` 是第 663-885 行的函数，供所属页面定位实现。
- **path_inside**：生成 `inside` 对应的数据与约束。
- **_knowledge_project_audit**：`_knowledge_project_audit` 是第 1292-1424 行的函数，供所属页面定位实现。
- **_object**：`_object` 是第 205-208 行的函数，供所属页面定位实现。
- **_validate_recovery_topology**：`_validate_recovery_to...` 是第 593-634 行的函数，供所属页面定位实现。
- **_reject_unknown**：`_reject_unknown` 是第 199-202 行的函数，供所属页面定位实现。
- **_origin_health**：`_origin_health` 是第 397-491 行的函数，供所属页面定位实现。
- **_project_operation_id**：`_project_operation_id` 是第 576-586 行的函数，供所属页面定位实现。

### ChineseRetrievalEffectRetestFixtureTests 相关职责

- **ChineseRetrievalEffectRetestFixtureTests**：该测试类核对三臂中文检索实验的协议、指标重算和来源漂移保护。
- **run_failure_probe**：代码单元 `run_failure_probe`负责在固定语料上比较旧词项、当前词项和显式关键词回放慢路径。
- **integrity**：`integrity` 完成tag 事务与回滚所需的一个明确步骤。
- **ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_damaging_copied_index**：验证检索基准发现来源漂移时停止测量且不改坏复制的索引。
- **run_benchmark**：`run_benchmark` 完成中文检索三臂基准所需的一个明确步骤。
- **run_row**：`run_row` 完成中文检索三臂基准所需的一个明确步骤。
- **invoke_arm**：`invoke_arm` 完成中文检索三臂基准所需的一个明确步骤。
- **ChineseRetrievalFixtureTests**：`ChineseRetrievalFixtureTests` 完成中文检索固定协议、基线、回放和来源漂移回归验证中的一个明确步骤。

### project_logseq 相关职责

- **project_logseq**：`project_logseq` 生成并写入知识库构建与投影主流程所需的数据或状态。
- **refresh_human_navigation**：`refresh_human_navigation` 完成知识库构建与投影主流程中的一个明确步骤。
- **project_markdown**：`project_markdown` 生成并写入知识库构建与投影主流程所需的数据或状态。
- **_audit_markdown**：`_audit_markdown` 校验知识库构建与投影主流程所需的数据或状态。
- **_normalized_edn_document**：`_normalized_edn_document` 解析并归一化知识库构建与投影主流程所需的数据或状态。
- **_render_markdown_page**：`_render_markdown_page` 生成并写入知识库构建与投影主流程所需的数据或状态。
- **_canonical_page_context**：`_canonical_page_context` 完成知识库构建与投影主流程中的一个明确步骤。
- **_logical_context_budgets**：`_logical_context_budgets` 完成知识库构建与投影主流程中的一个明确步骤。

### _retrieve_machine_deterministic 相关职责

- **_retrieve_machine_deterministic**：`_retrieve_machine_deterministic` 检索并组织机器索引与检索包生成所需的数据或状态。
- **coverage**：`coverage` 检索并组织机器索引与检索包生成所需的数据或状态。
- **build_machine_knowledge**：`build_machine_knowledge` 创建并初始化机器索引与检索包生成所需的数据或状态。
- **audit_machine_knowledge**：`audit_machine_knowledge` 校验机器索引与检索包生成所需的数据或状态。
- **_static_retrieval_context**：`_static_retrieval_context` 完成机器索引与检索包生成中的一个明确步骤。
- **gap_machine_records**：处理 `machine_records` 对应的数据与约束。
- **_bulk_entity_context**：`_bulk_entity_context` 完成机器索引与检索包生成中的一个明确步骤。
- **_compact_entity_block**：`_compact_entity_block` 完成机器索引与检索包生成中的一个明确步骤。

### ingest_event 相关职责

- **ingest_event**：代码单元 `ingest_event`负责接收多 Harness 事件，维持会话级 Skill 激活状态，并把待审阅事实写入机器层。
- **AutomationTest.register**：代码单元 `register`负责验证多 Harness 事件归一化、会话激活、并发采集和受控投影。
- **AutomationTest**：`setUp` 完成会话自动化回归验证中的一个明确步骤。
- **LspClient.stop**：`stop` 受控释放或回滚语言服务器语义采集所需的数据或状态。
- **automation_status**：`automation_status` 完成多 Harness 会话自动化中的一个明确步骤。
- **register_project**：`register_project` 登记并持久化多 Harness 会话自动化所需的数据或状态。
- **RealGitEventSequenceTest**：`setUp` 完成源码事实新鲜度回归验证中的一个明确步骤。
- **pending_automation_reviews**：`pending_automation_reviews` 完成多 Harness 会话自动化中的一个明确步骤。

### main 相关职责

- **main**：代码单元 `main`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。
- **_Transport.close**：`_Transport.close` 是 `scripts/ckb_core/session_stdio.py` 第 457-496 行定义的函数，本页绑定该固定源码范围。
- **SourceLinkRenderer.uri**：`SourceLinkRenderer.uri` 将仓库内源码位置编码为编辑器可打开的 URI。
- **connect**：`connect` 完成tag 事务与回滚所需的一个明确步骤。
- **ResourceAndIsolationTests**：该测试验证“json writer uses utf8 lf on win…”场景，保护语义向量实验测试的结果与失败边界。
- **_audit_note_storage**：审计 `note_storage` 对应的数据与约束。
- **change_documents**：`change_documents` 完成机器索引与检索包生成中的一个明确步骤。
- **neighbor_lookup**：`neighbor_lookup` 完成机器索引与检索包生成中的一个明确步骤。

### finalize 相关职责

- **finalize**：代码单元 `finalize`负责编排固定快照解析、Agent 审阅、页面投影、迁移、全局审计与最终生成。
- **audit_migration**：`audit_migration` 是 `scripts/ckb_core/migration.py` 第 367-479 行定义的函数，本页绑定该固定源码范围。
- **MigrationTest**：代码单元 `setUp`负责验证固定 blob 迁移时复用事实并重键语法警告引用。
- **utc_now**：处理 `now` 对应的数据与约束。
- **migrate_output**：`migrate_output` 是第 253-364 行的函数，供所属页面定位实现。
- **_preserve_mutable_layers**：`_preserve_mutable_layers` 是第 114-181 行的函数，供所属页面定位实现。
- **_replace_review_packs**：`_replace_review_packs` 是第 199-250 行的函数，供所属页面定位实现。
- **relink_preserved_notes**：`relink_preserved_notes` 是第 487-581 行的函数，供所属页面定位实现。

### ingest_reference 相关职责

- **ingest_reference**：代码单元 `ingest_reference`负责管理参考资料的吸收、审阅、投影、索引、失败重试与回滚。
- **audit_references**：`audit_references` 校验参考资料生命周期所需的数据或状态。
- **project_references**：`project_references` 生成并写入参考资料生命周期所需的数据或状态。
- **contains_chinese_narrative**：`contains_chinese_narrative` 完成机器索引与检索包生成中的一个明确步骤。
- **_powershell_command.quote**：`_powershell_command.q...` 是第 45-46 行的函数，供所属页面定位实现。
- **submit_reference_review**：`submit_reference_review` 完成参考资料生命周期中的一个明确步骤。
- **_render_reference_page**：`_render_reference_page` 生成并写入参考资料生命周期所需的数据或状态。
- **_validate_output**：`_validate_output` 校验参考资料生命周期所需的数据或状态。

### rollback_replacement 相关职责

- **rollback_replacement**：`rollback_replacement` 在 `record_replace.py` 中用于执行范围受控的恢复、撤销或清理。
- **_promotion**：`_promotion` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。
- **_commit_agent**：`_commit_agent` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。
- **_commit_machine**：`_commit_machine` 用于完成局部输入校验、转换或状态更新。
- **_trial_agent**：`_trial_agent` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。
- **_trial_machine**：`_trial_machine` 用于完成局部输入校验、转换或状态更新。
- **_verify_roles**：`_verify_roles` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。
- **_current_agent**：`_current_agent` 用于完成局部输入校验、转换或状态更新。

### FactFreshnessStateMachineTest.test_dead_lock_is_recovered_and_concurrent_checks_serialize.inspect 相关职责

- **FactFreshnessStateMachineTest.test_dead_lock_is_recovered_and_concurrent_checks_serialize.inspect**：`inspect` 完成源码事实新鲜度回归验证中的一个明确步骤。
- **inspect_page_author**：`inspect_page_author` 用于读取、定位并返回现有状态。
- **_candidate_validation**：`_candidate_validation` 用于处理当前模块的结构化输入或状态。
- **_failed**：`_failed` 用于处理当前模块的结构化输入或状态。
- **_load_source_for_render**：`_load_source_for_render` 用于读取、定位并返回现有状态。
- **_contract_result**：`_contract_result` 用于处理当前模块的结构化输入或状态。
- **HumanPageAuthoringValidationFailureTests.test_duplicate_title_path_escape_target_drift_and_existing_section_are_distinct**：该测试验证 V3 页面填写、渐进披露、证据分离或隔离打包边界。
- **PageFanoutBenchmarkTests.test_current_page_quota_v3_and_reference_projection_remain_compatible**：该测试验证“current page quota v3 and refer…”场景，保护页面扩张基准测试的结果与失败边界。

### ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append 相关职责

- **ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append**：该局部函数为并发测试追加一条固定结构的管理审计事件。
- **DeterministicMetricTests**：该测试验证“rank metrics and missing reason…”场景，保护语义向量实验测试的结果与失败边界。
- **KeywordFallbackRetrievalWiringTests.test_stdio_exposes_the_same_nested_canonical_options**：该测试验证“stdio exposes the same nested…”场景，保护关键词慢路径测试的结果与失败边界。
- **_machine_candidate**：`_machine_candidate` 用于完成局部输入校验、转换或状态更新。
- **DeterministicMetricTests.test_independent_aggregate_recomputes_report_fields**：该测试验证“independent aggregate recompute…”场景，保护语义向量实验测试的结果与失败边界。
- **_markdown_sections**：`_markdown_sections` 完成机器索引与检索包生成中的一个明确步骤。
- **build_review_packs.partition**：该附属代码负责按固定排序计算页面、附录、归属和审阅预算，并把结果交给所属页面中的主流程使用。
- **DeterministicMetricTests.test_hybrid_ties_have_stable_path_order**：该测试验证“hybrid ties have stable path or…”场景，保护语义向量实验测试的结果与失败边界。

### validate_human_page 相关职责

- **validate_human_page**：`validate_human_page` 校验人类页面模板校验所需的一个明确步骤。
- **HumanPageTemplateValidationTests**：该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。
- **_context**：该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。
- **_reasons**：该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。
- **_section_context**：该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。
- **HumanPageTemplateValidationTests.test_complete_test_total_shapes_are_l4_but_feature_coverage_is_not**：该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。
- **HumanPageTemplateValidationTests.test_every_page_type_accepts_one_minimal_v3_document**：该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。
- **HumanPageTemplateValidationTests.test_section_budget_is_scoped_to_the_named_section**：该测试验证 V3 页面标题、章节预算、链接、来源或披露边界。

### create_knowledge_batch_plan 相关职责

- **create_knowledge_batch_plan**：`create_knowledge_batc...` 是 `scripts/ckb_core/knowledge_batch_migration.py` 第 888-956 行定义的函数，本页绑定该固定源码范围。
- **preflight**：`preflight` 是 `scripts/ckb_core/gitrepo.py` 第 194-217 行定义的函数，本页绑定该固定源码范围。
- **KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures.refresh**：`KnowledgeBatchWorkflo...` 是 `tests/test_knowledge_batch_migration.py` 第 468-476 行定义的函数，本页绑定该固定源码范围。
- **KnowledgeBatchWorkflowTests**：`KnowledgeBatchWorkflo...` 是第 127-701 行的类，供所属页面定位实现。
- **apply_knowledge_batch_plan**：`apply_knowledge_batch...` 是第 1506-1552 行的函数，供所属页面定位实现。
- **KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures**：`KnowledgeBatchWorkflo...` 是第 457-575 行的函数，供所属页面定位实现。
- **KnowledgeBatchWorkflowTests.test_two_projects_isolate_partial_apply_cutover_and_subset_rollback**：`KnowledgeBatchWorkflo...` 是第 391-455 行的函数，供所属页面定位实现。
- **resume_knowledge_batch_state**：`resume_knowledge_batc...` 是第 1555-1561 行的函数，供所属页面定位实现。

### audit_feedback 相关职责

- **audit_feedback**：`audit_feedback` 是 `scripts/ckb_core/feedback.py` 中负责检查反馈锚点、状态、镜像、归档与落实记录的一致性的函数。
- **create_feedback**：创建 `feedback` 对应的数据与约束。
- **resolve_feedback**：解析并确定 `feedback` 对应的数据与约束。
- **locate_feedback**：定位 `feedback` 对应的数据与约束。
- **CodeKnowledgeBuilderTests.test_feedback_anchor_mirroring_audit_and_archive_are_deterministic**：该测试验证“feedback anchor mirroring aud…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。
- **list_feedback**：列出 `feedback` 对应的数据与约束。
- **_canonical_applied_record**：处理 `applied_record` 对应的数据与约束。
- **_canonical_relative_target**：处理 `relative_target` 对应的数据与约束。

### PdfReferenceExtractionTests 相关职责

- **PdfReferenceExtractionTests**：代码单元 `setUp`负责验证 PDF 页级提取、中文、代码表格、OCR 待处理状态、审阅和回滚。
- **ascii_pdf**：代码单元 `ascii_pdf`负责生成可重复的 PDF 测试样例，覆盖文本、中文、空白和加密文档。
- **PdfReferenceEndToEndTests**：`setUp` 完成PDF 参考资料回归验证中的一个明确步骤。
- **PdfReferenceEndToEndTests.test_pdf_ingest_review_audit_indexes_and_rollback**：该测试验证“pdf ingest review audit index…”场景，保护PDF 参考资料回归验证的预期结果与失败边界。
- **PdfReferenceExtractionTests.test_corrupt_encrypted_size_page_and_source_root_limits**：该测试验证“corrupt encrypted size page a…”场景，保护PDF 参考资料回归验证的预期结果与失败边界。
- **validate_pdf_extraction**：`validate_pdf_extraction` 校验PDF 页级提取与校验所需的数据或状态。
- **inspect_pdf**：`inspect_pdf` 完成PDF 页级提取与校验中的一个明确步骤。
- **PdfExtractionError**：`PdfExtractionError` 完成PDF 页级提取与校验中的一个明确步骤。

### HumanPageTemplateContract 相关职责

- **HumanPageTemplateContract**：`HumanPageTemplateContract` 用于处理当前模块的结构化输入或状态。
- **SectionContract**：`SectionContract` 用于处理当前模块的结构化输入或状态。
- **CountBudget**：`CountBudget` 用于处理当前模块的结构化输入或状态。
- **_section**：`_section` 用于处理当前模块的结构化输入或状态。
- **_validate_nested_input**：`_validate_nested_input` 用于校验输入、状态、证据或输出合同。
- **human_page_template_document**：`human_page_template_document` 用于处理当前模块的结构化输入或状态。
- **_effective_budget**：`_effective_budget` 用于处理当前模块的结构化输入或状态。
- **_section_by_id**：`_section_by_id` 用于处理当前模块的结构化输入或状态。

### module_name 相关职责

- **module_name**：`module_name` 是源码中负责页面配额、实体归属、关系预算和上下文预算的确定性决策的命名代码单元。
- **initialize**：`initialize` 创建并初始化知识库构建与投影主流程所需的数据或状态。
- **build_navigation_plan**：该附属代码负责按固定排序计算页面、附录、归属和审阅预算，并把结果交给所属页面中的主流程使用。
- **_chunks**：`_chunks` 完成知识库构建与投影主流程中的一个明确步骤。
- **_prepare_csharp_restore**：`_prepare_csharp_restore` 创建并初始化知识库构建与投影主流程所需的数据或状态。
- **_rekey_reused_file_parse**：`_rekey_reused_file_parse` 完成知识库构建与投影主流程中的一个明确步骤。
- **_resolve_entries**：`_resolve_entries` 完成知识库构建与投影主流程中的一个明确步骤。
- **_normalize_repo_selector**：`_normalize_repo_selector` 解析并归一化知识库构建与投影主流程所需的数据或状态。

### QueryTermsTests 相关职责

- **QueryTermsTests**：`QueryTermsTests` 是 `tests/test_query_terms.py` 第 25-107 行定义的类，本页绑定该固定源码范围。
- **search_terms**：`search_terms` 是 `scripts/ckb_core/query_terms.py` 第 65-69 行定义的函数，本页绑定该固定源码范围。
- **build_fts_query**：`build_fts_query` 是第 84-88 行的函数，供所属页面定位实现。
- **fts_query_terms**：`fts_query_terms` 是第 77-81 行的函数，供所属页面定位实现。
- **explicit_anchors**：`explicit_anchors` 是第 91-105 行的函数，供所属页面定位实现。
- **index_terms**：`index_terms` 是第 72-74 行的函数，供所属页面定位实现。
- **_ranked_terms**：`_ranked_terms` 是第 31-62 行的函数，供所属页面定位实现。
- **QueryTermsTests.test_compatibility_index_uses_the_same_rules_and_negative_boundary**：`QueryTermsTests.test_...` 是第 96-101 行的函数，供所属页面定位实现。

> 为保持阅读节奏，这里只展开最主要的职责群；图查询仍会使用完整关系。

## 围绕任务继续缩小范围

```powershell
& PYTHON scripts\ckb.py query --out OUTPUT "职责关键词" --budget 1500
& PYTHON scripts\ckb.py path --out OUTPUT "起点类或函数" "目标类或函数"
& PYTHON scripts\ckb.py explain --out OUTPUT "类名、函数名或职责关键词"
```

查询会先选择与问题最相关的代码，再沿真实关系扩展到预算允许的范围。
