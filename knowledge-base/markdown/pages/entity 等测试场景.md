# entity 等测试场景

标签：#类型/代码

> 检验增量迁移中旧页面标题向新归属页的重连规则。 用实际逻辑投影构造页面转附录和聚合页案例，验证唯一映射、歧义保留、代码示例与证据字节保护和幂等性。

## 什么时候需要修改

修改语义匹配、归属投影、双链替换或不可变记录边界时增补对应反例。

## 在代码中的位置

[打开源码：tests/test_migration_owner_relink.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration_owner_relink.py:1:1)  `tests/test_migration_owner_relink.py:1-104`

## 相关代码

- 主要代码单元是 [[entity]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 5 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `projection` | 调用实际逻辑投影并选取页面、链接和实体归属映射作为重连输入。 |
| `MigrationOwnerRelinkTests` | 验证页面转附录及聚合页的唯一归属重连，覆盖歧义保留和不可变证据边界。 |
| `MigrationOwnerRelinkTests.setUp` | 构造旧新投影、含代码示例的双镜像笔记与三类不可变文件作为重连夹具。 |
| `MigrationOwnerRelinkTests.test_page_to_appendix_and_unique_aggregate_links_follow_actual_owner_projection` | 验证页面转附录和聚合页链接指向真实新归属，且正文、证据及重复执行结果稳定。 |
| `MigrationOwnerRelinkTests.test_duplicate_semantic_entities_and_split_boundary_are_not_guessed` | 构造重复语义实体与拆分边界，断言旧链接保留并记录未唯一映射的标题。 |

</details>
