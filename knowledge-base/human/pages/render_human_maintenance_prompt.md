# render_human_maintenance_prompt

标签：#类型/代码

> `render_human_maintenance_prompt` 位于 `scripts/ckb_core/human_maintenance_prompts.py` 第 1918-1991 行，本页用固定源码范围说明它如何生成稳定排序的结构化表示或人类输出。 `render_human_maintenance_prompt` 负责在稳定维护 Prompt 的 action 映射、渲染和交付审计中生成稳定排序的结构化表示或人类输出。

## 什么时候需要修改

当 `scripts/ckb_core/human_maintenance_prompts.py` 中 `render_human_maintenance_prompt` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_maintenance_prompts.py 第 1918 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_maintenance_prompts.py:1918:1)  `scripts/ckb_core/human_maintenance_prompts.py:1918-1991`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]]。
- 实现时会用到 [[rollback]]。

## 谁会来到这里

- [[HumanMaintenancePromptRegistryTests 等测试场景]] 会使用这里提供的行为。
- [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]] 汇总了本页。

## 相关测试

- [[HumanMaintenancePromptRegistryTests 等测试场景]]
