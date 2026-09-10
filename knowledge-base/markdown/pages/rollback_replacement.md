# rollback_replacement

标签：#类型/代码

> 按照一个已完成替换的清单恢复其拥有的文件与索引逻辑状态，并报告回滚结果。 先检查清单归属和完整角色集合，再检测当前状态漂移；恢复后仍严格审计笔记和索引，若重新引入坏链等错误则补偿到替换后状态，不套用替换阶段的诊断保留规则。

## 什么时候需要修改

需要明确变更单篇回滚、幂等判断、冲突检测或失败补偿约束时修改。

## 在代码中的位置

[打开源码：scripts/ckb_core/record_replace.py 第 1082 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/record_replace.py:1082:1)  `scripts/ckb_core/record_replace.py:1082-1224`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_work_record_index]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index 与 _tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note 与 page_tag 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_operation]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[rollback_replacement 与 RecordReplaceLockError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[rollback_replacement 与 RecordReplaceLockError 的协作实现]] 汇总了本页。
