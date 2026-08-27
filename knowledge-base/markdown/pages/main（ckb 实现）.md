# main（ckb 实现）

标签：#类型/代码

> `main` 解析命令并把请求分派到对应的确定性实现。 它将 `automation activate` 路由到 session Skill 激活逻辑，并继续统一输出机器可读 JSON 与约定退出码。

## 什么时候需要修改

当子命令分派、激活返回值、错误传播或退出状态变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 331 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:331:1)  `scripts/ckb.py:331-483`

## 相关代码

- 实现时会用到 [[AutomationTest.event]]。
- 实现时会用到 [[AutomationTest.event 等测试场景]]。
- 实现时会用到 [[LspClient.start]]。
- 实现时会用到 [[LspClient.start 与 _version_matches 的协作实现]]。
- 实现时会用到 [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]]。
- 实现时会用到 [[audit_migration]]。
- 实现时会用到 [[audit_migration 与 _entity_key 的协作实现]]。
- 实现时会用到 [[ingest_event]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[load_page_config]]。
- 实现时会用到 [[load_page_config 与 _merge_known 的协作实现]]。
- 实现时会用到 [[package_showcase]]。
- 实现时会用到 [[parser]]。
- 实现时会用到 [[query_graph]]。
- 实现时会用到 [[query_graph 与 _networkx_modules 的协作实现]]。
- 实现时会用到 [[record_note]]。
- 实现时会用到 [[record_note 与 page_tag 的协作实现]]。
- 实现时会用到 [[remove 与 skill_root 的协作实现]]。
- 实现时会用到 [[retrieve_machine 与 estimated_tokens 的协作实现]]。
- 实现时会用到 [[status 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]] 汇总了本页。

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。
