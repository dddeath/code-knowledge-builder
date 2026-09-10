# audit_feedback

标签：#类型/代码

> `audit_feedback` 是 `scripts/ckb_core/feedback.py` 中负责检查反馈锚点、状态、镜像、归档与落实记录的一致性的函数。 它按源码所示的参数、条件分支和数据结构完成检查反馈锚点、状态、镜像、归档与落实记录的一致性，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当定位式人工反馈的创建、重定位、审计与归档的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/feedback.py 第 437 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/feedback.py:437:1)  `scripts/ckb_core/feedback.py:437-545`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_feedback 与 _contains_chinese 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_agent_protocol]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[audit_feedback 与 _contains_chinese 的协作实现]] 汇总了本页。
- 与 [[serve_stdio 与 _write_line 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
