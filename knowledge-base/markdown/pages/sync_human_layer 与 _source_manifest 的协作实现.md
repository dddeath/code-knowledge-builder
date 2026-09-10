# sync_human_layer 与 _source_manifest 的协作实现

标签：#类型/代码

> `scripts/ckb_core/knowledge_layers.py` 是 `scripts/ckb_core/knowledge_layers.py` 中负责汇总并提供机器事实到 human/markdown 双层投影和镜像审计的文件入口。 它按源码所示的参数、条件分支和数据结构完成汇总并提供机器事实到 human/markdown 双层投影和镜像审计，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当机器事实到 human/markdown 双层投影和镜像审计的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/knowledge_layers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:1:1)  `scripts/ckb_core/knowledge_layers.py:1-262`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[sync_human_layer]]。

## 谁会来到这里

- 与 [[audit_global]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。
- 与 [[sync_human_layer]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 内部细节

<details><summary>查看本页收纳的 7 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_source_manifest` | 处理 `manifest` 对应的数据与约束。 |
| `build_facts_layer` | 构建 `facts_layer` 对应的数据与约束。 |
| `audit_facts_layer` | 审计 `facts_layer` 对应的数据与约束。 |
| `_copy_file` | 复制 `file` 对应的数据与约束。 |
| `_generated_files` | 处理 `files` 对应的数据与约束。 |
| `audit_human_layer` | 审计 `human_layer` 对应的数据与约束。 |
| `mirror_note` | 镜像 `note` 对应的数据与约束。 |

</details>
