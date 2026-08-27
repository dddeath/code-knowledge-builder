# CodeKnowledgeBuilderTests 等测试场景

标签：#类型/代码

> 该文件包含主构建、局部扫描、投影、配置、C#、机器检索和完成门的端到端回归测试。 它用隔离多语言 Git 夹具验证成功路径、失败门、检索确定性、静态缓存命中和跨格式一致性。

## 什么时候需要修改

主 CLI 契约、知识库 Schema、检索统计、页面配置或语言支持变化时，需要修改该文件。

## 在代码中的位置

[打开源码：tests/test_ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb.py:1:1)  `tests/test_ckb.py:1-1152`

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
- [[SourceLinkRenderer.uri]] 关联到这里的验证场景。
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
- [[status 与 _replace_output_prefix 的协作实现]] 关联到这里的验证场景。
- [[sync_human_layer]] 关联到这里的验证场景。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]

## 内部细节

<details><summary>查看本页收纳的 5 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `invoke` | 在固定测试环境中调用 ckb.py 并捕获 UTF-8 输出和退出状态。 |
| `write` | 把测试夹具文本规范化为带结尾换行的 UTF-8 文件。 |
| `git` | 在指定测试仓库中执行 Git 命令并把失败转换为测试异常。 |
| `make_repo` | 创建含 Python、JavaScript、C、C++ 与排除目录的已提交测试仓库。 |
| `review_all` | 为测试输出构建全部分段并提交逐实体中文审阅。 |

</details>
