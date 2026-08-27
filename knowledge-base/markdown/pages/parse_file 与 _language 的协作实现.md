# parse_file 与 _language 的协作实现

标签：#类型/代码

> 该文件集中实现Tree-sitter 实体提取、C# partial 合并和词法引用关系。 它是 Code Knowledge Builder 中承载Tree-sitter 实体提取、C# partial 合并和词法引用关系的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当Tree-sitter 实体提取、C# partial 合并和词法引用关系的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/parsers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/parsers.py:1:1)  `scripts/ckb_core/parsers.py:1-437`

## 相关代码

- 实现时会用到 [[AutomationTest.event]]。
- 实现时会用到 [[LspClient.start]]。
- 主要代码单元是 [[parse_file]]。
- 实现时会用到 [[remove]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。

## 谁会来到这里

- [[parse_file]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 10 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_language` | 该附属代码负责Tree-sitter 实体提取、C# partial 合并和词法引用关系，并把结果交给所属页面中的主流程使用。 |
| `_walk` | 该附属代码负责Tree-sitter 实体提取、C# partial 合并和词法引用关系，并把结果交给所属页面中的主流程使用。 |
| `_node_text` | 该附属代码负责Tree-sitter 实体提取、C# partial 合并和词法引用关系，并把结果交给所属页面中的主流程使用。 |
| `_byte_position` | 该附属代码负责Tree-sitter 实体提取、C# partial 合并和词法引用关系，并把结果交给所属页面中的主流程使用。 |
| `_find_name` | 该附属代码负责Tree-sitter 实体提取、C# partial 合并和词法引用关系，并把结果交给所属页面中的主流程使用。 |
| `_public_evidence` | 该附属代码负责Tree-sitter 实体提取、C# partial 合并和词法引用关系，并把结果交给所属页面中的主流程使用。 |
| `_single_statement_shape` | 该附属代码负责计算机器交付物的完整性摘要，并把结果交给所属页面中的主流程使用。 |
| `_csharp_fallback_name` | 该附属代码负责计算机器交付物的完整性摘要，并把结果交给所属页面中的主流程使用。 |
| `merge_csharp_partials` | 该附属代码负责合并批次实体和跨批次关系，并把结果交给所属页面中的主流程使用。 |
| `lexical_links` | 该附属代码负责Tree-sitter 实体提取、C# partial 合并和词法引用关系，并把结果交给所属页面中的主流程使用。 |

</details>
