# generate 等测试场景

标签：#类型/代码

> 该脚本绘制带中英文、代码缩进和跨行表格的两页原生 PDF，再栅格化生成纯扫描版本，并组合一页原生与一页扫描的混合版本，保存标准答案和文件哈希。 它是开发阶段的冻结 OCR 测试输入生成器，通过提取文本是否存在检查三种文档类型，所需绘图和渲染库不由该脚本加入默认 CKB 运行时。

## 什么时候需要修改

标准页面内容、字体、布局、扫描分辨率或类型校验变化时修改此脚本，并重新冻结标准答案及所有 PDF 哈希。

## 在代码中的位置

[打开源码：tests/generate_reference_pdf_ocr_fixtures.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/generate_reference_pdf_ocr_fixtures.py:1:1)  `tests/generate_reference_pdf_ocr_fixtures.py:1-285`

## 相关代码

- 主要代码单元是 [[generate]]。

## 谁会来到这里

- 与 [[generate]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_sha256` | 计算一个样例文件的内容指纹，用于核对生成结果。 |
| `_font` | 按显式路径及备用列表顺序选择首个存在的字体文件，全部缺失时列出候选并报错。 |
| `_renderer` | 优先使用存在的指定渲染程序，否则在命令搜索路径寻找 pdftoppm，缺失时报错。 |
| `_draw_native` | 绘制包含中文说明、代码和换行表格的两页原生 PDF，作为可提取文本的保真度样例。 |
| `_render_pages` | 调用 pdftoppm 将原生样例按固定分辨率转成图片，并核对渲染退出状态和页面数量。 |
| `_draw_scanned` | 将已渲染页面图片写成纯图像 PDF，构造需要 OCR 的扫描样例。 |
| `_draw_hybrid` | 组合原生文档第一页与扫描文档第二页，生成混合文本和图像页面的 PDF。 |
| `_verify_kinds` | 检查三类样例各页是否具有可提取文本，确认原生、扫描和混合文档满足预定类型。 |
| `main` | 解析字体、渲染器及输出位置，调用样例生成流程并返回生成文档摘要。 |

</details>
