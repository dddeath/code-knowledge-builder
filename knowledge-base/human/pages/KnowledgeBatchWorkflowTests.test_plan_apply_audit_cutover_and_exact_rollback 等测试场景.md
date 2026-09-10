# KnowledgeBatchWorkflowTests.test_plan_apply_audit_cutover_and_exact_rollback 等测试场景

标签：#类型/代码

> 该文件验证真实历史发行矩阵、普通克隆与工作树来源访问，以及知识库批量迁移的计划、待审、切换、连续回滚和多项目隔离。 它使用完整可变层和故障注入检查迁移不损坏原库，作者包归档能跨两次切换保留，路径、清单、仓库漂移和锁冲突均在对应阶段阻断。

## 什么时候需要修改

历史版本、迁移角色、恢复拓扑或续跑状态变化时修改相应测试，保持来源核验、待审门和精确回滚的独立断言。

## 在代码中的位置

[打开源码：tests/test_knowledge_batch_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_knowledge_batch_migration.py:1:1)  `tests/test_knowledge_batch_migration.py:1-797`

## 相关代码

- 主要代码单元是 [[KnowledgeBatchWorkflowTests.test_plan_apply_audit_cutover_and_exact_rollback]]。

## 谁会来到这里

- 与 [[KnowledgeBatchWorkflowTests.test_plan_apply_audit_cutover_and_exact_rollback]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 26 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `KnowledgeBatchVersionMatrixTests` | 核对普通克隆与工作树的公共 Git 目录解析、真实历史版本矩阵以及非重标记的历史输出夹具配方。 |
| `KnowledgeBatchVersionMatrixTests.test_git_common_dir_resolves_worktree_and_ordinary_clone` | 从当前检出和新建共享普通克隆解析 Git 公共目录，并读取历史提交验证两种布局都能访问版本证据。 |
| `KnowledgeBatchVersionMatrixTests.test_matrix_uses_real_historical_releases` | 验证版本矩阵覆盖规定的真实历史发行及当前目标，并检查各版本的模式和协议组合。 |
| `KnowledgeBatchVersionMatrixTests.test_reference_matrix_matches_runtime_matrix` | 核对版本矩阵参考文档与运行时生成内容一致，防止维护两套不一致的兼容表。 |
| `KnowledgeBatchVersionMatrixTests.test_historical_output_fixture_recipes_are_not_relabelled_current_outputs` | 检查历史输出夹具配方绑定真实历史提交及版本，而不是给当前输出改标签冒充历史产物。 |
| `KnowledgeBatchWorkflowTests` | 贯通知识库批量迁移的计划、待审续跑、切换链和精确回滚，并用多项目及漂移故障验证来源保护与恢复隔离。 |
| `KnowledgeBatchWorkflowTests.setUp` | 创建已提交的小型仓库，临时启用确定性提供器并构建已完成知识库，作为每个批量迁移测试的基线。 |
| `KnowledgeBatchWorkflowTests.tearDown` | 恢复原提供器环境并清理临时目录，Windows 延迟释放文件时等待后重试清理。 |
| `KnowledgeBatchWorkflowTests._add_complete_mutable_fixture` | 加入已审阅参考、三个缺口、四十八条工作记录和两份用户笔记镜像，建立完整可变层迁移夹具。 |
| `KnowledgeBatchWorkflowTests._build_additional_output` | 为多项目测试额外构建独立仓库和已完成输出，返回源码、知识库及暂存路径。 |
| `KnowledgeBatchWorkflowTests._project_document` | 收集源库固定记录与目录摘要，绑定源目标快照、发行元组、范围和恢复目录，生成单项目迁移清单项。 |
| `KnowledgeBatchWorkflowTests._manifest` | 生成绑定允许根目录的批量迁移清单，未传项目集合时使用当前测试项目。 |
| `KnowledgeBatchWorkflowTests.test_v3_authoring_archives_survive_two_batch_cutovers_and_exact_rollback` | 删除外部作者包来源后执行两次知识库切换与逆序回滚，要求归档证据可复读、正文不变且原目录树精确恢复。 |
| `KnowledgeBatchWorkflowTests.test_partial_apply_failure_can_resume_without_touching_origin` | 在构建前注入批量迁移失败，再续跑到就绪或待审，要求整个过程不改动原知识库目录树。 |
| `KnowledgeBatchWorkflowTests.test_cold_build_has_zero_reuse_and_resume_obeys_review_gate` | 强制冷构建策略后要求源码和审阅复用数均为零，完成增量审阅后续跑才进入就绪。 |
| `KnowledgeBatchWorkflowTests.test_changed_target_commit_uses_delta_review_then_resumes_ready` | 提交目标源码修改后要求选择增量审阅且零审阅复用，提交新审阅后续跑进入就绪。 |
| `KnowledgeBatchWorkflowTests.test_two_projects_isolate_partial_apply_cutover_and_subset_rollback` | 用两个项目验证恢复拓扑、部分应用和切换失败隔离，分别重试与子集回滚而不撤销另一项目成功结果。 |
| `KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures` | 注入缺失来源记录、事实层、损坏索引、模式漂移、镜像差异和版本路径错误，核对计划阶段分类。 |
| `KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures.case_project` | 复制当前知识库为单个故障案例，并绑定对应暂存目录生成项目清单项。 |
| `KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures.refresh` | 按故障后的输出重新计算目录摘要和指定记录哈希，使测试聚焦目标故障而非外围清单漂移。 |
| `KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures.plan_for` | 为单个故障项目写入独立批量清单并返回只读计划判定。 |
| `KnowledgeBatchWorkflowTests.test_origin_records_are_exact_fixed_keys_before_any_external_read` | 注入越界或非规范来源记录键，要求任何外部文件读取前按固定键集合拒绝，并核对模式文档一致。 |
| `KnowledgeBatchWorkflowTests.test_origin_records_are_exact_fixed_keys_before_any_external_read.guarded` | 记录被请求读取的来源相对路径，断言其属于固定必需集合后再调用真实文件记录函数。 |
| `KnowledgeBatchWorkflowTests.test_recovery_topology_rejects_same_root_before_any_transaction_write` | 把备份和隔离根设置为同一目录，要求计划在任何事务、状态或暂存写入前拒绝恢复目标重叠。 |
| `KnowledgeBatchWorkflowTests.test_apply_rejects_manifest_origin_and_repository_drift_before_staging_write` | 分别改变计划清单、原库正文和仓库脏状态，要求应用或续跑在暂存写入前报告对应漂移。 |
| `KnowledgeBatchWorkflowTests.test_owner_token_lock_serializes_apply_and_cutover_then_allows_retry` | 持有输出锁时分别尝试应用与切换，要求并发失败，释放后可续跑、切换并回滚。 |

</details>
