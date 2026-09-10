# validate_web_extraction

标签：#类型/代码

> 该函数重新打开指定参考的网页提取清单及正文文件，核对受管路径、清单和正文哈希，并在原始响应存在时逐片段检查编号、行范围和原文摘要，再以片段正文重建正文摘要。 它为网页主张审阅和参考层审计提供提取一致性检查，返回有效提取或错误列表；原始响应存在性和完整原文哈希还需要外层参考审计核验，此函数不重新运行正文提取算法。

## 什么时候需要修改

网页提取路径、正文文件命名、片段行范围、摘要绑定或就绪状态要求变化时修改此函数，并验证缺失文件、重复片段、原文行漂移和正文重建不一致。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_inputs.py 第 468 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_inputs.py:468:1)  `scripts/ckb_core/reference_inputs.py:468-528`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[validate_web_extraction 与 WebSnapshotError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[ingest_web_reference 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[validate_web_extraction 与 WebSnapshotError 的协作实现]] 汇总了本页。
