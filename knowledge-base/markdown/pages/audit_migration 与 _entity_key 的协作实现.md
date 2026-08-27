# audit_migration 与 _entity_key 的协作实现

标签：#类型/代码

> 该代码页汇总 Code Knowledge Builder 的增量迁移实现，覆盖精确 blob 复用、审阅重建、可变知识保留和迁移审计。 它把已经审计的旧知识库迁移到新的固定 Git 提交，并用不可变基线证明用户笔记与自动化数据库已被保留，同时允许 Hook 后续继续追加内容。

## 什么时候需要修改

当复用判据、可变层范围、重链接规则、迁移状态机或审计门发生变化时，需要修改本页并重跑迁移回归测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`

## 相关代码

- 主要代码单元是 [[audit_migration]]。
- 实现时会用到 [[create_source_snapshot 与 git 的协作实现]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[module_name 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[render_integration 与 _looks_windows 的协作实现]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[status 与 _load_state 的协作实现]]。

## 谁会来到这里

- [[MigrationTest]] 会使用这里提供的行为。
- [[audit_migration]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[status 与 _load_state 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 15 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_entity_key` | 提取实体的路径、blob、类型、名称和源码范围，形成可比较的迁移复用键。 |
| `_review_shape` | 把实体分类归并为附录说明或完整叙述两种审阅字段形状。 |
| `_review_for_new_entity` | 把旧实体中已经核实的中文审阅字段改写到目标提交的新实体标识上。 |
| `_copy_file` | 复制可变文件并记录初始位置、大小和完整性证据。 |
| `_mutable_target` | 把迁移清单中的相对路径解析到输出目录内并阻止路径越界。 |
| `_add_mutable_baseline` | 为迁移时保留的工作副本创建不可变基线并登记两者的初始证据。 |
| `_generated_paths` | 读取投影所有权清单，识别可重建文件与用户维护文件的边界。 |
| `_preserve_mutable_layers` | 复制用户笔记、工作区记录和自动化数据库，同时为每项生成迁移基线。 |
| `_selected_entities` | 按照范围清单汇集目标实体，并从固定 Git 提交批量读取对应源码。 |
| `_replace_review_packs` | 把实体拆分为可复用审阅包和需要重新核实的差量审阅包。 |
| `migrate_output` | 编排目标初始化、精确文件复用、可变知识保存、分段构建和差量审阅检查点。 |
| `_semantic_page_key` | 用源码路径、实体类型和限定名建立跨提交页面标题匹配键。 |
| `relink_preserved_notes` | 根据新旧页面的语义匹配确定性重写保留笔记中的 Wiki 链接和本地文件位置。 |
| `relink_preserved_notes.replace_links` | 按标题长度排序替换普通 Wiki 链接与带别名的 Wiki 链接。 |
| `migration_status` | 汇总迁移复用统计、待审阅包、下一模板和当前迁移审计结果。 |

</details>
