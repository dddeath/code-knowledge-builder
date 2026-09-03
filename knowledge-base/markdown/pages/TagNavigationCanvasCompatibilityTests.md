# TagNavigationCanvasCompatibilityTests

标签：#类型/代码

> 代码单元 `test_canvas_contract_remains_valid_and_byte_unchanged`负责验证 tag 实验不会改变既有 JSON Canvas 合同。 它属于tag 与 Canvas 两个实验之间的兼容保护，说明只覆盖所列固定源码范围。

## 什么时候需要修改

当任一实验的文件或 Schema 边界变化时，应同步复查本页及其直接测试。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_canvas_compatibility.py 第 32 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_canvas_compatibility.py:32:1)  `tests/test_ckb_tag_navigation_canvas_compatibility.py:32-45`

## 相关代码

- 实现时会用到 [[TagNavigationCanvasCompatibilityTests 等测试场景]]。
- 实现时会用到 [[assertions]]。
- 实现时会用到 [[contracts 的协作边界（36093e4a）]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[projection 的协作边界]]。
- 实现时会用到 [[state_machine 的协作边界]]。

## 谁会来到这里

- [[TagNavigationCanvasCompatibilityTests 等测试场景]] 汇总了本页。
- [[assertions]] 关联到这里的验证场景。
- [[projection 的协作边界]] 关联到这里的验证场景。
- [[state_machine 的协作边界]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `TagNavigationCanvasCompatibilityTests.test_canvas_contract_remains_valid_and_byte_unchanged` | 该测试验证“canvas contract remains valid…”场景，保护tag 与 Canvas 兼容测试的结果与失败边界。 |

</details>
