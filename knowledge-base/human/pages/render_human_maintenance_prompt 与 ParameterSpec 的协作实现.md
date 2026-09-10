# render_human_maintenance_prompt 与 ParameterSpec 的协作实现

标签：#类型/代码

> `scripts/ckb_core/human_maintenance_prompts.py` 页面绑定固定源码第 1-2010 行，说明该文件如何承担参数化人类维护 Prompt 的动作合同、渲染和交付核对。 该文件负责参数化人类维护 Prompt 的动作合同、渲染和交付核对，并为相关命令、页面生成或测试提供源码入口。

## 什么时候需要修改

当 `scripts/ckb_core/human_maintenance_prompts.py` 的公开输入、生成结果、状态边界或与其他模块的协作关系变化时，应更新本页。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_maintenance_prompts.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_maintenance_prompts.py:1:1)  `scripts/ckb_core/human_maintenance_prompts.py:1-2010`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[render_human_maintenance_prompt]]。

## 谁会来到这里

- 与 [[render_human_maintenance_prompt]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_management_task 与 default_management_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 35 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ParameterSpec` | 保存维护参数的名称、类型、中文含义、必填标记、默认值和候选值集合。 |
| `CommandStep` | 保存执行步骤的指令、能力映射、条件参数、输入字段及预期结果约定。 |
| `RollbackContract` | 保存恢复要求、中文说明、命令模板、能力映射与外部依赖说明。 |
| `ActionContract` | 保存一个维护动作的目的、参数、步骤、确认条件、交付字段与恢复合同。 |
| `_p` | 组合参数名称、类型和约束，并把候选值序列转换为不可变元组。 |
| `_s` | 将步骤参数中的序列转换为元组，构造包含条件和结果约定的步骤合同。 |
| `_requirements` | 按固定顺序组合检索、来源、维护和人类审阅四类要求及其状态。 |
| `_check_registry` | `_check_registry` 用于检查内部不变量并拒绝不一致状态。 |
| `list_human_maintenance_actions` | `list_human_maintenance_actions` 用于读取、定位并返回现有状态。 |
| `get_human_maintenance_action` | `get_human_maintenance_action` 用于读取、定位并返回现有状态。 |
| `_parameter_document` | 将单个参数合同导出为含默认值、必填条件和候选值的独立字典。 |
| `_step_document` | 把步骤合同序列化为字典，保留执行条件、输入字段和输出格式约定。 |
| `human_maintenance_action_document` | 将动作合同转换为独立字典，完整保留参数、步骤、确认点、交付与恢复要求。 |
| `human_maintenance_registry_document` | 按登记顺序导出全部维护动作及协议版本，形成统一注册表文档。 |
| `serialize_human_maintenance_registry` | 以固定键排序和紧凑格式序列化维护注册表，保留中文并追加末尾换行。 |
| `human_maintenance_registry_sha256` | `human_maintenance_registry_sha256` 用于生成稳定序列化或内容摘要。 |
| `_error` | 将错误原因、中文消息和补充字段组合为统一错误对象。 |
| `_parse_parameter_items` | `_parse_parameter_items` 用于解析结构化输入并形成规范表示。 |
| `_normalize_value` | `_normalize_value` 用于规范化输入字段并拒绝未知或越界值。 |
| `validate_human_maintenance_invocation` | 解析 action 参数并按合同补默认值和校验类型，额外拒绝安装/建库职责混用、缺失人类确认、未知许可和模板版本或暂存边界冲突，返回规范参数与全部错误。 |
| `_quote` | 将参数包在单引号内并转义内部单引号，保持 PowerShell 参数边界。 |
| `_format_values` | 将参数转换为引号转义值与原始值，并按条件拼接作者、修订、来源和范围选项。 |
| `active_command_steps` | 按已给参数筛选满足启用条件的执行步骤，保持合同中的原有顺序。 |
| `render_step_command` | `render_step_command` 用于把结构化状态渲染为稳定输出。 |
| `_effective_requirement_state` | 按模板操作计算来源与人类审阅的实际要求，其他条件保留原声明。 |
| `_effective_rollback_requirement` | 按模板操作判定是否需要回滚或外部恢复依赖，其他动作沿用合同声明。 |
| `_effective_rollback_mapping_and_command` | 把页面打包的恢复标为外部依赖，其余动作按需要渲染已有恢复命令。 |
| `_acceptance_template` | 根据实际启用步骤生成交付模板，列出待填的命令结果、验收字段和恢复证据。 |
| `human_maintenance_delivery_template` | 校验动作参数后生成对应交付模板，参数无效时返回明确错误而不生成模板。 |
| `_is_placeholder` | 该函数识别交付摘要中尚未替换的类型槽和占位值。 |
| `_summary_parameter_items` | 将交付摘要参数还原为名称和值列表，保留未知键供后续检查并拒绝复合类型。 |
| `_literal_result_error` | 拒绝空输出和启动提示，按步骤检查结果格式与完成状态，返回首个证据错误。 |
| `_expected_rollback` | 从动作及参数对应的交付模板中取得预期恢复要求。 |
| `audit_human_maintenance_delivery` | `audit_human_maintenance_delivery` 用于汇总并判断受控对象是否满足当前合同。 |
| `audit_human_maintenance_delivery_file` | `audit_human_maintenance_delivery_file` 用于汇总并判断受控对象是否满足当前合同。 |

</details>
