# audit_work_record_index

标签：#类型/代码

> 该函数先审计 Markdown 工作记录导览的完整内容和链接，再检查人类镜像是否存在且与其逐字节相等，将差异合并为最终结果。 它是两个人类入口的工作记录导览一致性门，沿用单根审计的数量和分类统计，只在全部检查无错误时返回通过。

## 什么时候需要修改

导览镜像位置、字节一致性要求或单根审计结果合并方式变化时修改此函数，并验证缺失镜像和内容差异均导致失败。

## 在代码中的位置

[打开源码：scripts/ckb_core/work_record_index.py 第 230 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/work_record_index.py:230:1)  `scripts/ckb_core/work_record_index.py:230-241`

## 相关代码

- 与 [[audit_work_record_index 与 _contains_chinese 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_agent_protocol]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[audit_work_record_index 与 _contains_chinese 的协作实现]] 汇总了本页。
- 与 [[maintenance_check]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[rollback_replacement]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[rollback_replacement 与 RecordReplaceLockError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
