# doctor_report 与 _version_matches 的协作实现

标签：#类型/代码

> 文件 `scripts/ckb_core/providers.py`负责启动并约束语言服务器，收集 Python、JavaScript、C/C++ 和 C# 的语义证据。 它属于精确语义与无编译数据库时有界近似之间的提供器层，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当运行时定位、LSP 协议、编译参数、诊断分级或进程释放变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/providers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/providers.py:1:1)  `scripts/ckb_core/providers.py:1-638`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[doctor_report]]。

## 谁会来到这里

- 与 [[deploy 与 skill_root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[doctor_report]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 20 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_version_matches` | `_version_matches` 完成语言服务器语义采集中的一个明确步骤。 |
| `private_runtime_root` | `private_runtime_root` 完成语言服务器语义采集中的一个明确步骤。 |
| `_runtime_bin_candidates` | `_runtime_bin_candidates` 完成语言服务器语义采集中的一个明确步骤。 |
| `resolve_executable` | `resolve_executable` 完成语言服务器语义采集中的一个明确步骤。 |
| `path_to_uri` | `path_to_uri` 完成语言服务器语义采集中的一个明确步骤。 |
| `uri_to_path` | `uri_to_path` 完成语言服务器语义采集中的一个明确步骤。 |
| `LspClient` | `__init__` 完成语言服务器语义采集中的一个明确步骤。 |
| `LspClient.__init__` | `__init__` 完成语言服务器语义采集中的一个明确步骤。 |
| `LspClient.start` | `start` 完成语言服务器语义采集中的一个明确步骤。 |
| `LspClient._read_stdout` | `_read_stdout` 读取并判定语言服务器语义采集所需的数据或状态。 |
| `LspClient._read_stderr` | `_read_stderr` 读取并判定语言服务器语义采集所需的数据或状态。 |
| `LspClient.send` | `send` 完成语言服务器语义采集中的一个明确步骤。 |
| `LspClient.notify` | `notify` 完成语言服务器语义采集中的一个明确步骤。 |
| `LspClient.request` | `request` 完成语言服务器语义采集中的一个明确步骤。 |
| `LspClient.stop` | `stop` 受控释放或回滚语言服务器语义采集所需的数据或状态。 |
| `_provider_spec` | `_provider_spec` 完成语言服务器语义采集中的一个明确步骤。 |
| `_fallback_flags` | `_fallback_flags` 完成语言服务器语义采集中的一个明确步骤。 |
| `_flatten_symbols` | `_flatten_symbols` 完成语言服务器语义采集中的一个明确步骤。 |
| `_provider_status` | `_provider_status` 完成语言服务器语义采集中的一个明确步骤。 |
| `collect_semantics` | `collect_semantics` 完成语言服务器语义采集中的一个明确步骤。 |

</details>
