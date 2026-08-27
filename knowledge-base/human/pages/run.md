# run

标签：#类型/代码

> `run` 是源码中负责错误类型、JSON 写入、子进程调用、路径约束和状态标记的命名代码单元。 它在所属模块内执行错误类型、JSON 写入、子进程调用、路径约束和状态标记，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当错误类型、JSON 写入、子进程调用、路径约束和状态标记所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/common.py 第 77 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:77:1)  `scripts/ckb_core/common.py:77-99`

## 相关代码

- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.event 等测试场景]] 会使用这里提供的行为。
- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[LspClient.start 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[MigrationTest 等测试场景]] 会使用这里提供的行为。
- [[create_source_snapshot]] 会使用这里提供的行为。
- [[create_source_snapshot 与 git 的协作实现]] 会使用这里提供的行为。
- [[execute]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[main（generate_large_fixture 测试）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[query_graph 与 _networkx_modules 的协作实现]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[run 与 CkbError 的协作实现]] 汇总了本页。
- [[status 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
