# source 知识库

> 先按任务选择入口：理解代码进入职责导览，查找已有结论进入工作记录，精确定位交给确定性检索。

## 按任务选择入口

- **理解或修改代码**：从 [[source 代码导览]] 进入，再按职责缩小到类、函数或聚合页。
- **查找已有分析、变更和实验**：打开 [工作记录导览](RECORDS.md)，按任务目的浏览全部记录。
- **查找已审阅外部资料**：打开 [参考资料导览](REFERENCES.md)，摘要中的每项主张都链接到归档原文范围。
- **精确定位类、函数或源码范围**：使用 `brief --profile fast`，复杂问题再使用完整 `retrieve --profile precise`。
- **了解页面规则和阅读顺序**：打开 [阅读这套知识库的方法](WIKI.md)。

## 按职责浏览代码

- [[scripts 职责导览]]
- [[tests 职责导览]]

## 工作记录

[工作记录导览](RECORDS.md) 为每条分析、变更、实验、踩坑和会话记录提供一句中文说明，并按任务目的分组。导览由脚本从全部现有记录统一生成，不依赖手工挑选。

## 精确定位

遇到具体修改任务时，优先使用 `brief --profile fast` 获取预算内机器阅读包；复杂问题再使用完整 `retrieve --profile precise`。只在索引要求源码回退时读取最窄源码范围。两种档位都不调用向量模型。

## 在 Obsidian 中打开

把 `E:\knowledge_builder\self-workspace\kb-stg-89eac148\human` 作为 Obsidian vault 打开；从本页、工作记录导览、标签或反向链接进入。`E:\knowledge_builder\self-workspace\kb-stg-89eac148\markdown` 是兼容镜像。

## 在 Logseq 中打开

选择输出目录 `E:\knowledge_builder\self-workspace\kb-stg-89eac148`；配置文件位于 [logseq/config.edn](logseq/config.edn)。
