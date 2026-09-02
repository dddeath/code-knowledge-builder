# render_human_maintenance_prompt 与 ParameterSpec 的协作实现

标签：#类型/代码

> `scripts/ckb_core/human_maintenance_prompts.py` 页面绑定固定源码第 1-1992 行，说明该文件在稳定维护 Prompt 的 action 映射、渲染和交付审计中的整体职责。 该文件负责稳定维护 Prompt 的 action 映射、渲染和交付审计，并为相关命令或测试提供可复查实现入口。

## 什么时候需要修改

当 `scripts/ckb_core/human_maintenance_prompts.py` 中 `scripts/ckb_core/human_maintenance_prompts.py` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_maintenance_prompts.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_maintenance_prompts.py:1:1)  `scripts/ckb_core/human_maintenance_prompts.py:1-1992`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_global 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[audit_operation_journal 与 _root 的协作实现]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 主要代码单元是 [[render_human_maintenance_prompt]]。
- 实现时会用到 [[rollback]]。
- 实现时会用到 [[validate]]。

## 谁会来到这里

- [[HumanMaintenancePromptRegistryTests]] 会使用这里提供的行为。
- [[HumanMaintenancePromptRegistryTests 等测试场景]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[render_human_maintenance_prompt]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[HumanMaintenancePromptRegistryTests]]
- [[HumanMaintenancePromptRegistryTests 等测试场景]]

## 内部细节

<details><summary>查看本页收纳的 35 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ParameterSpec` | `ParameterSpec` 用于完成局部输入校验、转换或状态更新。 |
| `CommandStep` | `CommandStep` 在 `human_maintenance_prompts.py` 中用于编排命令入口、执行顺序和退出结果。 |
| `RollbackContract` | `RollbackContract` 在 `human_maintenance_prompts.py` 中用于执行范围受控的恢复、撤销或清理。 |
| `ActionContract` | `ActionContract` 用于完成局部输入校验、转换或状态更新。 |
| `_p` | `_p` 用于完成局部输入校验、转换或状态更新。 |
| `_s` | `_s` 用于完成局部输入校验、转换或状态更新。 |
| `_requirements` | `_requirements` 用于完成局部输入校验、转换或状态更新。 |
| `_check_registry` | `_check_registry` 在 `human_maintenance_prompts.py` 中用于校验输入、状态、证据或输出合同。 |
| `list_human_maintenance_actions` | `list_human_maintenance_actions` 用于完成局部输入校验、转换或状态更新。 |
| `get_human_maintenance_action` | `get_human_maintenance_action` 用于完成局部输入校验、转换或状态更新。 |
| `_parameter_document` | `_parameter_document` 在 `human_maintenance_prompts.py` 中用于生成稳定排序的结构化表示或人类输出。 |
| `_step_document` | `_step_document` 在 `human_maintenance_prompts.py` 中用于生成稳定排序的结构化表示或人类输出。 |
| `human_maintenance_action_document` | `human_maintenance_action_document` 用于完成局部输入校验、转换或状态更新。 |
| `human_maintenance_registry_document` | `human_maintenance_registry_document` 用于完成局部输入校验、转换或状态更新。 |
| `serialize_human_maintenance_registry` | `serialize_human_maintenance_registry` 用于完成局部输入校验、转换或状态更新。 |
| `human_maintenance_registry_sha256` | `human_maintenance_registry_sha256` 用于完成局部输入校验、转换或状态更新。 |
| `_error` | `_error` 用于完成局部输入校验、转换或状态更新。 |
| `_parse_parameter_items` | `_parse_parameter_items` 在 `human_maintenance_prompts.py` 中用于解析、规范化并冻结调用输入。 |
| `_normalize_value` | `_normalize_value` 在 `human_maintenance_prompts.py` 中用于解析、规范化并冻结调用输入。 |
| `validate_human_maintenance_invocation` | `validate_human_maintenance_invocati…` 用于完成局部输入校验、转换或状态更新。 |
| `_quote` | `_quote` 用于完成局部输入校验、转换或状态更新。 |
| `_format_values` | `_format_values` 在 `human_maintenance_prompts.py` 中用于生成稳定排序的结构化表示或人类输出。 |
| `active_command_steps` | `active_command_steps` 在 `human_maintenance_prompts.py` 中用于编排命令入口、执行顺序和退出结果。 |
| `render_step_command` | `render_step_command` 在 `human_maintenance_prompts.py` 中用于生成稳定排序的结构化表示或人类输出。 |
| `_effective_requirement_state` | `_effective_requirement_state` 用于完成局部输入校验、转换或状态更新。 |
| `_effective_rollback_requirement` | `_effective_rollback_requirement` 用于完成局部输入校验、转换或状态更新。 |
| `_effective_rollback_mapping_and_command` | `_effective_rollback_mapping_and_com…` 用于完成局部输入校验、转换或状态更新。 |
| `_acceptance_template` | `_acceptance_template` 用于完成局部输入校验、转换或状态更新。 |
| `human_maintenance_delivery_template` | `human_maintenance_delivery_template` 用于完成局部输入校验、转换或状态更新。 |
| `_is_placeholder` | `该辅助函数` 用于完成局部输入校验、转换或状态更新。 |
| `_summary_parameter_items` | `_summary_parameter_items` 用于完成局部输入校验、转换或状态更新。 |
| `_literal_result_error` | `_literal_result_error` 用于完成局部输入校验、转换或状态更新。 |
| `_expected_rollback` | `_expected_rollback` 在 `human_maintenance_prompts.py` 中用于执行范围受控的恢复、撤销或清理。 |
| `audit_human_maintenance_delivery` | `audit_human_maintenance_delivery` 用于完成局部输入校验、转换或状态更新。 |
| `audit_human_maintenance_delivery_file` | `audit_human_maintenance_delivery_fi…` 用于完成局部输入校验、转换或状态更新。 |

</details>
