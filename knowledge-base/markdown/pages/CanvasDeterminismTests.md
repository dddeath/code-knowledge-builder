# CanvasDeterminismTests

标签：#类型/代码

> `CanvasDeterminismTests` 位于 `tests/test_ckb_canvas_determinism.py` 第 20-52 行，本页用固定源码范围说明它如何验证目标行为、失败分类和回归边界。 `CanvasDeterminismTests` 负责在对应能力的可执行成功、失败和回归验证中验证目标行为、失败分类和回归边界。

## 什么时候需要修改

当 `tests/test_ckb_canvas_determinism.py` 中 `CanvasDeterminismTests` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：tests/test_ckb_canvas_determinism.py 第 20 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_canvas_determinism.py:20:1)  `tests/test_ckb_canvas_determinism.py:20-52`

## 相关代码

- 实现时会用到 [[build_case]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[graph 的协作边界]]。
- 实现时会用到 [[rollback]]。
- 实现时会用到 [[rollback 与 RenderedBundle 的协作实现]]。

## 谁会来到这里

- [[CanvasDeterminismTests 等测试场景]] 汇总了本页。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 关联到这里的验证场景。
- [[SourceLinkRenderer.uri]] 关联到这里的验证场景。
- [[build_case]] 关联到这里的验证场景。
- [[freeze 的协作边界]] 关联到这里的验证场景。
- [[graph 的协作边界]] 关联到这里的验证场景。
- [[render_integration 与 _looks_windows 的协作实现]] 关联到这里的验证场景。
- [[rollback 与 RenderedBundle 的协作实现]] 关联到这里的验证场景。
- [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]] 关联到这里的验证场景。
- [[source_files]] 关联到这里的验证场景。
- [[validate]] 关联到这里的验证场景。
- [[validate 与 canonical 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `CanvasDeterminismTests.test_ten_generations_have_one_canvas_and_two_single_manifest_hashes` | `test_ten_generations_have_one_canva…` 用于完成局部输入校验、转换或状态更新。 |

</details>
