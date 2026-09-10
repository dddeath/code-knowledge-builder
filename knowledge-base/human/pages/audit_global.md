# audit_global

标签：#类型/代码

> 重新生成知识库各层投影，并检查固定来源、审阅结果、页面内容和检索数据的一致性。 汇总构建完成前的检查结果；运行时会清除完成标记并写入投影，检查通过后仍需 finalize 才能完成，因此不是只读状态查询。

## 什么时候需要修改

调整构建完成条件、迁移来源保存、人类页面生成或双索引一致性要求时修改。

## 在代码中的位置

[打开源码：scripts/ckb_core/pipeline.py 第 3042 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:3042:1)  `scripts/ckb_core/pipeline.py:3042-3355`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_agent_protocol]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_agent_protocol 与 _default_python 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[audit_global 与 _replace_output_prefix 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_agent_index 与 _tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[deploy_obsidian_plugin_to_vault 与 default_obsidian_plugin_registry 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ingest_web_reference 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[migrate_output 与 _entity_key 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[module_name 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[normalize_page_config]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[normalize_page_config 与 _merge_known 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[preflight 与 git 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[project_graphify]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[project_graphify 与 _networkx_modules 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note 与 page_tag 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[sync_human_layer 与 _source_manifest 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[audit_global 与 _replace_output_prefix 的协作实现]] 汇总了本页。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
