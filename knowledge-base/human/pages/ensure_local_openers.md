# ensure_local_openers

标签：#类型/代码

> 该函数优先读取并验证已有本地源码打开配置，文件不存在时根据工作仓库和可选固定快照生成默认配置并写入。 它让页面和索引共用稳定的本地打开方式，已有配置不会因传入新的默认仓库参数而被静默覆盖。

## 什么时候需要修改

打开配置持久化入口、默认工作区与快照选择或配置校验方式变化时修改此函数，并分别检查已有配置复用和首次创建。

## 在代码中的位置

[打开源码：scripts/ckb_core/source_links.py 第 96 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:96:1)  `scripts/ckb_core/source_links.py:96-102`

## 相关代码

- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ensure_local_openers 与 SourceLinkRenderer 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[build_agent_index 与 _tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[ensure_local_openers 与 SourceLinkRenderer 的协作实现]] 汇总了本页。
- 与 [[record_note 与 page_tag 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
