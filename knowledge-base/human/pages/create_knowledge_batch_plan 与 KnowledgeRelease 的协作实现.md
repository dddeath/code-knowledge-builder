# create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现

标签：#类型/代码

> 通过显式清单批量迁移已完成知识库，记录每个项目的计划、迁移或冷启动、待审、审计、切换和回滚结果，并允许失败项目单独恢复。 计划固定旧输出全树、关键记录、版本链、目标快照与路径边界；执行复用既有迁移和审阅门。切换使用输出目录外的所属锁、备份及控制记录，只有暂存审计和摘要仍匹配才提升；回滚拒绝正式输出、协议或备份漂移，并保留被替换版本与操作父链。

## 什么时候需要修改

修改历史版本矩阵、迁移策略、可变层保全或路径拓扑时，联动项目预检与完整审计；切换/回滚流程变化须同时检查快照注册修复、协议备份、目录改名故障恢复和状态幂等规则。

## 在代码中的位置

[打开源码：scripts/ckb_core/knowledge_batch_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_batch_migration.py:1:1)  `scripts/ckb_core/knowledge_batch_migration.py:1-2101`

## 相关代码

- 与 [[BatchProjectError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[BatchProjectError 与 ProtocolRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_agent_protocol]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_agent_protocol 与 _default_python 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_gap 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[create_knowledge_batch_plan]]。
- 与 [[ingest_web_reference 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[migrate_output]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[migrate_output 与 _entity_key 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[preflight 与 git 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_operation 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[start_scope_extension 与 _error 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[create_knowledge_batch_plan]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 62 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `KnowledgeRelease` | 保存发行版本对应的核心、协议、机器库 schema、源码提交、下一版本及兼容迁移标记。 |
| `_canonical_bytes` | 按固定键排序和紧凑 JSON 格式生成保留中文的 UTF-8 字节。 |
| `_digest_value` | 对规范化 JSON 字节计算 SHA-256，形成计划或清单的稳定摘要。 |
| `_reject_unknown` | 比较对象键与允许字段集合，发现未知键时报告所在清单位置。 |
| `_object` | 要求清单指定位置为字典对象，类型不符时直接报错。 |
| `_absolute` | 要求非空绝对路径，展开用户目录并解析为规范路径，拒绝相对路径。 |
| `_within_any` | 检查路径是否位于任一显式允许根内部，返回布尔值。 |
| `_normalized_protocol` | 将空值及 none/absent 标记统一为无协议，其余值转换为协议字符串。 |
| `_release_for` | 同时匹配核心、schema、规范协议和源码提交，只有冻结矩阵中唯一发行记录匹配时才返回该记录。 |
| `_release_chain` | 沿冻结发行表的下一版本链接生成升级链，缺失节点、断链或循环时明确失败。 |
| `knowledge_version_matrix` | 确认当前版本在冻结迁移矩阵中后，导出各历史发行的兼容性、协议、数据库版本和后继关系。 |
| `_validate_version` | 核验版本描述的允许键、核心版本字符串、正 schema、可空协议及完整提交标识。 |
| `_validate_snapshot` | 核验快照对象只含合法完整的 Git 提交与目录树标识，并返回这两个字段。 |
| `_validate_tree_summary` | 要求全树摘要使用固定算法、非负文件与字节数及有效小写哈希，返回独立摘要副本。 |
| `_validate_structural_manifest` | 校验批次和项目标识、允许根及项目数，拒绝越界和重复嵌套的输出/暂存目录，返回规范根与项目列表。 |
| `load_knowledge_batch_manifest` | 读取存在的批量知识库清单 JSON 对象，并在返回前执行完整结构校验。 |
| `_file_record` | 记录知识库内一个相对文件是否存在，以及存在时的字节大小和 SHA-256。 |
| `_origin_health` | 检查旧输出完成标记、图与实体审阅、双库完整性、事实层和人类镜像，汇总各项健康结果及读取的关键记录。 |
| `_origin_health.check` | 向旧输出健康检查列表追加名称、布尔通过状态、类别和详情。 |
| `_complete_layer_inventory` | 在基础分层清单上补充用户笔记镜像哈希、资料文件、反馈和操作记录数量及自动化和协议文件存在性。 |
| `_sqlite_schema_versions` | 只读打开机器与兼容 SQLite，读取 meta 中的 schema 版本，缺失或读取错误时该项返回 None。 |
| `_normalized_scope` | 规范范围路径、入口、展开方向和 C# 选项，拒绝未知键、负深度及非法方向。 |
| `_path_risks` | 列出字符串长度超过指定上限的路径，并记录实际长度与限制。 |
| `_operation_token` | 以操作标识和项目标识计算哈希前二十位，生成恢复目录使用的短令牌。 |
| `_project_operation_id` | 将批次标识、项目标识、旧树哈希和目标提交绑定成项目迁移操作身份。 |
| `_paths_overlap` | 判断两个路径是否相同或相互嵌套，作为目录冲突判定。 |
| `_validate_recovery_topology` | 验证备份与隔离恢复根在允许范围内，且不与任何输出/暂存路径及其他项目恢复目标重叠。 |
| `_validate_origin_record_keys` | 要求旧记录映射恰好包含固定八个键，并拒绝反斜线、绝对路径或非规范相对路径。 |
| `_inspect_knowledge_project` | 核验项目路径、旧输出哈希和健康、目标快照及发行链，依据允许策略选择兼容迁移、冷启动、待审或失败。 |
| `_load_knowledge_batch_plan` | 读取计划并核验 schema 与正文摘要，摘要比较排除 plan_digest 和辅助 plan_path 字段。 |
| `_verify_plan_manifest_binding` | 重新读取清单、规范项目与允许根并复查恢复拓扑，确认其摘要仍与已生成计划一致。 |
| `_save_knowledge_state` | 刷新批量迁移状态的更新时间并将状态对象写入 JSON。 |
| `_load_knowledge_state` | 读取迁移状态并校验 schema 与 state 绝对路径绑定，拒绝缺失或被移动冒用的状态文件。 |
| `_state_event` | 追加带稳定标识、项目、动作、状态和时间的迁移事件，并裁剪最早记录以保持固定容量。 |
| `_new_knowledge_state` | 从不可变计划建立批量执行状态，将可行动项目设为 pending，保留各项目路径、摘要和失败信息并绑定计划与状态路径。 |
| `_summarize_knowledge_state` | 依据各项目完成、待审、失败或回滚状态，按固定优先顺序计算批次整体状态。 |
| `_manifest_matches` | 比较全树清单的算法、文件数、字节数、总哈希和逐文件记录是否全部一致。 |
| `_manifest_delta` | 比较两份文件清单，返回缺失、新增及大小或哈希变化的路径和双方总摘要。 |
| `_verify_plan_bindings` | 重新核对旧输出完整清单与目标仓库干净 commit/tree，任一偏离计划时抛出分类漂移错误。 |
| `_knowledge_output_lock` | 在输出目录旁建立稳定锁锚点并复用所属令牌锁，避免目录改名时内部打开的锁文件阻碍切换。 |
| `_detach_staging_workspace_roots` | 将暂存协议记录的外部工作区绑定清空，更新运行时和输出路径，再仅为暂存输出投影协议。 |
| `_cold_build` | 沿原范围和配置冷启动暂存建库，保留可变层但不复用旧事实或审阅，并把全部新实体放入待审迁移计划。 |
| `_project_record` | 在暂存中记录批次、操作身份、源目标绑定、版本链和保留文件，初始状态为等待审阅。 |
| `_pending_reviews` | 从暂存状态中返回所有尚未 passed 的审阅包标识。 |
| `_mutable_preservation_check` | 检查可变文件保全结果及不可变备份的存在和哈希，汇总丢失或漂移的基线。 |
| `_old_entity_id_errors` | 对照迁移旧新身份映射，找出仍残留在新图中的已被替换实体标识。 |
| `_knowledge_project_audit` | 逐项审计暂存绑定、审阅、完成标记、双库、保全层和维护门，条件满足时执行 finalize，再保存 ready/待审/失败结果。 |
| `_knowledge_project_audit.check` | 向项目审计列表追加检查名称、布尔结果、错误类别和详情。 |
| `_apply_one_project` | 在输出锁内按计划迁移或冷启动，恢复已有待审项目时重新审计，并保存执行阶段、暂存摘要和失败信息。 |
| `apply_knowledge_batch_plan` | 核验不可变计划及外置状态绑定后依次执行项目，分别记录异常并继续其他项目，最后返回汇总状态。 |
| `resume_knowledge_batch_state` | 从既有状态读取绑定计划，以允许重试失败项目的方式继续批量迁移。 |
| `knowledge_batch_status` | 按项目当前阶段比较暂存、已提升或已回滚输出的摘要，返回漂移诊断、状态计数和后续命令入口。 |
| `audit_knowledge_batch_state` | 逐项目重新审计可用暂存并保存摘要和待审包列表，对未开始或已切换项目分别处理，再汇总批次验收状态。 |
| `_control_path` | 由输出名称和项目操作短令牌生成输出目录旁的迁移控制记录路径。 |
| `_control_records` | 读取输出旁符合命名规则的控制记录，只保留 schema 和绝对输出绑定一致的条目，跳过读取异常。 |
| `_active_control` | 用当前全树清单匹配已完成切换的控制记录，多个记录同时匹配时报告活动链歧义。 |
| `_repair_moved_snapshot` | 读取移动后输出的快照描述，只修复相应 Git worktree 注册，不改写备份或隔离副本的状态基线。 |
| `_protocol_digest` | 对输出及其登记工作区的协议文件快照计算摘要，用于切换后漂移检测。 |
| `_cutover_one` | 锁内复查暂存审计和摘要后备份旧输出并提升暂存，校验协议、双库和维护结果，失败时恢复目录及协议并保存控制记录。 |
| `cutover_knowledge_batch_state` | 选择指定或审计就绪项目逐个切换，分别记录失败而不中断其他项目，汇总成功、跳过和失败数量。 |
| `_rollback_one` | 恢复单个已切换知识库及其协议备份，核对外部漂移与数据库状态；失败时尝试恢复切换后的目录。 |
| `rollback_knowledge_batch_state` | 按指定项目或可回滚项目集合执行逐库恢复，分别记录失败并汇总全部、部分或无成功结果。 |

</details>
