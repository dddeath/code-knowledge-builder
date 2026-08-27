# create_source_snapshot

标签：#类型/代码

> `create_source_snapshot` 为固定 commit 创建独立 detached worktree 并验证其干净状态。 它让语言提供器始终读取不可变基线，同时允许 Agent 在实时工作树继续修改代码。

## 什么时候需要修改

快照布局、Git worktree 管理或漂移检查方式变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/ckb_core/gitrepo.py 第 230 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:230:1)  `scripts/ckb_core/gitrepo.py:230-257`

## 相关代码

- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[create_source_snapshot 与 git 的协作实现]]。
- 实现时会用到 [[parser]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[create_source_snapshot 与 git 的协作实现]] 汇总了本页。
- [[status 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
