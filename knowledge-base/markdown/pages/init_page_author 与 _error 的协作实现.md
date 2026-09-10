# init_page_author 与 _error 的协作实现

标签：#类型/代码

> 按照冻结的人类页面合同生成新建、补充或修订候选文稿，立即验证候选内容，并可打包为含正文、证据副本与路由清单的独立暂存产物。 inspect 只读取工作区内指定来源并核验哈希；supplement 只添加缺失章节，revise 要求原段落在指定章节唯一匹配。正文与机器证据分离验证，打包拒绝受管目录和已有目标，临时写入及重开核验后才返回 ready；不直接修改人类投影或 SQLite。

## 什么时候需要修改

页面合同版本、章节输入、来源哈希、修订定位或证据移植规则变化时，联动模板校验器、渲染上下文与打包清单；新增页面类型还需更新后续 record/reference/feedback 或生成器路由。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_page_authoring.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_page_authoring.py:1:1)  `scripts/ckb_core/human_page_authoring.py:1-1447`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 实现时会用到 [[HumanPageTemplateContract]]。
- 与 [[HumanPageTemplateContract 与 SectionContract 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[init_page_author]]。

## 谁会来到这里

- 与 [[init_page_author]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 32 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_error` | 把错误原因、中文消息及补充字段组合为统一错误对象。 |
| `_failed` | 将一个错误封装为带操作名、作者协议版本和 failed 状态的结果。 |
| `_missing` | 对缺失字段去重排序，返回包含页面类型和编写模式的 missing-fields 结果。 |
| `_contract_result` | 核验编写模式及 V3 合同版本，再查找页面合同；失败时返回稳定错误对象而不是合同。 |
| `_field_slot` | 把字段名、类型和填写目的组合为一个类型槽描述。 |
| `_section_slot` | 为章节建立空的人类摘要及实体、链接、指标、来源和机器证据列表，动态标题章节额外保留 heading 槽。 |
| `_resolve_within` | 将相对来源路径解析到工作区内部，拒绝越界或非文件目标，成功返回可读取的绝对路径。 |
| `_sha256_text` | 对文本的 UTF-8 字节计算十六进制 SHA-256，用于候选文稿来源和产物漂移比较。 |
| `_document_sections` | 跳过围栏代码块中的标题，识别 Markdown 标题与行位置，并以之后同级或更高层标题划分各章节正文。 |
| `_matches` | 先匹配标题层级，再按合同的固定标题或完整正则匹配判断章节是否对应。 |
| `_managed_source` | 根据相对路径中是否含 human/markdown 或文件是否为 SQLite/DB，判断来源是否属于受管内容。 |
| `inspect_page_author` | 只读核验来源路径与可选哈希，识别缺失、重复或空章节和标题冲突，返回已满足字段、缺失字段及后续可用操作。 |
| `_non_empty` | 将去空白后的非空字符串、非空列表/元组/字典或其他非 None 值判断为已提供字段。 |
| `_validate_top_level` | 比较输入顶层键与当前编写模式的允许字段，出现未知字段时返回 render 失败信息。 |
| `_section_by_id` | 将合同中的必填及可选章节合并为以 section_id 索引的查找表。 |
| `_normalize_section_input` | 核验章节对象、允许键、动态标题模式与五类列表字段，并返回规范化标题、人类摘要及独立证据上下文。 |
| `_render_section` | 按合同标题层级把章节标题与 human_summary 拼成 Markdown，不渲染机器证据字段。 |
| `_section_validation_context` | 从章节输入复制实体、链接、指标、来源及机器证据列表，作为独立验证上下文。 |
| `_canonical_reference` | 规范引用的 kind、purpose、target 文本，并在提供时附带小写 SHA-256。 |
| `_section_evidence_document` | 按合同章节顺序规范并排序来源与机器证据引用，输出带披露层级和章节标识的证据文档。 |
| `_base_missing_fields` | 检查页面合同要求的 evidence 字段和 validation_context 对象，返回需要补充的字段路径。 |
| `_load_source_for_render` | 要求具体来源路径和有效 SHA-256，重新读取工作区内文件并比较内容哈希，拒绝 inspect 后的来源漂移。 |
| `_validate_nested_input` | 逐层检查证据、时效事实、章节上下文及引用条目的未知键，返回第一个超出合同的字段错误，缺失和类型问题留给后续校验。 |
| `_candidate_validation` | 核验必需证据后调用完整页面校验，按结构、预算、链接、披露、当前事实及适用边界分类结果，并将未归类错误单独报告。 |
| `_candidate_validation.status_for` | 检查已收集错误原因是否与指定类别相交，返回该类别的 passed 或 failed。 |
| `validate_page_author` | 拒绝非对象、未知顶层字段、合同不兼容和空 Markdown，再统一执行候选页结构、预算、链接与证据校验。 |
| `render_page_author` | 按新建、补充或修订模式在内存生成候选文稿，限制章节与唯一替换目标，校验通过后返回正文、哈希和独立证据。 |
| `_package_route` | 按页面类型返回正式提交入口的命令或人工路由，分别指向记录、资料、反馈、学习页、README 或导航生成器，不执行这些入口。 |
| `_staging_target` | 解析工作区内的新暂存目录，拒绝根目录、越界、受管投影、数据库路径或已有目标。 |
| `_portable_section_evidence` | 核验工作区内文件引用及哈希并生成去重复制计划，将文件改为包内证据相对路径，URI 则保留原解析基础。 |
| `package_page_author` | 渲染并校验候选文稿后，将正文、证据副本和路由清单写入新暂存目录，重开核验哈希与清单，返回下一提交入口。 |
| `load_authoring_input` | 以兼容 UTF-8 BOM 的方式读取 JSON 输入，并拒绝非对象的页面编写数据。 |

</details>
