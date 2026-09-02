# retrieve_machine

标签：#类型/代码

> `retrieve_machine` 是 `scripts/ckb_core/machine_knowledge.py` 第 1600-1709 行定义的函数，本页绑定该固定源码范围。 负责机器知识 SQLite 的构建、FTS5 检索、实体邻接和源码定位。

## 什么时候需要修改

当 `retrieve_machine` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/machine_knowledge.py 第 1600 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1600:1)  `scripts/ckb_core/machine_knowledge.py:1600-1709`

## 相关代码

- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run_keyword_provider]]。
- 实现时会用到 [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]。
- 实现时会用到 [[search_terms]]。
- 实现时会用到 [[search_terms 与 _split_camel 的协作实现]]。

## 谁会来到这里

- [[KeywordFallbackRetrievalWiringTests]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 会使用这里提供的行为。
- [[bind_conversation 与 default_management_registry_path 的协作实现]] 会使用这里提供的行为。
- [[build_manual_index 等测试场景]] 会使用这里提供的行为。
- [[command 等测试场景]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 汇总了本页。
- [[run_keyword_benchmark 与 _text_list 的协作实现]] 会使用这里提供的行为。
- [[serve_stdio]] 会使用这里提供的行为。
- [[start_session]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[HumanPageTemplateValidationTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[KeywordFallbackRetrievalWiringTests 等测试场景]]
- [[append 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
