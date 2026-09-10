# propose_template 与 _canonical_bytes 的协作实现

标签：#类型/代码

> `scripts/ckb_core/human_page_template_proposals.py` 页面绑定固定源码第 1-1452 行，说明该文件如何承担人类页面模板提议、人工审阅、版本化状态和回滚。 该文件负责人类页面模板提议、人工审阅、版本化状态和回滚，并为相关命令、页面生成或测试提供源码入口。

## 什么时候需要修改

当 `scripts/ckb_core/human_page_template_proposals.py` 的公开输入、生成结果、状态边界或与其他模块的协作关系变化时，应更新本页。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_page_template_proposals.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_page_template_proposals.py:1:1)  `scripts/ckb_core/human_page_template_proposals.py:1-1452`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[HumanPageTemplateContract 与 SectionContract 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[propose_template]]。

## 谁会来到这里

- 与 [[propose_template]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 49 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_canonical_bytes` | `_canonical_bytes` 用于生成稳定序列化或内容摘要。 |
| `_sha256` | `_sha256` 用于生成稳定序列化或内容摘要。 |
| `_store_root` | 返回知识库工作元数据下专用的模板提案存储路径。 |
| `_validated_output` | `_validated_output` 用于校验输入、状态、证据或输出合同。 |
| `_expect_object` | 要求输入为字典对象并返回独立浅拷贝，类型不符时报告所在字段。 |
| `_expect_fields` | 严格比较对象键集合与允许字段，分别报告未知字段和缺失字段。 |
| `_text` | 要求非空字符串，去除首尾空白并限制字符长度及空字节。 |
| `_string_list` | 逐项校验有界文本列表并拒绝重复值，仅在明确允许时接受空列表。 |
| `_boolean` | 要求输入是真正的布尔值，拒绝其他类型并返回原值。 |
| `_integer` | 要求数值为指定范围内的整数，显式排除布尔值并返回有效输入。 |
| `_semantic_version` | 规范版本文本并要求符合三段式语义版本，格式错误时中止。 |
| `_semantic_version_key` | 将合法三段式版本解析成整数元组，供提案按数值版本排序。 |
| `_template_name` | 校验不含路径分隔符的模板名，并拒绝与内置页面类型忽略大小写重名。 |
| `_target_document` | 返回内置人类页面注册表的合同版本、编号、模式版本和内容摘要。 |
| `_validate_target` | `_validate_target` 用于校验输入、状态、证据或输出合同。 |
| `_normalize_count_budget` | `_normalize_count_budget` 用于规范化输入字段并拒绝未知或越界值。 |
| `_normalize_section_length_budget` | `_normalize_section_length_budget` 用于规范化输入字段并拒绝未知或越界值。 |
| `_normalize_section_link_budget` | `_normalize_section_link_budget` 用于规范化输入字段并拒绝未知或越界值。 |
| `_normalize_fields` | `_normalize_fields` 用于规范化输入字段并拒绝未知或越界值。 |
| `_normalize_sections` | `_normalize_sections` 用于规范化输入字段并拒绝未知或越界值。 |
| `_normalize_examples` | `_normalize_examples` 用于规范化输入字段并拒绝未知或越界值。 |
| `normalize_template_proposal` | `normalize_template_proposal` 用于规范化输入字段并拒绝未知或越界值。 |
| `template_proposal_skeleton` | 生成模板提案的字段骨架，包含章节、预算、来源、样例、迁移影响和恢复约定。 |
| `write_template_proposal_skeleton` | `write_template_proposal_skeleton` 用于生成范围受控且可重新打开的输出。 |
| `_store_schema_document` | 导出模板提案存储的字段、状态与审阅约束，声明内置模板和历史记录保持不变。 |
| `_validate_store_schema` | `_validate_store_schema` 用于校验输入、状态、证据或输出合同。 |
| `_prepare_store` | 核验知识库输出后创建其本地模板提案目录，返回存储根路径。 |
| `_initialize_store_locked` | `_initialize_store_locked` 用于创建受控候选状态而不越过后续确认边界。 |
| `_store_lock` | 限时等待目录锁以串行化模板写入，记录进程号并在退出时移除锁标记。 |
| `_proposal_event_errors` | 核验提案事件字段、序号、内容摘要和稳定编号，汇总格式与来源绑定错误。 |
| `_reviewer` | 校验审阅者只含身份与类型字段，并要求审阅及回滚操作由人类确认。 |
| `_audit_event_errors` | `_audit_event_errors` 用于汇总并判断受控对象是否满足当前合同。 |
| `_rollback_event_errors` | `_rollback_event_errors` 用于执行范围受控的恢复或撤销。 |
| `_load_events` | `_load_events` 用于读取、定位并返回现有状态。 |
| `_builtin_items` | 按固定顺序把内置页面合同转换为始终启用的只读模板索引项。 |
| `_item_sort_key` | 内置模板按原顺序优先排列，扩展提案再按状态、名称、语义版本和编号排序。 |
| `_index_from_events` | 重放提案、审阅和回滚事件，核对版本及启用关系，生成排序索引与状态计数。 |
| `_operation_log_bytes` | `_operation_log_bytes` 用于生成稳定序列化或内容摘要。 |
| `_atomic_write_bytes` | `_atomic_write_bytes` 用于生成稳定序列化或内容摘要。 |
| `_rebuild_store` | 重放事件生成提案索引和操作日志，写入后复读核对内容一致性。 |
| `_load_verified_store` | `_load_verified_store` 用于读取、定位并返回现有状态。 |
| `_validate_local_version` | `_validate_local_version` 用于校验输入、状态、证据或输出合同。 |
| `validate_template_proposal` | `validate_template_proposal` 用于校验输入、状态、证据或输出合同。 |
| `list_templates` | `list_templates` 用于读取、定位并返回现有状态。 |
| `show_template` | `show_template` 用于读取、定位并返回现有状态。 |
| `_event_by_id` | 按事件编号查找首个匹配事件，未找到时返回空值。 |
| `_proposal_payload` | 查找指定编号的原始提案事件并返回其正文，找不到时明确报错。 |
| `audit_template_proposal` | `audit_template_proposal` 用于汇总并判断受控对象是否满足当前合同。 |
| `rollback_template_extension` | `rollback_template_extension` 用于执行范围受控的恢复或撤销。 |

</details>
