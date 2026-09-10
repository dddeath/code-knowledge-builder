# project_graphify

标签：#类型/代码

> 将已审阅规范图转换为 Graphify 兼容节点链接图、社区记录和中文图报告，同时生成各产物的哈希与计数记录。 对节点和边按标识排序后建图，调用社区聚类、枢纽标签与评分，为每个节点补充社区信息；输出保留固定提交与上游版本，projection.json 记录置信度分布和生成产物，但该函数返回的是 projected 而非最终全局审计完成。

## 什么时候需要修改

节点/边映射、社区算法、中文报告或 Graphify 固定版本改变时，联动 _graphify_node、_graphify_link、_community_records、_report 和后续投影一致性审计。

## 在代码中的位置

[打开源码：scripts/ckb_core/graphify_core.py 第 256 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/graphify_core.py:256:1)  `scripts/ckb_core/graphify_core.py:256-339`

## 相关代码

- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[project_graphify 与 _networkx_modules 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_global]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[project_graphify 与 _networkx_modules 的协作实现]] 汇总了本页。
