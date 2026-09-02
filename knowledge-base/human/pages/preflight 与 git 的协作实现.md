# preflight 与 git 的协作实现

标签：#类型/代码

> `scripts/ckb_core/gitrepo.py` 是 `scripts/ckb_core/gitrepo.py` 中负责汇总并提供固定 Git 提交、blob、工作树与源码快照读取的文件入口。 它按源码所示的参数、条件分支和数据结构完成汇总并提供固定 Git 提交、blob、工作树与源码快照读取，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当固定 Git 提交、blob、工作树与源码快照读取的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/gitrepo.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:1:1)  `scripts/ckb_core/gitrepo.py:1-419`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[FactFreshnessStateMachineTest]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[parser]]。
- 主要代码单元是 [[preflight]]。

## 谁会来到这里

- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[finalize 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[preflight]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[FactFreshnessStateMachineTest]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 13 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `git` | 处理 `git` 对应的数据与约束。 |
| `_git_probe` | 处理 `probe` 对应的数据与约束。 |
| `_identity_value` | 处理 `value` 对应的数据与约束。 |
| `prepare_git_repository` | 准备 `git_repository` 对应的数据与约束。 |
| `assert_unchanged` | 处理 `unchanged` 对应的数据与约束。 |
| `create_source_snapshot` | 创建 `source_snapshot` 对应的数据与约束。 |
| `assert_source_snapshot` | 处理 `source_snapshot` 对应的数据与约束。 |
| `tracked_sources` | 处理 `sources` 对应的数据与约束。 |
| `tracked_csharp_project_files` | 处理 `csharp_project_files` 对应的数据与约束。 |
| `blob_bytes` | 处理 `bytes` 对应的数据与约束。 |
| `blob_bytes_many` | `blob_bytes_many` 是第 363-393 行的函数，供所属页面定位实现。 |
| `object_exists` | 判断 `object_exists` 所表达的条件。 |
| `resolve_scope_paths` | 解析并确定 `scope_paths` 对应的数据与约束。 |

</details>
