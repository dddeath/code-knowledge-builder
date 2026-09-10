# ReferenceMarkerMigrationTests.migrate_failed_reference_marker

标签：#类型/代码

> 构造真实失败标记后修正原文，把保留层复制到已有图的小库并记录迁移计划。 先实际审阅资料，再通过原文漂移生成失败状态；恢复原字节后保留该历史标记，使用真实保留函数和已完成目标库验证后续重建清理，而非伪造成功标记。

## 什么时候需要修改

需要改变历史状态标记、已有图迁移计划或非标记文件缺失对照夹具时修改。

## 在代码中的位置

[打开源码：tests/test_reference_marker_migration.py 第 16 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_reference_marker_migration.py:16:1)  `tests/test_reference_marker_migration.py:16-54`

## 谁会来到这里

- [[ReferenceMarkerMigrationTests.migrate_failed_reference_marker 等测试场景]] 汇总了本页。
