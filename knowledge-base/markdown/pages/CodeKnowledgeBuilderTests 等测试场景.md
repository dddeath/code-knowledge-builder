# CodeKnowledgeBuilderTests 等测试场景

标签：#类型/代码

> 该页面汇总 CKB 范围、语言、导航、投影、中文、Logseq、C# 和完成门回归测试。 它通过真实临时 Git 仓库验证主流水线的成功、失败、恢复和审计行为。

## 什么时候需要修改

核心构建契约、输出格式或语言支持变化时，需要修改相应测试与夹具。

## 在代码中的位置

[打开源码：tests/test_ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb.py:1:1)  `tests/test_ckb.py:1-1137`

## 相关代码

- 主要代码单元是 [[CodeKnowledgeBuilderTests]]。
- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- [[CodeKnowledgeBuilderTests]] 会使用这里提供的行为。
- [[LspClient.start]] 关联到这里的验证场景。
- [[LspClient.start 与 _version_matches 的协作实现]] 关联到这里的验证场景。
- [[audit_migration]] 关联到这里的验证场景。
- [[audit_migration 与 _entity_key 的协作实现]] 关联到这里的验证场景。
- [[create_source_snapshot]] 关联到这里的验证场景。
- [[create_source_snapshot 与 git 的协作实现]] 关联到这里的验证场景。
- [[execute]] 关联到这里的验证场景。
- [[load_page_config]] 关联到这里的验证场景。
- [[load_page_config 与 _merge_known 的协作实现]] 关联到这里的验证场景。
- [[module_name 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[parse_file]] 关联到这里的验证场景。
- [[parse_file 与 _language 的协作实现]] 关联到这里的验证场景。
- [[query_graph 与 _networkx_modules 的协作实现]] 关联到这里的验证场景。
- [[record_note 与 page_tag 的协作实现]] 关联到这里的验证场景。
- [[retrieve 与 _tokens 的协作实现]] 关联到这里的验证场景。
- [[retrieve_machine]] 关联到这里的验证场景。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 关联到这里的验证场景。
- [[run]] 关联到这里的验证场景。
- [[run 与 CkbError 的协作实现]] 关联到这里的验证场景。
- [[status]] 关联到这里的验证场景。
- [[status 与 _load_state 的协作实现]] 关联到这里的验证场景。
- [[sync_human_layer]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]

## 内部细节

<details><summary>查看本页收纳的 5 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `invoke` | 该附属代码负责构造或执行可重复的回归验证场景，并把结果交给所属页面中的主流程使用。 |
| `write` | 创建父目录并写入规范 UTF-8 测试文本。 |
| `git` | 该附属代码负责范围、分段、审阅、格式、索引、C#、配置和完成门回归测试，并把结果交给所属页面中的主流程使用。 |
| `make_repo` | 构造覆盖多语言、依赖排除和 Git 来源的测试仓库。 |
| `review_all` | 该附属代码负责核对并登记逐实体 Agent 审阅结果，并把结果交给所属页面中的主流程使用。 |

</details>
