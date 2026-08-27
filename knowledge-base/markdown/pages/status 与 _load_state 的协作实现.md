# status 与 _load_state 的协作实现

标签：#类型/代码

> 该代码页汇总知识库从范围解析、分段构建、Agent 审阅到人类与机器投影、全局审计和完成标记的主流水线。 它串联固定源码快照、页面压缩、中文说明、Markdown/Logseq/SQLite 投影和迁移门，是所有命令共享的确定性执行核心。

## 什么时候需要修改

当构建阶段、页面投影、完成门、上下文预算或增量迁移联动方式变化时，需要修改本页并重跑主测试集。

## 在代码中的位置

[打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3242`

## 相关代码

- 实现时会用到 [[LspClient.start 与 _version_matches 的协作实现]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[create_source_snapshot]]。
- 实现时会用到 [[create_source_snapshot 与 git 的协作实现]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[load_page_config]]。
- 实现时会用到 [[load_page_config 与 _merge_known 的协作实现]]。
- 实现时会用到 [[parse_file]]。
- 实现时会用到 [[prepare_vault]]。
- 实现时会用到 [[record_note 与 page_tag 的协作实现]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 主要代码单元是 [[status]]。
- 实现时会用到 [[sync_human_layer]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[LspClient.start 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[MigrationTest]] 会使用这里提供的行为。
- [[MigrationTest 等测试场景]] 会使用这里提供的行为。
- [[add_git_bootstrap_arguments]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[create_source_snapshot 与 git 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[query_graph 与 _networkx_modules 的协作实现]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[start_session]] 会使用这里提供的行为。
- [[status]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 65 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_load_state` | 读取构建状态并核对版本、仓库快照和输出目录基本约束。 |
| `_module` | 从仓库相对路径提取用于分段和索引的模块名称。 |
| `_parse_entry` | 解析带语言、路径和限定名的显式入口选择器。 |
| `_resolve_entries` | 在候选实体中解析入口并对重名情况生成确定性候选结果。 |
| `_expand_entries` | 按 callers、callees 和深度扩展入口范围并形成一跳边界。 |
| `_chunks` | 按模块、文件数、实体数和源码大小上限制定可恢复分段计划。 |
| `_chunks.flush` | 把当前累计文件与实体封装成一个确定性分段记录。 |
| `_chunks.units_for_file` | 按顶层声明边界把超大文件拆成可独立分段的单元。 |
| `_write_review_pack_templates` | 为页面说明与附录说明生成逐实体源码证据审阅模板。 |
| `_normalize_repo_selector` | 规范化 C# 工作区选择器并约束其位于仓库内部。 |
| `_resolve_csharp_workspace` | 解析显式或自动发现的 C# solution/project 工作区。 |
| `_prepare_csharp_restore` | 在固定快照中执行受控 C# restore 并记录生成文件清单。 |
| `_prepare_csharp_fallback_workspace` | 缺少 C# 项目文件时生成有界近似工作区和精度证据。 |
| `_rekey_reused_file_parse` | 把精确复用的文件解析结果按目标提交重建实体与关系标识。 |
| `initialize` | 固定 Git 提交、发现范围、解析源码、规划分段并建立初始状态。 |
| `_selected_catalog` | 从目录、范围和边界清单中返回本次扫描实际选中的事实集合。 |
| `_chunk` | 按标识读取单个分段并对不存在的标识报告输入错误。 |
| `_review_pack` | 按标识读取单个审阅包并对不存在的标识报告输入错误。 |
| `_invalidate_after_build` | 重建后撤销旧投影和完成标记，使后续审计基于最新事实。 |
| `build_chunk` | 按 syntax、semantics、classify、project 阶段构建或返工指定分段。 |
| `_substantive_chinese` | 判断审阅字段是否包含足够的中文叙述而不是空泛占位。 |
| `_single_chinese_sentence` | 验证附录说明为一条简短且含中文语义的句子。 |
| `_source_check` | 在固定 Git blob 的指定范围内核对实体名称和源码位置。 |
| `_partial_fragment_source_errors` | 检查超大文件分段后的局部实体范围是否仍与源码一致。 |
| `audit_chunk` | 执行范围、语法、分类、语义、来源、中文说明和段内链接门。 |
| `audit_chunk.gate` | 把分段审计的单项结果与证据加入当前审计报告。 |
| `review_chunk` | 校验旧式逐分段 Agent 审阅文件并登记通过状态。 |
| `review_pack` | 校验页面或附录审阅包的实体集合、源码位置和中文字段后登记结果。 |
| `merge` | 合并已经通过的分段事实并解析跨段关系，生成唯一逻辑图。 |
| `_repository_name` | 从仓库根路径提取适合人类首页使用的项目名称。 |
| `_short_code_unit_name` | 生成保留类归属且去除多余命名空间的代码单元标题。 |
| `_source_role` | 依据后缀和路径把源码文件判定为接口、测试或实现。 |
| `_human_page_base_title` | 根据页面对应的类、函数或文件聚合生成无机器前缀的基础标题。 |
| `_assign_human_titles` | 为页面分配短标题，并用源码角色和位置确定性消解重名。 |
| `_logical_projection` | 把完整实体图压缩为受页面配额和关系预算约束的人类导航图。 |
| `_logical_projection.new_page` | 初始化人类导航页的实体归属、附录、边界和链接容器。 |
| `_logical_projection.relation_category` | 把底层关系类型归并为人类导航所需的有限关系类别。 |
| `_source_manifest` | 生成页面到固定源码路径和行范围的可点击来源清单。 |
| `_page_sections` | 按页面类型与配置返回需要渲染的章节顺序。 |
| `_overview_text` | 从 Agent 审阅字段组合代码页的中文概览。 |
| `_aggregate_overview` | 为文件、模块或边界聚合页生成简明中文职责说明。 |
| `_canonical_page_context` | 生成供机器检索与人类投影共同使用的规范页面上下文。 |
| `_logical_context_budgets` | 根据模块和任务上限计算每个导航入口的上下文预算。 |
| `_relation_phrase` | 把确定性关系类型转换为自然中文短语。 |
| `_human_relation_sentences` | 把压缩后的页面关系渲染为有限数量的中文导航句。 |
| `_normalized_edn_document` | 把唯一逻辑投影序列化为 Markdown 与 Logseq 共用的规范 EDN。 |
| `_render_markdown_page` | 按配置章节、双链和源码链接渲染一张人类可读 Markdown 页面。 |
| `_logseq_file_graph_config_bytes` | 生成 Logseq 文件图谱要求的最小 config.edn 内容。 |
| `_install_logseq_file_graph_config` | 把最小 Logseq 配置安装到导入根和兼容目录。 |
| `_audit_logseq_file_graph_config` | 核对 Logseq 配置存在、内容一致且位于正确导入根。 |
| `_human_page_filenames` | 为人类页面生成稳定、去前缀且无文件名冲突的 Markdown 文件名。 |
| `_wiki_document` | 生成中文知识库首页、阅读路线、标签说明和范围边界。 |
| `_readability_report` | 统计标题、属性、标签、源码链接和中文叙述问题并生成可读性审计。 |
| `project_markdown` | 从逻辑图生成 Markdown/Obsidian 页面、索引、反向链接和规范 EDN。 |
| `_logseq` | 以受控环境运行 Logseq CLI 并返回原样输出与退出状态。 |
| `_logseq_count` | 递归读取 Logseq CLI 查询结果中的实体或关系计数。 |
| `_logseq_count.visit` | 遍历 Logseq 查询返回值并累计目标键对应的整数。 |
| `_logseq_count.contains_null_result` | 检查 Logseq 查询返回值是否包含空结果。 |
| `project_logseq` | 导入规范 EDN、验证图谱、导出 SQLite 并核对双投影一致性。 |
| `_audit_markdown` | 检查 Markdown 双链、反向链接、页面配额、来源字段和归属集合。 |
| `audit_global` | 重跑分段、审阅、迁移、来源、中文、投影、SQLite 和链接等全局完成门。 |
| `finalize` | 在全局审计通过后重新读取状态并独占写入机器、人类与总完成标记。 |
| `relink_sources` | 更新本地可点击源码链接配置并重新执行完整完成门。 |
| `build_context` | 按模块或入口构造受 token 预算约束的确定性 Agent 上下文包。 |
| `run_fast` | 实现 run/resume 快速入口，依次推进初始化、首段构建、审阅检查点和完成。 |

</details>
