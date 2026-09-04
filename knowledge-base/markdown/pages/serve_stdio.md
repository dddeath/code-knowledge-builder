# serve_stdio

标签：#类型/代码

> `serve_stdio` 提供会话内 JSONL 检索服务，当前同时接受 passed 与 needs-source-read，并对同一扩库建议执行会话内去重。 它复用 canonical 检索实现，保持 CLI 与 stdio 的 scope offer、诊断和失败语义一致。

## 什么时候需要修改

当 stdio 方法、检索状态、扩库建议或重复询问规则变化时，应更新本函数及传输正负例。

## 在代码中的位置

[打开源码：scripts/ckb_core/stdio_server.py 第 202 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/stdio_server.py:202:1)  `scripts/ckb_core/stdio_server.py:202-412`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[ScopeExtensionOfferTests.retrieval]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[contracts 的协作边界（prototypes）]]。
- 实现时会用到 [[finalize]]。
- 实现时会用到 [[maintenance_check 与 capability_matrix 的协作实现]]。
- 实现时会用到 [[retrieve]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[serve_stdio 与 _write_line 的协作实现]]。
- 实现时会用到 [[start_scope_extension 与 _error 的协作实现]]。

## 谁会来到这里

- [[serve_stdio 与 _write_line 的协作实现]] 汇总了本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[ScopeExtensionOfferTests.retrieval 等测试场景]]
- [[ScopeExtensionTest]]
- [[refresh 等测试场景]]
