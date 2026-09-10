# project_output_contract

标签：#类型/代码

> 该函数检查目标 vault 是否安装配套插件，已安装时生成输出绑定契约并登记投影归属，未安装时删除旧契约并撤销归属，返回不需要契约的状态。 它让输出契约与实际目标 vault 的插件安装状态保持一致，避免把未安装插件的 vault 当作契约消费者；契约内容由统一的预期契约函数生成。

## 什么时候需要修改

插件安装判定、契约字段或投影归属登记方式变化时修改此函数，并分别核对安装和卸载状态下的契约文件与归属清单。

## 在代码中的位置

[打开源码：scripts/ckb_core/output_contract.py 第 76 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/output_contract.py:76:1)  `scripts/ckb_core/output_contract.py:76-97`

## 相关代码

- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[deploy_obsidian_plugin_to_vault 与 default_obsidian_plugin_registry 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[project_output_contract 与 _default_ckb 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- 与 [[deploy_obsidian_plugin_to_vault 与 default_obsidian_plugin_registry 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[project_output_contract 与 _default_ckb 的协作实现]] 汇总了本页。
- 与 [[sync_human_layer]] 存在待核验的词法关联；是否调用或依赖需查看源码。
