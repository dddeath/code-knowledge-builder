# IncrementalRecordReplaceTests.prepare_dangling

标签：#类型/代码

> 创建另一篇受管记录，并向指定历史笔记双镜像注入坏链以构造修复前状态。 先把复制库的协议和插件契约绑定到本次测试目录，再保存目标全部角色快照，避免把夹具路径漂移混成待测试的坏链问题。

## 什么时候需要修改

需要改变多笔记错误场景、镜像基线或临时库绑定方式时修改。

## 在代码中的位置

[打开源码：tests/test_record_replace_incremental.py 第 23 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_record_replace_incremental.py:23:1)  `tests/test_record_replace_incremental.py:23-36`

## 谁会来到这里

- [[IncrementalRecordReplaceTests.prepare_dangling 等测试场景]] 汇总了本页。
