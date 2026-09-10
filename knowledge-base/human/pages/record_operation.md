# record_operation

标签：#类型/代码

> 该函数校验操作类别、命令状态词和相对证据路径，将操作记录写入按 UTC 日期分片的机器日志；同日相同操作、状态和证据生成同一事件编号，重复调用只更新去重统计。 它在日志锁内执行过期清理、按记录数和字节数淘汰旧项、分片写入及最新摘要更新，为维护活动保留有界机器证据，而不生成面向人类的知识页面。

## 什么时候需要修改

操作类型、事件去重键、证据路径限制、分片容量或摘要字段发生变化时修改此函数，并检查重复记录、容量淘汰和摘要与实际日志的一致性。

## 在代码中的位置

[打开源码：scripts/ckb_core/operation_journal.py 第 261 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/operation_journal.py:261:1)  `scripts/ckb_core/operation_journal.py:261-309`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_operation 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[BatchProjectError 与 ProtocolRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[record_operation 与 _root 的协作实现]] 汇总了本页。
- 与 [[rollback_replacement]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[rollback_replacement 与 RecordReplaceLockError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
