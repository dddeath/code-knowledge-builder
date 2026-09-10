# review_automation

标签：#类型/代码

> 把待审自动化事件正式转换为人类笔记，并将数据库待审项和对应 sidecar 更新为 agent-reviewed。 提交前检查中文正文、标题、中文核验说明和 仍处于 pending-agent-review 的记录；source_checks 必须与 changed_paths 精确相等且逐项已审，有改动时还检查正文标题。笔记写入成功后才更新 SQLite，并记录审阅文件及来源检查。

## 什么时候需要修改

改变自动化待审字段、改动集合、正文标题或人类记录入口时，联动模板生成、source_checks 校验、数据库状态和 sidecar 更新，确保机器事件不会跳过审阅直接成为人类笔记。

## 在代码中的位置

[打开源码：scripts/ckb_core/automation.py 第 1655 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1655:1)  `scripts/ckb_core/automation.py:1655-1729`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note 与 page_tag 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_automation 与 default_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[review_automation 与 default_registry_path 的协作实现]] 汇总了本页。
