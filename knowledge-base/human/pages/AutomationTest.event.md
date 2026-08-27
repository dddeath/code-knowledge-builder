# AutomationTest.event

标签：#类型/代码

> `AutomationTest.event` 为测试构造统一的 Harness 事件夹具。 它默认附带精确 `applied_skills` 元数据，并允许测试显式关闭该字段以覆盖激活前静默分支。

## 什么时候需要修改

当测试事件公共字段或 Skill 激活证据结构变化时，需要修改该辅助函数。

## 在代码中的位置

[打开源码：tests/test_automation.py 第 80 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:80:1)  `tests/test_automation.py:80-90`

## 谁会来到这里

- [[AutomationTest.event 等测试场景]] 汇总了本页。
- [[LspClient.start 与 _version_matches 的协作实现]] 会使用这里提供的行为。
- [[MigrationTest]] 会使用这里提供的行为。
- [[ingest_event]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[parse_file 与 _language 的协作实现]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[render_integration]] 会使用这里提供的行为。
- [[render_integration 与 _looks_windows 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]
