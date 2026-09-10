# HumanPageTemplateContract 与 SectionContract 的协作实现

标签：#类型/代码

> 集中定义人类页面 V3 合同，输出稳定注册表并验证页面结构、内容预算与证据边界。 以章节合同连接生成输入和可读性校验；正文扫描区分 SQLite 的普通实现叙述与检查结果，不把共同底线检查当作完整 V3 审阅。

## 什么时候需要修改

需要调整页面类型、章节预算、链接与时效证据要求，或修正机器证据识别的误报与漏报时修改。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_page_templates.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_page_templates.py:1:1)  `scripts/ckb_core/human_page_templates.py:1-1578`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[HumanPageTemplateContract]]。

## 谁会来到这里

- 与 [[HumanPageTemplateContract]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[init_page_author]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[init_page_author 与 _error 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[propose_template 与 _canonical_bytes 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note 与 page_tag 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 43 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `SectionContract` | 定义章节的内容边界、披露层级、长度与链接预算及空章节规则。 |
| `CountBudget` | 保存计数上下限、统计作用域、计数规则与超额动作。 |
| `LengthBudget` | 保存字符、段落、列表与指标数量上限及长度统计规则。 |
| `LinkBudget` | 保存链接数量范围、允许目标类型、计数规则与超额动作。 |
| `FirstScreenContract` | 定义页面首屏职责、必备元素和关键项数量上限。 |
| `EvidenceContract` | 定义证据必备字段、当前事实判定规则与时效字段。 |
| `_section` | 按披露层级设置默认预算，结合显式覆盖值构造完整章节合同。 |
| `_optional_section` | 沿用章节构造规则，把可选章节的空内容行为设为省略。 |
| `_budget` | 用指定范围、作用域和超额策略构造通用计数预算。 |
| `_section_entity_budget` | 创建章节级实体预算，超额时要求压缩职责或转移深入阅读。 |
| `_section_length_budget` | 构造章节长度预算，限定字符、段落、列表与指标数量。 |
| `_section_link_budget` | 构造章节链接预算，并在未指定类型时采用固定目标类型集合。 |
| `_first` | 将首屏职责、必备元素与数量上限封装为不可变合同。 |
| `_evidence` | 将证据字段与时效要求转为元组，构造证据合同。 |
| `_check_registry` | 检查注册表类型和章节标识唯一性、合同字段完整性及预算合法性。 |
| `list_human_page_types` | 按注册顺序返回不可变的页面类型元组。 |
| `_compatible_version` | 判断模式版本与合同版本是否同时精确匹配当前常量。 |
| `get_human_page_template` | 按忽略大小写的页面类型读取合同，对未知类型或版本不兼容给出诊断。 |
| `human_page_section_document` | 将章节合同及嵌套预算转换为可序列化字典。 |
| `_budget_document` | 将计数预算转换为包含范围、作用域和超额策略的字典。 |
| `human_page_template_document` | 将页面合同转换为独立字典，展开章节、首屏、证据和预算字段。 |
| `human_page_template_registry_document` | 验证版本后按注册顺序生成完整合同文档及注册表标识。 |
| `serialize_human_page_template_registry` | 用稳定键顺序、缩进和末尾换行序列化合同注册表。 |
| `human_page_template_registry_sha256` | 对稳定序列化的注册表计算 SHA-256 摘要。 |
| `human_output_errors` | 扫描实际页面正文中的机器证据、空泛叙述和含糊链接，并返回行号诊断。 |
| `human_output_errors.match_line` | 把正则匹配起点与前导空白中的换行转换为实际内容行号。 |
| `_visible_lines` | 跳过三反引号或波浪线围栏内容，保留可见文本及原始行号。 |
| `_headings` | 从可见文本提取 Markdown 标题的层级、文字和行号。 |
| `_section_bodies` | 将每个标题后的内容截取到下一同级或更高级标题之前。 |
| `_matches_section` | 先检查标题层级，再按合同的完整正则或固定文字匹配章节。 |
| `_effective_budget` | 对条目作用域预算按入口章节数量缩放，否则保持单页上下限。 |
| `_normalize_fact_line` | 移除事实行首的引用和列表标记并清理两端空白。 |
| `_validation_error` | 把错误原因、中文说明和附加字段组合为结构化诊断。 |
| `_context_sequence` | 读取上下文数组字段，类型不符时登记错误并返回空列表。 |
| `_link_occurrences` | 从围栏外正文提取 Markdown 与双链的目标和显示文字。 |
| `_paragraph_count` | 按空行分隔统计非空段落，空正文返回零。 |
| `_list_item_count` | 统计正文中无序或有序 Markdown 列表项的行数。 |
| `_normalized_text_list` | 检查字符串列表并清理空白，对非数组和空条目登记诊断。 |
| `_normalized_ref_list` | 校验引用目标、用途、类型和可选摘要，检测同一目标的重复或冲突。 |
| `validate_human_page` | 校验 V3 页面的章节、预算、链接和逐行事实证据，汇总机器信息泄漏诊断。 |
| `_load_context` | 读取可选 JSON 上下文文件，拒绝无效 JSON 或非对象根值。 |
| `_parser` | 构造注册表输出、合同查询和页面验证命令及版本参数。 |
| `main` | 执行合同查询或页面验证并输出 JSON，以退出状态区分通过与输入错误。 |

</details>
