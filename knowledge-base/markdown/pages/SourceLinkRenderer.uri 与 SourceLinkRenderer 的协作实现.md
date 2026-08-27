# SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现

标签：#类型/代码

> 该文件生成指向本地源码精确位置和 Obsidian 笔记的可点击链接。 它集中验证打开器配置、限制仓库路径边界，并让批量检索复用同一渲染器与路径缓存。

## 什么时候需要修改

支持的编辑器、URI 格式、路径边界或缓存行为变化时，需要修改该文件。

## 在代码中的位置

[打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`

## 相关代码

- 主要代码单元是 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[render_integration 与 _looks_windows 的协作实现]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。

## 谁会来到这里

- [[SourceLinkRenderer.uri]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]

## 内部细节

<details><summary>查看本页收纳的 14 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `SourceLinkRenderer` | 复用已验证配置和路径缓存，为多个实体生成可点击的本地源码链接。 |
| `SourceLinkRenderer.__init__` | 一次验证源码打开器配置并初始化仓库根目录与路径缓存。 |
| `SourceLinkRenderer.cache_size` | 报告当前已缓存的源码相对路径数量。 |
| `SourceLinkRenderer.absolute_path` | 校验相对路径边界，并按需缓存对应的仓库内绝对路径。 |
| `SourceLinkRenderer.markdown_link` | 把源码 URI、可读路径和行范围组合为 Markdown 链接。 |
| `default_openers` | 根据仓库和可选快照目录生成默认源码打开器配置。 |
| `ensure_local_openers` | 读取已有打开器配置，或在缺失时写入并返回默认配置。 |
| `validate_local_openers` | 校验编辑器类型、源码视图、模板和仓库根目录字段。 |
| `update_local_openers` | 合并用户指定的编辑器选项并重新验证后保存配置。 |
| `source_absolute_path` | 通过一次性渲染器把仓库相对路径转换为受边界约束的绝对路径。 |
| `source_uri` | 通过一次性渲染器生成指定源码行列的编辑器 URI。 |
| `source_markdown_link` | 通过一次性渲染器生成带可读行范围的源码 Markdown 链接。 |
| `obsidian_open_uri` | 把本地 Markdown 路径编码为 Obsidian 打开链接。 |
| `audit_source_uri` | 解析并核对源码 URI 是否准确指向配置根目录内的目标行。 |

</details>
