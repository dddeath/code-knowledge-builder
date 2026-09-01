# main 与 sha256 的协作实现

标签：#类型/代码

> 该文件集中实现离线运行时清单、可复现压缩和归档校验。 它是 Code Knowledge Builder 中承载离线运行时清单、可复现压缩和归档校验的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当离线运行时清单、可复现压缩和归档校验的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/build_runtime_payload.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/build_runtime_payload.py:1:1)  `scripts/build_runtime_payload.py:1-117`

## 相关代码

- 主要代码单元是 [[main（build_runtime_payload 实现）]]。

## 谁会来到这里

- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 3 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `sha256` | 该附属代码负责计算机器交付物的完整性摘要，并把结果交给所属页面中的主流程使用。 |
| `relative_files` | 该附属代码负责离线运行时清单、可复现压缩和归档校验，并把结果交给所属页面中的主流程使用。 |
| `build` | `build` 是第 32-98 行的函数，供所属页面定位实现。 |

</details>
