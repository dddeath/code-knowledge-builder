# RecordReplaceTests.test_replace_updates_every_role_and_rollback_is_exact_and_idempo…（test_record_replace 测试）

标签：#类型/代码

> 该测试替换工作记录后核对全部文件与双索引角色、双镜像新正文和稳定元数据，再回滚并重复回滚以验证精确恢复与幂等。 它验证替换事务更新派生角色但保留记录身份、创建时间和原有证据链接，恢复比较采用目标角色逻辑快照而非只看命令成功。

## 什么时候需要修改

记录角色集合、稳定元数据、正文替换或回滚幂等规则变化时修改此测试，并保留替换后变化及回滚后完全相等两组断言。

## 在代码中的位置

[打开源码：tests/test_record_replace.py 第 148 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_record_replace.py:148:1)  `tests/test_record_replace.py:148-189`

## 相关代码

- 与 [[RecordReplaceTests.test_replace_updates_every_role_and_rollback_is_exact_and_idempo…（tests/test_record_replace.py:1）]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[RecordReplaceTests.test_replace_updates_every_role_and_rollback_is_exact_and_idempo…（tests/test_record_replace.py:1）]] 汇总了本页。
