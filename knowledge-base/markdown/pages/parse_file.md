# parse_file

标签：#类型/代码

> 代码单元 `parse_file`负责从固定源码提取结构，并把可局部归因的 C++ 语法问题降级为有边界警告。 它属于源码图谱事实生成与语法失败边界的第一层判断，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当语言语法、实体分类、警告标识、影响范围或失败升级规则变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/parsers.py 第 383 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/parsers.py:383:1)  `scripts/ckb_core/parsers.py:383-611`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[doctor_report 与 _version_matches 的协作实现]]。
- 实现时会用到 [[parse_file 与 _language 的协作实现]]。
- 实现时会用到 [[parser]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[finalize 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[parse_file 与 _language 的协作实现]] 汇总了本页。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
