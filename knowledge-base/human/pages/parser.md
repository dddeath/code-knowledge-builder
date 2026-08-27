# parser

标签：#类型/代码

> `parser` 定义 Code Knowledge Builder 的完整命令树和参数约束。 它为自动化增加 `activate` 子命令，接收 Harness、session、任务根、注册表和激活来源，同时保留原有构建与审计接口。

## 什么时候需要修改

当命令名称、参数默认值、Harness 列表或激活握手字段变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 115 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:115:1)  `scripts/ckb.py:115-324`

## 相关代码

- 实现时会用到 [[AutomationTest.event]]。
- 实现时会用到 [[AutomationTest.event 等测试场景]]。
- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[add_git_bootstrap_arguments]]。
- 实现时会用到 [[add_initial_arguments]]。
- 实现时会用到 [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[remove]]。
- 实现时会用到 [[remove 与 skill_root 的协作实现]]。
- 实现时会用到 [[retrieve]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[status 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[add_git_bootstrap_arguments]] 会使用这里提供的行为。
- [[add_initial_arguments]] 会使用这里提供的行为。
- [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]] 汇总了本页。
- [[create_source_snapshot]] 会使用这里提供的行为。
- [[execute 等测试场景]] 会使用这里提供的行为。
- [[main（build_runtime_payload 实现）]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[main（generate_large_fixture 测试）]] 会使用这里提供的行为。
- [[main（make_source_patch 实现）]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[source_files 与 sha256 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[MigrationTest]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]
