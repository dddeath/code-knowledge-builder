# render_integration

标签：#类型/代码

> `render_integration` 为目标 Harness 生成自动化适配文件及机器清单，并在清单中写入该 Harness 的检索契约。 它连接项目注册、会话事件、管理能力和跨 Harness 检索入口，但不把静态声明冒充为运行时验证。

## 什么时候需要修改

当适配器文件、manifest schema、管理能力或检索契约字段变化时，应更新本函数和安装副本测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/automation_integrations.py 第 512 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:512:1)  `scripts/ckb_core/automation_integrations.py:512-655`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[render_integration 与 harness_retrieval_contract 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_management_task 与 default_management_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[render_integration 与 harness_retrieval_contract 的协作实现]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `render_integration.write` | `render_integration.write` 是第 461-467 行的函数，供所属页面定位实现。 |

</details>
