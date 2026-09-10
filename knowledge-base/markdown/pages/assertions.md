# assertions

标签：#类型/代码

> 该函数按行解析固定标签断言 JSONL 文件，返回完整断言列表。 它为标签合同测试提供同一组冻结输入，不过滤空行或修复格式错误，输入问题会直接暴露。

## 什么时候需要修改

fixture 路径或逐行 JSON 格式变化时修改此函数，并检查测试读取的断言集合保持一致。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_contracts.py 第 23 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_contracts.py:23:1)  `tests/test_ckb_tag_navigation_contracts.py:23-24`

## 谁会来到这里

- [[assertions 等测试场景]] 汇总了本页。
