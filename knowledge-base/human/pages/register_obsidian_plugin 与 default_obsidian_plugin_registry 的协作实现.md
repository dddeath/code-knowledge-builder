# register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现

标签：#类型/代码

> `scripts/ckb_core/obsidian_plugin.py` 是 `scripts/ckb_core/obsidian_plugin.py` 中负责汇总并提供Obsidian Companion 包注册、部署、状态与移除的文件入口。 它按源码所示的参数、条件分支和数据结构完成汇总并提供Obsidian Companion 包注册、部署、状态与移除，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当Obsidian Companion 包注册、部署、状态与移除的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/obsidian_plugin.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian_plugin.py:1:1)  `scripts/ckb_core/obsidian_plugin.py:1-262`

## 相关代码

- 实现时会用到 [[AutomationTest.register]]。
- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[audit_output_contract]]。
- 实现时会用到 [[audit_output_contract 与 _default_ckb 的协作实现]]。
- 主要代码单元是 [[register_obsidian_plugin]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[audit_global]] 会使用这里提供的行为。
- [[audit_obsidian]] 会使用这里提供的行为。
- [[audit_obsidian 与 prepare_vault 的协作实现]] 会使用这里提供的行为。
- [[audit_output_contract]] 会使用这里提供的行为。
- [[audit_output_contract 与 _default_ckb 的协作实现]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[register_obsidian_plugin]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanPageTemplateValidationTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[MigrationTest]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 10 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `default_obsidian_plugin_registry` | 返回默认 `obsidian_plugin_registry` 对应的数据与约束。 |
| `obsidian_plugin_installation` | 处理 `plugin_installation` 对应的数据与约束。 |
| `_payload_from_package` | 处理 `from_package` 对应的数据与约束。 |
| `_validate_payload` | 验证 `payload` 对应的数据与约束。 |
| `_registered_payload` | 处理 `payload` 对应的数据与约束。 |
| `deploy_obsidian_plugin_to_vault` | 部署 `obsidian_plugin_to_vault` 对应的数据与约束。 |
| `deploy_obsidian_plugin` | 部署 `obsidian_plugin` 对应的数据与约束。 |
| `obsidian_plugin_status` | 汇总 `obsidian_plugin_status` 状态与计数。 |
| `remove_obsidian_plugin` | 移除 `obsidian_plugin` 对应的数据与约束。 |
| `deploy_registered_plugin_if_available` | 部署 `registered_plugin_if_available` 对应的数据与约束。 |

</details>
