# 项目关系导览

> 这份导览把经常一起工作的类和函数聚成职责群，帮助人先理解结构，再进入具体实现。

## 建议先看的代码

- **CkbError**：`CkbError` 是 `scripts/ckb_core/common.py` 中负责为 CKB 输入或状态错误提供固定进程退出码的类。
- **audit_global**：重新生成知识库各层投影，并检查固定来源、审阅结果、页面内容和检索数据的一致性。
- **BatchProjectError**：保存批量项目失败的分类与错误说明：构造时把 detail 交给 CkbError，再将 category 保留为独立属性。
- **build_machine_knowledge**：从固定图谱、中文记录和参考资料重建机器检索数据库。
- **invoke**：使用选定 Python 运行 CKB 命令，并返回捕获的 UTF-8 标准输出、错误和退出状态。
- **start_scope_extension**：`start_scope_extension` 是 `scripts/ckb_core/scope_extension.py` 第 261-451 行定义的函数，本页绑定该固定源码范围。
- **maintenance_check**：重新执行独立审计并写出可重开的维护报告，汇总固定快照、双镜像可读性与事实时效。
- **record_note**：把已审阅正文写为工作记录，同步人类页面、镜像与记录元数据。
- **check_fact_freshness**：代码单元 `check_fact_freshness`负责比较知识库固定提交与 Git 当前状态，生成事实新鲜度状态、迁移计划和协作记录。
- **audit_agent_protocol**：`audit_agent_protocol` 是 `scripts/ckb_core/agent_protocol.py` 中负责核对各 Harness 指令文件、工作区绑定、反馈、工作记录与输出契约的函数。
- **parse_file**：将固定源码解析为带范围、父子归属和来源完整性标记的实体集合。
- **record_operation**：该函数校验操作类别、命令状态词和相对证据路径，将操作记录写入按 UTC 日期分片的机器日志；同日相同操作、状态和证据生成同一事件编号，重复调用只更新去重统计。

## 按职责群浏览

### start_scope_extension 相关职责

- **start_scope_extension**：`start_scope_extension` 是 `scripts/ckb_core/scope_extension.py` 第 261-451 行定义的函数，本页绑定该固定源码范围。
- **create_knowledge_batch_plan**：读取并规范化批量迁移清单，为各项目生成只读预检结果、可执行策略和不可变计划摘要，可选择写到所有知识库目录之外。
- **_inspect_knowledge_project**：核验项目路径、旧输出哈希和健康、目标快照及发行链，依据允许策略选择兼容迁移、冷启动、待审或失败。
- **_cutover_one**：锁内复查暂存审计和摘要后备份旧输出并提升暂存，校验协议、双库和维护结果，失败时恢复目录及协议并保存控制记录。
- **_knowledge_project_audit**：逐项审计暂存绑定、审阅、完成标记、双库、保全层和维护门，条件满足时执行 finalize，再保存 ready/待审/失败结果。
- **_rollback_one**：恢复单个已切换知识库及其协议备份，核对外部漂移与数据库状态；失败时尝试恢复切换后的目录。
- **audit_scope_extension**：`audit_scope_extension` 是第 598-692 行的函数，供所属页面定位实现。
- **_tree_manifest**：`_tree_manifest` 是第 57-72 行的函数，供所属页面定位实现。

### CkbError 相关职责

- **CkbError**：`CkbError` 是 `scripts/ckb_core/common.py` 中负责为 CKB 输入或状态错误提供固定进程退出码的类。
- **check_fact_freshness**：代码单元 `check_fact_freshness`负责比较知识库固定提交与 Git 当前状态，生成事实新鲜度状态、迁移计划和协作记录。
- **propose_template**：`propose_template` 位于 `scripts/ckb_core/human_page_template_proposals.py` 第 1121-1178 行，用于把通过校验的模板扩展写入待人工审阅状态，不直接激活模板。
- **package_showcase**：`package_showcase` 是源码中负责构建可复现发行归档并复核成员集合的命名代码单元。
- **stable_id**：根据固定输入计算 `stable_id` 稳定标识。
- **_text**：要求非空字符串，去除首尾空白并限制字符长度及空字节。
- **audit_template_proposal**：`audit_template_proposal` 用于汇总并判断受控对象是否满足当前合同。
- **normalize_template_proposal**：`normalize_template_proposal` 用于规范化输入字段并拒绝未知或越界值。

### build_machine_knowledge 相关职责

- **build_machine_knowledge**：从固定图谱、中文记录和参考资料重建机器检索数据库。
- **build_agent_index**：从人类投影、固定图和工作笔记生成兼容检索库 agent-index.sqlite，包含页面、符号归属、关系、词项、笔记及 FTS5 索引。
- **create_gap**：该函数校验输出、缺口种类、中文说明和一至十二个证据文件，以规范化内容生成稳定编号；重复编号直接返回原记录，新记录按种类进入开放或暂缓状态。
- **serve_stdio**：`serve_stdio` 提供会话内 JSONL 检索服务，当前同时接受 passed 与 needs-source-read，并对同一扩库建议执行会话内去重。
- **search_terms**：`search_terms` 是 `scripts/ckb_core/query_terms.py` 第 65-69 行定义的函数，本页绑定该固定源码范围。
- **_retrieve_machine_deterministic**：`_retrieve_machine_deterministic` 检索并组织机器索引与检索包生成所需的数据或状态。
- **resolve_gap**：为未关闭缺口写入中文关闭说明与证据，刷新相关索引并审计，已关闭缺口拒绝重复关闭。
- **audit_gap_register**：审计缺口记录与索引、唯一人类导览入口及机器数量，禁止为每个缺口生成独立人类页面。

### ingest_web_reference 相关职责

- **ingest_web_reference**：该函数在本地响应快照和显式联网请求之间要求恰选一种输入，先完成响应与正文提取核验，再归档原始 HTML、提取证据、来源清单和待审模板；相同来源内容幂等返回，变化必须指向最新已审阅修订。
- **validate_web_extraction**：该函数重新打开指定参考的网页提取清单及正文文件，核对受管路径、清单和正文哈希，并在原始响应存在时逐片段检查编号、行范围和原文摘要，再以片段正文重建正文摘要。
- **validate_pdf_extraction**：该函数重新打开 PDF 提取清单，核对参考身份、锁定解析器、页数顺序、页面路径和哈希、片段字符范围及非重叠约束，并对已记录的 OCR 输出检查精确路径和文件哈希。
- **path_inside**：生成 `inside` 对应的数据与约束。
- **audit_references**：审计参考原文、提取、审阅、修订状态、双镜像和机器记录数量，写入通过、待审或失败结果及标记。
- **ingest_reference**：归档本地参考原文并核验来源和许可，按内容哈希识别幂等或显式修订，生成提取证据、待审模板和事务记录。
- **extract_pdf**：逐页优先提取原生布局文本，仅在显式启用且预算允许时运行 OCR，保存页面与片段证据并明确列出待处理页。
- **_project_reference_pages**：重新核验全部有效审阅参考，在两份镜像生成每来源一页的摘要及完整导览，并登记投影文件集合。

### HumanPageTemplateContract 相关职责

- **HumanPageTemplateContract**：保存一种人类页面的不可变完整合同，包括读者任务、章节、预算、证据和适用边界。
- **init_page_author**：生成符合所选页面类型的新建、补充或修订填写骨架。
- **validate_human_page**：校验 V3 页面的章节、预算、链接和逐行事实证据，汇总机器信息泄漏诊断。
- **render_page_author**：按新建、补充或修订模式在内存生成候选文稿，限制章节与唯一替换目标，校验通过后返回正文、哈希和独立证据。
- **_failed**：将一个错误封装为带操作名、作者协议版本和 failed 状态的结果。
- **SectionContract**：定义章节的内容边界、披露层级、长度与链接预算及空章节规则。
- **_candidate_validation**：核验必需证据后调用完整页面校验，按结构、预算、链接、披露、当前事实及适用边界分类结果，并将未归类错误单独报告。
- **human_page_template_registry_sha256**：对稳定序列化的注册表计算 SHA-256 摘要。

### render_integration 相关职责

- **render_integration**：`render_integration` 为目标 Harness 生成自动化适配文件及机器清单，并在清单中写入该 Harness 的检索契约。
- **review_management_task**：复验已派发开发任务的声明测试与提交状态，生成管理侧验证记录。
- **create_management_task**：只在绑定状态、知识库状态和 Git 派发条件满足时，从固定 HEAD 创建独立开发 worktree。
- **bind_conversation**：规范管理会话输入并预检项目，在注册表锁内幂等复用、重新激活或建立绑定，拒绝身份或项目冲突并记录审计事件。
- **management_task_status**：核对开发 worktree、提交、验证记录和 integration HEAD，计算是否达到合并就绪状态。
- **_locked_registry**：`_locked_registry` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。
- **_git**：`_git` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。
- **_knowledge_snapshot**：`_knowledge_snapshot` 完成跨 Harness 管理对话绑定、状态检查和独立开发任务派发中的一个明确步骤。

### BatchProjectError 相关职责

- **BatchProjectError**：保存批量项目失败的分类与错误说明：构造时把 detail 交给 CkbError，再将 category 保留为独立属性。
- **apply_batch_plan**：`apply_batch_plan` 是第 1414-1516 行的函数，供所属页面定位实现。
- **_inspect_project**：`_inspect_project` 是第 541-654 行的函数，供所属页面定位实现。
- **_output_lock**：`_output_lock` 是第 1178-1256 行的函数，供所属页面定位实现。
- **_replace_lock**：以描述符锁串行化替换，只回收过期且确认死亡或进程复用的所有者锁。
- **rollback_batch_state**：`rollback_batch_state` 是第 1626-1713 行的函数，供所属页面定位实现。
- **snapshot_files**：`snapshot_files` 是第 422-435 行的函数，供所属页面定位实现。
- **audit_batch_state**：`audit_batch_state` 是第 1563-1623 行的函数，供所属页面定位实现。

### record_note 相关职责

- **record_note**：把已审阅正文写为工作记录，同步人类页面、镜像与记录元数据。
- **rollback_replacement**：按照一个已完成替换的清单恢复其拥有的文件与索引逻辑状态，并报告回滚结果。
- **audit_work_record_index**：该函数先审计 Markdown 工作记录导览的完整内容和链接，再检查人类镜像是否存在且与其逐字节相等，将差异合并为最终结果。
- **_prepare_replacement**：准备单篇替换的正文、来源、元数据与索引角色，保存原件并试验候选事务。
- **_promotion**：按角色顺序写入并再次核验，保留未处理基线诊断，失败时补偿已写入角色。
- **replace_note**：在锁内协调单篇替换与日志，返回回滚入口及未处理诊断，不宣称全库维护完成。
- **audit_notes**：检查记录类型标签、中文正文和知识链接，并报告可见哈希或缺失目录等问题。
- **_commit_agent**：在写事务中检查 Agent 目标未漂移，验证新状态与完整性后提交。

### invoke 相关职责

- **invoke**：使用选定 Python 运行 CKB 命令，并返回捕获的 UTF-8 标准输出、错误和退出状态。
- **CodeKnowledgeBuilderTests**：组织临时仓库上的建库、检索、参考资料、插件和维护集成测试，覆盖完成门与反例。
- **write**：创建父目录并以 UTF-8 和固定末尾换行写入测试文本。
- **CppParserAndSconsTests**：覆盖 C++ 局部解析恢复、警告传播及 SCons 标准推导，区分近似与编译数据库精确模式。
- **git**：在指定测试仓库执行 Git 命令，退出失败时抛出捕获的错误信息。
- **review_all**：构建全部测试分段，填入确定性审阅夹具并提交各包，失败时抛出完整诊断。
- **CodeKnowledgeBuilderTests.test_page_configuration_controls_quotas_content_and_is_pinned**：验证自定义页面配额与章节进入固定配置，并检测配置漂移和缺失必备章节。
- **CodeKnowledgeBuilderTests.test_stdio_retrieval_protocol_is_jsonl_and_errors_do_not_stop_server**：用检索与记录替身验证逐行协议、异常文本修复、错误隔离和关闭后停止响应。

### review_automation 相关职责

- **review_automation**：把待审自动化事件正式转换为人类笔记，并将数据库待审项和对应 sidecar 更新为 agent-reviewed。
- **ingest_event**：将 Harness 事件归一化并匹配注册与 Skill 激活，已激活事件脱敏后入队和排空，同时在激活或结束时维护 stdio 生命周期并返回 Hook 上下文。
- **initialize_automation_database**：`initialize_automation_database` 创建并初始化多 Harness 会话自动化所需的数据或状态。
- **normalize_event**：`normalize_event` 解析并归一化多 Harness 会话自动化所需的数据或状态。
- **drain_automation**：`drain_automation` 完成多 Harness 会话自动化中的一个明确步骤。
- **register_project**：`register_project` 登记并持久化多 Harness 会话自动化所需的数据或状态。
- **_automation_root**：`_automation_root` 完成多 Harness 会话自动化中的一个明确步骤。
- **_create_pending_review**：`_create_pending_review` 创建并初始化多 Harness 会话自动化所需的数据或状态。

### tests/fixtures/obsidian-interactive-nodes/overview-host.cjs 相关职责


### ProvenanceTests.setUp 相关职责

- **ProvenanceTests.setUp**：该初始化方法创建临时小型 Git 仓库并提交固定的双倍计算函数，登记临时目录自动清理，并设置旧新输出位置。
- **ProvenanceTests**：通过真实小仓库验证快照移动注册、被引用证据闭包、参考提取来源和连续迁移的路径与原文字节保留。
- **MigrationDirectoryDescriptionTests**：区分目录说明与正式证据链接，要求迁移不复制未引用缓存树，而明确引用的缺失文件必须提前阻断。
- **V3AuthoringMigrationTests**：验证 V3 作者包跨连续迁移、改名和目录回退仍可独立复核，缺失或漂移证据必须在创建暂存前失败。
- **git**：在测试仓库禁用自动垃圾回收和维护后执行 Git 命令，按可选检查参数传播失败并返回完整执行结果。
- **MigrationTransactionArchiveTests**：验证多次记录替换的历史事务作为不可变归档迁移，当前证据根与已消费排队记录的历史引用分开计算。
- **SQLiteGapAuditLifecycleTests**：跟踪缺口审计的 SQLite 读取连接，验证正常和异常路径显式关闭，随后可在同进程重建与替换索引。
- **SQLiteGapAuditLifecycleTests.track_gap_connections**：仅拦截缺口审计创建的 SQLite 连接，保留连接对象以防垃圾回收掩盖遗漏关闭，并可注入查询错误。

### close_session 相关职责

- **close_session**：该函数按 Harness、会话摘要和输出身份匹配租约，为匹配会话写入关闭控制请求并等待服务及监督进程退出；超时后强制终止记录中的进程并调用限定会话清理。
- **request_session**：`request_session` 是第 1139-1255 行的函数，供所属页面定位实现。
- **_start_supervisor_locked**：`_start_supervisor_locked` 是第 908-1004 行的函数，供所属页面定位实现。
- **cleanup_sessions**：`cleanup_sessions` 是第 1392-1431 行的函数，供所属页面定位实现。
- **controller_main**：`controller_main` 是第 518-722 行的函数，供所属页面定位实现。
- **pid_exists**：`pid_exists` 是第 188-218 行的函数，供所属页面定位实现。
- **_read_json**：`_read_json` 是第 132-137 行的函数，供所属页面定位实现。
- **activate_session_stdio**：`activate_session_stdio` 是第 802-887 行的函数，供所属页面定位实现。

### audit_agent_protocol 相关职责

- **audit_agent_protocol**：`audit_agent_protocol` 是 `scripts/ckb_core/agent_protocol.py` 中负责核对各 Harness 指令文件、工作区绑定、反馈、工作记录与输出契约的函数。
- **audit_feedback**：`audit_feedback` 是 `scripts/ckb_core/feedback.py` 中负责检查反馈锚点、状态、镜像、归档与落实记录的一致性的函数。
- **project_agent_protocol**：投影 `agent_protocol` 对应的数据与约束。
- **create_feedback**：创建 `feedback` 对应的数据与约束。
- **install_agent_protocol**：安装 `agent_protocol` 对应的数据与约束。
- **resolve_feedback**：解析并确定 `feedback` 对应的数据与约束。
- **_canonical_applied_record**：处理 `applied_record` 对应的数据与约束。
- **locate_feedback**：定位 `feedback` 对应的数据与约束。

### project_graphify 相关职责

- **project_graphify**：将已审阅规范图转换为 Graphify 兼容节点链接图、社区记录和中文图报告，同时生成各产物的哈希与计数记录。
- **doctor_report**：代码单元 `doctor_report`负责启动并约束语言服务器，收集 Python、JavaScript、C/C++ 和 C# 的语义证据。
- **LspClient**：`__init__` 完成语言服务器语义采集中的一个明确步骤。
- **collect_semantics**：`collect_semantics` 完成语言服务器语义采集中的一个明确步骤。
- **query_graph**：从 Graphify 匹配种子选出可扩展主种子，按 BFS 或 DFS 在深度四以内扩展预算化子图，并保存含节点、关系和源码文件的查询记录。
- **_load_projected_graph**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **audit_graphify**：该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。
- **resolve_executable**：`resolve_executable` 完成语言服务器语义采集中的一个明确步骤。

### parse_file 相关职责

- **parse_file**：将固定源码解析为带范围、父子归属和来源完整性标记的实体集合。
- **_python_lexical_pairs.Collector**：遍历 Python 名称、属性、导入、定义和局部作用域，收集使用点、绑定及成员写入，为保守词法解析提供上下文。
- **_python_lexical_pairs**：按 Python 词法作用域、导入和唯一绑定解析内部引用，重绑定或未知接收者不连边，结果明确不确认运行时分派。
- **_python_lexical_pairs.bind**：向作用域某个名称的绑定列表追加一个候选或未知标记。
- **_python_lexical_pairs.Collector.definition**：将定义绑定到已有源码实体，分别访问头部表达式和新作用域正文，并为明确实例或类方法绑定首参数接收者。
- **_byte_position**：直接从源码字节与偏移计算一基行号和零基 UTF-8 字节列，不读取语法节点 Point。
- **_node_text**：按节点字节范围切出源码并解码 UTF-8，非法字节用替代字符处理。
- **_find_name**：先从名字字段再遍历节点寻找标识符，返回名称与字节位置，并保留访问过的节点引用。

### maintenance_check 相关职责

- **maintenance_check**：重新执行独立审计并写出可重开的维护报告，汇总固定快照、双镜像可读性与事实时效。
- **module_name**：`module_name` 是源码中负责页面配额、实体归属、关系预算和上下文预算的确定性决策的命名代码单元。
- **refresh_human_navigation**：从现有图与全部记录刷新导览和投影元数据，核验页面及笔记字节不变，并在非暂存模式安装核验协议。
- **project_markdown**：生成兼容 Markdown 页面、导览、规范块文档及来源清单，记录预算、可读性和文件归属，不在该镜像部署配套插件。
- **_logical_projection**：将完整实体图投影为受预算限制的页面导航，归并附录和边界、聚合关系，并保留隐藏数量与候选关系标记。
- **project_logseq**：在隔离运行目录导入和核验 Logseq 图，逐类核对查询数量，导出 SQLite 并检查完整性和工作进程清理记录。
- **_readability_report**：检查人类页面、导览和记录的中文叙述、链接及机器证据泄漏，核验显式作者包，并将限定历史例外单列为告警。
- **_audit_markdown**：核对 Markdown 投影的配置、链接、附录、可读性、规范块文档及文件图配置，并合并笔记与宿主配置审计错误。

### render_human_maintenance_prompt 相关职责

- **render_human_maintenance_prompt**：把一个已登记的人类维护 action 与通过验证的参数渲染为中文执行 Prompt，包含执行顺序、确认点、停止条件和结构化交付模板。
- **ActionContract**：保存一个维护动作的目的、参数、步骤、确认条件、交付字段与恢复合同。
- **audit_human_maintenance_delivery**：`audit_human_maintenance_delivery` 用于汇总并判断受控对象是否满足当前合同。
- **_acceptance_template**：根据实际启用步骤生成交付模板，列出待填的命令结果、验收字段和恢复证据。
- **validate_human_maintenance_invocation**：解析 action 参数并按合同补默认值和校验类型，额外拒绝安装/建库职责混用、缺失人类确认、未知许可和模板版本或暂存边界冲突，返回规范参数与全部错误。
- **CommandStep**：保存执行步骤的指令、能力映射、条件参数、输入字段及预期结果约定。
- **_error**：将错误原因、中文消息和补充字段组合为统一错误对象。
- **human_maintenance_registry_sha256**：`human_maintenance_registry_sha256` 用于生成稳定序列化或内容摘要。

### audit_global 相关职责

- **audit_global**：重新生成知识库各层投影，并检查固定来源、审阅结果、页面内容和检索数据的一致性。
- **normalize_page_config**：该函数把用户提交的局部页面配置与默认配置合并，检查模式版本、已知字段、章节集合、标题、概览字段和附录展示模式，并规范化页面与关系数量限制。
- **utc_now**：处理 `now` 对应的数据与约束。
- **AuditError**：处理 `auditerror` 对应的数据与约束。
- **_load_state**：读取构建状态并兼容旧批次键，检查固定源码和规范化页面配置的哈希，发现漂移即报错。
- **audit_chunk**：核验批次范围、语法、分类、语义覆盖、源码、中文审阅与链接端点，并写入逐门结果和审计标记。
- **build_chunk**：按阶段生成批次语法结果或语义候选，收集警告并写入审阅模板与待审状态。
- **review_pack**：独立核验审阅包的实体集合、分类、来源和中文字段，关联包全部通过后合并批次审阅并执行批次审计。

### HumanMaintenancePromptCliTests.test_audit_exit_status_is_zero_only_for_verified_completion 相关职责

- **HumanMaintenancePromptCliTests.test_audit_exit_status_is_zero_only_for_verified_completion**：该测试向维护摘要审计命令提交完整通过样例，要求退出零；再把命令输出改为仅已启动，要求退出五并指出启动不等于完成。
- **HumanMaintenancePromptValidationTests**：该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。
- **HumanMaintenanceDeliveryAuditTests**：该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。
- **HumanMaintenancePromptRegistryTests**：核对人类维护动作注册表的固定顺序、合同字段、稳定哈希和管理入口复用，以及模板命令的实际能力映射。
- **HumanMaintenancePromptRenderTests**：该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。
- **_valid_maintain_summary**：该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。
- **HumanMaintenancePromptCliTests**：该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。
- **HumanMaintenancePromptFixtureTests**：该测试验证人类维护 Prompt 的注册、参数、交付或失败边界。

### importInput 相关职责

- **importInput**：通过导入按钮和 JSON 文本框提交指定功能交换输入。

### git 相关职责

- **git**：该函数在指定仓库执行 Git 子命令并捕获 UTF-8 输出，默认非零退出抛错，显式关闭检查时返回原始执行结果。
- **FactFreshnessStateMachineTest**：覆盖 Git 事实六状态、脏树临时层、迁移就绪门、检索结论限制及锁并发恢复，确保不静默改写稳定事实。
- **FactFreshnessStateMachineTest._commit**：`_commit` 完成源码事实新鲜度回归验证中的一个明确步骤。
- **GitTriggerAndCollaborationTest**：`setUp` 完成源码事实新鲜度回归验证中的一个明确步骤。
- **FactFreshnessStateMachineTest._write_output_state**：`_write_output_state` 生成并写入源码事实新鲜度回归验证所需的数据或状态。
- **RealGitEventSequenceTest**：`setUp` 完成源码事实新鲜度回归验证中的一个明确步骤。
- **RealGitEventSequenceTest.test_commit_branch_switch_merge_and_pull_each_drive_a_real_check**：该测试验证“commit branch switch merge an…”场景，保护源码事实新鲜度回归验证的预期结果与失败边界。
- **FactFreshnessStateMachineTest.setUp**：`setUp` 完成源码事实新鲜度回归验证中的一个明确步骤。

### HumanPageAuthoringRenderTests.test_revise_separates_human_summary_from_machine_evidence_refs 相关职责

- **HumanPageAuthoringRenderTests.test_revise_separates_human_summary_from_machine_evidence_refs**：该测试修订中文原因摘要并同时登记来源引用和机器验证引用，要求候选正文只展示人类摘要、不泄漏机器证据文件名。
- **_change_payload**：该测试验证 V3 页面填写、渐进披露、证据分离或隔离打包边界。
- **HumanPageAuthoringValidationFailureTests**：验证页面作者合同的结构、预算、链接、证据披露和当前事实失败分类，覆盖旧版本、路径漂移及受管页直改限制。
- **_section**：该测试验证 V3 页面填写、渐进披露、证据分离或隔离打包边界。
- **HumanPageAuthoringRenderTests**：该测试验证 V3 页面填写、渐进披露、证据分离或隔离打包边界。
- **HumanPageAuthoringPackageTests**：该测试验证“all fourteen page types keep …”场景，保护V3 页面生成测试的结果与失败边界。
- **_payload**：该测试验证 V3 页面填写、渐进披露、证据分离或隔离打包边界。
- **HumanPageAuthoringInitTests**：该测试验证 V3 页面填写、渐进披露、证据分离或隔离打包边界。

### run_keyword_benchmark 相关职责

- **run_keyword_benchmark**：`run_keyword_benchmark` 是 `scripts/ckb_core/keyword_benchmark.py` 第 139-227 行定义的函数，本页绑定该固定源码范围。
- **KeywordFallbackOptions**：保存一次关键词扩展请求使用的提供器配置与强制触发、缓存选项。
- **run_keyword_provider**：校验环境与缓存后通过命令标准输入请求关键词，规范失败、有限重试并只缓存成功响应，返回次数、耗时和缓存状态。
- **KeywordProviderConfig**：保存关键词适配器的命令、Provider/模型/版本标识以及超时、重试和环境变量要求。
- **_read_cache**：只接受字段和身份均匹配且响应重新校验成功的缓存，其余缺失、损坏或不匹配情况返回 None。
- **validate_provider_response**：核验响应 schema、请求身份和候选列表，成功必须含至少一个候选，失败则规范为带空候选的标准失败对象。
- **keyword_cache_key**：校验配置后，将问题哈希、Provider、模型、版本与提示协议稳定序列化并计算缓存键。
- **validate_provider_config**：检查非空命令参数、机器身份标记、超时范围、零或一次重试及合法环境变量名称。

### AutomationTest.register 相关职责

- **AutomationTest.register**：代码单元 `register`负责验证多 Harness 事件归一化、会话激活、并发采集和受控投影。
- **AutomationTest**：`setUp` 完成会话自动化回归验证中的一个明确步骤。
- **AutomationTest.event**：`event` 完成会话自动化回归验证中的一个明确步骤。
- **git**：`git` 完成会话自动化回归验证中的一个明确步骤。
- **AutomationTest.test_agent_review_promotes_one_chinese_human_note**：该测试验证“agent review promotes one chi…”场景，保护会话自动化回归验证的预期结果与失败边界。
- **AutomationTest.test_claude_without_turn_ids_allows_repeated_prompt_after_completion**：该测试验证“claude without turn ids allow…”场景，保护会话自动化回归验证的预期结果与失败边界。
- **AutomationTest.test_project_opt_in_and_hook_output**：该测试验证“project opt in and hook output”场景，保护会话自动化回归验证的预期结果与失败边界。
- **AutomationTest.test_redaction_idempotency_change_capture_and_pending_review**：该测试验证“redaction idempotency change …”场景，保护会话自动化回归验证的预期结果与失败边界。

### git 相关职责

- **git**：该函数在指定管理测试仓库运行 Git 子命令，捕获 UTF-8 输出并在非零退出时抛出错误，成功返回去除首尾空白的标准输出。
- **ManagementBindingLifecycleTest**：`ManagementBindingLifecycleTest` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。
- **ManagementBindingLifecycleTest.payload**：`payload` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。
- **ManagementSchemaPersistenceTest**：`ManagementSchemaPersistenceTest` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。
- **ManagementBindingLifecycleTest.test_concurrent_repeated_bind_and_unbind_have_one_active_object**：该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。
- **ManagementBindingLifecycleTest.ready_context**：`ready_context` 完成管理对话绑定、状态阻断、并发和任务复核回归验证中的一个明确步骤。
- **ManagementBindingLifecycleTest.test_task_dispatch_creates_independent_worktree_prompt_and_review_gate**：该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。
- **ManagementBindingLifecycleTest.test_task_dispatch_is_idempotent_and_blocks_integration_drift**：该测试完成管理对话绑定、状态检查或独立开发任务控制中的一个明确步骤。

### preflight 相关职责

- **preflight**：确认可用 Git 仓库并拒绝任何已跟踪或未跟踪的工作树改动，返回规范化仓库根、HEAD 提交、tree 及初始化记录。
- **initialize**：固定仓库提交和页面配置，解析选定范围及边界，生成导航、解析批次和待审模板，并仅复用精确匹配的已通过解析。
- **run**：执行 `run` 对应的数据与约束。
- **DependencyError**：处理 `dependencyerror` 对应的数据与约束。
- **StaleSourceError**：处理 `stalesourceerror` 对应的数据与约束。
- **background_process_options**：处理 `process_options` 对应的数据与约束。
- **_prepare_csharp_restore**：在隔离工作树中执行显式请求的依赖还原，隔离包缓存，保存命令输出、文件哈希和回滚脚本。
- **assert_source_snapshot**：确认绑定提交仍存在且快照目录的 HEAD、tree 和已跟踪文件未漂移，同时允许原仓库活动工作树继续变化。

### migrate_output 相关职责

- **migrate_output**：从完成且全局审计通过的旧库创建增量输出，并返回迁移计划、复用统计和下一审阅包。
- **json_load**：处理 `load` 对应的数据与约束。
- **json_write**：处理 `write` 对应的数据与约束。
- **_preserve_mutable_layers**：保留用户资料与证据基线，单独标记参考状态文件，并仅重定位可变元数据。
- **_replace_review_packs**：将复用与待审实体拆为不同审阅包，提交精确复用项并设置增量检查点。
- **audit_migration**：核对迁移来源和保留基线，允许精确参考状态标记退出当前状态，实际资料缺失仍阻塞。
- **relink_preserved_notes**：按唯一新归属重连旧笔记双链，保留正文和不可变证据并登记歧义标题。
- **_relocate_completed_output**：识别随输出目录移动的固定快照，修复受管路径并记录迁移审计，同时保留不可变证据文件。

### make_output 相关职责

- **make_output**：该函数创建最小源码文件和含单个实体、范围与页面映射的 SQLite 测试输出，写入测试用完成状态与快照绑定。
- **SessionStdioLifecycleTests**：验证会话首次应用 Skill 后的进程复用、并发隔离与结束清理，并覆盖崩溃恢复、路径限制和协议异常的回退行为。
- **SessionStdioLifecycleTests.test_close_timeout_escalates_to_terminate_then_kill_and_waits.TimeoutProcess**：`SessionStdioLifecycle...` 是第 500-526 行的类，供所属页面定位实现。
- **SessionStdioLifecycleTests.test_protocol_version_mismatch_fails_handshake_with_bounded_reason.FakeProcess**：`SessionStdioLifecycle...` 是第 457-477 行的类，供所属页面定位实现。
- **SessionStdioLifecycleTests.test_sixteen_concurrent_first_requests_singleflight_and_isolation**：`SessionStdioLifecycle...` 是第 186-240 行的函数，供所属页面定位实现。
- **SessionStdioLifecycleTests.event**：`SessionStdioLifecycle...` 是第 109-116 行的函数，供所属页面定位实现。
- **SessionStdioLifecycleTests.test_close_timeout_escalates_to_terminate_then_kill_and_waits**：`SessionStdioLifecycle...` 是第 499-536 行的函数，供所属页面定位实现。
- **SessionStdioLifecycleTests.test_protocol_version_mismatch_fails_handshake_with_bounded_reason**：`SessionStdioLifecycle...` 是第 456-497 行的函数，供所属页面定位实现。

### KnowledgeBatchWorkflowTests.test_plan_apply_audit_cutover_and_exact_rollback 相关职责

- **KnowledgeBatchWorkflowTests.test_plan_apply_audit_cutover_and_exact_rollback**：该测试用含工作记录、参考、缺口和用户笔记的基线贯通计划、应用、审计与切换，再执行第二次切换并按父链逆序回滚。
- **KnowledgeBatchWorkflowTests**：贯通知识库批量迁移的计划、待审续跑、切换链和精确回滚，并用多项目及漂移故障验证来源保护与恢复隔离。
- **KnowledgeBatchWorkflowTests._manifest**：生成绑定允许根目录的批量迁移清单，未传项目集合时使用当前测试项目。
- **KnowledgeBatchWorkflowTests.test_plan_classifies_required_origin_version_and_path_failures**：注入缺失来源记录、事实层、损坏索引、模式漂移、镜像差异和版本路径错误，核对计划阶段分类。
- **KnowledgeBatchVersionMatrixTests**：核对普通克隆与工作树的公共 Git 目录解析、真实历史版本矩阵以及非重标记的历史输出夹具配方。
- **KnowledgeBatchWorkflowTests._project_document**：收集源库固定记录与目录摘要，绑定源目标快照、发行元组、范围和恢复目录，生成单项目迁移清单项。
- **KnowledgeBatchWorkflowTests.test_origin_records_are_exact_fixed_keys_before_any_external_read**：注入越界或非规范来源记录键，要求任何外部文件读取前按固定键集合拒绝，并核对模式文档一致。
- **KnowledgeBatchWorkflowTests.test_two_projects_isolate_partial_apply_cutover_and_subset_rollback**：用两个项目验证恢复拓扑、部分应用和切换失败隔离，分别重试与子集回滚而不撤销另一项目成功结果。

> 为保持阅读节奏，这里只展开最主要的职责群；图查询仍会使用完整关系。

## 围绕任务继续缩小范围

```powershell
& PYTHON scripts\ckb.py query --out OUTPUT "职责关键词" --budget 1500
& PYTHON scripts\ckb.py path --out OUTPUT "起点类或函数" "目标类或函数"
& PYTHON scripts\ckb.py explain --out OUTPUT "类名、函数名或职责关键词"
```

查询会先选择与问题最相关的代码，再沿真实关系扩展到预算允许的范围。
