# serve_stdio

标签：#类型/代码

> `serve_stdio` 是 `scripts/ckb_core/stdio_server.py` 第 202-391 行定义的函数，本页绑定该固定源码范围。 负责实现 `stdio_server.py` 中由固定源码定义的命令或知识库处理步骤。

## 什么时候需要修改

当 `serve_stdio` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/stdio_server.py 第 202 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/stdio_server.py:202:1)  `scripts/ckb_core/stdio_server.py:202-391`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[contracts 的协作边界（36093e4a）]]。
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
