# validate_human_maintenance_invocation

标签：#类型/代码

> `validate_human_maintenance_invocation` 位于 `scripts/ckb_core/human_maintenance_prompts.py` 第 1391-1516 行，用于核对参数化维护动作的必填参数、类型、确认点和停止条件。 `validate_human_maintenance_invocation` 在参数化人类维护 Prompt 的动作合同、渲染和交付核对中负责核对参数化维护动作的必填参数、类型、确认点和停止条件。

## 什么时候需要修改

当 `validate_human_maintenance_invocation` 的输入、输出、状态转换或失败边界变化时，应更新对应说明和测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_maintenance_prompts.py 第 1391 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_maintenance_prompts.py:1391:1)  `scripts/ckb_core/human_maintenance_prompts.py:1391-1516`

## 相关代码

- 实现时会用到 [[FactFreshnessStateMachineTest]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[validate_human_maintenance_invocation 与 ParameterSpec 的协作实现]]。

## 谁会来到这里

- [[HumanMaintenancePromptRegistryTests 等测试场景]] 会使用这里提供的行为。
- [[validate_human_maintenance_invocation 与 ParameterSpec 的协作实现]] 汇总了本页。

## 相关测试

- [[HumanMaintenancePromptRegistryTests 等测试场景]]
