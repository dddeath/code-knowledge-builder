# LspClient.start 与 _version_matches 的协作实现

标签：#类型/代码

> 该文件集中实现Pyright、TypeScript、clangd 与 csharp-ls 的真实 LSP 证据采集。 它是 Code Knowledge Builder 中承载Pyright、TypeScript、clangd 与 csharp-ls 的真实 LSP 证据采集的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当Pyright、TypeScript、clangd 与 csharp-ls 的真实 LSP 证据采集的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/providers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/providers.py:1:1)  `scripts/ckb_core/providers.py:1-596`

## 相关代码

- 实现时会用到 [[AutomationTest.event]]。
- 主要代码单元是 [[LspClient.start]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[execute]]。
- 实现时会用到 [[query_graph 与 _networkx_modules 的协作实现]]。
- 实现时会用到 [[render_integration 与 _looks_windows 的协作实现]]。
- 实现时会用到 [[retrieve_machine]]。
- 实现时会用到 [[run]]。
- 实现时会用到 [[run 与 CkbError 的协作实现]]。
- 实现时会用到 [[status]]。
- 实现时会用到 [[status 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[AutomationTest.event 等测试场景]] 会使用这里提供的行为。
- [[LspClient.start]] 会使用这里提供的行为。
- [[ingest_event 与 default_registry_path 的协作实现]] 会使用这里提供的行为。
- [[main（ckb 实现）]] 会使用这里提供的行为。
- [[main（fake_logseq 测试）]] 会使用这里提供的行为。
- [[parse_file]] 会使用这里提供的行为。
- [[remove]] 会使用这里提供的行为。
- [[remove 与 skill_root 的协作实现]] 会使用这里提供的行为。
- [[render_integration 与 _looks_windows 的协作实现]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[status 与 _replace_output_prefix 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.event 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[MigrationTest]]
- [[MigrationTest 等测试场景]]
- [[execute 等测试场景]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 19 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_version_matches` | 该附属代码负责Pyright、TypeScript、clangd 与 csharp-ls 的真实 LSP 证据采集，并把结果交给所属页面中的主流程使用。 |
| `private_runtime_root` | 该附属代码负责管理隔离离线运行时及其回滚，并把结果交给所属页面中的主流程使用。 |
| `_runtime_bin_candidates` | 该附属代码负责管理隔离离线运行时及其回滚，并把结果交给所属页面中的主流程使用。 |
| `resolve_executable` | 该附属代码负责Pyright、TypeScript、clangd 与 csharp-ls 的真实 LSP 证据采集，并把结果交给所属页面中的主流程使用。 |
| `doctor_report` | 该附属代码负责检查依赖版本和本地运行条件，并把结果交给所属页面中的主流程使用。 |
| `path_to_uri` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `uri_to_path` | 该附属代码负责构造职责关系图并提供职责群或路径查询，并把结果交给所属页面中的主流程使用。 |
| `LspClient` | 该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。 |
| `LspClient.__init__` | 该附属代码负责固定仓库来源并规划扫描、页面与审阅批次，并把结果交给所属页面中的主流程使用。 |
| `LspClient._read_stdout` | 该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。 |
| `LspClient._read_stderr` | 该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。 |
| `LspClient.send` | 该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。 |
| `LspClient.notify` | 该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。 |
| `LspClient.request` | 该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。 |
| `LspClient.stop` | 该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。 |
| `_provider_spec` | 该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。 |
| `_fallback_flags` | 该附属代码负责Pyright、TypeScript、clangd 与 csharp-ls 的真实 LSP 证据采集，并把结果交给所属页面中的主流程使用。 |
| `_flatten_symbols` | 该附属代码负责Pyright、TypeScript、clangd 与 csharp-ls 的真实 LSP 证据采集，并把结果交给所属页面中的主流程使用。 |
| `collect_semantics` | 该附属代码负责调用语言提供器并整理定义、符号与诊断证据，并把结果交给所属页面中的主流程使用。 |

</details>
