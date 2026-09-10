# parse_file

标签：#类型/代码

> 将固定源码解析为带范围、父子归属和来源完整性标记的实体集合。 从 Tree-sitter 声明提取候选实体并保留诊断；局部语法问题附带警告与低置信度标记，整体不可用时仍返回失败。

## 什么时候需要修改

调整 C++ 声明识别、页面候选分类、解析对象生命周期或局部错误传播时修改。

## 在代码中的位置

[打开源码：scripts/ckb_core/parsers.py 第 383 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/parsers.py:383:1)  `scripts/ckb_core/parsers.py:383-611`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[parse_file 与 _language 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[parse_file 与 _language 的协作实现]] 汇总了本页。
