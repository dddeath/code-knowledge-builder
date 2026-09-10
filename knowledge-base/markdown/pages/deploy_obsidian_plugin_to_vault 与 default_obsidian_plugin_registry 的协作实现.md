# deploy_obsidian_plugin_to_vault 与 default_obsidian_plugin_registry 的协作实现

标签：#类型/代码

> 管理独立 Obsidian 插件包的注册、指定库部署、状态检查与卸载。 注册缓存和实际安装分别判定；升级只替换声明包文件并保存失败恢复副本，保留用户设置和未知文件，显式卸载则删除插件目录。

## 什么时候需要修改

需要变更包文件清单、注册版本校验、升级保留规则或部署与输出契约的绑定时修改。

## 在代码中的位置

[打开源码：scripts/ckb_core/obsidian_plugin.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian_plugin.py:1:1)  `scripts/ckb_core/obsidian_plugin.py:1-291`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[deploy_obsidian_plugin_to_vault]]。
- 与 [[project_output_contract]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[project_output_contract 与 _default_ckb 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[BatchProjectError 与 ProtocolRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_obsidian]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_obsidian 与 prepare_vault 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[deploy_obsidian_plugin_to_vault]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[project_output_contract]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[project_output_contract 与 _default_ckb 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 10 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `default_obsidian_plugin_registry` | 返回用户目录下默认的 Obsidian 插件注册文件路径。 |
| `obsidian_plugin_installation` | 检查指定库的包文件与启用列表，分别报告安装和启用状态。 |
| `_payload_from_package` | 接受插件目录或校验 ZIP，从归档中仅提取声明的必需及可选文件。 |
| `_validate_payload` | 检查必需包文件、插件标识和非空版本，返回有效清单。 |
| `register_obsidian_plugin` | 验证插件包后复制声明文件到版本缓存，并写出全局注册记录。 |
| `_registered_payload` | 读取已注册包并校验载荷及版本一致性，缺失注册或版本漂移时报错。 |
| `deploy_obsidian_plugin` | 向知识库人类目录部署插件，投影输出契约并记录部署结果。 |
| `obsidian_plugin_status` | 汇总注册与部署记录，检查必需文件缺失漂移并审计输出契约。 |
| `remove_obsidian_plugin` | 卸载指定库中的插件目录，移除启用项、部署记录和输出契约。 |
| `deploy_registered_plugin_if_available` | 仅在存在默认注册包时部署插件，可同时投影指定知识库的输出契约。 |

</details>
