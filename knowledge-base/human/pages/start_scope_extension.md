# start_scope_extension

标签：#类型/代码

> `start_scope_extension` 是 `scripts/ckb_core/scope_extension.py` 第 261-451 行定义的函数，本页绑定该固定源码范围。 负责实现 `scope_extension.py` 中由固定源码定义的命令或知识库处理步骤。

## 什么时候需要修改

当 `start_scope_extension` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/scope_extension.py 第 666 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/scope_extension.py:666:1)  `scripts/ckb_core/scope_extension.py:666-856`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[finalize 与 _replace_output_prefix 的协作实现]]。
- 实现时会用到 [[preflight]]。
- 实现时会用到 [[start_scope_extension 与 _error 的协作实现]]。

## 谁会来到这里

- [[ScopeExtensionTest]] 会使用这里提供的行为。
- [[start_scope_extension 与 _error 的协作实现]] 汇总了本页。

## 相关测试

- [[ScopeExtensionTest]]
- [[refresh 等测试场景]]
