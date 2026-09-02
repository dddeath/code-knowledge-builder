# TagNavigationCanvasCompatibilityTests 等测试场景

标签：#类型/代码

> 文件 `tests/test_ckb_tag_navigation_canvas_compatibility.py`负责验证 tag 实验不会改变既有 JSON Canvas 合同。 它属于tag 与 Canvas 两个实验之间的兼容保护，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当任一实验的文件或 Schema 边界变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_canvas_compatibility.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_canvas_compatibility.py:1:1)  `tests/test_ckb_tag_navigation_canvas_compatibility.py:1-50`

## 相关代码

- 主要代码单元是 [[TagNavigationCanvasCompatibilityTests]]。

## 谁会来到这里

- [[TagNavigationCanvasCompatibilityTests]] 会使用这里提供的行为。
- 可从 [[tests 职责导览]] 进入本页。

## 相关测试

- [[TagNavigationCanvasCompatibilityTests]]

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `digest_tree` | `digest_tree` 完成tag 与 Canvas 兼容测试所需的一个明确步骤。 |

</details>
