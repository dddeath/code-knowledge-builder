# audit_work_record_index 与 _contains_chinese 的协作实现

标签：#类型/代码

> 该模块从全部工作记录生成按任务分类的中文导览，提取标题和有界摘要，统一呈现分析、修改、实验、问题和会话记录，并可加入研究缺口的单一计数入口。 它为人类阅读提供完整记录集合的稳定入口，不按单次检索问题挑选记录；写入和审计函数核对预期内容、标题唯一性、中文摘要以及两份导览镜像一致性。

## 什么时候需要修改

记录分类顺序、摘要选择、最新追加内容、缺口入口或导览审计合同变化时修改此模块，并检查每条已有记录都有且仅有对应导航标题。

## 在代码中的位置

[打开源码：scripts/ckb_core/work_record_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/work_record_index.py:1:1)  `scripts/ckb_core/work_record_index.py:1-242`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[audit_work_record_index]]。
- 与 [[create_gap 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_work_record_index]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_gap 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[rollback_replacement 与 RecordReplaceLockError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_contains_chinese` | 判断字符串是否至少包含两个中文字符，供记录摘要语言检查。 |
| `_title` | 从文本首行提取标题并去除一级标题前缀，结果为空时采用备用名称。 |
| `_plain_text` | 去除图片、链接目标与部分 Markdown 标记，压缩空白并保留可读链接文字。 |
| `_first_narrative` | 优先从最新追加段落提取中文叙述，跳过代码与结构行，按句子或长度截断，无有效段落时返回默认摘要。 |
| `collect_work_records` | 按固定类别顺序收集全部记录标题、路径和摘要，拒绝重复标题及与生成导览重名的记录。 |
| `render_work_record_index` | 按任务类别生成完整工作记录导览，附中文摘要，并在缺口索引存在时加入单一缺口计数入口。 |
| `write_work_record_index` | 将完整工作记录导览写入指定人类根目录，返回文件位置、总数和各类别数量。 |
| `refresh_work_record_index` | 由 Markdown 记录全集生成同字节的两份导览，再审计并保存结果，失败时中止。 |
| `audit_work_record_root` | 重新生成预期导览，核对正文、标签、无哈希泄漏、完整链接集合及中文摘要，返回分类数量与错误。 |

</details>
