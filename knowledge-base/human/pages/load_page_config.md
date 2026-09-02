# load_page_config

标签：#类型/代码

> `load_page_config` 是源码中负责规范化并校验不可漂移的页面配置的命名代码单元。 它在所属模块内执行规范化并校验不可漂移的页面配置，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当规范化并校验不可漂移的页面配置所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/page_config.py 第 209 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/page_config.py:209:1)  `scripts/ckb_core/page_config.py:209-219`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[load_page_config 与 _merge_known 的协作实现]]。

## 谁会来到这里

- [[audit_global 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[load_page_config 与 _merge_known 的协作实现]] 汇总了本页。

## 相关测试

- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[ScopeExtensionTest]]
- [[ScopeExtensionTest 等测试场景]]
- [[build_manual_index 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
