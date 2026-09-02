# CKB 人类知识库投影生成流程

标签：#类型/分析

## 投影的目标

CKB 的人类知识库不是机器实体清单的 Markdown 导出，而是从完整固定源码事实中生成的确定性、有配额、面向理解和修改代码的中文导航。事实层负责重建，机器层负责检索，人类层负责阅读与行动；机器层继续保存全部实体、关系、来源范围和审计字段，人类层只展示有限的独立页、聚合关系和可直接打开的源码入口。

```text
固定 Git 源码
→ Tree-sitter/LSP 与来源事实
→ 完整 graph.json 和 facts
→ navigation plan
→ Agent 来源绑定的中文审阅
→ logical projection
→ markdown 兼容投影
→ human 主人类知识库
→ 中文、链接、镜像、可读性和完成门审计
```

## 页面分类由确定性脚本决定

`build_navigation_plan` 接收实体、关系、显式入口和固定 `page-config.json`，为每个实体分配 `page`、`appendix` 或 `boundary`，并写出唯一 owner page。Agent 不决定页面数量、重要性、排序或所属关系，只负责根据精确源码范围审阅中文含义、职责、修改时机和附属实体的一句话说明。

- `page`：文件页、入口核心实体页、有限的邻近实体页以及仓库/模块聚合页。
- `appendix`：没有独立成页的访问器、简单判断、局部辅助函数和薄包装，收纳到词法祖先页或文件页的“内部细节”。
- `boundary`：局部扫描范围外的一跳协作实体，按源码路径聚合为边界页，不为每个端点扩散页面。

当前页面配额为：普通文件最多一个关键实体页，入口核心文件最多四个，邻近文件最多一个；每个入口最多四个核心页和三个邻近页。超过配额的实体仍完整保留在机器层，并通过 appendix 或 boundary 进入人类导航。

## 逻辑人类导航图

`_logical_projection` 根据已应用分类建立 `entity`、`file`、`boundary`、`module` 和 `repository` 五类逻辑页面。所有机器实体都映射到一个 owner page：独立页指向自己，appendix 指向所属页，boundary 指向按路径聚合的边界页。

机器实体关系先按来源页、目标页和关系类型聚合，再分为 navigation、direct、aggregate、test 和 boundary。当前每页最多显示十二组直接关系、八组聚合关系、六组测试关系和六组边界关系；被预算隐藏的关系继续保存在机器图中，页面只显示“可用图查询继续缩小范围”的提示。

页面标题通过确定性规则生成自然标题。文件名以清洗后的标题为基础，只有清洗后冲突时才加中文数字后缀。人类页不展示内部稳定 ID、完整提交标识、blob、机器 classification、原始关系类型或关系数量。

## Markdown 页面正文

`_render_markdown_page` 按固定页面配置渲染正文。当前代码页依次包含：

1. 概述；
2. 什么时候需要修改；
3. 在代码中的位置；
4. partial 类型片段；
5. 相关代码；
6. 谁会来到这里；
7. 相关测试；
8. 隐藏关系提示；
9. 内部细节。

页面以一个自然标题和一个 `#类型/...` 标签开始，不使用 YAML frontmatter。源码位置由本地 opener 生成可点击链接。关系被改写为“会使用”“由测试覆盖”“谁会来到这里”等自然中文句子。appendix 使用折叠表格，每行只包含代码符号和一句具体中文作用。

## 先生成 markdown，再同步 human

`project_markdown` 先在 `OUTPUT/markdown` 生成兼容 vault：渲染 `pages/*.md`，生成 `INDEX.md`、`WIKI.md`、`RECORDS.md`、`normalized.edn`、上下文预算、可读性报告、`projection.json`、Obsidian 配置和 Logseq 配置，并写入 `.ckb-generated-files.json` 标记生成器所有权。

`sync_human_layer` 再把已审计的生成文件同步到 `OUTPUT/human`。同步前只删除上一版清单中由生成器拥有的文件；正式工作记录、反馈和用户自有 Obsidian 状态按独立规则保留。代码页、导航页、正式记录和反馈要求 human/markdown 镜像一致；human 可以额外保存 Agent Policy、已安装插件和不属于生成器的用户状态。

`human/manifest.json` 记录主 vault、兼容 vault、生成文件、笔记目录、反馈目录和中文契约。`projection.json` 记录页面、可见关系、实体 owner、固定来源清单、页面配置、关系配额、上下文预算和生成器所有权；这些机器清单不进入普通页面正文。

## 导航、工作记录、reference、gap 与 feedback

- `INDEX.md` 按任务目的区分代码理解、历史工作记录、reference 和精确机器检索，不是页面字母表。
- `WIKI.md` 解释阅读顺序、页面保留内容、中文规范、页面配置、修改入口和 Agent 检索方式。
- analysis、changes、pitfalls、experiments、sessions 通过 `record` 写入。`RECORDS.md` 从完整记录集合重新生成，每条正式记录恰好出现一次并带一句中文摘要。
- reference 经过 ingest、精确行范围 review 和 audit 后进入独立资料层；每个 active source 最多投影一个人类摘要页，并由 `REFERENCES.md` 导航，不成为代码实体。
- research gap 保持机器优先，不为每项缺口生成页面，只在 `RECORDS.md` 中保留一个聚合入口。关闭必须提交中文结论和新的证据路径。
- feedback 进入 `feedback/open` 或 `feedback/resolved`，采纳时先修改来源、生成规则或正式记录，再由命令归档；不直接编辑生成页面。

## 生成器所有权与刷新边界

`.ckb-generated-files.json` 是生成器删除和替换文件的边界。重投影只替换清单中的页面、导航、配置和审计文件，不清空整个 vault。直接编辑 `human/pages`、`markdown/pages`、`INDEX.md`、`WIKI.md`、`RECORDS.md`、`REFERENCES.md`、投影清单或 SQLite 会在后续投影中被覆盖或触发审计失败；持久分析和修改原因必须通过 `record`，资料通过 `reference`，缺口和反馈通过各自命令管理。

`human-refresh` 只重写 INDEX、WIKI、RECORDS、projection/readability 元数据和 human manifest/audit，不重新解析源码、重新分类实体或改写代码页与正式笔记。刷新前后会比较受保护页面和笔记的字节；集合或内容变化会使刷新失败。

源码 HEAD 变化时需要在隔离 staging 中执行 migrate 或 rebuild，重新生成机器事实、navigation plan、delta 审阅、Markdown 投影和 human 镜像。只增加工作记录、reference 或 gap 时使用对应命令更新记录与索引，不无条件重扫源码。

## 完成门

人类知识库完成不等于 Markdown 文件已经生成。可读性审计检查自然标题、单一类型标签、无 frontmatter、无内部 ID/完整提交标识/机器字段、无死链和孤页、中文叙述、源码链接、appendix 一句话说明以及页面集合与 navigation plan 一致。

`audit_human_layer` 继续检查生成文件、工作记录、feedback 的 human/markdown 镜像，以及 page/boundary 的中文含义、职责、修改时机和 appendix 的中文说明。最终 `audit_global` 与 `maintain` 聚合固定源码、审阅、Graphify、投影、双 SQLite、Agent Policy、reference、gap、operation journal 和人类可读性；只有全部通过，机器与人类完成标记才同时成立。

## 相关知识页

- [[audit_work_record_index 与 _contains_chinese 的协作实现]]
- [[sync_human_layer]]
- [[audit_agent_protocol]]
- [[maintenance_check]]
- [[audit_references 与 _root 的协作实现]]
- [[module_name 与 estimated_tokens 的协作实现]]
- [[load_page_config 与 _merge_known 的协作实现]]
- [[audit_global 与 _replace_output_prefix 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/work_record_index.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/work_record_index.py:1:1)  `scripts/ckb_core/work_record_index.py:1-242`
- [打开源码：scripts/ckb_core/knowledge_layers.py 第 126 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/knowledge_layers.py:126:1)  `scripts/ckb_core/knowledge_layers.py:126-192`
- [打开源码：scripts/ckb_core/agent_protocol.py 第 420 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol.py:420:1)  `scripts/ckb_core/agent_protocol.py:420-496`
- [打开源码：scripts/ckb_core/llm_wiki_capabilities.py 第 404 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/llm_wiki_capabilities.py:404:1)  `scripts/ckb_core/llm_wiki_capabilities.py:404-452`
- [打开源码：scripts/ckb_core/reference_documents.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_documents.py:1:1)  `scripts/ckb_core/reference_documents.py:1-604`
- [打开源码：scripts/ckb_core/navigation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/navigation.py:1:1)  `scripts/ckb_core/navigation.py:1-456`
- [打开源码：scripts/ckb_core/page_config.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/page_config.py:1:1)  `scripts/ckb_core/page_config.py:1-244`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3482`
