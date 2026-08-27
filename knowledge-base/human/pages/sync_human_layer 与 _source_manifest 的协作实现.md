# sync_human_layer 与 _source_manifest 的协作实现

标签：#类型/代码

> 该文件集中实现可重建事实层、中文人类 vault 镜像与跨层一致性审计。 它是 Code Knowledge Builder 中承载可重建事实层、中文人类 vault 镜像与跨层一致性审计的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当可重建事实层、中文人类 vault 镜像与跨层一致性审计的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/knowledge_layers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:1:1)  `scripts/ckb_core/knowledge_layers.py:1-239`

## 相关代码

- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。
- 主要代码单元是 [[sync_human_layer]]。

## 谁会来到这里

- [[record_note]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[sync_human_layer]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 7 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_source_manifest` | 该附属代码负责可重建事实层、中文人类 vault 镜像与跨层一致性审计，并把结果交给所属页面中的主流程使用。 |
| `build_facts_layer` | 该附属代码负责生成事实层与中文人类层并核对跨层一致性，并把结果交给所属页面中的主流程使用。 |
| `audit_facts_layer` | 该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。 |
| `_copy_file` | 该附属代码负责可重建事实层、中文人类 vault 镜像与跨层一致性审计，并把结果交给所属页面中的主流程使用。 |
| `_generated_files` | 该附属代码负责可重建事实层、中文人类 vault 镜像与跨层一致性审计，并把结果交给所属页面中的主流程使用。 |
| `audit_human_layer` | 该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。 |
| `mirror_note` | 该附属代码负责保存实时工作区变化和双链知识记录，并把结果交给所属页面中的主流程使用。 |

</details>
