# sync_human_layer

标签：#类型/代码

> `sync_human_layer` 是源码中负责生成事实层与中文人类层并核对跨层一致性的命名代码单元。 它在所属模块内执行生成事实层与中文人类层并核对跨层一致性，并把确定结果交给调用方、审计门或投影阶段。

## 什么时候需要修改

当生成事实层与中文人类层并核对跨层一致性所依赖的输入格式、排序规则、状态转换或输出契约变化时，需要修改该代码单元。

## 在代码中的位置

[打开源码：scripts/ckb_core/knowledge_layers.py 第 126 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:126:1)  `scripts/ckb_core/knowledge_layers.py:126-181`

## 相关代码

- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[sync_human_layer 与 _source_manifest 的协作实现]]。

## 谁会来到这里

- [[status 与 _load_state 的协作实现]] 会使用这里提供的行为。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 汇总了本页。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
