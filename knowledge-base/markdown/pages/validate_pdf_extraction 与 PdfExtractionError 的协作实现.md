# validate_pdf_extraction 与 PdfExtractionError 的协作实现

标签：#类型/代码

> 该模块使用锁定版本的 PDF 解析器按页提取布局文本，对低质量页面仅在显式启用且预算允许时调用 OCR 适配器，保存页面文本、字符范围片段、提取方法和质量证据，并列出仍待处理的页面。 它为参考审阅提供页码与片段级原文定位，并通过复读清单、页面和 OCR 结果核对来源、哈希、范围与状态；布局结构分类属于带置信度的推断，提取就绪也不等于主张已经审阅。

## 什么时候需要修改

解析器锁定版本、页面质量阈值、OCR 预算和取消规则、片段分割或证据校验变化时修改此模块，并核对低质量页保留待处理状态及归档证据可复读。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_pdf.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_pdf.py:1:1)  `scripts/ckb_core/reference_pdf.py:1-771`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[validate_pdf_extraction]]。

## 谁会来到这里

- 与 [[ingest_web_reference 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 16 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `PdfExtractionError` | 为 PDF 确定性校验与提取失败定义独立异常类型。 |
| `_load_pypdf` | 从可选隔离库目录加载 PDF 解析器并要求版本精确匹配，缺少依赖或版本漂移时中止。 |
| `_validate_positive_limit` | 核验数值为规定绝对上限内的正整数，返回通过校验的限制值。 |
| `validate_pdf_limits` | 分别核验 PDF 字节数和页数上限，并返回合法的限制组合。 |
| `validate_ocr_limits` | 分别核验 OCR 页数、超时和输入字节上限，并返回合法的限制组合。 |
| `_normalized_layout_text` | 统一提取文本换行、移除空字符和行尾空白，再删除首尾空行以保留内部布局。 |
| `_text_metrics` | 统计文本总字符、非空白字符、可打印比例和替代字符数量，供提取质量判断。 |
| `_usable_text` | 综合非空白长度、可打印比例和替代字符数量阈值，判断页面文本是否满足可用条件。 |
| `_native_confidence` | 按非空白字符数和可打印比例将原生提取文本标为高或中等置信度。 |
| `_classify_block` | 依据列表符号、列间隔、缩进、代码信号和短行特征分类布局块，并为推断结构附加置信度和警告。 |
| `segment_page_text` | 仅以空行为页面文本硬边界，保留非空行布局，为片段生成字符偏移、结构分类、置信度和稳定编号。 |
| `_resolve_ocr_adapter` | 核验显式 OCR 适配器为现存 Python 文件，返回路径与哈希，缺失或不可用时返回原因。 |
| `_run_ocr_page` | 后台运行单页 OCR 适配器并限制超时与取消，核对输出文件、模式、页码、文本和置信分值，失败保留待处理原因。 |
| `inspect_pdf` | 在创建受管文件前核对 PDF 大小、文件头、加密状态及页数，通过后返回锁定解析器和读取对象。 |
| `extract_pdf` | 逐页优先提取原生布局文本，仅在显式启用且预算允许时运行 OCR，保存页面与片段证据并明确列出待处理页。 |
| `pdf_fragment` | 遍历 PDF 提取清单查找指定片段编号，返回所属页与片段，缺失时抛出错误。 |

</details>
