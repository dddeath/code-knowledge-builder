# parse_file

标签：#类型/代码

> `parse_file` 是源码中负责解析命名声明并保存稳定源码范围的命名代码单元。 它在所属模块内执行解析命名声明并保存稳定源码范围，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当解析命名声明并保存稳定源码范围所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/parsers.py 第 191 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/parsers.py:191:1)  `scripts/ckb_core/parsers.py:191-329`

## 相关代码

- 实现时会用到 [[AutomationTest.event]]。
- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[LspClient.start 与 _version_matches 的协作实现]]。
- 实现时会用到 [[parse_file 与 _language 的协作实现]]。
- 实现时会用到 [[parser]]。
- 实现时会用到 [[remove]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[parse_file 与 _language 的协作实现]] 汇总了本页。
- [[status 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
