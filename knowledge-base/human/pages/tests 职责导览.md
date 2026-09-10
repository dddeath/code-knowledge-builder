# tests 职责导览

标签：#类型/职责

> 这里汇集 tests 范围内彼此协作的类、函数和辅助实现。

## 相关代码

- 继续浏览 [[AutomationTest.register 等测试场景]]。
- 继续浏览 [[Box 等测试场景（explicit-instantiation-valid 测试）]]。
- 继续浏览 [[Box 等测试场景（main 测试）]]。
- 继续浏览 [[CanvasBenchmarkContractTests.test_judge_owns_page_source_and_range_verdict 等测试场景]]。
- 继续浏览 [[CanvasContractTests.test_each_request_object_layer_rejects_unknown_field_with_exit_…]]。
- 继续浏览 [[CanvasDeterminismTests 等测试场景]]。
- 继续浏览 [[CanvasGraphTests 等测试场景]]。
- 继续浏览 [[CanvasPathTests.test_corrupt_request_and_record_emit_one_failure_object_without_tra…（tests/test_ckb_canvas_paths.py:1）]]。
- 继续浏览 [[CanvasRollbackTests 等测试场景]]。
- 继续浏览 [[CanvasTransactionTests.test_promotion_detects_concurrent_canvas_and_preserves_exter…（tests/test_ckb_canvas_transaction.py:1）]]。
- 继续浏览 [[ChineseRetrievalEffectRetestFixtureTests.test_source_corpus_drift_fails_without_dam…（tests/test_chinese_retrieval_fixture.py:1）]]。
- 继续浏览 [[DeploymentPreservationTests.assert_preserved 等测试场景]]。
- 继续浏览 [[HumanMaintenancePromptCliTests.test_audit_exit_status_is_zero_only_for_verified_com…（tests/test_human_maintenance_prompts.py:1）]]。
- 继续浏览 [[HumanPageAuthoringRenderTests.test_revise_separates_human_summary_from_machine_evid…（tests/test_human_page_authoring.py:1）]]。
- 继续浏览 [[HumanPageTemplateValidationTests.test_every_page_type_accepts_one_minimal_v3_docume…（tests/test_human_page_templates.py:1）]]。
- 继续浏览 [[IncrementalRecordReplaceTests.prepare_dangling 等测试场景]]。
- 继续浏览 [[KeywordRealProviderBenchmarkTests 等测试场景]]。
- 继续浏览 [[KnowledgeBatchWorkflowTests.test_plan_apply_audit_cutover_and_exact_rollback 等测试场景]]。
- 继续浏览 [[PackageReleaseTests 等测试场景]]。
- 继续浏览 [[PageFanoutBenchmarkTests.test_blinded_judge_recomputes_fixed_task_and_integrity_met…（tests/test_ckb_page_fanout_benchmark.py:1）]]。
- 继续浏览 [[PageFanoutGeneratorTests.test_non_entailed_chinese_claim_stops_without_residue 等测试场景]]。
- 继续浏览 [[PdfReferenceEndToEndTests.test_pdf_ingest_review_audit_indexes_and_rollback 等测试场景]]。
- 继续浏览 [[ProvenanceTests.setUp 等测试场景]]。
- 继续浏览 [[QmdAvailabilityAndFailureTests.test_qmd_process_failure_is_not_treated_as_a_result…]]。
- 继续浏览 [[QueryTermsTests 等测试场景]]。
- 继续浏览 [[RealVaultStudyTests.setUp 等测试场景]]。
- 继续浏览 [[RecordReplaceTests.test_replace_updates_every_role_and_rollback_is_exact_and_idempo…（tests/test_record_replace.py:1）]]。
- 继续浏览 [[ReferenceMarkerMigrationTests.migrate_failed_reference_marker 等测试场景]]。
- 继续浏览 [[ReferencePdfEffectBenchmarkTests 等测试场景]]。
- 继续浏览 [[ReferencePdfOcrFidelityBenchmarkTests.test_frozen_protocol_binds_distinct_native_sc…（tests/test_reference_pdf_ocr_fidelity_benchmark.py:1）]]。
- 继续浏览 [[SQLiteNarrativeBoundaryTests 等测试场景]]。
- 继续浏览 [[ScopeExtensionOfferTests.retrieval 等测试场景]]。
- 继续浏览 [[TagNavigationBenchmarkTests 等测试场景]]。
- 继续浏览 [[TagNavigationProjectionTests 等测试场景]]。
- 继续浏览 [[TagNavigationRollbackTests.test_present_target_returns_to_byte_identical_baseline 等…]]。
- 继续浏览 [[TagNavigationStateMachineTests.by_tag 等测试场景]]。
- 继续浏览 [[TemplateProposalStoreTests.test_concurrent_writers_preserve_unique_events_and_repla…（tests/test_human_page_template_proposals.py:1）]]。
- 继续浏览 [[WebReferenceEndToEndTests.test_static_ingest_review_drift_duplicate_audit_and_rollb…（tests/test_reference_web.py:1）]]。
- 继续浏览 [[aggregate 等测试场景]]。
- 继续浏览 [[ascii_pdf 等测试场景]]。
- 继续浏览 [[assertions 等测试场景]]。
- 继续浏览 [[build_case 等测试场景]]。
- 继续浏览 [[clickNode 等测试场景]]。
- 继续浏览 [[contract_errors 等测试场景]]。
- 继续浏览 [[create_protocol_fixture 等测试场景]]。
- 继续浏览 [[debug_value 等测试场景]]。
- 继续浏览 [[digest_tree 等测试场景]]。
- 继续浏览 [[empty_ocr_adapter 等测试场景]]。
- 继续浏览 [[entity 等测试场景]]。
- 继续浏览 [[execute 等测试场景]]。
- 继续浏览 [[fake_qmd_adapter 等测试场景]]。
- 继续浏览 [[fixture_output 等测试场景]]。
- 继续浏览 [[generate 等测试场景]]。
- 继续浏览 [[git 等测试场景（test_git_fact_freshness 测试）]]。
- 继续浏览 [[git 等测试场景（test_management_agent 测试）]]。
- 继续浏览 [[git 等测试场景（test_migration 测试）]]。
- 继续浏览 [[graph 等测试场景]]。
- 继续浏览 [[historical_output 等测试场景]]。
- 继续浏览 [[invoke 等测试场景（test_ckb 测试）]]。
- 继续浏览 [[invoke 等测试场景（test_recruitment_output_contract 测试）]]。
- 继续浏览 [[keyword_provider 等测试场景]]。
- 继续浏览 [[layout_text 等测试场景]]。
- 继续浏览 [[load_module 等测试场景]]。
- 继续浏览 [[main 等测试场景（benchmark_obsidian_canvas_navigation 测试）]]。
- 继续浏览 [[main 等测试场景（generate_large_fixture 测试）]]。
- 继续浏览 [[main 等测试场景（session_stdio_harness_probe 测试）]]。
- 继续浏览 [[main 等测试场景（session_stdio_reactivation_probe 测试）]]。
- 继续浏览 [[make_output 等测试场景]]。
- 继续浏览 [[one_cycle 等测试场景]]。
- 继续浏览 [[option 等测试场景]]。
- 继续浏览 [[resolve_checkout_git_dir 等测试场景]]。
- 继续浏览 [[review_all 等测试场景]]。
- 继续浏览 [[run 等测试场景]]。
- 继续浏览 [[run_benchmark 等测试场景（benchmark_chinese_retrieval 测试）]]。
- 继续浏览 [[run_benchmark 等测试场景（benchmark_keyword_real_provider 测试）]]。
- 继续浏览 [[run_benchmark 等测试场景（benchmark_reference_pdf_effect 测试）]]。
- 继续浏览 [[run_probe 等测试场景]]。
- 继续浏览 [[sample 等测试场景]]。
- 继续浏览 [[score 等测试场景]]。
- 继续浏览 [[searchAndOpen 等测试场景]]。
- 继续浏览 [[slow_ocr_adapter 等测试场景]]。
- 继续浏览 [[source_value 等测试场景]]。

## 谁会来到这里

- 可从 [[source 代码导览]] 进入本页。
