# build_agent_index

标签：#类型/代码

> 从人类投影、固定图和工作笔记生成兼容检索库 agent-index.sqlite，包含页面、符号归属、关系、词项、笔记及 FTS5 索引。 先构建候选索引，核对数据及引用一致性后替换正式文件；词项按页面标题、符号、摘要和路径加权，关系来自投影链接。

## 什么时候需要修改

投影页面结构、实体所有者、检索权重或笔记格式改变时，联动文档提取和索引审计；数据库表与 FTS 定义调整时同时检查兼容检索消费者和临时库替换流程。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_index.py 第 163 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_index.py:163:1)  `scripts/ckb_core/agent_index.py:163-341`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index 与 _tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[search_terms 与 _split_camel 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[audit_global]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[build_agent_index 与 _tokens 的协作实现]] 汇总了本页。
- 与 [[create_gap 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ingest_web_reference 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note 与 page_tag 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
