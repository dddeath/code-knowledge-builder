# digest_tree

标签：#类型/代码

> 该函数递归收集根目录文件的相对路径和 SHA-256，排除 Python 字节码缓存目录。 它为标签实验前后 Canvas 原型未改动提供文件集合和字节基线，既检查内容变化也体现文件增删。

## 什么时候需要修改

兼容性保护目录或应忽略的生成缓存规则变化时修改此函数，并检查稳定文件仍被纳入摘要。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_canvas_compatibility.py 第 24 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_canvas_compatibility.py:24:1)  `tests/test_ckb_tag_navigation_canvas_compatibility.py:24-29`

## 谁会来到这里

- [[digest_tree 等测试场景]] 汇总了本页。
