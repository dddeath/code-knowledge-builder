# web_input_adapter_contract 与 ReferenceInputRequest 的协作实现

标签：#类型/代码

> 文件 `scripts/ckb_core/reference_inputs.py`负责定义本地文件与 Web 等参考输入适配器的最小协议。 它属于新增资料来源而不改变参考资料主流程的扩展边界，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当输入类型、适配器责任、准备结果或网络权限边界变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_inputs.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_inputs.py:1:1)  `scripts/ckb_core/reference_inputs.py:1-77`

## 相关代码

- 主要代码单元是 [[web_input_adapter_contract]]。

## 谁会来到这里

- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `ReferenceInputRequest` | `ReferenceInputRequest` 完成参考输入适配协议中的一个明确步骤。 |
| `PreparedReferenceInput` | `PreparedReferenceInput` 创建并初始化参考输入适配协议所需的数据或状态。 |
| `ReferenceInputAdapter` | `prepare` 创建并初始化参考输入适配协议所需的数据或状态。 |
| `ReferenceInputAdapter.prepare` | `prepare` 创建并初始化参考输入适配协议所需的数据或状态。 |

</details>
