# source_files

标签：#类型/代码

> `source_files` 是 `scripts/package_release.py` 第 42-63 行定义的函数，本页绑定该固定源码范围。 负责实现 `package_release.py` 中由固定源码定义的命令或知识库处理步骤。

## 什么时候需要修改

当 `source_files` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/package_release.py 第 42 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/package_release.py:42:1)  `scripts/package_release.py:42-63`

## 相关代码

- 实现时会用到 [[append]]。

## 谁会来到这里

- [[PackageReleaseTests]] 会使用这里提供的行为。
- [[query_graph]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[source_files 与 sha256 的协作实现]] 汇总了本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[PackageReleaseTests]]
- [[ScopeExtensionTest]]
- [[refresh 等测试场景]]
