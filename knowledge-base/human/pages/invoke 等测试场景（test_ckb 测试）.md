# invoke 等测试场景（test_ckb 测试）

标签：#类型/代码

> 提供多语言固定快照建库、审阅完成门、检索与维护链路的集成测试及 C++ 解析边界测试。 以临时 Git 仓库和确定性服务替身覆盖真实命令与文件结果；同时核对插件部署、参考资料、双镜像和局部语法警告，不将替身断言等同实际模型或界面验证。

## 什么时候需要修改

建库协议、来源完整性、检索预算、可变知识写入或发行绑定规则变化时修改对应测试与夹具。

## 在代码中的位置

[打开源码：tests/test_ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb.py:1:1)  `tests/test_ckb.py:1-2499`

## 相关代码

- 主要代码单元是 [[invoke（test_ckb 测试）]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 54 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `write` | 创建父目录并以 UTF-8 和固定末尾换行写入测试文本。 |
| `git` | 在指定测试仓库执行 Git 命令，退出失败时抛出捕获的错误信息。 |
| `make_repo` | 创建含多语言调用与排除目录的测试仓库，并提交初始固定快照。 |
| `review_all` | 构建全部测试分段，填入确定性审阅夹具并提交各包，失败时抛出完整诊断。 |
| `CodeKnowledgeBuilderTests` | 组织临时仓库上的建库、检索、参考资料、插件和维护集成测试，覆盖完成门与反例。 |
| `CodeKnowledgeBuilderTests.setUp` | 为每个集成用例创建临时根目录和已提交的多语言样例仓库。 |
| `CodeKnowledgeBuilderTests.tearDown` | 清理当前集成用例的临时目录。 |
| `CodeKnowledgeBuilderTests.test_noninteractive_subprocesses_use_the_platform_background_flag` | 核对平台后台进程参数，并用调用替身断言公共命令入口传递该参数。 |
| `CodeKnowledgeBuilderTests.test_bounded_machine_operation_journal_is_private_deduplicated_and_audited` | 验证机器操作日志固定字段、隐私过滤、去重和容量上限，并检测篡改字段。 |
| `CodeKnowledgeBuilderTests.test_research_gap_register_is_machine_only_deduplicated_and_resolvable` | 验证研究缺口仅入机器层、去重和证据关闭，并检查单一导览入口与模式篡改。 |
| `CodeKnowledgeBuilderTests.test_llm_wiki_capability_matrix_has_closed_four_state_boundaries` | 检查能力矩阵四态、字段完整性和条目标识唯一性，并核对文档与渲染器一致。 |
| `CodeKnowledgeBuilderTests.test_reviewed_text_reference_is_searchable_revisioned_and_reversible` | 验证参考资料审阅、精确引文、检索、版本替换与回滚，并覆盖缺口来源和失败门。 |
| `CodeKnowledgeBuilderTests.test_empty_document_symbols_are_not_a_provider_failure` | 断言空符号结果仍可通过，而实际服务诊断错误才判为失败。 |
| `CodeKnowledgeBuilderTests.test_python_attribute_accessors_stay_in_the_file_appendix` | 构造模块属性访问函数，断言其被硬排除为所属文件附录。 |
| `CodeKnowledgeBuilderTests.test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server` | 用检索与记录替身验证逐行协议、异常文本修复、错误隔离和关闭后停止响应。 |
| `CodeKnowledgeBuilderTests.test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server.fake_retrieve` | 记录检索调用参数并返回固定路径与模拟缓存状态，用于标准输入输出协议测试。 |
| `CodeKnowledgeBuilderTests.test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server.fake_record` | 记录解释写入调用并返回固定结果，验证请求与检索响应的绑定。 |
| `CodeKnowledgeBuilderTests.test_record_explanation_writes_utf8_machine_evidence_not_analysis_page` | 在审计替身下验证中文解释写入机器证据，且不生成分析页面。 |
| `CodeKnowledgeBuilderTests.test_obsidian_plugin_package_can_be_registered_deployed_and_removed` | 注册并部署测试插件包，核对启用列表与输出契约，最后验证卸载清除。 |
| `CodeKnowledgeBuilderTests.test_obsidian_plugin_deploy_falls_back_when_vault_directory_is_locked` | 模拟文件替换权限错误，断言插件部署采用原位复制且包文件内容正确。 |
| `CodeKnowledgeBuilderTests.test_obsidian_output_contract_is_not_required_without_installed_plugin` | 断言未安装插件的库既不投影输出契约，也不把缺少契约视为审计错误。 |
| `CodeKnowledgeBuilderTests.test_non_git_path_reminds_then_opt_in_creates_one_initial_commit` | 验证非 Git 目录默认仅提醒，显式启用才建立一次初始提交且重复初始化不追加。 |
| `CodeKnowledgeBuilderTests.test_unborn_git_repo_requires_opt_in_and_existing_dirty_repo_is_not_committed` | 验证无提交仓库需显式初始化，而已有脏仓库保持原提交且不创建输出。 |
| `CodeKnowledgeBuilderTests.test_fast_run_can_bootstrap_non_git_source_and_stops_for_review` | 验证快速运行可显式建立初始提交后停在审阅门，恢复阶段拒绝再次初始化 Git。 |
| `CodeKnowledgeBuilderTests.test_feedback_anchor_mirroring_audit_and_archive_are_deterministic` | 验证反馈锚点重定位、双镜像和决议归档，并检测失效锚点及缺少落实记录的采纳。 |
| `CodeKnowledgeBuilderTests.test_work_record_index_covers_every_note_with_one_chinese_summary` | 验证工作记录导览覆盖全部笔记、每项保留中文摘要且双镜像一致。 |
| `CodeKnowledgeBuilderTests.test_markdown_whole_repository_and_completion_gate` | 贯穿整库完成门、双镜像和机器检索，验证受控记录、维护不改页及漂移检测。 |
| `CodeKnowledgeBuilderTests.test_local_scope_has_one_hop_boundary` | 验证局部文件范围只引入一跳相邻实体，不扩张为整个相邻文件。 |
| `CodeKnowledgeBuilderTests.test_entry_scope_uses_fixed_snapshot_while_live_worktree_changes` | 验证入口范围使用固定快照，并让构建期间排队的会话在投影完成后落页与回链。 |
| `CodeKnowledgeBuilderTests.test_review_set_mismatch_fails` | 删除一个审阅实体后提交，断言实体集合不匹配触发失败标记。 |
| `CodeKnowledgeBuilderTests.test_runtime_plan_lite` | 检查轻量运行时计划的允许状态，并核对内置图分析依赖版本。 |
| `CodeKnowledgeBuilderTests.test_obsidian_companion_distribution_reuses_pinned_claudian` | 核对插件发行清单、锁定上游和关键补丁标记，保持源码复用与独立部署边界。 |
| `CodeKnowledgeBuilderTests.test_required_format_duplicate_entry_and_syntax_stage` | 验证输出格式必填、重复入口给出候选诊断，并可单独执行语法阶段。 |
| `CodeKnowledgeBuilderTests.test_oversized_file_splits_on_declarations_without_duplicate_ids` | 构造大量声明，验证解析批次内标识唯一且审阅包按配额拆分。 |
| `CodeKnowledgeBuilderTests.test_both_projection_parity_with_cli_contract_double` | 借助 Logseq 命令替身验证双投影归属、来源清单与规范化内容一致。 |
| `CodeKnowledgeBuilderTests.test_logseq_only_projection_has_format_neutral_agent_index` | 借助命令替身验证仅 Logseq 模式仍生成格式中立索引、中文镜像和来源链接。 |
| `CodeKnowledgeBuilderTests.test_english_only_agent_review_is_rejected` | 提交纯英文审阅字段，断言实质中文审阅合同校验失败。 |
| `CodeKnowledgeBuilderTests.test_navigation_page_quota_relation_budget_and_context_bundle` | 验证默认页面配额、模块上下文预算和直接关系截断汇总。 |
| `CodeKnowledgeBuilderTests.test_page_configuration_controls_quotas_content_and_is_pinned` | 验证自定义页面配额与章节进入固定配置，并检测配置漂移和缺失必备章节。 |
| `CodeKnowledgeBuilderTests.test_csharp_project_selection_partial_types_and_generated_exclusions` | 验证 C# 项目唯一选择、分部类型合并与生成文件排除，并拒绝多解决方案歧义。 |
| `CodeKnowledgeBuilderTests.test_csharp_property_and_enum_land_in_class_or_file_aggregation` | 验证 C# 属性归入类型附录、枚举归入文件附录，而非独立职责页。 |
| `CodeKnowledgeBuilderTests.test_fallback_standard_derivation_and_stable_ids` | 验证构建文件中的语言标准推导，以及相同输入标识稳定、范围变化标识不同。 |
| `CppParserAndSconsTests` | 覆盖 C++ 局部解析恢复、警告传播及 SCons 标准推导，区分近似与编译数据库精确模式。 |
| `CppParserAndSconsTests.setUp` | 创建 C++ 解析和构建配置测试的临时根目录。 |
| `CppParserAndSconsTests.tearDown` | 清理 C++ 解析测试的临时目录。 |
| `CppParserAndSconsTests.parse_fixture` | 读取指定 C++ 夹具原始字节，构造固定测试来源并调用解析入口。 |
| `CppParserAndSconsTests.test_cpp_conditional_compilation_valid_and_incomplete` | 验证条件编译的有效函数范围与不完整输入的局部警告状态。 |
| `CppParserAndSconsTests.test_cpp_reference_direct_initialization_is_declaration_not_function` | 验证引用直接初始化被识别为局部声明而非函数，并保留不完整输入诊断。 |
| `CppParserAndSconsTests.test_cpp_explicit_template_instantiation_has_no_pseudo_entities` | 验证显式模板实例化不产生伪实体，可恢复形式与大范围错误分别判定。 |
| `CppParserAndSconsTests.test_cpp_local_diagnostic_contract_marks_only_affected_ranges_and_blocks_broad_errors` | 验证局部诊断只降低受影响范围置信度，而大范围错误阻止可用解析。 |
| `CppParserAndSconsTests.test_cpp_parser_dependency_and_root_unavailable_still_fail` | 模拟解析依赖缺失和语法树根缺失，断言入口继续抛出明确错误。 |
| `CppParserAndSconsTests.test_cpp_local_warning_reaches_status_machine_index_and_brief` | 验证局部 C++ 警告贯穿状态、语法阶段、图、机器索引及紧凑阅读包。 |
| `CppParserAndSconsTests.test_cpp_broad_syntax_error_still_blocks_syntax_stage` | 构造大范围语法错误，断言语法阶段失败并保留根节点不可用原因。 |
| `CppParserAndSconsTests.test_scons_fallback_is_auditable_and_compile_database_stays_exact` | 验证 SCons 标准证据、缺失或歧义回退，以及编译数据库优先的精确模式。 |

</details>
