# MigrationTest 等测试场景

标签：#类型/代码

> 该文件验证知识库在新 Git 提交上的精确增量迁移和完成态目录提升。 它覆盖 blob 与中文审阅复用、可变笔记、Hook 数据、不可变基线、Wiki 重链接、输出路径重定位及篡改失败门。

## 什么时候需要修改

迁移复用、目录切换、可变层或审计契约变化时，需要修改该文件。

## 在代码中的位置

[打开源码：tests/test_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:1:1)  `tests/test_migration.py:1-194`

## 相关代码

- 主要代码单元是 [[MigrationTest]]。
- 实现时会用到 [[audit_global 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[doctor_report 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[load_page_config]] 关联到这里的验证场景。
- [[load_page_config 与 _merge_known 的协作实现]] 关联到这里的验证场景。
- [[parse_file]] 关联到这里的验证场景。
- [[parse_file 与 _language 的协作实现]] 关联到这里的验证场景。
- [[preflight]] 关联到这里的验证场景。
- [[preflight 与 git 的协作实现]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 2 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `git` | 在临时夹具仓库执行 Git 命令并把非零退出转为测试错误。 |
| `review_all` | 逐包填充固定中文审阅字段并通过普通审阅门。 |

</details>
