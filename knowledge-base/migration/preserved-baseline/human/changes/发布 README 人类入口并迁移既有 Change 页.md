# 发布 README 人类入口并迁移既有 Change 页

标签：#类型/变更

## 修改内容

项目 README 现在从人类要完成的任务出发，只保留三个入门入口：了解本项目知识库结构、让 Agent 安装本项目、让 Agent 解释自己的项目。安装 Skill 与为业务仓库建库使用两段独立 Prompt，后续阅读、记录、维护、迁移和 Harness 接入按自然顺序继续展开。

## 修改时间

2026 年 9 月 3 日。

## 修改原因

旧说明把安装、使用、维护和内部核验混在同一层级，人类需要先理解大量实现细节，仍不清楚应怎样指挥 Agent、最终会得到什么，以及只需验收哪些结果。

## 实现概述

每个入口统一展示“会直接得到什么、复制给 Agent 的 Prompt、只验收哪些最终结果”。第一屏不出现命令行、内部审计过程、SQLite 或门数量。五个既有 change 页同时改用 V3 结构，依次说明修改内容、时间、原因、关键实现、关联特性、当前结果、适用边界和深入阅读。

## 关联特性

这项修改连接 README、人类页面模板、受控 record 正文替换和渐进式披露。完整命令、哈希、逐项审计和失败调试仍保存在机器证据层；人类明确追问时，再由 Agent 读取并解释。

## 当前结果

README 三个入口及其职责分离已有自动回归保护。五个目标 change 页已经通过受控替换写入稳定记录层，人类与 Markdown 镜像一致，原记录身份、索引和回滚链保持有效。

## 适用边界

README 负责帮助人类开始使用和继续指挥 Agent，不承担完整 API 或内部实现手册。需要修改知识库时，仍由 Agent 执行对应工具并返回最终结果；人类无需预先学习命令参数。

## 深入阅读

需要复查三个入口和安装/建库职责分离时，从“ReadmeHumanEntryTests”进入，让 Agent 只展开与当前阅读任务有关的检查。

## 相关知识页

- [[ReadmeHumanEntryTests]]

## 源码入口

- [打开源码：tests/test_readme_human_entry.py 第 20 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_readme_human_entry.py:20:1)  `tests/test_readme_human_entry.py:20-73`
