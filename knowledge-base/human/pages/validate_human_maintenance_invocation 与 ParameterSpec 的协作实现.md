# validate_human_maintenance_invocation 与 ParameterSpec 的协作实现

标签：#类型/代码

> `scripts/ckb_core/human_maintenance_prompts.py` 页面绑定固定源码第 1-2010 行，说明该文件如何承担参数化人类维护 Prompt 的动作合同、渲染和交付核对。 该文件负责参数化人类维护 Prompt 的动作合同、渲染和交付核对，并为相关命令、页面生成或测试提供源码入口。

## 什么时候需要修改

当 `scripts/ckb_core/human_maintenance_prompts.py` 的公开输入、生成结果、状态边界或与其他模块的协作关系变化时，应更新本页。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_maintenance_prompts.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_maintenance_prompts.py:1:1)  `scripts/ckb_core/human_maintenance_prompts.py:1-2010`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[FactFreshnessStateMachineTest]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_operation_journal 与 _root 的协作实现]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[validate]]。
- 主要代码单元是 [[validate_human_maintenance_invocation]]。

## 谁会来到这里

- [[HumanMaintenancePromptRegistryTests]] 会使用这里提供的行为。
- [[HumanMaintenancePromptRegistryTests 等测试场景]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[validate_human_maintenance_invocation]] 会使用这里提供的行为。

## 相关测试

- [[HumanMaintenancePromptRegistryTests]]
- [[HumanMaintenancePromptRegistryTests 等测试场景]]

## 内部细节

<details><summary>查看本页收纳的 35 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ParameterSpec` | `ParameterSpec` 用于处理当前模块的结构化输入或状态。 |
| `CommandStep` | `CommandStep` 用于处理当前模块的结构化输入或状态。 |
| `RollbackContract` | `RollbackContract` 用于处理当前模块的结构化输入或状态。 |
| `ActionContract` | `ActionContract` 用于处理当前模块的结构化输入或状态。 |
| `_p` | `_p` 用于处理当前模块的结构化输入或状态。 |
| `_s` | `_s` 用于处理当前模块的结构化输入或状态。 |
| `_requirements` | `_requirements` 用于处理当前模块的结构化输入或状态。 |
| `_check_registry` | `_check_registry` 用于检查内部不变量并拒绝不一致状态。 |
| `list_human_maintenance_actions` | `list_human_maintenance_actions` 用于读取、定位并返回现有状态。 |
| `get_human_maintenance_action` | `get_human_maintenance_action` 用于读取、定位并返回现有状态。 |
| `_parameter_document` | `_parameter_document` 用于处理当前模块的结构化输入或状态。 |
| `_step_document` | `_step_document` 用于处理当前模块的结构化输入或状态。 |
| `human_maintenance_action_document` | `human_maintenance_action_document` 用于处理当前模块的结构化输入或状态。 |
| `human_maintenance_registry_document` | `human_maintenance_registry_document` 用于处理当前模块的结构化输入或状态。 |
| `serialize_human_maintenance_registry` | `serialize_human_maintenance_registry` 用于处理当前模块的结构化输入或状态。 |
| `human_maintenance_registry_sha256` | `human_maintenance_registry_sha256` 用于生成稳定序列化或内容摘要。 |
| `_error` | `_error` 用于处理当前模块的结构化输入或状态。 |
| `_parse_parameter_items` | `_parse_parameter_items` 用于解析结构化输入并形成规范表示。 |
| `_normalize_value` | `_normalize_value` 用于规范化输入字段并拒绝未知或越界值。 |
| `_quote` | `_quote` 用于处理当前模块的结构化输入或状态。 |
| `_format_values` | `_format_values` 用于处理当前模块的结构化输入或状态。 |
| `active_command_steps` | `active_command_steps` 用于处理当前模块的结构化输入或状态。 |
| `render_step_command` | `render_step_command` 用于把结构化状态渲染为稳定输出。 |
| `_effective_requirement_state` | `_effective_requirement_state` 用于处理当前模块的结构化输入或状态。 |
| `_effective_rollback_requirement` | `_effective_rollback_requirement` 用于处理当前模块的结构化输入或状态。 |
| `_effective_rollback_mapping_and_command` | `_effective_rollback_mapping_and_command` 用于处理当前模块的结构化输入或状态。 |
| `_acceptance_template` | `_acceptance_template` 用于处理当前模块的结构化输入或状态。 |
| `human_maintenance_delivery_template` | `human_maintenance_delivery_template` 用于处理当前模块的结构化输入或状态。 |
| `_is_placeholder` | 该函数识别交付摘要中尚未替换的类型槽和占位值。 |
| `_summary_parameter_items` | `_summary_parameter_items` 用于处理当前模块的结构化输入或状态。 |
| `_literal_result_error` | `_literal_result_error` 用于处理当前模块的结构化输入或状态。 |
| `_expected_rollback` | `_expected_rollback` 用于处理当前模块的结构化输入或状态。 |
| `audit_human_maintenance_delivery` | `audit_human_maintenance_delivery` 用于汇总并判断受控对象是否满足当前合同。 |
| `audit_human_maintenance_delivery_file` | `audit_human_maintenance_delivery_file` 用于汇总并判断受控对象是否满足当前合同。 |
| `render_human_maintenance_prompt` | `render_human_maintenance_prompt` 用于把结构化状态渲染为稳定输出。 |

</details>
