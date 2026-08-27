# ensure_local_openers

标签：#类型/代码

> `ensure_local_openers` 是源码中负责生成并核对可直接打开源码位置的 URI的命名代码单元。 它在所属模块内执行生成并核对可直接打开源码位置的 URI，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当生成并核对可直接打开源码位置的 URI所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/source_links.py 第 29 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:29:1)  `scripts/ckb_core/source_links.py:29-35`

## 相关代码

- 实现时会用到 [[ensure_local_openers 与 default_openers 的协作实现]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。

## 谁会来到这里

- [[ensure_local_openers 与 default_openers 的协作实现]] 汇总了本页。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[MigrationTest]]
