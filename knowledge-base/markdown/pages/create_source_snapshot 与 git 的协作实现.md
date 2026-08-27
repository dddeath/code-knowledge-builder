# create_source_snapshot 与 git 的协作实现

标签：#类型/代码

> 该页面汇总 Git 预检、固定快照、来源对象读取和扫描范围发现。 它把干净 commit、blob 和仓库内路径设为知识图谱的真实性边界，并排除依赖目录。

## 什么时候需要修改

Git 边界、默认排除项、快照方式或来源读取协议变化时，需要修改本文件。

## 在代码中的位置

[打开源码：scripts/ckb_core/gitrepo.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:1:1)  `scripts/ckb_core/gitrepo.py:1-417`

## 相关代码

- 实现时会用到 [[audit_migration]]。
- 主要代码单元是 [[create_source_snapshot]]。
- 实现时会用到 [[remove]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[status 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[audit_migration 与 _entity_key 的协作实现]] 会使用这里提供的行为。
- [[create_source_snapshot]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[status 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 13 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `git` | 该附属代码负责Git 预检、固定源码快照、tracked source 范围和 blob 读取，并把结果交给所属页面中的主流程使用。 |
| `_git_probe` | 该附属代码负责Git 预检、固定源码快照、tracked source 范围和 blob 读取，并把结果交给所属页面中的主流程使用。 |
| `_identity_value` | 该附属代码负责Git 预检、固定源码快照、tracked source 范围和 blob 读取，并把结果交给所属页面中的主流程使用。 |
| `prepare_git_repository` | 该附属代码负责Git 预检、固定源码快照、tracked source 范围和 blob 读取，并把结果交给所属页面中的主流程使用。 |
| `preflight` | 该附属代码负责Git 预检、固定源码快照、tracked source 范围和 blob 读取，并把结果交给所属页面中的主流程使用。 |
| `assert_unchanged` | 该附属代码负责Git 预检、固定源码快照、tracked source 范围和 blob 读取，并把结果交给所属页面中的主流程使用。 |
| `assert_source_snapshot` | 该附属代码负责建立并验证与固定提交一致的源码快照，并把结果交给所属页面中的主流程使用。 |
| `tracked_sources` | 该附属代码负责解析 tracked source 范围、显式路径和边界实体，并把结果交给所属页面中的主流程使用。 |
| `tracked_csharp_project_files` | 该附属代码负责计算机器交付物的完整性摘要，并把结果交给所属页面中的主流程使用。 |
| `blob_bytes` | 该附属代码负责Git 预检、固定源码快照、tracked source 范围和 blob 读取，并把结果交给所属页面中的主流程使用。 |
| `blob_bytes_many` | 该附属代码负责Git 预检、固定源码快照、tracked source 范围和 blob 读取，并把结果交给所属页面中的主流程使用。 |
| `object_exists` | 该附属代码负责Git 预检、固定源码快照、tracked source 范围和 blob 读取，并把结果交给所属页面中的主流程使用。 |
| `resolve_scope_paths` | 该附属代码负责解析 tracked source 范围、显式路径和边界实体，并把结果交给所属页面中的主流程使用。 |

</details>
