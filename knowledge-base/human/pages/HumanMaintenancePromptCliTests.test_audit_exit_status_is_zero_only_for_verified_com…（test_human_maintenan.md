# HumanMaintenancePromptCliTests.test_audit_exit_status_is_zero_only_for_verified_com…（test_human_maintenance_prompts 测试）

标签：#类型/代码

> 该测试向维护摘要审计命令提交完整通过样例，要求退出零；再把命令输出改为仅已启动，要求退出五并指出启动不等于完成。 它把命令行成功状态与可核验的完成证据绑定，防止叙述式进度被当作维护完成。

## 什么时候需要修改

摘要审计字段、退出码或完成证据判断变化时修改此测试，并保留正反两种实际命令返回断言。

## 在代码中的位置

[打开源码：tests/test_human_maintenance_prompts.py 第 459 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_human_maintenance_prompts.py:459:1)  `tests/test_human_maintenance_prompts.py:459-473`

## 相关代码

- 与 [[HumanMaintenancePromptCliTests.test_audit_exit_status_is_zero_only_for_verified_com…（tests/test_human_maintenance_prompts.py:1）]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[HumanMaintenancePromptCliTests.test_audit_exit_status_is_zero_only_for_verified_com…（tests/test_human_maintenance_prompts.py:1）]] 汇总了本页。
