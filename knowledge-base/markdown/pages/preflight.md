# preflight

标签：#类型/代码

> `preflight` 是 `scripts/ckb_core/gitrepo.py` 第 194-217 行定义的函数，本页绑定该固定源码范围。 负责验证固定 Git 快照，并读取提交、树、文件模式和对象内容。

## 什么时候需要修改

当 `preflight` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/gitrepo.py 第 194 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:194:1)  `scripts/ckb_core/gitrepo.py:194-217`

## 相关代码

- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[preflight 与 git 的协作实现]]。

## 谁会来到这里

- [[bind_conversation]] 会使用这里提供的行为。
- [[command 等测试场景]] 会使用这里提供的行为。
- [[initialize]] 会使用这里提供的行为。
- [[preflight 与 git 的协作实现]] 汇总了本页。
- [[start_scope_extension]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[ScopeExtensionTest]]
- [[ScopeExtensionTest 等测试场景]]
- [[append 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
