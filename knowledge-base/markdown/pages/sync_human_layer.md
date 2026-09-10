# sync_human_layer

标签：#类型/代码

> `sync_human_layer` 是 `scripts/ckb_core/knowledge_layers.py` 中负责把已审计 Markdown 投影同步到 human 层，并保持生成文件清单和镜像一致的函数。 它按源码所示的参数、条件分支和数据结构完成把已审计 Markdown 投影同步到 human 层，并保持生成文件清单和镜像一致，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当机器事实到 human/markdown 双层投影和镜像审计的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/knowledge_layers.py 第 126 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:126:1)  `scripts/ckb_core/knowledge_layers.py:126-192`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[project_output_contract]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[sync_human_layer 与 _source_manifest 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[sync_human_layer 与 _source_manifest 的协作实现]] 汇总了本页。
