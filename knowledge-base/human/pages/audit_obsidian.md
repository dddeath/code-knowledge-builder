# audit_obsidian

标签：#类型/代码

> `audit_obsidian` 是 `scripts/ckb_core/obsidian.py` 中负责检查 Obsidian 配置、样式、所有权清单与页面投影约束的函数。 它按源码所示的参数、条件分支和数据结构完成检查 Obsidian 配置、样式、所有权清单与页面投影约束，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当Obsidian vault 配置、页面投影和本地编辑器集成的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/obsidian.py 第 118 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:118:1)  `scripts/ckb_core/obsidian.py:118-165`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[audit_output_contract]]。
- 实现时会用到 [[register_obsidian_plugin 与 default_obsidian_plugin_registry 的协作实现]]。

## 谁会来到这里

- [[audit_obsidian 与 prepare_vault 的协作实现]] 汇总了本页。
- [[initialize 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[MigrationTest]]
- [[ScopeExtensionTest]]
- [[command 等测试场景]]
- [[refresh 等测试场景]]
- [[run 等测试场景]]
