# ingest_event

标签：#类型/代码

> `ingest_event` 是 `scripts/ckb_core/automation.py` 第 1394-1504 行定义的函数，本页绑定该固定源码范围。 负责跨 Harness 自动化事件、会话状态、任务队列和 SQLite 状态的确定性处理。

## 什么时候需要修改

当 `ingest_event` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/automation.py 第 1394 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1394:1)  `scripts/ckb_core/automation.py:1394-1504`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.register 等测试场景]] 会使用这里提供的行为。
- [[SessionStdioLifecycleTests]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 汇总了本页。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[SessionStdioLifecycleTests]]
