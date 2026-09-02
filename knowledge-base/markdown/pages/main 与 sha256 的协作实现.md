# main 与 sha256 的协作实现

标签：#类型/代码

> 文件 `scripts/build_runtime_payload.py`负责构建并核验 Windows 完整运行时归档，包括 PDF 解析依赖、许可证和可重复载荷清单。 它属于完整发行包的运行时边界与可回滚部署依据，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当运行时依赖、归档成员、锁版本或完整性规则变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/build_runtime_payload.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/build_runtime_payload.py:1:1)  `scripts/build_runtime_payload.py:1-158`

## 相关代码

- 主要代码单元是 [[main（build_runtime_payload 实现）]]。

## 谁会来到这里

- [[PackageReleaseTests]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[PackageReleaseTests]]

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `sha256` | `sha256` 完成完整运行时归档校验中的一个明确步骤。 |
| `relative_files` | `relative_files` 完成完整运行时归档校验中的一个明确步骤。 |
| `validate_pdf_runtime` | `validate_pdf_runtime` 校验完整运行时归档校验所需的数据或状态。 |
| `build` | `build` 创建并初始化完整运行时归档校验所需的数据或状态。 |

</details>
