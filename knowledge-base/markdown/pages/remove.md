# remove

标签：#类型/代码

> `remove` 是源码中负责管理隔离离线运行时及其回滚的命名代码单元。 它在所属模块内执行管理隔离离线运行时及其回滚，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当管理隔离离线运行时及其回滚所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/runtime.py 第 126 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/runtime.py:126:1)  `scripts/ckb_core/runtime.py:126-147`

## 相关代码

- 实现时会用到 [[LspClient.start 与 _version_matches 的协作实现]]。
- 实现时会用到 [[remove 与 skill_root 的协作实现]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[create_source_snapshot 与 git 的协作实现]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[parse_file 与 _language 的协作实现]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[remove 与 skill_root 的协作实现]] 汇总了本页。

## 相关测试

- [[MigrationTest]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]
