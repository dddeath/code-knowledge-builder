# replace_note 与 RecordReplaceLockError 的协作实现

标签：#类型/代码

> `scripts/ckb_core/record_replace.py` 页面绑定固定源码第 1-1156 行，说明该文件在工作记录正文替换、候选验证、原子 promotion 和回滚中的整体职责。 该文件负责工作记录正文替换、候选验证、原子 promotion 和回滚，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `scripts/ckb_core/record_replace.py` 中 `scripts/ckb_core/record_replace.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/record_replace.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/record_replace.py:1:1)  `scripts/ckb_core/record_replace.py:1-1156`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_work_record_index 与 _contains_chinese 的协作实现]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[record_note 与 page_tag 的协作实现]]。
- 主要代码单元是 [[replace_note]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[rollback]]。

## 谁会来到这里

- [[RecordReplaceTests 等测试场景]] 会使用这里提供的行为。
- [[replace_note]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[RecordReplaceTests]]
- [[RecordReplaceTests 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 43 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `RecordReplaceLockError` | `RecordReplaceLockError` 用于完成局部输入校验、转换或状态更新。 |
| `RecordReplaceLockError.__init__` | `__init__` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。 |
| `_json_digest` | `_json_digest` 在 `record_replace.py` 中用于生成稳定标识或字节校验值。 |
| `_body_digest` | `_body_digest` 在 `record_replace.py` 中用于生成稳定标识或字节校验值。 |
| `_token_estimate` | `_token_estimate` 用于完成局部输入校验、转换或状态更新。 |
| `_operation_root` | `_operation_root` 用于完成局部输入校验、转换或状态更新。 |
| `_journal_evidence` | `_journal_evidence` 用于完成局部输入校验、转换或状态更新。 |
| `_new_replace_lock_record` | `_new_replace_lock_record` 用于完成局部输入校验、转换或状态更新。 |
| `_parse_replace_lock` | `_parse_replace_lock` 在 `record_replace.py` 中用于解析、规范化并冻结调用输入。 |
| `_replace_lock_owner_state` | `_replace_lock_owner_state` 用于完成局部输入校验、转换或状态更新。 |
| `_release_replace_lock` | `_release_replace_lock` 用于完成局部输入校验、转换或状态更新。 |
| `_replace_lock` | `_replace_lock` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。 |
| `_rollback_argv` | `_rollback_argv` 在 `record_replace.py` 中用于执行范围受控的恢复、撤销或清理。 |
| `_powershell_command` | `_powershell_command` 在 `record_replace.py` 中用于编排命令入口、执行顺序和退出结果。 |
| `_new_operation` | `_new_operation` 用于完成局部输入校验、转换或状态更新。 |
| `_read_title` | `_read_title` 在 `record_replace.py` 中用于读取、规范化并返回既有状态。 |
| `_locate_existing` | `_locate_existing` 用于完成局部输入校验、转换或状态更新。 |
| `_copy_candidate_note_roots` | `_copy_candidate_note_roots` 用于完成局部输入校验、转换或状态更新。 |
| `_file_state` | `_file_state` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。 |
| `_stage_file_role` | `_stage_file_role` 在 `record_replace.py` 中用于写入受控 staging 并重开核对结果。 |
| `_agent_snapshot` | `_agent_snapshot` 用于完成局部输入校验、转换或状态更新。 |
| `_agent_candidate` | `_agent_candidate` 用于完成局部输入校验、转换或状态更新。 |
| `_apply_agent_state` | `_apply_agent_state` 用于完成局部输入校验、转换或状态更新。 |
| `_machine_snapshot` | `_machine_snapshot` 用于完成局部输入校验、转换或状态更新。 |
| `_machine_candidate` | `_machine_candidate` 用于完成局部输入校验、转换或状态更新。 |
| `_apply_machine_state` | `_apply_machine_state` 用于完成局部输入校验、转换或状态更新。 |
| `_sqlite_integrity` | `_sqlite_integrity` 用于完成局部输入校验、转换或状态更新。 |
| `_trial_agent` | `_trial_agent` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。 |
| `_trial_machine` | `_trial_machine` 用于完成局部输入校验、转换或状态更新。 |
| `_current_agent` | `_current_agent` 用于完成局部输入校验、转换或状态更新。 |
| `_current_machine` | `_current_machine` 用于完成局部输入校验、转换或状态更新。 |
| `_commit_agent` | `_commit_agent` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。 |
| `_commit_machine` | `_commit_machine` 用于完成局部输入校验、转换或状态更新。 |
| `_cleanup_new_sqlite_sidecars` | `_cleanup_new_sqlite_sidecars` 在 `record_replace.py` 中用于执行范围受控的恢复、撤销或清理。 |
| `_promote_file` | `_promote_file` 在 `record_replace.py` 中用于写入受控 staging 并重开核对结果。 |
| `_restore_file` | `_restore_file` 在 `record_replace.py` 中用于执行范围受控的恢复、撤销或清理。 |
| `_verify_roles` | `_verify_roles` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。 |
| `_candidate_contract` | `_candidate_contract` 用于完成局部输入校验、转换或状态更新。 |
| `_prepare_replacement` | `_prepare_replacement` 用于完成局部输入校验、转换或状态更新。 |
| `_restore_promoted` | `_restore_promoted` 在 `record_replace.py` 中用于执行范围受控的恢复、撤销或清理。 |
| `_promotion` | `_promotion` 在 `record_replace.py` 中用于完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。 |
| `_load_rollback_manifest` | `_load_rollback_manifest` 在 `record_replace.py` 中用于执行范围受控的恢复、撤销或清理。 |
| `rollback_replacement` | `rollback_replacement` 在 `record_replace.py` 中用于执行范围受控的恢复、撤销或清理。 |

</details>
