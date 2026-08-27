# render_integration

标签：#类型/代码

> `render_integration` 在隔离目录中生成指定 Harness 的完整适配包和清单。 它写入 Hook/Plugin 文件，并在 `integration.json` 固定 `session_skill_activation_required=true` 与精确 required skill。

## 什么时候需要修改

当适配器文件布局、集成版本、激活字段或宿主命令模板变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/ckb_core/automation_integrations.py 第 391 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:391:1)  `scripts/ckb_core/automation_integrations.py:391-501`

## 相关代码

- 实现时会用到 [[AutomationTest.event]]。
- 实现时会用到 [[render_integration 与 _looks_windows 的协作实现]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[render_integration 与 _looks_windows 的协作实现]] 汇总了本页。

## 相关测试

- [[AutomationTest.event 等测试场景]]

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `render_integration.write` | 把适配器文件按 UTF-8 写入隔离目标并登记到清单。 |

</details>
