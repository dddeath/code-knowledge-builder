# create_gap 与 _root 的协作实现

标签：#类型/代码

> 该模块把证据不足、来源冲突和暂缓反馈保存为机器缺口记录，要求中文待验证说明及输出内现存证据，提供幂等创建、筛选和带关闭证据的结案。 它把未决事项与已确认事实分开，并通过工作记录导览中的唯一计数入口连接人类阅读；机器索引保留独立缺口文档，不为每项缺口生成单独知识页。

## 什么时候需要修改

缺口类型、状态转换、稳定编号、证据范围或导航索引合同变化时修改此模块，并验证未关闭记录不包含关闭字段及机器数量与清单一致。

## 在代码中的位置

[打开源码：scripts/ckb_core/research_gaps.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/research_gaps.py:1:1)  `scripts/ckb_core/research_gaps.py:1-274`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_work_record_index 与 _contains_chinese 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[create_gap]]。

## 谁会来到这里

- 与 [[audit_work_record_index 与 _contains_chinese 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_gap]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[maintenance_check]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_management_task 与 default_management_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 15 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_root` | 返回输出目录内研究缺口的机器元数据根目录。 |
| `_records_root` | 返回研究缺口根目录下保存独立记录的子目录。 |
| `_narrative` | 读取并压缩说明文本空白，要求长度和中文字符数量满足阈值，返回有界中文陈述。 |
| `_evidence` | 要求一至十二个现存输出内证据文件，将路径规范化为去重排序的输出相对路径。 |
| `_record_path` | 根据缺口编号生成其机器记录 JSON 路径。 |
| `gap_records` | 按文件名排序读取缺口记录对象，记录目录不存在时返回空列表。 |
| `_index_value` | 汇总缺口总量、状态和类型计数，生成含说明、证据数量及更新时间的紧凑索引结构。 |
| `_write_index` | 读取全部缺口记录并写入统一索引，返回实际写入的索引结构。 |
| `gap_navigation_counts` | 从人类目录对应的缺口索引读取状态数量，索引缺失或计数字段无效时返回空值。 |
| `_sync_indexes` | 按已有目录和索引条件刷新工作记录导览、兼容索引和机器索引，不无条件初始化缺失层。 |
| `resolve_gap` | 为未关闭缺口写入中文关闭说明与证据，刷新相关索引并审计，已关闭缺口拒绝重复关闭。 |
| `list_gaps` | 校验状态和类型筛选值，再返回匹配的缺口记录与筛选条件。 |
| `gap_machine_records` | 将缺口说明、状态和证据转换为独立机器文档，明确未决或已关闭状态，且不创建人类单页。 |
| `_record_errors` | 核验缺口固定字段、稳定编号、中文说明、证据文件及关闭字段的一致性，返回记录错误列表。 |
| `audit_gap_register` | 审计缺口记录与索引、唯一人类导览入口及机器数量，禁止为每个缺口生成独立人类页面。 |

</details>
