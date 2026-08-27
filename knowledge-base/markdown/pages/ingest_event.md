# ingest_event

标签：#类型/代码

> `ingest_event` 是所有 Harness Hook 进入 CKB 自动化核心的统一边界。 它先匹配项目，再核对当前 session 的精确 Skill 激活；显式 prompt、原生 Skill 元数据或已登记激活通过后才脱敏、入队和写入数据库。

## 什么时候需要修改

当项目路由、激活判据、静默忽略语义、脱敏或 Hook 输出约定变化时，需要修改该函数并重跑正反向 canary。

## 在代码中的位置

[打开源码：scripts/ckb_core/automation.py 第 1321 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1321:1)  `scripts/ckb_core/automation.py:1321-1392`

## 相关代码

- 实现时会用到 [[AutomationTest.event]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[AutomationTest.event 等测试场景]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 汇总了本页。
- [[main（ckb 实现）]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
