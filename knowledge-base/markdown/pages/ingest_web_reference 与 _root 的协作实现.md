# ingest_web_reference 与 _root 的协作实现

标签：#类型/代码

> 该模块将本地文本、PDF 和显式网页快照保存到独立参考层，保留原始来源、许可、修订和提取证据，并要求中文摘要及逐条原文定位审阅后才生成有效参考页面。参考资料不转换为固定源码实体。 它编排导入、幂等识别、显式修订、审阅、双镜像投影、索引生成、路径重绑定和回滚；文本采用原文行范围，PDF 采用页面片段字符范围，网页采用归档 HTML 片段行范围。

## 什么时候需要修改

输入准入、修订身份、引用定位、许可字段、参考页展示或索引与回滚合同变化时修改此模块，并核对归档字节、待审状态和有效参考集合的一致性。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_documents.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_documents.py:1:1)  `scripts/ckb_core/reference_documents.py:1-1337`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[ingest_web_reference]]。
- 与 [[validate_pdf_extraction]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[validate_pdf_extraction 与 PdfExtractionError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[validate_web_extraction]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_global]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ingest_web_reference]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[maintenance_check]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[migrate_output 与 _entity_key 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 30 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_root` | 返回输出目录下独立的外部参考资料根目录。 |
| `_manifests` | 按文件名排序读取全部参考清单，清单目录不存在时返回空列表。 |
| `_manifest` | 按参考编号读取对应清单，文件不存在时抛出参考不存在错误。 |
| `_validate_output` | 检查输出目录具有状态文件及人类和 Markdown 目录，满足结构前提后返回绝对路径。 |
| `_validate_license` | 去除许可声明首尾空白并排除预定义无效占位值，返回具体声明文本。 |
| `_decode_source` | 按后缀读取本地文本或 PDF，文本核对大小、UTF-8 和空字节并统一换行，PDF 先执行结构与预算检查。 |
| `_managed_path` | 要求相对路径无上级跳转且目标落在指定受管父目录内，同时与输出拼接后的路径完全一致。 |
| `_set_marker` | 清除参考层旧状态标记，再按通过、待审或失败状态写入唯一对应标记。 |
| `_pending_pdf_next_steps` | 为待提取 PDF 返回先回滚再带 OCR 参数重新导入的步骤描述，不修改既有幂等记录。 |
| `ingest_reference` | 归档本地参考原文并核验来源和许可，按内容哈希识别幂等或显式修订，生成提取证据、待审模板和事务记录。 |
| `write_reference_review_template` | 把指定参考的审阅模板复制到尚不存在的目标文件，并返回新文件绝对路径。 |
| `_source_lines` | 复读非 PDF 归档原文并核对哈希，按声明编码解码和统一换行后返回逐行文本。 |
| `_validate_pdf_claims` | 要求 PDF 提取已就绪，逐项核对中文主张、页码、单片段内字符范围和完全匹配的原文摘录。 |
| `_validate_web_claims` | 要求网页提取已就绪，逐项核对中文主张、片段编号及片段内行范围与归档原文的一致性。 |
| `_validate_review` | 核对参考审阅身份、源码哈希、中文摘要及非空主张，再按文本、PDF 或网页定位规则验证引用依据。 |
| `_source_uri` | 把绝对路径编码为带行列位置的编辑器源码链接。 |
| `_pdf_source_uri` | 把绝对路径编码为本地文件链接，并在指定页码时追加 PDF 页定位片段。 |
| `_render_reference_page` | 根据已审阅摘要和主张生成中文参考页，附原文定位、来源和许可，网页追加获取证据并拒绝暴露长哈希。 |
| `_active_reviewed` | 仅选取状态为已审阅的参考清单，按标题与参考编号稳定排序。 |
| `relocate_reference_paths` | 先核对归档原文与提取清单的既有哈希，再重绑定参考层可变 JSON 路径并更新提取清单摘要。 |
| `relocate_reference_paths.rebind` | 按旧路径前缀从长到短依次执行输出路径替换，避免较短前缀先匹配影响重绑定。 |
| `_project_reference_pages` | 重新核验全部有效审阅参考，在两份镜像生成每来源一页的摘要及完整导览，并登记投影文件集合。 |
| `project_references` | 生成参考页面后刷新人类导览，并重建机器知识索引和兼容 Agent 索引。 |
| `submit_reference_review` | 核验并保存参考审阅，标记被替代修订，重建投影与索引，审计通过后写入参考层完成标记。 |
| `reference_machine_records` | 导出全部参考来源清单，并仅为有效已审阅来源生成独立参考文档及文本、PDF 或网页片段检索记录。 |
| `_reference_sections` | 将纯文本按八十行分段，Markdown 按围栏外标题分段，无标题时退回固定行数，并保留原文行范围。 |
| `_web_capture_errors` | 核对网页获取证据的必需字段、模式与网络标记、地址、时间、状态、类型及双哈希和大小的一致性。 |
| `audit_references` | 审计参考原文、提取、审阅、修订状态、双镜像和机器记录数量，写入通过、待审或失败结果及标记。 |
| `list_references` | 按可选状态筛选参考清单，返回来源、许可、修订、提取和网页获取证据的紧凑记录列表。 |
| `rollback_reference` | 按修订逆序回滚参考，恢复被替代版本并删除当前归档及提取文件，重建投影索引后核验状态。 |

</details>
