# ensure_local_openers 与 default_openers 的协作实现

标签：#类型/代码

> 该文件集中实现VS Code、file 与自定义模板源码 URI 的生成和核对。 它是 Code Knowledge Builder 中承载VS Code、file 与自定义模板源码 URI 的生成和核对的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当VS Code、file 与自定义模板源码 URI 的生成和核对的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-146`

## 相关代码

- 主要代码单元是 [[ensure_local_openers]]。
- 实现时会用到 [[render_integration 与 _looks_windows 的协作实现]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。

## 谁会来到这里

- [[ensure_local_openers]] 会使用这里提供的行为。
- [[record_note]] 会使用这里提供的行为。
- [[record_note 与 page_tag 的协作实现]] 会使用这里提供的行为。
- [[retrieve 与 _tokens 的协作实现]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]

## 内部细节

<details><summary>查看本页收纳的 8 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `default_openers` | 该附属代码负责生成并核对可直接打开源码位置的 URI，并把结果交给所属页面中的主流程使用。 |
| `validate_local_openers` | 该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。 |
| `update_local_openers` | 该附属代码负责生成并核对可直接打开源码位置的 URI，并把结果交给所属页面中的主流程使用。 |
| `source_absolute_path` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `source_uri` | 该附属代码负责生成并核对可直接打开源码位置的 URI，并把结果交给所属页面中的主流程使用。 |
| `source_markdown_link` | 该附属代码负责VS Code、file 与自定义模板源码 URI 的生成和核对，并把结果交给所属页面中的主流程使用。 |
| `obsidian_open_uri` | 该附属代码负责维护 Obsidian vault 配置和生成文件所有权，并把结果交给所属页面中的主流程使用。 |
| `audit_source_uri` | 该附属代码负责执行确定性完整性与来源真实性检查，并把结果交给所属页面中的主流程使用。 |

</details>
