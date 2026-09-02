# 增加可追溯的 PDF 参考资料吸收

标签：#类型/变更

## 修改内容

参考资料层现在可以直接吸收 PDF，并把每条可确认主张绑定到具体页码和原文片段。文本不足、扫描页或混合文档会进入待补充状态，不会伪装成已经完成的资料吸收。

## 修改时间

2026 年 9 月 3 日。

## 修改原因

PDF 是项目设计、论文和外部资料的主要载体。仅把整份文档转成无页码文本，会丢失引用位置、代码与表格边界，也难以判断空白页、乱码、扫描件和加密文档究竟是“没有信息”还是“提取失败”。

## 修改方式

完整运行时固定携带 `pypdf`，按页保留文本、代码块、表格行和质量指标。资料审阅必须提交页码、精确原文片段和字符范围；可选 OCR 通过外部适配器接入，并受页面数、输入大小、单页时间和取消信号限制。待补充文档提供可执行的回滚与重新吸收步骤，Web 输入目前只固定适配协议，不主动联网抓取。

## 关联影响

这项修改影响完整运行时、参考资料清单、人类与 Markdown 镜像、双 SQLite 检索、许可证清单和回滚流程。Lite 发行边界没有增加 PDF 运行时；OCR 引擎及其模型也没有被打包进项目。

## 已验证结果

固定样例已覆盖多页布局、中文文本、代码与表格、空白和扫描页、混合文档、有界 OCR、损坏与加密文件、大小和页数限制、页级审阅、索引、回滚及文本资料兼容。完整运行时安装后可直接导入固定版本的 PDF 解析库。

## 相关知识页

- [[extract_pdf 与 PdfExtractionError 的协作实现]]
- [[ingest_reference 与 _root 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/reference_pdf.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_pdf.py:1:1)  `scripts/ckb_core/reference_pdf.py:1-685`
- [打开源码：scripts/ckb_core/reference_documents.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_documents.py:1:1)  `scripts/ckb_core/reference_documents.py:1-903`
