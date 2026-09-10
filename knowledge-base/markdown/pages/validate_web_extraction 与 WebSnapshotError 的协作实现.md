# validate_web_extraction 与 WebSnapshotError 的协作实现

标签：#类型/代码

> 该模块准备本地参考文件和显式网页快照，区分无网络的静态输入与有界实时获取，并提取带原始 HTML 行范围的正文片段，保留导航排除区域和请求响应证据。 它提供参考导入前的输入适配合同、网页内存快照及提取归档核验；地址、响应状态、类型、编码和大小先校验，原始响应与正文分别计算哈希，具体主张由参考审阅层验证。

## 什么时候需要修改

适配器字段、网页获取限制、响应头保留规则、正文排除和分段算法或提取复读校验变化时修改此模块，并核对静态输入不联网以及片段来源范围保持一致。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_inputs.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_inputs.py:1:1)  `scripts/ckb_core/reference_inputs.py:1-566`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[validate_web_extraction]]。

## 谁会来到这里

- 与 [[ingest_web_reference]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。
- 与 [[validate_web_extraction]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 内部细节

<details><summary>查看本页收纳的 26 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `WebSnapshotError` | 为网页快照获取或校验失败定义独立异常类型，供参考输入流程识别错误。 |
| `ReferenceInputRequest` | 定义参考适配器输入的来源、标题、出处、许可和可选作者字段。 |
| `PreparedReferenceInput` | 定义适配器产出的本地文件、媒体类型、适配器编号和来源证据结构。 |
| `PreparedWebSnapshot` | 定义待归档网页快照的原始字节、解码文本、获取证据与正文提取结果结构。 |
| `ReferenceInputAdapter` | 约定参考输入适配器的编号及准备接口，将输入请求转换为本地参考文件而不审阅主张。 |
| `ReferenceInputAdapter.prepare` | 声明参考适配器的准备方法签名，具体适配器负责生成本地文件与来源证据。 |
| `_validated_url` | 要求地址为无内嵌凭据的绝对 HTTP 或 HTTPS 链接，并去除首尾空白。 |
| `_validated_timestamp` | 解析带时区偏移的时间戳并统一为 UTC 秒级格式，无时区或格式错误时中止。 |
| `_normalized_response_headers` | 规范化响应头名称和值，保留多值并记录省略字段，拒绝空名称及含换行的值。 |
| `_content_type_details` | 核对网页媒体类型并解析字符集，默认使用 UTF-8，声明编码不可识别时中止。 |
| `_decode_html` | 按声明字符集严格解码非空 HTML，拒绝空字节字符并统一换行。 |
| `_HtmlBodyExtractor` | 从 HTML 正文收集可审阅文本片段及原文行范围，排除导航和非内容容器，并记录排除区域。 |
| `_HtmlBodyExtractor.__init__` | 初始化实体解码解析器、原文行集合、标签栈、片段列表和正文边界状态。 |
| `_HtmlBodyExtractor.handle_starttag` | 记录起始标签与行号，按标签或导航角色标记排除区域，并追踪正文嵌套深度。 |
| `_HtmlBodyExtractor.handle_startendtag` | 对自闭合标签依次执行起始与结束回调，使标签栈和区域记录保持一致。 |
| `_HtmlBodyExtractor.handle_endtag` | 关闭匹配标签及内层栈项，保存排除区域行范围，并在正文结束时更新边界和深度。 |
| `_HtmlBodyExtractor.handle_data` | 仅提取未被排除的正文数据，压缩展示空白并保留结构标签、原文行范围和来源文本哈希。 |
| `extract_web_snapshot` | 解析完整 HTML 正文并要求存在闭合正文和有效片段，生成正文快照、哈希及排序后的排除区域。 |
| `_prepare_web_snapshot` | 核验响应大小、状态、地址、时间和类型一致性，解码并提取正文，形成带原始及正文哈希的内存快照。 |
| `prepare_static_web_snapshot` | 有界读取调用方提供的本地网页响应文件，规范化响应元数据后准备快照，全程不打开网络连接。 |
| `_RecordingRedirectHandler` | 继承标准重定向处理器，记录每跳状态、来源地址、目标地址和响应位置字段。 |
| `_RecordingRedirectHandler.__init__` | 初始化标准重定向处理器并建立空的重定向证据列表。 |
| `_RecordingRedirectHandler.redirect_request` | 解析相对重定向地址，记录该跳转证据，再交给标准处理器生成后续请求。 |
| `fetch_web_snapshot` | 显式请求单个网页并限制超时和响应大小，记录重定向及响应证据，经统一验证后返回内存快照。 |
| `archive_web_extraction` | 归档已验证快照的正文及提取清单，绑定参考编号和原始响应哈希，返回文件位置与片段数量。 |
| `web_input_adapter_contract` | 返回本地静态快照和显式联网获取的适配器合同，列明保存证据及仍需参考导入审阅的边界。 |

</details>
