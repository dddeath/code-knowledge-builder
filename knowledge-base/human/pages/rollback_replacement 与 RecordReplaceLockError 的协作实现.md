# rollback_replacement 与 RecordReplaceLockError 的协作实现

标签：#类型/代码

> 受控替换一篇已审阅工作记录，同时更新双镜像、元数据、导览和两个索引，并提供失败补偿与回滚入口。 以所有者锁串行化操作，先核对候选再按角色顺序写入；只容许其他未变化笔记的完全相同既存坏链作为未处理诊断，单篇替换与全库维护明确分开。

## 什么时候需要修改

需要调整精确目标定位、来源继承、文件与索引角色、既存诊断边界或回滚冲突规则时修改。

## 在代码中的位置

[打开源码：scripts/ckb_core/record_replace.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/record_replace.py:1:1)  `scripts/ckb_core/record_replace.py:1-1225`

## 相关代码

- 与 [[BatchProjectError 与 ProtocolRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_work_record_index]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_work_record_index 与 _contains_chinese 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index 与 _tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ensure_local_openers 与 SourceLinkRenderer 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note 与 page_tag 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_operation]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[rollback_replacement]]。

## 谁会来到这里

- 与 [[rollback_replacement]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 46 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `RecordReplaceLockError` | 定义带稳定分类字段的记录替换锁异常。 |
| `RecordReplaceLockError.__init__` | 把锁错误分类加入异常消息，并保存分类属性供调用方判别。 |
| `_json_digest` | 对稳定键序和紧凑格式的 JSON 表示计算摘要。 |
| `_body_digest` | 清理正文末尾空白并补一个换行，再计算正文摘要。 |
| `_token_estimate` | 按 UTF-8 字节数除以三并向上取整，估算记录文本预算。 |
| `_operation_root` | 返回当前知识库的记录替换操作目录。 |
| `_journal_evidence` | 将替换清单路径转换为知识库内的相对证据路径。 |
| `_new_replace_lock_record` | 确认当前进程身份可验证后，生成带所有者令牌与启动身份的锁记录。 |
| `_parse_replace_lock` | 解析锁记录并校验精确字段、版本、进程标识、令牌和文本长度。 |
| `_replace_lock_owner_state` | 比较主机、进程存活与启动身份，区分活跃、死亡、复用和不可验证的锁所有者。 |
| `_release_replace_lock` | 校验锁文件身份与所有者令牌后释放描述符，仅删除仍属于本次操作的锁。 |
| `_replace_lock` | 以描述符锁串行化替换，只回收过期且确认死亡或进程复用的所有者锁。 |
| `_rollback_argv` | 构造包含解释器、入口、输出目录和清单路径的回滚参数列表。 |
| `_powershell_command` | 转义参数中的单引号，生成 PowerShell 调用文本。 |
| `_new_operation` | 创建唯一替换操作目录及初始清单，记录目标、时间和回滚入口。 |
| `_read_title` | 以 UTF-8 读取笔记首行标题，编码错误时给出受管笔记诊断。 |
| `_locate_existing` | 按精确类型和标题定位双镜像及元数据，拒绝类型、标题或镜像不一致。 |
| `_copy_candidate_note_roots` | 复制候选库的笔记目录、投影清单与缺口记录，隔离候选审计。 |
| `_file_state` | 读取文件存在状态、摘要和大小，缺失文件用空摘要表示。 |
| `_stage_file_role` | 保存文件角色原件并暂存候选，记录路径及前后状态证据。 |
| `_agent_snapshot` | 读取指定标题的 Agent 笔记、链接和全文检索行，形成逻辑快照。 |
| `_agent_candidate` | 在唯一笔记基线上替换正文与预算，并构造去重链接和全文检索候选。 |
| `_apply_agent_state` | 更新指定 Agent 笔记行，并重建它拥有的链接与全文检索行。 |
| `_machine_snapshot` | 读取指定机器文档、章节、来源关联、链接与全文检索行作为逻辑快照。 |
| `_machine_candidate` | 按新正文重新切分机器文档章节，构造章节索引和去重双链候选。 |
| `_apply_machine_state` | 更新机器文档并重建其章节、来源关联、双链及全文检索记录。 |
| `_sqlite_integrity` | 检查数据库完整性和外键，存在异常时阻止候选或正式提交。 |
| `_trial_agent` | 在临时事务中核对 Agent 基线、试写候选和回读结果，验证后回滚试写。 |
| `_trial_machine` | 在临时事务中核对机器文档基线、试写候选并验证，最后回滚试写。 |
| `_current_agent` | 以只读连接取得指定 Agent 笔记逻辑状态，并及时关闭连接。 |
| `_current_machine` | 以只读连接取得指定机器文档逻辑状态，并及时关闭连接。 |
| `_commit_agent` | 在写事务中检查 Agent 目标未漂移，验证新状态与完整性后提交。 |
| `_commit_machine` | 在写事务中检查机器文档未漂移，验证新状态与完整性后提交。 |
| `_cleanup_new_sqlite_sidecars` | 仅移除操作前不存在的数据库旁路文件，保留原有旁路状态。 |
| `_promote_file` | 确认文件基线未漂移后原子替换候选，并回读核对新摘要。 |
| `_restore_file` | 从原件原子恢复文件，若基线原本缺失则删除该操作新增的文件。 |
| `_verify_roles` | 逐角色比较文件状态或索引逻辑摘要，返回与指定前后状态不符的清单。 |
| `_relative_note_error` | 将诊断路径规范化为输出目录内相对路径，目录外诊断不获得内部笔记身份。 |
| `_note_error_baseline` | 记录操作前诊断，仅为非目标且双镜像一致的坏链笔记建立未变化基线。 |
| `_replacement_note_errors` | 逐项比较完整诊断及双镜像摘要，仅保留完全相同的其他笔记既存坏链。 |
| `_candidate_contract` | 检查候选笔记和导览镜像，保留严格匹配的基线坏链并明确单篇验证范围。 |
| `_prepare_replacement` | 准备单篇替换的正文、来源、元数据与索引角色，保存原件并试验候选事务。 |
| `_restore_promoted` | 按正式写入的逆序恢复文件与两个索引的目标逻辑状态。 |
| `_promotion` | 按角色顺序写入并再次核验，保留未处理基线诊断，失败时补偿已写入角色。 |
| `replace_note` | 在锁内协调单篇替换与日志，返回回滚入口及未处理诊断，不宣称全库维护完成。 |
| `_load_rollback_manifest` | 读取本库操作目录内的回滚清单，校验版本、操作类型、输出归属和可回滚状态。 |

</details>
