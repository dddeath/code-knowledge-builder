# audit_output_contract 与 _default_ckb 的协作实现

标签：#类型/代码

> `scripts/ckb_core/output_contract.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责投影并校验面向 Agent 的输出契约。

## 什么时候需要修改

当 `scripts/ckb_core/output_contract.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/output_contract.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/output_contract.py:1:1)  `scripts/ckb_core/output_contract.py:1-144`

## 相关代码

- 主要代码单元是 [[audit_output_contract]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]]。

## 谁会来到这里

- [[audit_output_contract]] 会使用这里提供的行为。
- [[create_batch_plan 与 ProtocolRelease 的协作实现]] 会使用这里提供的行为。
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[sync_human_layer]] 会使用这里提供的行为。

## 相关测试

- [[AgentProtocolBatchApplyTests]]
- [[CodeKnowledgeBuilderTests]]
- [[MigrationTest]]
- [[RecordReplaceTests]]
- [[ScopeExtensionTest]]
- [[command 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 7 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_default_ckb` | `_default_ckb` 是第 19-20 行的函数，供所属页面定位实现。 |
| `_runtime_binding` | `_runtime_binding` 是第 23-28 行的函数，供所属页面定位实现。 |
| `expected_output_contract` | `expected_output_contract` 是第 31-35 行的函数，供所属页面定位实现。 |
| `output_contract_for_runtime` | `output_contract_for_r...` 是第 38-58 行的函数，供所属页面定位实现。 |
| `_update_ownership` | `_update_ownership` 是第 61-73 行的函数，供所属页面定位实现。 |
| `project_output_contract` | `project_output_contract` 是第 76-97 行的函数，供所属页面定位实现。 |
| `remove_output_contract` | `remove_output_contract` 是第 100-108 行的函数，供所属页面定位实现。 |

</details>
