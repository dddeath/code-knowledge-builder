# assertions 等测试场景

标签：#类型/代码

> 该文件验证标签断言和策略的严格模式、路径与标签限制、幂等回放及回滚工作区边界。 它用隔离数据库和命令行失败样本检验越界目标、清单和备份均被阻断，并检查失败没有改写受保护文件。

## 什么时候需要修改

标签协议、幂等键、工作区约束或回滚参数变化时修改此文件，并保留对未知字段和外部路径的拒绝断言。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_contracts.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_contracts.py:1:1)  `tests/test_ckb_tag_navigation_contracts.py:1-217`

## 相关代码

- 主要代码单元是 [[assertions]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `TagNavigationContractTests` | 验证标签断言与策略的严格模式、路径和标签边界、幂等回放及工作区外输出和回滚目标保护。 |
| `TagNavigationContractTests.test_six_schemas_are_strict_json_objects` | 核对标签原型包含六个对象模式且均禁止未知字段。 |
| `TagNavigationContractTests.test_assertion_schema_excludes_conversation_and_secret_fields` | 向合法标签断言加入会话、提示或秘密字段，要求严格模式校验拒绝。 |
| `TagNavigationContractTests.test_paths_tags_and_policy_are_bounded` | 检查绝对目标路径、不规范标签和上级跳转标签被拒绝，同时验证固定策略可被接受。 |
| `TagNavigationContractTests.test_replay_deduplicates_identical_idempotency_key` | 回放固定断言集合，核对重复幂等键只计一次且数据库完整性通过。 |
| `TagNavigationContractTests.test_idempotency_conflict_rolls_back_entire_new_database` | 构造同幂等键不同内容的冲突，要求回放失败并撤销新建数据库。 |
| `TagNavigationContractTests.test_cli_rejects_output_outside_workspace` | 通过命令行验证输出、回滚清单、目标和备份必须位于指定工作区，越界时保留现有文件原字节。 |
| `TagNavigationContractTests.test_cli_rejects_output_outside_workspace.digest` | 计算回滚路径测试中字节内容的 SHA-256，以构造预期目标和备份身份。 |
| `TagNavigationContractTests.test_cli_rejects_output_outside_workspace.run_rollback` | 以指定工作区调用标签回滚命令，捕获退出状态与 UTF-8 输出供边界断言。 |

</details>
