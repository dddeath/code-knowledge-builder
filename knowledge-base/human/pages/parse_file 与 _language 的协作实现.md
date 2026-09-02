# parse_file 与 _language 的协作实现

标签：#类型/代码

> 文件 `scripts/ckb_core/parsers.py`负责从固定源码提取结构，并把可局部归因的 C++ 语法问题降级为有边界警告。 它属于源码图谱事实生成与语法失败边界的第一层判断，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当语言语法、实体分类、警告标识、影响范围或失败升级规则变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/parsers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/parsers.py:1:1)  `scripts/ckb_core/parsers.py:1-719`

## 相关代码

- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 主要代码单元是 [[parse_file]]。
- 实现时会用到 [[parser]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。

## 谁会来到这里

- [[parse_file]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]

## 内部细节

<details><summary>查看本页收纳的 18 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_language` | `_language` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_walk` | `_walk` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_node_text` | `_node_text` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_byte_position` | `_byte_position` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_find_name` | `_find_name` 读取并判定源码结构与局部语法警告提取所需的数据或状态。 |
| `_public_evidence` | `_public_evidence` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_single_statement_shape` | `_single_statement_shape` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_csharp_fallback_name` | `_csharp_fallback_name` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_has_ancestor` | `_has_ancestor` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_cpp_function_declarator_kind` | `_cpp_function_declarator_kind` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_cpp_explicit_class_instantiation_recovery` | `_cpp_explicit_class_instantiation_r…` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_parse_diagnostics` | `_parse_diagnostics` 解析并归一化源码结构与局部语法警告提取所需的数据或状态。 |
| `_union_size` | `_union_size` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_diagnostic_contract` | `_diagnostic_contract` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `_diagnostic_overlaps` | `_diagnostic_overlaps` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `syntax_warning_id` | `syntax_warning_id` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `merge_csharp_partials` | `merge_csharp_partials` 完成源码结构与局部语法警告提取中的一个明确步骤。 |
| `lexical_links` | `lexical_links` 完成源码结构与局部语法警告提取中的一个明确步骤。 |

</details>
