# build_agent_index 与 _tokens 的协作实现

标签：#类型/代码

> `scripts/ckb_core/agent_index.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责构建兼容 Agent 索引，并按预算执行确定性检索与结果排序。

## 什么时候需要修改

当 `scripts/ckb_core/agent_index.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:1:1)  `scripts/ckb_core/agent_index.py:1-555`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[build_agent_index]]。
- 与 [[ensure_local_openers]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ensure_local_openers 与 SourceLinkRenderer 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[search_terms]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[search_terms 与 _split_camel 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_global]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[maintenance_check]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[rollback_replacement]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[rollback_replacement 与 RecordReplaceLockError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_tokens` | `_tokens` 是第 24-25 行的函数，供所属页面定位实现。 |
| `_note_documents` | `_note_documents` 是第 28-44 行的函数，供所属页面定位实现。 |
| `_projection` | `_projection` 是第 47-60 行的函数，供所属页面定位实现。 |
| `_page_documents` | `_page_documents` 是第 63-160 行的函数，供所属页面定位实现。 |
| `audit_agent_index` | `audit_agent_index` 是第 344-390 行的函数，供所属页面定位实现。 |
| `_agent_index_ready` | `_agent_index_ready` 是第 393-405 行的函数，供所属页面定位实现。 |
| `_fts_query` | `_fts_query` 是第 408-409 行的函数，供所属页面定位实现。 |
| `_next_pack_path` | `_next_pack_path` 是第 412-423 行的函数，供所属页面定位实现。 |
| `retrieve` | 在只读兼容 SQLite 中融合标题、符号、词项、FTS5 和前三个种子的一跳关系得分，按预算写阅读包与检索记录，无候选时返回 needs-grep。 |

</details>
