# deployment_plan 与 skill_root 的协作实现

标签：#类型/代码

> 该文件集中实现私有离线运行时部署、复用检查和移除。 它是 Code Knowledge Builder 中承载私有离线运行时部署、复用检查和移除的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当私有离线运行时部署、复用检查和移除的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/runtime.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/runtime.py:1:1)  `scripts/ckb_core/runtime.py:1-153`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 主要代码单元是 [[deployment_plan]]。
- 实现时会用到 [[doctor_report 与 _version_matches 的协作实现]]。

## 谁会来到这里

- [[deployment_plan]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 6 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `skill_root` | 该附属代码负责私有离线运行时部署、复用检查和移除，并把结果交给所属页面中的主流程使用。 |
| `lock_document` | 该附属代码负责私有离线运行时部署、复用检查和移除，并把结果交给所属页面中的主流程使用。 |
| `payload_path` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `deploy` | 该附属代码负责管理隔离离线运行时及其回滚，并把结果交给所属页面中的主流程使用。 |
| `remove` | 移除 `remove` 对应的数据与约束。 |
| `_host_snapshot` | 该附属代码负责建立并验证与固定提交一致的源码快照，并把结果交给所属页面中的主流程使用。 |

</details>
