# parser

标签：#类型/代码

> `parser` 是 `scripts/ckb.py` 第 270-743 行定义的函数，本页绑定该固定源码范围。 负责注册 CKB 命令、校验参数，并把子命令分派到对应的知识库实现。

## 什么时候需要修改

当 `parser` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 270 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:270:1)  `scripts/ckb.py:270-743`

## 相关代码

- 实现时会用到 [[AutomationTest.register]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[append 等测试场景]]。
- 实现时会用到 [[bind_conversation 与 default_management_registry_path 的协作实现]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[initialize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[keyword_provider_config 与 parser 的协作实现]]。
- 实现时会用到 [[normalize]]。
- 实现时会用到 [[refresh]]。
- 实现时会用到 [[retrieve]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[start_scope_extension 与 _error 的协作实现]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests 等测试场景]] 会使用这里提供的行为。
- [[build 的协作边界]] 会使用这里提供的行为。
- [[command 等测试场景]] 会使用这里提供的行为。
- [[deploy 的协作边界]] 会使用这里提供的行为。
- [[execute 等测试场景]] 会使用这里提供的行为。
- [[keyword_provider_config 与 parser 的协作实现]] 汇总了本页。
- [[main（build_runtime_payload 实现）]] 会使用这里提供的行为。
- [[main（generate_large_fixture 测试）]] 会使用这里提供的行为。
- [[main（make_source_patch 实现）]] 会使用这里提供的行为。
- [[main（session_stdio_harness_probe 测试）]] 会使用这里提供的行为。
- [[main（session_stdio_reactivation_probe 测试）]] 会使用这里提供的行为。
- [[normalize 等测试场景]] 会使用这里提供的行为。
- [[one_cycle 等测试场景]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[preflight 与 git 的协作实现]] 会使用这里提供的行为。
- [[run 等测试场景]] 会使用这里提供的行为。
- [[source_files 与 sha256 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[ScopeExtensionTest]]
- [[command 等测试场景]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
