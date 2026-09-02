# Tag 导航实验官方来源

访问日期统一为 `2026-09-03`。本目录只保存 URL、许可结论和中文释义，不复制外部全文。

## Obsidian

| 来源 | 已核对事实 | 许可与使用边界 |
|---|---|---|
| [Tags](https://obsidian.md/help/tags) | tag 可写在正文或 `tags` 属性中；可点击、使用 `tag:` 搜索、在 Tags view 中浏览；`/` 表示层级；tag 不区分大小写且不能含空格。 | Obsidian 保留其文档和应用内容权利；本研究只写中文释义。 |
| [Properties](https://obsidian.md/help/properties) | Properties 保存 YAML 结构化数据，支持 list、number、checkbox、date、tags 等类型；属性名在同一 note 中唯一；不支持嵌套属性、内建批量编辑和属性内 Markdown 渲染。 | 同上，不复制页面正文。 |
| [Search](https://obsidian.md/help/plugins/search) | `tag:#name` 只返回真实 tag，忽略代码块中的伪匹配；`[property:value]` 可查询属性；搜索只覆盖 note 与 Canvas 内容。 | 同上，不把搜索结果当机器层完整召回。 |
| [Canvas](https://obsidian.md/help/plugins/canvas) | Canvas 是 core plugin，使用 `.canvas` 文件；卡片可引用 note、附件和网页，边可带方向、标签和颜色；text card 不进入 backlinks。 | 同上；网页卡片可能触发网络访问，本原型不生成网页卡片。 |
| [Privacy](https://obsidian.md/privacy) | 桌面与移动端 vault 数据默认保存在本地；Sync、Publish、插件、主题和嵌入网页有各自的数据边界。 | 本原型不调用 Sync、Publish、插件市场或远程嵌入。 |
| [License overview](https://obsidian.md/license) | Obsidian 可免费用于个人、商业、非营利等用途，用户保留自己的内容；Obsidian 保留其应用、文字、图像和代码内容权利。 | 该结论不等同于文档开放许可；仓库不收录 Obsidian 文档正文。 |

## 开放格式与确定性存储

| 来源 | 已核对事实 | 许可 |
|---|---|---|
| [JSON Canvas 1.0](https://github.com/obsidianmd/jsoncanvas/blob/main/spec/1.0.md) | 顶层是 `nodes` 与 `edges`；节点类型为 text、file、link、group；通用节点必须有唯一 ID、位置和尺寸；边引用两端节点 ID。 | MIT。 |
| [JSON Canvas repository](https://github.com/obsidianmd/jsoncanvas) | JSON Canvas 面向可读、可移植和可扩展的本地文件；仓库与相关资源声明为 MIT。 | MIT。 |
| [SQLite UPSERT](https://www.sqlite.org/lang_upsert.html) | `ON CONFLICT` 只由 `PRIMARY KEY`、`UNIQUE` 或 unique index 触发，可用于幂等键去重。 | SQLite 代码与文档为 Public Domain。 |
| [SQLite transactions](https://www.sqlite.org/lang_transaction.html) | SQLite 的读写在事务中发生；显式 `BEGIN` 到 `COMMIT`/`ROLLBACK` 可把一批 assertion 写入作为一个原子单元。 | Public Domain。 |
| [SQLite copyright](https://www.sqlite.org/copyright.html) | SQLite 官方明确把代码和文档贡献到 Public Domain。 | Public Domain。 |
| [Git data model](https://git-scm.com/docs/gitdatamodel.html) | commit 对象固定树、父提交、作者、提交者与消息；对象创建后不可变，适合作为证据快照身份。 | Git 项目 GPL-2.0；本原型只调用 Git 输出的 commit ID，不复制其代码。 |

## 对实验设计的约束

1. Obsidian tag 适合做点击、搜索和层级浏览入口，但不是证据数据库；支持票、反对票、幂等键、来源独立性和状态原因保留在 SQLite。
2. Properties 适合 note 级结构化字段，但 CKB 当前人类页明确禁止 YAML frontmatter；本实验不把审计状态写进稳定页面。
3. Canvas 适合空间导航，不是 tag 状态存储；现有 Canvas 原型继续独立，兼容测试只证明二者没有修改彼此合同。
4. 运行期只读取本地 JSONL、SQLite 和 JSON；不访问网络，不保存对话原文、环境变量值、凭据或 source 正文。
