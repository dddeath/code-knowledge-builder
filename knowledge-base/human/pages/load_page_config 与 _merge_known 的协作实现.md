# load_page_config 与 _merge_known 的协作实现

标签：#类型/代码

> 该文件集中实现页面配置合并、规范化、校验和固定。 它是 Code Knowledge Builder 中承载页面配置合并、规范化、校验和固定的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当页面配置合并、规范化、校验和固定的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/page_config.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/page_config.py:1:1)  `scripts/ckb_core/page_config.py:1-244`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 主要代码单元是 [[load_page_config]]。

## 谁会来到这里

- [[audit_global]] 会使用这里提供的行为。
- [[audit_global 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。
- [[load_page_config]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[HumanPageTemplateValidationTests]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 7 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_merge_known` | 该附属代码负责合并批次实体和跨批次关系，并把结果交给所属页面中的主流程使用。 |
| `_integer` | 该附属代码负责页面配置合并、规范化、校验和固定，并把结果交给所属页面中的主流程使用。 |
| `_section_list` | 该附属代码负责页面配置合并、规范化、校验和固定，并把结果交给所属页面中的主流程使用。 |
| `normalize_page_config` | 该附属代码负责规范化并校验不可漂移的页面配置，并把结果交给所属页面中的主流程使用。 |
| `page_config_bytes` | 该附属代码负责规范化并校验不可漂移的页面配置，并把结果交给所属页面中的主流程使用。 |
| `page_config_sha256` | 该附属代码负责规范化并校验不可漂移的页面配置，并把结果交给所属页面中的主流程使用。 |
| `write_page_config` | 该附属代码负责规范化并校验不可漂移的页面配置，并把结果交给所属页面中的主流程使用。 |

</details>
