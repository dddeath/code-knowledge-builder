# 项目关系导览

> 这份导览把经常一起工作的类和函数聚成职责群，帮助人先理解结构，再进入具体实现。

## 建议先看的代码

- **status**：`status` 根据分段和审阅包的当前状态计算下一项可执行动作。
- **main**：`main` 解析命令并把请求分派到对应的确定性实现。
- **CodeKnowledgeBuilderTests**：`CodeKnowledgeBuilderTests` 汇集主构建流水线的端到端回归场景与断言。
- **execute**：`execute` 是源码中负责真实语义提供器精确、近似和失败路径集成测试的命名代码单元。
- **run**：`run` 是源码中负责错误类型、JSON 写入、子进程调用、路径约束和状态标记的命名代码单元。
- **LspClient.start**：`LspClient.start` 是源码中负责调用语言提供器并整理定义、符号与诊断证据的命名代码单元。
- **AutomationTest.event**：`AutomationTest.event` 为测试构造统一的 Harness 事件夹具。
- **ingest_event**：`ingest_event` 是所有 Harness Hook 进入 CKB 自动化核心的统一边界。
- **parser**：`parser` 定义 Code Knowledge Builder 的完整命令树和参数约束。
- **retrieve_machine**：`retrieve_machine` 组合精确锚点、FTS、图传播和页面优先规则生成限额阅读包。
- **record_note**：`record_note` 是源码中负责保存实时工作区变化和双链知识记录的命名代码单元。
- **parse_file**：`parse_file` 是源码中负责解析命名声明并保存稳定源码范围的命名代码单元。

## 按职责群浏览

### status 相关职责

- **status**：`status` 根据分段和审阅包的当前状态计算下一项可执行动作。
- **execute**：`execute` 是源码中负责真实语义提供器精确、近似和失败路径集成测试的命名代码单元。
- **LspClient.start**：`LspClient.start` 是源码中负责调用语言提供器并整理定义、符号与诊断证据的命名代码单元。
- **AutomationTest.event**：`AutomationTest.event` 为测试构造统一的 Harness 事件夹具。
- **ingest_event**：`ingest_event` 是所有 Harness Hook 进入 CKB 自动化核心的统一边界。
- **main**：`main` 是源码中负责接收命令参数并把请求路由到对应实现的命名代码单元。
- **AutomationTest**：`AutomationTest` 汇集同一功能域的测试夹具、执行步骤和验收断言。
- **LspClient.stop**：该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。

### main 相关职责

- **main**：`main` 解析命令并把请求分派到对应的确定性实现。
- **record_note**：`record_note` 是源码中负责保存实时工作区变化和双链知识记录的命名代码单元。
- **start_session**：`start_session` 是源码中负责管理 Agent 会话、构建中记录和修改总结落页的命名代码单元。
- **sync_human_layer**：`sync_human_layer` 是源码中负责生成事实层与中文人类层并核对跨层一致性的命名代码单元。
- **json_load**：该附属代码负责稳定读取或写入机器状态记录，并把结果交给所属页面中的主流程使用。
- **audit_global**：重跑分段、审阅、迁移、来源、中文、投影、SQLite 和链接等全局完成门。
- **json_write**：该附属代码负责稳定读取或写入机器状态记录，并把结果交给所属页面中的主流程使用。
- **utc_now**：该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。

### CodeKnowledgeBuilderTests 相关职责

- **CodeKnowledgeBuilderTests**：`CodeKnowledgeBuilderTests` 汇集主构建流水线的端到端回归场景与断言。
- **run**：`run` 是源码中负责错误类型、JSON 写入、子进程调用、路径约束和状态标记的命名代码单元。
- **source_files**：`source_files` 枚举允许进入发行包的 Skill 文件，并按发行类型决定是否包含 Windows 离线运行时。
- **main**：`main` 是源码中负责接收命令参数并把请求路由到对应实现的命名代码单元。
- **retrieve_machine.add**：该附属代码负责维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把结果交给所属页面中的主流程使用。
- **finalize**：在全局审计通过后重新读取状态并独占写入机器、人类与总完成标记。
- **merge**：合并已经通过的分段事实并解析跨段关系，生成唯一逻辑图。
- **invoke**：该附属代码负责构造或执行可重复的回归验证场景，并把结果交给所属页面中的主流程使用。

### retrieve 相关职责

- **retrieve**：`retrieve` 是源码中负责维护旧版页面索引兼容接口并生成受预算约束的阅读包的命名代码单元。
- **ensure_local_openers**：`ensure_local_openers` 是源码中负责生成并核对可直接打开源码位置的 URI的命名代码单元。
- **package_showcase**：`package_showcase` 是源码中负责构建可复现发行归档并复核成员集合的命名代码单元。
- **load_page_config**：`load_page_config` 是源码中负责规范化并校验不可漂移的页面配置的命名代码单元。
- **CkbError**：该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。
- **build_agent_index**：该附属代码负责维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把结果交给所属页面中的主流程使用。
- **normalize_page_config**：该附属代码负责规范化并校验不可漂移的页面配置，并把结果交给所属页面中的主流程使用。
- **run_fast**：实现 run/resume 快速入口，依次推进初始化、首段构建、审阅检查点和完成。

### module_name 相关职责

- **module_name**：`module_name` 是源码中负责页面配额、实体归属、关系预算和上下文预算的确定性决策的命名代码单元。
- **prepare_vault**：`prepare_vault` 清理上一轮生成器拥有的文件，并建立页面与五类笔记目录。
- **sha256_file**：该附属代码负责计算机器交付物的完整性摘要，并把结果交给所属页面中的主流程使用。
- **project_logseq**：导入规范 EDN、验证图谱、导出 SQLite 并核对双投影一致性。
- **project_markdown**：从逻辑图生成 Markdown/Obsidian 页面、索引、反向链接和规范 EDN。
- **_logical_context_budgets**：根据模块和任务上限计算每个导航入口的上下文预算。
- **_normalized_edn_document**：把唯一逻辑投影序列化为 Markdown 与 Logseq 共用的规范 EDN。
- **_prepare_csharp_restore**：在固定快照中执行受控 C# restore 并记录生成文件清单。

### parse_file 相关职责

- **parse_file**：`parse_file` 是源码中负责解析命名声明并保存稳定源码范围的命名代码单元。
- **remove**：`remove` 是源码中负责管理隔离离线运行时及其回滚的命名代码单元。
- **LspClient**：该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。
- **collect_semantics**：该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。
- **deploy**：该附属代码负责管理隔离离线运行时及其回滚，并把结果交给所属页面中的主流程使用。
- **doctor_report**：该附属代码负责检查依赖版本和本地运行条件，并把结果交给所属页面中的主流程使用。
- **deployment_plan**：该附属代码负责管理隔离离线运行时及其回滚，并把结果交给所属页面中的主流程使用。
- **DependencyError**：该附属代码负责检查依赖版本和本地运行条件，并把结果交给所属页面中的主流程使用。

### create_source_snapshot 相关职责

- **create_source_snapshot**：`create_source_snapshot` 为固定 commit 创建独立 detached worktree 并验证其干净状态。
- **initialize**：固定 Git 提交、发现范围、解析源码、规划分段并建立初始状态。
- **stable_id**：该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。
- **build_navigation_plan**：该附属代码负责按固定排序计算页面、附录、归属和审阅预算，并把结果交给所属页面中的主流程使用。
- **prepare_git_repository**：该附属代码负责Git 预检、固定源码快照、tracked source 范围和 blob 读取，并把结果交给所属页面中的主流程使用。
- **StaleSourceError**：该附属代码负责错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把结果交给所属页面中的主流程使用。
- **blob_bytes_many**：该附属代码负责Git 预检、固定源码快照、tracked source 范围和 blob 读取，并把结果交给所属页面中的主流程使用。
- **assert_source_snapshot**：该附属代码负责建立并验证与固定提交一致的源码快照，并把结果交给所属页面中的主流程使用。

### query_graph 相关职责

- **query_graph**：`query_graph` 是源码中负责构造职责关系图并提供职责群或路径查询的命名代码单元。
- **project_graphify**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **audit_graphify**：该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。
- **_load_projected_graph**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **shortest_path**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **explain_node**：该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。
- **_graphify_node**：该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。
- **_networkx_modules**：该附属代码负责Graphify 兼容图、确定性职责群、路径查询和关系报告，并把结果交给所属页面中的主流程使用。

### retrieve_machine 相关职责

- **retrieve_machine**：`retrieve_machine` 组合精确锚点、FTS、图传播和页面优先规则生成限额阅读包。
- **build_machine_knowledge**：该附属代码负责构建完整机器库并执行分节全文检索和确定性图扩展，并把结果交给所属页面中的主流程使用。
- **search_terms**：该附属代码负责维护旧版页面索引兼容接口并生成受预算约束的阅读包，并把结果交给所属页面中的主流程使用。
- **_human_projection**：该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。
- **_create_schema**：该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。
- **_openers**：该附属代码负责生成并核对可直接打开源码位置的 URI，并把结果交给所属页面中的主流程使用。
- **_review_paths**：该附属代码负责核对并登记逐实体 Agent 审阅结果，并把结果交给所属页面中的主流程使用。
- **_sections_for_entity**：该附属代码负责完整机器 SQLite、分节 FTS5、确定性图检索和源码查询，并把结果交给所属页面中的主流程使用。

### render_integration 相关职责

- **render_integration**：`render_integration` 在隔离目录中生成指定 Harness 的完整适配包和清单。
- **_opencode_v2_plugin**：生成 OpenCode V2 Plugin，通过 context、tool hook 与事件流同步 Skill 激活和会话证据。
- **_opencode_stable_plugin**：生成 OpenCode stable Plugin，监听消息、命令、工具和 session 事件并输出精确 Skill 激活事件。
- **_generic_schema**：生成含 `skill.applied`、精确 skill name 与显式布尔证据的通用事件 Schema。
- **_copilot_hooks**：生成同时包含 bash 与 PowerShell 的 Copilot VS Code 兼容配置。
- **_cursor_hooks**：生成 Cursor 项目级会话、工具、文件和停止事件配置。
- **_powershell_command**：生成带安全单引号转义的 PowerShell Hook 命令。
- **emit**：该附属代码负责命令行参数、子命令路由、统一退出码和顶层异常边界，并把结果交给所属页面中的主流程使用。

### audit_migration 相关职责

- **audit_migration**：`audit_migration` 对增量迁移计划、复用集合、可变层基线、审阅状态和目标图来源执行确定性复核。
- **MigrationTest**：`MigrationTest` 是增量迁移的端到端回归测试夹具。
- **migrate_output**：编排目标初始化、精确文件复用、可变知识保存、分段构建和差量审阅检查点。
- **MigrationTest.test_exact_blob_facts_and_agent_reviews_are_reused**：端到端验证精确复用、差量审阅、基线保留、合法 Hook 写入、篡改失败和 Wiki 重链接。
- **migration_status**：汇总迁移复用统计、待审阅包、下一模板和当前迁移审计结果。
- **_preserve_mutable_layers**：复制用户笔记、工作区记录和自动化数据库，同时为每项生成迁移基线。
- **_mutable_target**：把迁移清单中的相对路径解析到输出目录内并阻止路径越界。
- **_selected_entities**：按照范围清单汇集目标实体，并从固定 Git 提交批量读取对应源码。

### parser 相关职责

- **parser**：`parser` 定义 Code Knowledge Builder 的完整命令树和参数约束。
- **add_git_bootstrap_arguments**：`add_git_bootstrap_arguments` 登记可选 Git 初始化、首次提交信息和作者参数。
- **add_initial_arguments**：`add_initial_arguments` 为首次构建命令登记仓库、输出、范围、格式和语言选项。
- **main**：`main` 是源码中负责接收命令参数并把请求路由到对应实现的命名代码单元。
- **add_csharp_arguments**：该附属代码负责计算机器交付物的完整性摘要，并把结果交给所属页面中的主流程使用。
- **build**：收集发行文件、生成逐文件清单、写入可复现 ZIP，并复查 CRC 与内嵌清单一致性。
- **relative_files**：该附属代码负责离线运行时清单、可复现压缩和归档校验，并把结果交给所属页面中的主流程使用。
- **validate_full_payload**：核对 full 运行时载荷的路径、大小、摘要和必需成员是否符合锁定清单。

### scripts/ckb_core/__init__.py 相关职责


## 围绕任务继续缩小范围

```powershell
& PYTHON scripts\ckb.py query --out OUTPUT "职责关键词" --budget 1500
& PYTHON scripts\ckb.py path --out OUTPUT "起点类或函数" "目标类或函数"
& PYTHON scripts\ckb.py explain --out OUTPUT "类名、函数名或职责关键词"
```

查询会先选择与问题最相关的代码，再沿真实关系扩展到预算允许的范围。
