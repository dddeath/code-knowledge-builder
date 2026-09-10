# preflight 与 git 的协作实现

标签：#类型/代码

> 为固定源码建库提供 Git 预检、源码快照、受跟踪文件筛选和二进制 blob 读取，将仓库身份与实际源码字节保持绑定。 已有仓库必须有干净提交；只有显式允许初始化且尚无提交时才创建首个提交。语义分析使用锁定的 detached worktree，移动后的快照只修复自身注册。源码枚举排除依赖和生成目录，C# 项目元数据独立收集，批量读取 blob 时逐帧校验对象和字节长度。

## 什么时候需要修改

修改支持的后缀、排除规则或范围选择时联动解析入口；调整仓库初始化、快照移动或 cat-file 协议时，复查显式初始化权限、commit/tree 清洁校验、Git 注册反向链接和二进制边界测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/gitrepo.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/gitrepo.py:1:1)  `scripts/ckb_core/gitrepo.py:1-476`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[preflight]]。

## 谁会来到这里

- 与 [[audit_global]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[maintenance_check]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[migrate_output 与 _entity_key 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[preflight]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 14 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `git` | 在指定仓库运行 Git 并返回标准输出，默认将非零退出转换为含错误详情的 CkbError。 |
| `_git_probe` | 在指定仓库运行 Git 并直接返回含退出码与输出的进程结果，交由调用者判断失败。 |
| `_identity_value` | 读取指定 Git 配置键，成功且非空时返回去除首尾空白的值，其余情况返回 None。 |
| `prepare_git_repository` | 核验仓库目录与 Git 可用性；仅在显式允许且无提交时暂存文件并创建一次初始提交，返回提交、作者来源及是否执行初始化的记录。 |
| `assert_unchanged` | 重新执行干净仓库预检，并在提交或 tree 与绑定基线不一致时抛出来源陈旧错误。 |
| `create_source_snapshot` | 在知识库内创建锁定的 detached 固定提交工作树，核验其提交和 tree 后返回源码快照描述。 |
| `relocate_source_snapshot` | 验证移动快照的 Git 管理目录、反向链接、提交、tree 与干净状态，只修复本快照注册路径并保持锁定，不接管其他工作树。 |
| `assert_source_snapshot` | 确认绑定提交仍存在且快照目录的 HEAD、tree 和已跟踪文件未漂移，同时允许原仓库活动工作树继续变化。 |
| `tracked_sources` | 枚举固定提交中受支持语言文件，依据目录和生成文件规则分离纳入与排除清单，显式 include 模式可覆盖默认排除。 |
| `tracked_csharp_project_files` | 从固定 Git tree 单独收集 C# 项目和构建配置元数据并按路径排序，不将其登记为源码实体。 |
| `blob_bytes` | 用二进制 Git show 读取固定提交中一个路径的原始字节，失败时将 stderr 转为来源陈旧错误。 |
| `blob_bytes_many` | 用单次二进制 cat-file 会话读取去重后的 blob，逐帧校验对象类型、标识、长度和分隔符，再映射回各源码路径。 |
| `object_exists` | 调用 Git cat-file 检查对象是否存在，并将零退出码转换为布尔值。 |
| `resolve_scope_paths` | 将范围选择规范化为相对路径前缀，拒绝空路径和上跳段，再选出受支持文件；任何前缀没有匹配文件时明确报错。 |

</details>
