# ingest_event 与 default_registry_path 的协作实现

标签：#类型/代码

> 该代码页汇总跨 Harness 会话与修改自动化，包括项目登记、session 级 Skill 激活、事件规范化、脱敏、spool、SQLite 和 Agent 审阅。 它要求仓库登记与 `code-knowledge-builder` 精确激活同时成立；激活前事件静默忽略，激活后才记录会话、工具、修改与待审阅证据。

## 什么时候需要修改

当激活证据、注册表 Schema、Harness 事件映射、SQLite 表、幂等键、路径过滤或晋升规则变化时，需要修改本页。

## 在代码中的位置

[打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1632`

## 相关代码

- 实现时会用到 [[AutomationTest.event]]。
- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[LspClient.start 与 _version_matches 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[execute]]。
- 主要代码单元是 [[ingest_event]]。
- 实现时会用到 [[record_note]]。
- 实现时会用到 [[record_note 与 page_tag 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[AutomationTest.event 等测试场景]] 会使用这里提供的行为。
- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[ingest_event]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[MigrationTest]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]

## 内部细节

<details><summary>查看本页收纳的 54 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `default_registry_path` | 选择环境变量指定或用户目录下的自动化注册表路径。 |
| `_path_key` | 把跨平台路径规范化为可稳定比较的注册键。 |
| `_is_within` | 判断事件或文件路径是否位于指定根目录内部。 |
| `_read_registry` | 读取自动化注册表，并把 schema 1/2 确定性补齐为要求 session Skill 激活的 schema 3 视图。 |
| `register_project` | 登记仓库、知识库、工作区和 Harness，并固定 required skill 与 session 激活硬门。 |
| `unregister_project` | 按源码仓库根移除项目注册但保留已经落库的知识记录。 |
| `registry_status` | 返回当前自动化注册表、项目数量和登记明细。 |
| `_registration_for_event` | 按直接仓库优先和最深 workspace 根选择唯一事件注册。 |
| `_walk_values` | 递归遍历嵌套事件中的键值以支持通用字段提取。 |
| `_first_scalar` | 从不同 Harness 嵌套字段中选择首个非空标量。 |
| `_text_content` | 从消息、part、content 或 delta 结构中抽取文本。 |
| `_event_name` | 从原始 payload 的候选字段中确定原生事件名称。 |
| `_message_role` | 提取并规范化 OpenCode 等消息结构中的角色。 |
| `_normalized_skill_name` | 去除调用前缀与括号并规范化 skill name，供精确名称比较使用。 |
| `_skill_name` | 从原生 Skill 元数据、Skill 工具输入或显式调用 prompt 中提取精确的 code-knowledge-builder 名称。 |
| `_canonical_type` | 把宿主事件映射到十种规范事件，并将原生 Skill 调用映射为 `skill.applied`。 |
| `_extract_paths` | 从路径字段和 apply_patch 文本中收集候选变化路径。 |
| `normalize_event` | 把 Harness 原始负载规范化为统一事件，同时保留 session、turn、工具、路径与 Skill 激活证据。 |
| `_redact_text` | 按凭据、私钥、自定义规则和长度上限处理单个文本字段。 |
| `redact_event` | 递归脱敏规范事件并记录脱敏类型与次数。 |
| `redact_event.redact` | 递归处理事件字典、数组、标量和敏感键值。 |
| `_automation_root` | 建立自动化 spool、失败区和待审阅 sidecar 目录。 |
| `initialize_automation_database` | 初始化自动化 SQLite、FTS 与 `skill_activations` 表，并升级既有数据库 Schema。 |
| `_git_status_paths` | 读取限定在源码仓库当前目录的 Git 变化路径。 |
| `_change_path_allowed` | 过滤缓存、依赖、构建目录和字节码文件。 |
| `_working_file_state` | 记录变化文件的存在性、大小和内容摘要以识别后续修改。 |
| `_relative_changed_paths` | 把 workspace 或仓库相对路径安全映射为源码仓库相对路径。 |
| `_drain_lock` | 以单输出锁串行化并发 Hook 的队列导入。 |
| `enqueue_event` | 把脱敏事件原子写入待处理 spool。 |
| `_spool_events` | 按文件名稳定排序一个 spool 目录中的事件。 |
| `_session_key` | 由 Harness、外部会话和源码仓库生成稳定会话键。 |
| `default_session_id` | 按 Harness 从环境变量推断当前 session ID，并优先使用通用 CKB session 变量。 |
| `_activation_key` | 根据 Harness、session、仓库根和精确 skill name 生成稳定激活键。 |
| `_record_skill_activation` | 幂等写入 session Skill 激活证据，并返回首次激活或已激活状态。 |
| `_skill_activation` | 查询指定 Harness、session 和仓库是否已经存在精确 Skill 激活记录。 |
| `activate_skill_session` | 实现 Agent 主动激活命令，匹配注册项目后为当前 Harness session 写入激活证据。 |
| `_explicit_skill_application` | 判定规范事件是否携带显式 prompt、原生 Skill 事件或精确 Harness 元数据激活证据。 |
| `_ensure_session` | 创建或恢复自动化 session，并在首次 Skill 激活时保存当前 Git 工作树基线。 |
| `_resolve_turn` | 把 Skill/session 事件保持在会话层，并为 prompt、工具与 Stop 确定性解析活动 turn。 |
| `_event_id` | 优先使用外部幂等键，否则由规范事件内容生成稳定事件键。 |
| `_pending_review_content` | 把用户请求、最终回答和变化路径聚合为机器待审阅正文。 |
| `_create_pending_review` | 在轮次结束时合并路径证据并创建唯一待审阅记录。 |
| `_process_event` | 在单个 SQLite 事务内更新事件、轮次、工具、路径与审阅状态。 |
| `drain_automation` | 持锁导入待处理 spool，并把成功、重复和失败事件分别归档。 |
| `retry_failed_automation` | 把失败事件显式移回待处理区并重新执行导入。 |
| `_hook_context` | 为已经激活的 Skill session 生成简短中文自动化上下文和待审阅计数。 |
| `_hook_output` | 按 Harness 原生输出协议返回附加上下文或空对象。 |
| `automation_status` | 汇总 Skill 激活、事件、会话、轮次、路径、待审阅、spool 与 SQLite 完整性状态。 |
| `pending_automation_reviews` | 查询待审阅或全部自动化审阅记录。 |
| `write_automation_review_template` | 根据机器记录写出带逐路径来源检查的审阅模板。 |
| `_heading_errors` | 检查修改记录是否包含修改内容、原因和验证结果三个标题。 |
| `review_automation` | 验证中文正文与逐路径证据后把机器记录晋升为人类笔记。 |
| `search_automation` | 使用 SQLite FTS 检索机器层自动化记录。 |
| `automation_documents` | 按类型和时间导出机器检索可消费的自动化文档。 |

</details>
