# 项目关系导览

> 这份导览把经常一起工作的类和函数聚成职责群，帮助人先理解结构，再进入具体实现。

## 建议先看的代码

- **ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append**：代码单元 `append`负责验证跨 Harness 对话绑定、仓库预检、任务派发和管理复查。
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
- **path_inside**：生成 `inside` 对应的数据与约束。
- **create_protocol_fixture**：`create_protocol_fixture` 是第 47-118 行的函数，供所属页面定位实现。

### SessionStdioLifecycleTests 相关职责

- **SessionStdioLifecycleTests**：`SessionStdioLifecycle...` 是 `tests/test_session_stdio.py` 第 77-536 行定义的类，本页绑定该固定源码范围。
- **main**：`main` 是 `tests/session_stdio_reactivation_probe.py` 第 16-112 行定义的函数，本页绑定该固定源码范围。
- **one_cycle**：`one_cycle` 是 `tests/session_stdio_stress.py` 第 22-45 行定义的函数，本页绑定该固定源码范围。
- **close_session**：`close_session` 是第 1330-1389 行的函数，供所属页面定位实现。
- **request_session**：`request_session` 是第 1139-1255 行的函数，供所属页面定位实现。
- **activate_session_stdio**：`activate_session_stdio` 是第 802-887 行的函数，供所属页面定位实现。
- **cleanup_sessions**：`cleanup_sessions` 是第 1392-1431 行的函数，供所属页面定位实现。
- **audit_sessions**：`audit_sessions` 是第 1434-1458 行的函数，供所属页面定位实现。

### parse_file 相关职责

- **parse_file**：代码单元 `parse_file`负责从固定源码提取结构，并把可局部归因的 C++ 语法问题降级为有边界警告。
- **doctor_report**：代码单元 `doctor_report`负责启动并约束语言服务器，收集 Python、JavaScript、C/C++ 和 C# 的语义证据。
- **deployment_plan**：`deployment_plan` 是 `scripts/ckb_core/runtime.py` 中负责根据锁定运行时清单生成所需组件、来源和部署动作的函数。
- **source_value**：代码单元 `reference-direct-init-valid.cpp`负责提供引用直接初始化的固定 C++ 解析样例。
- **stable_id**：根据固定输入计算 `stable_id` 稳定标识。
- **CppParserAndSconsTests**：`setUp` 完成CKB 核心合同回归验证中的一个明确步骤。
- **LspClient**：`__init__` 完成语言服务器语义采集中的一个明确步骤。
- **collect_semantics**：`collect_semantics` 完成语言服务器语义采集中的一个明确步骤。

### PdfReferenceExtractionTests 相关职责

- **PdfReferenceExtractionTests**：代码单元 `setUp`负责验证 PDF 页级提取、中文、代码表格、OCR 待处理状态、审阅和回滚。
- **extract_pdf**：代码单元 `extract_pdf`负责按页提取 PDF 文本、代码和表格结构，评估质量并在需要时调用受限 OCR 适配器。
- **ingest**：代码单元 `ingest`负责以 SQLite 幂等保存 tag 事件，并为写入失败和回滚保留可恢复状态。
- **ingest_reference**：代码单元 `ingest_reference`负责管理参考资料的吸收、审阅、投影、索引、失败重试与回滚。
- **ascii_pdf**：代码单元 `ascii_pdf`负责生成可重复的 PDF 测试样例，覆盖文本、中文、空白和加密文档。
- **web_input_adapter_contract**：代码单元 `web_input_adapter_contract`负责定义本地文件与 Web 等参考输入适配器的最小协议。
- **audit_references**：`audit_references` 校验参考资料生命周期所需的数据或状态。
- **PdfReferenceEndToEndTests**：`setUp` 完成PDF 参考资料回归验证中的一个明确步骤。

### validate_human_maintenance_invocation 相关职责

- **validate_human_maintenance_invocation**：`validate_human_maintenance_invocation` 位于 `scripts/ckb_core/human_maintenance_prompts.py` 第 1391-1516 行，用于核对参数化维护动作的必填参数、类型、确认点和停止条件。
- **HumanMaintenancePromptRegistryTests**：`HumanMaintenancePromptRegistryTests` 位于 `tests/test_human_maintenance_prompts.py` 第 102-184 行，用于覆盖维护 Prompt 注册表顺序、稳定序列化和管理入口复用。
- **audit_human_maintenance_delivery**：`audit_human_maintenance_delivery` 用于汇总并判断受控对象是否满足当前合同。
- **render_human_maintenance_prompt**：`render_human_maintenance_prompt` 用于把结构化状态渲染为稳定输出。
- **HumanMaintenancePromptValidationTests**：该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。
- **human_maintenance_registry_sha256**：`human_maintenance_registry_sha256` 用于生成稳定序列化或内容摘要。
- **HumanMaintenancePromptRenderTests**：该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。
- **HumanMaintenanceDeliveryAuditTests**：该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。

### CkbError 相关职责

- **CkbError**：`CkbError` 是 `scripts/ckb_core/common.py` 中负责为 CKB 输入或状态错误提供固定进程退出码的类。
- **TemplateProposalStoreTests**：`TemplateProposalStoreTests` 位于 `tests/test_human_page_template_proposals.py` 第 39-370 行，用于覆盖模板提议的待审、批准、退回、撤销和并发安全状态。
- **propose_template**：`propose_template` 位于 `scripts/ckb_core/human_page_template_proposals.py` 第 1121-1178 行，用于把通过校验的模板扩展写入待人工审阅状态，不直接激活模板。
- **normalize_template_proposal**：`normalize_template_proposal` 用于规范化输入字段并拒绝未知或越界值。
- **audit_template_proposal**：`audit_template_proposal` 用于汇总并判断受控对象是否满足当前合同。
- **rollback_template_extension**：`rollback_template_extension` 用于执行范围受控的恢复或撤销。
- **_text**：`_text` 用于处理当前模块的结构化输入或状态。
- **_normalize_sections**：`_normalize_sections` 用于规范化输入字段并拒绝未知或越界值。

### assertions 相关职责

- **assertions**：代码单元 `assertions`负责验证 tag assertion、策略、幂等写入和路径失败边界。
- **TagNavigationStateMachineTests**：代码单元 `setUp`负责验证 candidate、confirmed、contested 和 deprecated 四态及原因码。
- **TagNavigationRollbackTests**：代码单元 `test_absent_target_returns_to_absent`负责验证 tag 数据库回滚、漂移保护和恢复失败证据保留。
- **TagNavigationBenchmarkTests**：代码单元 `setUp`负责验证 tag 导航逐题记录与聚合指标可独立重算。
- **TagNavigationCanvasCompatibilityTests**：代码单元 `test_canvas_contract_remains_valid_and_byte_unchanged`负责验证 tag 实验不会改变既有 JSON Canvas 合同。
- **package_showcase**：`package_showcase` 是源码中负责构建可复现发行归档并复核成员集合的命名代码单元。
- **TagNavigationProjectionTests**：代码单元 `test_only_confirmed_tags_project_with_per_page_quota`负责验证仅确认 tag 进入配额受限的人类导航投影。
- **replay_with_rollback**：`replay_with_rollback` 完成tag 事务与回滚所需的一个明确步骤。

### FactFreshnessStateMachineTest 相关职责

- **FactFreshnessStateMachineTest**：代码单元 `setUp`负责验证 Git 驱动的事实新鲜度状态机、迁移计划、并发锁和协作记录。
- **check_fact_freshness**：代码单元 `check_fact_freshness`负责比较知识库固定提交与 Git 当前状态，生成事实新鲜度状态、迁移计划和协作记录。
- **_state_lock**：`_state_lock` 完成Git 源码事实新鲜度中的一个明确步骤。
- **record_collaboration**：`record_collaboration` 登记并持久化Git 源码事实新鲜度所需的数据或状态。
- **GitTriggerAndCollaborationTest**：`setUp` 完成源码事实新鲜度回归验证中的一个明确步骤。
- **create_migration_plan**：`create_migration_plan` 创建并初始化Git 源码事实新鲜度所需的数据或状态。
- **query_collaboration_records**：`query_collaboration_records` 读取并判定Git 源码事实新鲜度所需的数据或状态。
- **FactFreshnessStateMachineTest._commit**：`_commit` 完成源码事实新鲜度回归验证中的一个明确步骤。

### command 相关职责

- **command**：`command` 是 `tests/e2e_knowledge_batch_migration.py` 第 42-65 行定义的函数，本页绑定该固定源码范围。
- **parser**：代码单元 `parser`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。
- **render_integration**：`render_integration` 是 `scripts/ckb_core/automation_integrations.py` 第 432-574 行定义的函数，本页绑定该固定源码范围。
- **keyword_provider_config**：代码单元 `keyword_provider_config`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。
- **emit**：代码单元 `emit`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。
- **main**：`main` 解析补丁输出路径并生成从空目录到完整 Skill 的文本统一差异。
- **historical_output**：`historical_output` 是第 96-152 行的函数，供所属页面定位实现。
- **add_initial_arguments**：`add_initial_arguments` 完成CKB 公开命令分派中的一个明确步骤。

### CodeKnowledgeBuilderTests 相关职责

- **CodeKnowledgeBuilderTests**：代码单元 `setUp`负责验证 CKB 核心构建、检索、投影、参考资料、运行时和 C++ 语法边界。
- **finalize**：代码单元 `finalize`负责编排固定快照解析、Agent 审阅、页面投影、迁移、全局审计与最终生成。
- **retrieve**：`retrieve` 是 `scripts/ckb_core/agent_index.py` 第 426-554 行定义的函数，本页绑定该固定源码范围。
- **serve_stdio**：`serve_stdio` 是 `scripts/ckb_core/stdio_server.py` 第 202-391 行定义的函数，本页绑定该固定源码范围。
- **KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures.refresh**：`KnowledgeBatchWorkflo...` 是 `tests/test_knowledge_batch_migration.py` 第 468-476 行定义的函数，本页绑定该固定源码范围。
- **merge**：`merge` 完成知识库构建与投影主流程中的一个明确步骤。
- **coverage**：`coverage` 检索并组织机器索引与检索包生成所需的数据或状态。
- **CodeKnowledgeBuilderTests.test_markdown_whole_repository_and_completion_gate**：该测试验证“markdown whole repository and…”场景，保护CKB 核心合同回归验证的预期结果与失败边界。

### module_name 相关职责

- **module_name**：`module_name` 是源码中负责页面配额、实体归属、关系预算和上下文预算的确定性决策的命名代码单元。
- **initialize**：`initialize` 创建并初始化知识库构建与投影主流程所需的数据或状态。
- **project_logseq**：`project_logseq` 生成并写入知识库构建与投影主流程所需的数据或状态。
- **_audit_markdown**：`_audit_markdown` 校验知识库构建与投影主流程所需的数据或状态。
- **build_context**：`build_context` 创建并初始化知识库构建与投影主流程所需的数据或状态。
- **_normalized_edn_document**：`_normalized_edn_document` 解析并归一化知识库构建与投影主流程所需的数据或状态。
- **_render_markdown_page**：`_render_markdown_page` 生成并写入知识库构建与投影主流程所需的数据或状态。
- **_canonical_page_context**：`_canonical_page_context` 完成知识库构建与投影主流程中的一个明确步骤。

### ScopeExtensionTest 相关职责

- **ScopeExtensionTest**：`ScopeExtensionTest` 是 `tests/test_scope_extension.py` 第 63-418 行定义的类，本页绑定该固定源码范围。
- **start_scope_extension**：`start_scope_extension` 是 `scripts/ckb_core/scope_extension.py` 第 261-451 行定义的函数，本页绑定该固定源码范围。
- **preflight**：`preflight` 是 `scripts/ckb_core/gitrepo.py` 第 194-217 行定义的函数，本页绑定该固定源码范围。
- **_tree_manifest**：`_tree_manifest` 是第 57-72 行的函数，供所属页面定位实现。
- **audit_scope_extension**：`audit_scope_extension` 是第 598-692 行的函数，供所属页面定位实现。
- **cutover_scope_extension**：`cutover_scope_extension` 是第 699-804 行的函数，供所属页面定位实现。
- **ScopeExtensionTest.add_preserved_layers**：`ScopeExtensionTest.ad...` 是第 93-192 行的函数，供所属页面定位实现。
- **_sqlite_checks**：`_sqlite_checks` 是第 79-100 行的函数，供所属页面定位实现。

### _inspect_knowledge_project 相关职责

- **_inspect_knowledge_project**：`_inspect_knowledge_pr...` 是第 663-885 行的函数，供所属页面定位实现。
- **_knowledge_project_audit**：`_knowledge_project_audit` 是第 1292-1424 行的函数，供所属页面定位实现。
- **_cutover_one**：`_cutover_one` 是第 1721-1880 行的函数，供所属页面定位实现。
- **_apply_one_project**：`_apply_one_project` 是第 1427-1503 行的函数，供所属页面定位实现。
- **_object**：`_object` 是第 205-208 行的函数，供所属页面定位实现。
- **_validate_recovery_topology**：`_validate_recovery_to...` 是第 593-634 行的函数，供所属页面定位实现。
- **_reject_unknown**：`_reject_unknown` 是第 199-202 行的函数，供所属页面定位实现。
- **_verify_plan_bindings**：`_verify_plan_bindings` 是第 1116-1126 行的函数，供所属页面定位实现。

### PageFanoutGeneratorTests 相关职责

- **PageFanoutGeneratorTests**：代码单元 `setUp`负责验证来源漂移、重复、配额、链接、隔离输出和守卫式回滚。
- **PageFanoutBenchmarkTests**：代码单元 `setUp`负责验证固定任务的盲化导航指标、负结果和现有投影合同兼容性。
- **PageFanoutGeneratorTests._generate**：`_generate` 生成并写入页面扩张生成测试所需的一个明确步骤。
- **PageFanoutBenchmarkTests._judge**：`_judge` 校验页面扩张基准测试所需的一个明确步骤。
- **PageFanoutGeneratorTests._write_json**：`_write_json` 生成并写入页面扩张生成测试所需的一个明确步骤。
- **PageFanoutBenchmarkTests._aggregate**：`_aggregate` 解析并归一化页面扩张基准测试所需的一个明确步骤。
- **PageFanoutBenchmarkTests.test_read_only_guard_rejects_any_snapshot_drift**：该测试验证“read only guard rejects any sna…”场景，保护页面扩张基准测试的结果与失败边界。
- **PageFanoutGeneratorTests.test_broken_link_failure_cleans_staging_and_output**：该测试验证“broken link failure cleans stag…”场景，保护页面扩张生成测试的结果与失败边界。

### ChineseRetrievalEffectRetestFixtureTests 相关职责

- **ChineseRetrievalEffectRetestFixtureTests**：代码单元 `setUp`负责验证三臂协议、旧词项、相关性标注、排序指标和来源漂移失败门。
- **run_failure_probe**：代码单元 `run_failure_probe`负责在固定语料上比较旧词项、当前词项和显式关键词回放慢路径。
- **integrity**：`integrity` 完成tag 事务与回滚所需的一个明确步骤。
- **ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_damaging_copied_index**：该测试验证“source corpus drift fails wit…”场景，保护中文检索合同测试的结果与失败边界。
- **run_benchmark**：`run_benchmark` 完成中文检索三臂基准所需的一个明确步骤。
- **run_row**：`run_row` 完成中文检索三臂基准所需的一个明确步骤。
- **invoke_arm**：`invoke_arm` 完成中文检索三臂基准所需的一个明确步骤。
- **ChineseRetrievalFixtureTests**：该测试验证“frozen protocol shape”场景，保护中文检索合同测试的结果与失败边界。

### replace_note 相关职责

- **replace_note**：`replace_note` 位于 `scripts/ckb_core/record_replace.py` 第 930-991 行，本页用固定源码范围说明它如何完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。
- **rollback_replacement**：`rollback_replacement` 在 `record_replace.py` 中用于执行范围受控的恢复、撤销或清理。
- **_promotion**：`_promotion` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。
- **_replace_lock**：`_replace_lock` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。
- **_commit_agent**：`_commit_agent` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。
- **_commit_machine**：`_commit_machine` 用于完成局部输入校验、转换或状态更新。
- **_trial_agent**：`_trial_agent` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。
- **_trial_machine**：`_trial_machine` 用于完成局部输入校验、转换或状态更新。

### validate_human_page 相关职责

- **validate_human_page**：`validate_human_page` 校验人类页面模板校验所需的一个明确步骤。
- **SectionContract**：`SectionContract` 用于处理当前模块的结构化输入或状态。
- **main**：`main` 用于根据已解析子命令调用对应 CKB 能力并返回稳定退出状态。
- **CountBudget**：`CountBudget` 用于处理当前模块的结构化输入或状态。
- **_section**：`_section` 用于处理当前模块的结构化输入或状态。
- **_validation_error**：`_validation_error` 用于处理当前模块的结构化输入或状态。
- **human_page_template_document**：`human_page_template_document` 用于处理当前模块的结构化输入或状态。
- **_context_sequence**：`_context_sequence` 用于处理当前模块的结构化输入或状态。

### _Transport.close 相关职责

- **_Transport.close**：`_Transport.close` 是 `scripts/ckb_core/session_stdio.py` 第 457-496 行定义的函数，本页绑定该固定源码范围。
- **SourceLinkRenderer.uri**：`SourceLinkRenderer.uri` 将仓库内源码位置编码为编辑器可打开的 URI。
- **connect**：`connect` 完成tag 事务与回滚所需的一个明确步骤。
- **initialize_automation_database**：`initialize_automation_database` 创建并初始化多 Harness 会话自动化所需的数据或状态。
- **pending_automation_reviews**：`pending_automation_reviews` 完成多 Harness 会话自动化中的一个明确步骤。
- **ResourceAndIsolationTests**：该测试验证“json writer uses utf8 lf on win…”场景，保护语义向量实验测试的结果与失败边界。
- **_audit_note_storage**：审计 `note_storage` 对应的数据与约束。
- **change_documents**：`change_documents` 完成机器索引与检索包生成中的一个明确步骤。

### create_knowledge_batch_plan 相关职责

- **create_knowledge_batch_plan**：`create_knowledge_batc...` 是 `scripts/ckb_core/knowledge_batch_migration.py` 第 888-956 行定义的函数，本页绑定该固定源码范围。
- **KnowledgeBatchWorkflowTests**：`KnowledgeBatchWorkflo...` 是第 127-701 行的类，供所属页面定位实现。
- **apply_knowledge_batch_plan**：`apply_knowledge_batch...` 是第 1506-1552 行的函数，供所属页面定位实现。
- **cutover_knowledge_batch_state**：`cutover_knowledge_bat...` 是第 1883-1923 行的函数，供所属页面定位实现。
- **rollback_knowledge_batch_state**：`rollback_knowledge_ba...` 是第 2035-2075 行的函数，供所属页面定位实现。
- **_rollback_one**：`_rollback_one` 是第 1926-2032 行的函数，供所属页面定位实现。
- **KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures**：`KnowledgeBatchWorkflo...` 是第 457-575 行的函数，供所属页面定位实现。
- **audit_knowledge_batch_state**：`audit_knowledge_batch...` 是第 1623-1679 行的函数，供所属页面定位实现。

### ingest_event 相关职责

- **ingest_event**：代码单元 `ingest_event`负责接收多 Harness 事件，维持会话级 Skill 激活状态，并把待审阅事实写入机器层。
- **AutomationTest.register**：代码单元 `register`负责验证多 Harness 事件归一化、会话激活、并发采集和受控投影。
- **AutomationTest**：`setUp` 完成会话自动化回归验证中的一个明确步骤。
- **automation_status**：`automation_status` 完成多 Harness 会话自动化中的一个明确步骤。
- **drain_automation**：`drain_automation` 完成多 Harness 会话自动化中的一个明确步骤。
- **activate_skill_session**：`activate_skill_session` 登记并持久化多 Harness 会话自动化所需的数据或状态。
- **AutomationTest.test_agent_review_promotes_one_chinese_human_note**：该测试验证“agent review promotes one chi…”场景，保护会话自动化回归验证的预期结果与失败边界。
- **_automation_root**：`_automation_root` 完成多 Harness 会话自动化中的一个明确步骤。

### LspClient.stop 相关职责

- **LspClient.stop**：`stop` 受控释放或回滚语言服务器语义采集所需的数据或状态。
- **register_project**：`register_project` 登记并持久化多 Harness 会话自动化所需的数据或状态。
- **normalize_event**：`normalize_event` 解析并归一化多 Harness 会话自动化所需的数据或状态。
- **_process_event**：`_process_event` 完成多 Harness 会话自动化中的一个明确步骤。
- **AutomationTest.test_workspace_root_maps_parent_task_to_nested_repository**：该测试验证“workspace root maps parent ta…”场景，保护会话自动化回归验证的预期结果与失败边界。
- **_create_pending_review**：`_create_pending_review` 创建并初始化多 Harness 会话自动化所需的数据或状态。
- **default_registry_path**：`default_registry_path` 完成多 Harness 会话自动化中的一个明确步骤。
- **AutomationTest.test_automation_fts_finds_pending_machine_record**：该测试验证“automation fts finds pending …”场景，保护会话自动化回归验证的预期结果与失败边界。

### utc_now 相关职责

- **utc_now**：处理 `now` 对应的数据与约束。
- **audit_global**：`audit_global` 校验知识库构建与投影主流程所需的数据或状态。
- **audit_chunk**：`audit_chunk` 校验知识库构建与投影主流程所需的数据或状态。
- **review_pack**：`review_pack` 完成知识库构建与投影主流程中的一个明确步骤。
- **AuditError**：处理 `auditerror` 对应的数据与约束。
- **build_chunk**：`build_chunk` 创建并初始化知识库构建与投影主流程所需的数据或状态。
- **_replace_review_packs**：`_replace_review_packs` 是第 199-250 行的函数，供所属页面定位实现。
- **write_marker**：写入 `marker` 对应的数据与约束。

### record_note 相关职责

- **record_note**：`record_note` 位于 `scripts/ckb_core/workspace_notes.py` 第 138-210 行，本页用固定源码范围说明它如何完成该文件所属能力的输入、状态、输出和失败边界中的局部职责。
- **start_session**：`start_session` 是源码中负责管理 Agent 会话、构建中记录和修改总结落页的命名代码单元。
- **_prepare_replacement**：`_prepare_replacement` 用于完成局部输入校验、转换或状态更新。
- **review_automation**：`review_automation` 完成多 Harness 会话自动化中的一个明确步骤。
- **contains_chinese_narrative**：`contains_chinese_narrative` 完成机器索引与检索包生成中的一个明确步骤。
- **finish_session**：该附属代码负责管理 Agent 会话、构建中记录和修改总结落页，并把结果交给所属页面中的主流程使用。
- **safe_title**：处理 `title` 对应的数据与约束。
- **audit_notes**：`audit_notes` 在 `workspace_notes.py` 中用于校验输入、状态、证据或输出合同。

### run_keyword_provider 相关职责

- **run_keyword_provider**：`run_keyword_provider` 是 `scripts/ckb_core/keyword_fallback.py` 第 380-461 行定义的函数，本页绑定该固定源码范围。
- **KeywordFallbackAdapterTests**：`setUp` 完成关键词慢路径测试所需的一个明确步骤。
- **KeywordProviderConfig**：`KeywordProviderConfig` 是第 81-90 行的类，供所属页面定位实现。
- **validate_provider_response**：`validate_provider_res...` 是第 219-300 行的函数，供所属页面定位实现。
- **keyword_cache_key**：`keyword_cache_key` 是第 110-120 行的函数，供所属页面定位实现。
- **validate_provider_config**：`validate_provider_config` 是第 149-161 行的函数，供所属页面定位实现。
- **_read_cache**：`_read_cache` 是第 349-366 行的函数，供所属页面定位实现。
- **keyword_cache_path**：`keyword_cache_path` 是第 326-327 行的函数，供所属页面定位实现。

### main 相关职责

- **main**：代码单元 `main`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。
- **maintenance_check**：代码单元 `maintenance_check`负责维护外部 Wiki 能力的吸收状态，并给 Agent 生成紧凑能力说明。
- **query_graph**：`query_graph` 是源码中负责构造职责关系图并提供职责群或路径查询的命名代码单元。
- **project_graphify**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **audit_graphify**：该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。
- **capability_matrix**：`capability_matrix` 完成Wiki 能力状态维护中的一个明确步骤。
- **render_capability_matrix_markdown**：`render_capability_matrix_markdown` 生成并写入Wiki 能力状态维护所需的数据或状态。
- **_load_projected_graph**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。

### FactFreshnessStateMachineTest.test_dead_lock_is_recovered_and_concurrent_checks_serialize.inspect 相关职责

- **FactFreshnessStateMachineTest.test_dead_lock_is_recovered_and_concurrent_checks_serialize.inspect**：`inspect` 完成源码事实新鲜度回归验证中的一个明确步骤。
- **inspect_page_author**：`inspect_page_author` 用于读取、定位并返回现有状态。
- **HumanPageTemplateContract**：`HumanPageTemplateContract` 用于处理当前模块的结构化输入或状态。
- **_candidate_validation**：`_candidate_validation` 用于处理当前模块的结构化输入或状态。
- **_failed**：`_failed` 用于处理当前模块的结构化输入或状态。
- **_load_source_for_render**：`_load_source_for_render` 用于读取、定位并返回现有状态。
- **_contract_result**：`_contract_result` 用于处理当前模块的结构化输入或状态。
- **HumanMaintenancePromptRegistryTests.test_template_maps_the_existing_proposal_state_machine_but_not_page_authoring**：该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。

### ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append 相关职责

- **ManagementSchemaPersistenceTest.test_locked_registry_serializes_concurrent_audit_events.append**：代码单元 `append`负责验证跨 Harness 对话绑定、仓库预检、任务派发和管理复查。
- **DeterministicMetricTests**：该测试验证“rank metrics and missing reason…”场景，保护语义向量实验测试的结果与失败边界。
- **KeywordFallbackRetrievalWiringTests.test_stdio_exposes_the_same_nested_canonical_options**：该测试验证“stdio exposes the same nested…”场景，保护关键词慢路径测试的结果与失败边界。
- **redact_event**：`redact_event` 完成多 Harness 会话自动化中的一个明确步骤。
- **redact_event.redact**：`redact` 完成多 Harness 会话自动化中的一个明确步骤。
- **DeterministicMetricTests.test_independent_aggregate_recomputes_report_fields**：该测试验证“independent aggregate recompute…”场景，保护语义向量实验测试的结果与失败边界。
- **_redact_text**：`_redact_text` 完成多 Harness 会话自动化中的一个明确步骤。
- **build_review_packs.partition**：该附属代码负责按固定排序计算页面、附录、归属和审阅预算，并把结果交给所属页面中的主流程使用。

### bind_conversation 相关职责

- **bind_conversation**：代码单元 `bind_conversation`负责把任意 Harness 对话绑定到源码仓库和知识库，并管理独立开发任务的创建与复查。
- **ManagementBindingLifecycleTest**：`setUp` 完成管理 Agent 回归验证中的一个明确步骤。
- **management_context**：`management_context` 完成跨 Harness 管理对话绑定中的一个明确步骤。
- **unbind_conversation**：`unbind_conversation` 受控释放或回滚跨 Harness 管理对话绑定所需的数据或状态。
- **binding_status**：`binding_status` 登记并持久化跨 Harness 管理对话绑定所需的数据或状态。
- **ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object**：该测试验证“concurrent repeated bind and …”场景，保护管理 Agent 回归验证的预期结果与失败边界。
- **ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object.unbind**：`unbind` 受控释放或回滚管理 Agent 回归验证所需的数据或状态。
- **ManagementBindingLifecycleTest.test_task_dispatch_is_idempotent_and_blocks_integration_drift**：该测试验证“task dispatch is idempotent a…”场景，保护管理 Agent 回归验证的预期结果与失败边界。

### _retrieve_machine_deterministic 相关职责

- **_retrieve_machine_deterministic**：`_retrieve_machine_deterministic` 检索并组织机器索引与检索包生成所需的数据或状态。
- **_static_retrieval_context**：`_static_retrieval_context` 完成机器索引与检索包生成中的一个明确步骤。
- **_bulk_entity_context**：`_bulk_entity_context` 完成机器索引与检索包生成中的一个明确步骤。
- **_compact_entity_block**：`_compact_entity_block` 完成机器索引与检索包生成中的一个明确步骤。
- **_document_block**：`_document_block` 完成机器索引与检索包生成中的一个明确步骤。
- **_document_source_link**：`_document_source_link` 完成机器索引与检索包生成中的一个明确步骤。
- **_indexed_warning_summary**：`_indexed_warning_summary` 完成机器索引与检索包生成中的一个明确步骤。
- **_sql_placeholders**：该函数生成参数化 SQL 所需的占位符列表，并拒绝空输入。

> 为保持阅读节奏，这里只展开最主要的职责群；图查询仍会使用完整关系。

## 围绕任务继续缩小范围

```powershell
& PYTHON scripts\ckb.py query --out OUTPUT "职责关键词" --budget 1500
& PYTHON scripts\ckb.py path --out OUTPUT "起点类或函数" "目标类或函数"
& PYTHON scripts\ckb.py explain --out OUTPUT "类名、函数名或职责关键词"
```

查询会先选择与问题最相关的代码，再沿真实关系扩展到预算允许的范围。
