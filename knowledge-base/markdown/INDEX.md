# source 知识库

> 用类、函数和职责聚合页理解代码；机器审计信息不占用阅读页面。

## 从这里开始

- [[source 代码导览]]
- [阅读这套知识库的方法](WIKI.md)

## 按职责浏览

- [[scripts 职责导览]]
- [[tests 职责导览]]

## 精确定位

遇到具体修改任务时，优先使用 `retrieve --profile fast` 获取预算内机器阅读包；复杂问题再使用 `precise`。只在索引返回 `needs-source-read` 时读取最窄源码范围。两种档位都不调用向量模型。

## 工作记录

Agent 的分析、修改、踩坑、实验和会话笔记分别保存在同名目录，并通过双链回到代码页。

## 在 Obsidian 中打开

把 `E:\knowledge_builder\self-workspace\knowledge-base\human` 作为 Obsidian vault 打开；从本页、标签或反向链接进入。`E:\knowledge_builder\self-workspace\knowledge-base\markdown` 是兼容镜像。

## 在 Logseq 中打开

选择输出目录 `E:\knowledge_builder\self-workspace\knowledge-base`；配置文件位于 [logseq/config.edn](logseq/config.edn)。
