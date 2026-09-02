# AutomationTest.register

标签：#类型/代码

> 代码单元 `register`负责验证多 Harness 事件归一化、会话激活、并发采集和受控投影。 它属于会话自动化生命周期的回归保护，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当自动化事件、会话状态、并发行为或人类投影规则变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：tests/test_automation.py 第 79 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:79:1)  `tests/test_automation.py:79-81`

## 相关代码

- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.register 等测试场景]] 汇总了本页。
- [[CkbError]] 关联到这里的验证场景。
- [[CkbError 与 DependencyError 的协作实现]] 关联到这里的验证场景。
- [[_Transport.close]] 关联到这里的验证场景。
- [[append]] 关联到这里的验证场景。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 关联到这里的验证场景。
- [[ckb_canvas 的协作边界]] 关联到这里的验证场景。
- [[contracts 的协作边界（2ef5688e）]] 关联到这里的验证场景。
- [[ingest 与 connect 的协作实现]] 关联到这里的验证场景。
- [[ingest_event 与 default_registry_path 的协作实现]] 关联到这里的验证场景。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[parser]] 会使用这里提供的行为。
- [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]] 会使用这里提供的行为。
- [[source_files 与 sha256 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[PdfReferenceExtractionTests]]
- [[PdfReferenceExtractionTests 等测试场景]]
- [[command 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
