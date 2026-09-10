# ProvenanceTests.setUp 等测试场景

标签：#类型/代码

> 该文件使用真实小型 Git 仓库验证知识库迁移中的快照注册、明确引用的证据保留、作者包归档、Windows 路径与隐藏属性，以及目录切换后的参考来源和历史事务字节。 它把文件计数之外的来源完整性变成回归断言，覆盖连续迁移和改名、缺失证据提前失败、SQLite 读取句柄释放、说明性路径不作为归档根，以及旧事务不可跨输出静默重放。

## 什么时候需要修改

源码快照重定位、证据闭包、作者包和事务归档、Windows 文件打开或参考路径重绑定变化时修改此文件，并保留原字节、精确来源及错误前置检查。

## 在代码中的位置

[打开源码：tests/test_recruitment_migration_provenance.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_recruitment_migration_provenance.py:1:1)  `tests/test_recruitment_migration_provenance.py:1-937`

## 相关代码

- 主要代码单元是 [[ProvenanceTests.setUp]]。

## 谁会来到这里

- 与 [[ProvenanceTests.setUp]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 47 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `git` | 在测试仓库禁用自动垃圾回收和维护后执行 Git 命令，按可选检查参数传播失败并返回完整执行结果。 |
| `ProvenanceTests` | 通过真实小仓库验证快照移动注册、被引用证据闭包、参考提取来源和连续迁移的路径与原文字节保留。 |
| `ProvenanceTests.test_snapshot_registration_survives_two_renames_cleanup_and_rollback` | 连续移动固定快照并清理另一临时工作树，要求反向注册、提交和锁保持有效，最终 Git 指针文件恢复原字节。 |
| `ProvenanceTests.test_relocation_repairs_relative_gitdir_after_depth_change` | 将快照 Git 管理目录改为相对路径后改变目录深度，要求重定位修复指针及反向注册。 |
| `ProvenanceTests.test_dirty_or_foreign_registration_fails_before_backlink_write` | 分别制造脏快照和外来反向注册，要求重定位在写回管理指针前失败并保留原字节。 |
| `ProvenanceTests.evidence_fixture` | 构造记录、缺口、参考和 Markdown 链接引用的嵌套证据，同时加入未引用缓存与目录状态对照。 |
| `ProvenanceTests.test_preserves_only_referenced_machine_evidence_and_original_notes` | 迁移时只保存明确引用的机器证据及原笔记，排除未引用阅读包和旧机器索引，并重绑定可变元数据路径。 |
| `ProvenanceTests.test_missing_required_evidence_fails_without_empty_substitute` | 删除必需引用证据后要求迁移保留失败，不生成空文件冒充原证据。 |
| `ProvenanceTests.test_prefix_relocation_does_not_rewrite_sibling_or_original_prose` | 核对输出路径替换遵守目录边界，不改写同前缀兄弟目录和中文原文中的路径文字。 |
| `ProvenanceTests.test_pdf_and_static_web_relocation_preserves_extraction_provenance` | 迁移原生 PDF 与静态网页提取证据并反复改名，要求原文及提取核验保持有效，损坏清单不得重算哈希接受。 |
| `ProvenanceTests.test_two_migrations_reproject_reference_and_navigation_at_target` | 连续迁移并改名后要求参考与导航链接指向新输出，同时保留归档原文、明确引用证据及用户笔记原字节。 |
| `ProvenanceTests.test_two_migrations_reproject_reference_and_navigation_at_target.assert_reference_sources` | 解析参考页中的本地来源 URI，核对目标位于当前输出、文件存在且原文相等，并排除旧输出路径残留。 |
| `create_v3_record` | 生成带本地机器证据和历史来源 URI 的有效作者包，再通过受控记录入口写入 V3 变更记录。 |
| `V3AuthoringMigrationTests` | 验证 V3 作者包跨连续迁移、改名和目录回退仍可独立复核，缺失或漂移证据必须在创建暂存前失败。 |
| `V3AuthoringMigrationTests.setUp` | 创建已完成小型知识库与外部 V3 作者包，保存包基线并加入不应被复制的无关文件。 |
| `V3AuthoringMigrationTests.assert_package` | 复读迁移后作者包所有文件与原字节比较，重新验证章节证据及上下文与记录元数据一致。 |
| `V3AuthoringMigrationTests.test_real_v3_record_survives_two_migrations_rename_maintain_and_rollback` | 删除原外部包后连续迁移与改名，要求正文和归档证据不变，最后篡改正文必须令维护及迁移审计失败。 |
| `V3AuthoringMigrationTests.test_missing_drifted_or_detached_metadata_fails_before_staging_write` | 逐项删除或篡改作者包正文、清单、证据和上下文，要求普通迁移与冷构建在暂存创建前阻断。 |
| `V3AuthoringMigrationTests.test_workspace_package_is_preserved_without_mutating_signed_context` | 把作者包放入输出内工作区再迁移，核对归档仍精确保留且签名上下文不被路径重写。 |
| `WindowsHiddenSnapshotTests` | 验证 Windows 固定快照指针采用非截断写入，目录深度变化后仍保留隐藏属性和有效 Git 注册。 |
| `WindowsHiddenSnapshotTests.test_existing_gitfile_update_uses_nontruncating_open` | 模拟隐藏 Git 指针文件拒绝截断打开，要求重定位使用读写模式修复且提交仍正确。 |
| `WindowsHiddenSnapshotTests.test_existing_gitfile_update_uses_nontruncating_open.open_existing` | 记录目标 Git 指针文件的打开模式，遇到截断写入模式即注入权限错误，其余交给真实文件打开。 |
| `WindowsHiddenSnapshotTests.test_hidden_relative_gitfile_survives_depth_change_and_keeps_attribute` | 设置真实 Windows 隐藏属性后移动相对 Git 指针，核对属性、提交和反向注册均保持有效。 |
| `SQLiteGapAuditLifecycleTests` | 跟踪缺口审计的 SQLite 读取连接，验证正常和异常路径显式关闭，随后可在同进程重建与替换索引。 |
| `SQLiteGapAuditLifecycleTests.setUp` | 建立已完成测试输出并准备缺口说明和机器证据，供读取连接生命周期探针使用。 |
| `SQLiteGapAuditLifecycleTests.track_gap_connections` | 仅拦截缺口审计创建的 SQLite 连接，保留连接对象以防垃圾回收掩盖遗漏关闭，并可注入查询错误。 |
| `SQLiteGapAuditLifecycleTests.track_gap_connections.TrackedConnection` | 扩展 SQLite 连接以记录显式关闭，并按开关在模式查询时注入错误。 |
| `SQLiteGapAuditLifecycleTests.track_gap_connections.TrackedConnection.close` | 标记连接已由所有者关闭，再执行基类关闭逻辑。 |
| `SQLiteGapAuditLifecycleTests.track_gap_connections.TrackedConnection.execute` | 按故障开关在数据库模式查询时抛出操作错误，其他 SQL 交给基类执行。 |
| `SQLiteGapAuditLifecycleTests.track_gap_connections.connect` | 识别直接调用者为缺口审计时使用跟踪连接并保存引用，其余连接保持原实现。 |
| `SQLiteGapAuditLifecycleTests.test_create_gap_releases_reader_before_record_and_same_process_replace` | 创建缺口后验证读取连接已关闭且不可再查询，并要求后续记录、索引重建与同进程文件替换成功。 |
| `SQLiteGapAuditLifecycleTests.test_gap_audit_query_exception_also_closes_reader` | 在缺口审计查询时注入异常，要求读取连接仍被显式关闭且机器索引可随后重建。 |
| `ReferenceWindowsPrefixTests` | 验证 Windows 历史路径的反斜杠与混合分隔符重绑定，保留原文和审阅字节并拒绝漂移来源。 |
| `ReferenceWindowsPrefixTests.test_windows_history_prefix_matches_backslash_and_mixed_paths` | 核对历史 Windows 路径的混合分隔符可重绑定，同时不改写原文、同前缀兄弟目录和签名上下文。 |
| `ReferenceWindowsPrefixTests.test_windows_history_reference_reprojects_existing_raw_and_review_bytes` | 将参考清单指向旧 Windows 路径后恢复现存归档绑定，要求原文与审阅字节不变，来源损坏时拒绝重新信任。 |
| `MigrationDirectoryDescriptionTests` | 区分目录说明与正式证据链接，要求迁移不复制未引用缓存树，而明确引用的缺失文件必须提前阻断。 |
| `MigrationDirectoryDescriptionTests.setUp` | 构造含目录、临时索引和未生成路径说明的笔记及未引用缓存，供证据闭包边界测试。 |
| `MigrationDirectoryDescriptionTests.test_existing_directory_description_migrates_without_copying_cache_tree` | 迁移仅作说明的目录与路径文字，要求笔记原字节保留且不复制阅读包缓存或旧临时索引。 |
| `MigrationDirectoryDescriptionTests.test_explicit_archives_from_links_and_machine_fields_are_preserved` | 加入真实 Markdown 来源链接和缺口证据字段，要求只保存被明确引用的归档文件。 |
| `MigrationDirectoryDescriptionTests.test_missing_explicit_markdown_source_link_fails_before_staging` | 添加指向缺失机器证据的正式 Markdown 链接，要求迁移在创建暂存目录前失败。 |
| `MigrationDirectoryDescriptionTests.test_explicit_missing_evidence_file_still_fails_before_staging` | 删除正式缺口引用的证据文件，要求迁移前置检查失败且不创建暂存目录。 |
| `MigrationDirectoryDescriptionTests.test_explicit_file_field_referencing_a_directory_still_fails` | 把要求文件的检索记录字段指向目录，要求迁移判为缺失必需文件而不是复制目录树。 |
| `MigrationTransactionArchiveTests` | 验证多次记录替换的历史事务作为不可变归档迁移，当前证据根与已消费排队记录的历史引用分开计算。 |
| `MigrationTransactionArchiveTests.setUp` | 创建有旧检索依据的记录后连续替换两次，保存事务历史字节并删除仅历史记录引用的阅读包。 |
| `MigrationTransactionArchiveTests.test_two_replacements_migrate_current_record_and_freeze_transaction_history` | 迁移及改名后要求当前正文和历史事务原字节保留，禁止跨输出回放旧事务，并检测历史归档篡改。 |
| `MigrationTransactionArchiveTests.test_pending_record_is_a_root_until_materialization_finishes` | 验证待落页记录仍要求其证据根，落页完成并解绑缺失可选阅读包后该队列只作为历史记录。 |
| `MigrationTransactionArchiveTests.test_same_missing_pack_is_required_when_current_record_or_formal_gap_references_it` | 将同一缺失阅读包重新绑定到当前记录或正式缺口，要求迁移在暂存创建前失败。 |

</details>
