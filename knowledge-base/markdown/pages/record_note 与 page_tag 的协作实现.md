# record_note 与 page_tag 的协作实现

标签：#类型/代码

> 该模块把中文分析、修改、实验、问题和会话记录叠加在固定代码知识库之上，维护知识页及源码链接、双镜像正文、元数据和已有索引，并保存工作树变化的独立覆盖层。 它区分旧式正文与经过作者包验证的结构化正文，后者重新校验章节证据且不允许普通追加降级；人类投影尚未就绪时可排队，之后按变更路径或检索证据落地。

## 什么时候需要修改

记录正文合同、链接映射、作者包验证、追加与排队规则或工作树变化采集变化时修改此模块，并核对正文不泄漏机器证据、镜像同步以及固定快照与工作树事实分离。

## 在代码中的位置

[打开源码：scripts/ckb_core/workspace_notes.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/workspace_notes.py:1:1)  `scripts/ckb_core/workspace_notes.py:1-464`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[HumanPageTemplateContract 与 SectionContract 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ensure_local_openers]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ensure_local_openers 与 SourceLinkRenderer 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[record_note]]。

## 谁会来到这里

- 与 [[audit_agent_protocol 与 _default_python 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[finish_session]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[finish_session 与 _session_directory 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[migrate_output 与 _entity_key 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[review_automation]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[rollback_replacement]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[rollback_replacement 与 RecordReplaceLockError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 13 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `page_tag` | 按页面类型返回边界、职责或代码的中文类型标签。 |
| `_markdown_root` | 要求 Markdown 投影清单已存在，满足记录写入前提后返回该镜像根目录。 |
| `_resolve_page_titles` | 将明确标题或唯一子串选择器以及检索记录中的页面和实体映射到现有知识页，并按首次出现顺序去重。 |
| `_source_links_for_titles` | 将选定页面映射到图中实体，按本地打开配置生成带源码行范围的链接，跳过不对应源码实体的页面。 |
| `read_note_body` | 读取并检查中文笔记正文的编码、非空内容和人类输出约束，发现不符合项时在写入前报错。 |
| `render_note_text` | 按传统记录或 V3 正文生成页面；V3 保留已编排章节，仅插入类型标签并核对标题。 |
| `note_contract_metadata` | 重新验证显式 V3 编写包的正文、章节证据和本地来源文件，不把普通旧正文标为已通过 V3。 |
| `queue_pending_note` | 在人类投影尚未就绪时保存带来源和变化路径的中文待办笔记，以递增文件名避免覆盖。 |
| `selectors_for_changed_paths` | 将变化源码路径映射到已有页面，匹配不到时最多返回一个仓库级入口。 |
| `materialize_pending_notes` | 把尚未投影的待办笔记逐项写成正式记录，缺失的检索文件不作为有效引用，成功后记录投影位置。 |
| `audit_notes` | 检查记录类型标签、中文正文和知识链接，并报告可见哈希或缺失目录等问题。 |
| `sync_workspace` | 记录绑定工作树的状态、当前提交与未暂存差异；它不重建固定源码事实，也不将暂存区差异包含在该补丁中。 |
| `workspace_status` | 返回固定快照基线、最近工作树记录与笔记检查状态，不主动更新工作树记录。 |

</details>
