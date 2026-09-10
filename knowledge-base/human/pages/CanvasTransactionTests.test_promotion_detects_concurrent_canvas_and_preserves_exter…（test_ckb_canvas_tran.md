# CanvasTransactionTests.test_promotion_detects_concurrent_canvas_and_preserves_exter…（test_ckb_canvas_transaction 测试）

标签：#类型/代码

> 在发布前模拟外部改写，检验 Canvas 保留外部字节并终止本次发布。 覆盖并发修改冲突，检查失败后不残留本次验证与回滚清单。

## 什么时候需要修改

调整发布顺序、冲突识别或失败清理时补测。

## 在代码中的位置

[打开源码：tests/test_ckb_canvas_transaction.py 第 55 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_canvas_transaction.py:55:1)  `tests/test_ckb_canvas_transaction.py:55-75`

## 谁会来到这里

- [[CanvasTransactionTests.test_promotion_detects_concurrent_canvas_and_preserves_exter…（tests/test_ckb_canvas_transaction.py:1）]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `CanvasTransactionTests.test_promotion_detects_concurrent_canvas_and_preserves_external_bytes.hook` | `hook` 在 `test_ckb_canvas_transaction.py` 中用于验证目标行为、失败分类和回归边界。 |

</details>
