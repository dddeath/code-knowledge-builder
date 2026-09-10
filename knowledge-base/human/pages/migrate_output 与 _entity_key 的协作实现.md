# migrate_output 与 _entity_key 的协作实现

标签：#类型/代码

> 把已审计知识库迁移到新的固定源码版本，复用精确匹配的事实与审阅，并保留可变知识及历史证据。 协调增量拆包、保留层、迁移审计和唯一归属重连；参考状态标记保留历史原字节，但当前标记可随生成器状态变化退出，原文等实际资料仍须存在。

## 什么时候需要修改

需要调整精确复用、笔记与证据保留、参考状态标记生命周期或跨版本链接归属规则时修改。

## 在代码中的位置

[打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-912`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ingest_web_reference 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[migrate_output]]。
- 与 [[module_name 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[preflight 与 git 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note 与 page_tag 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_automation 与 default_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_global]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[migrate_output]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。
- 与 [[start_scope_extension]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[start_scope_extension 与 _error 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 内部细节

<details><summary>查看本页收纳的 22 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_entity_key` | 组合路径、文件对象、声明类型、名称和字节范围，生成精确实体复用键。 |
| `_review_shape` | 把附录分类映射为单句审阅形状，其余分类映射为叙述形状。 |
| `_review_for_new_entity` | 以新实体标识和归属重建审阅项，并按分类复制原有中文说明与证据。 |
| `_copy_file` | 创建父目录并复制文件，返回来源、目标、摘要和大小记录。 |
| `_mutable_target` | 从输出根重新解析迁移相对路径，并阻止目标越出输出目录。 |
| `_add_mutable_baseline` | 为保留文件保存不可变初始副本，按角色选择基线路径并记录原始摘要。 |
| `_generated_paths` | 合并页面与参考资料投影清单，并统一生成路径的分隔符。 |
| `_referenced_machine_evidence` | 从保留记录与笔记追踪必需机器证据的引用闭包，缺少证据时停止。 |
| `_referenced_machine_evidence.consider` | 解析引用路径并验证必需文件，把未访问的机器证据加入待查队列。 |
| `_referenced_machine_evidence.visit` | 递归遍历 JSON 对象和数组，仅从指定证据字段提取文件引用。 |
| `authoring_package_inventory` | 核对保留 V3 记录正文与创作包证据，列出经验证的包内文件依赖。 |
| `authoring_package_inventory.add` | 限制依赖文件位于创作包内，按相对路径去重并合并证据角色。 |
| `_preserve_mutable_layers` | 保留用户资料与证据基线，单独标记参考状态文件，并仅重定位可变元数据。 |
| `_selected_entities` | 按范围与边界记录选取实体，再批量读取这些实体的固定 Git 文件内容。 |
| `_replace_review_packs` | 将复用与待审实体拆为不同审阅包，提交精确复用项并设置增量检查点。 |
| `audit_migration` | 核对迁移来源和保留基线，允许精确参考状态标记退出当前状态，实际资料缺失仍阻塞。 |
| `audit_migration.check` | 把检查名称、布尔结果与详情追加到迁移审计列表。 |
| `_semantic_page_key` | 用路径、原始声明类型与限定名称构造跨版本语义键。 |
| `relink_preserved_notes` | 按唯一新归属重连旧笔记双链，保留正文和不可变证据并登记歧义标题。 |
| `relink_preserved_notes.owner_for` | 要求语义实体唯一匹配，再返回新投影中实际存在的归属页。 |
| `relink_preserved_notes.replace_links` | 逐行替换真实双链目标，保留别名、锚点、换行及行内和围栏代码。 |
| `migration_status` | 结合待审包与迁移审计返回当前阶段，并指出下一审阅模板。 |

</details>
