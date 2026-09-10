# maintenance_check

标签：#类型/代码

> 重新执行独立审计并写出可重开的维护报告，汇总固定快照、双镜像可读性与事实时效。 逐项捕获常见审计错误，固定快照失败不压制其他发现；不写知识页面，也不宣称历史页面已完整覆盖 V3。

## 什么时候需要修改

需要调整维护完成门、审计异常隔离、可读性覆盖或报告字段时修改，并核对落盘报告与返回状态一致。

## 在代码中的位置

[打开源码：scripts/ckb_core/llm_wiki_capabilities.py 第 432 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/llm_wiki_capabilities.py:432:1)  `scripts/ckb_core/llm_wiki_capabilities.py:432-527`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[KeywordFallbackOptions 与 KeywordProviderConfig 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_agent_protocol]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_work_record_index]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index 与 _tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[check_fact_freshness]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_gap 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ingest_web_reference 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[maintenance_check 与 capability_matrix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[preflight 与 git 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_operation 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[maintenance_check 与 capability_matrix 的协作实现]] 汇总了本页。
- 与 [[review_management_task 与 default_management_registry_path 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[start_scope_extension 与 _error 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
