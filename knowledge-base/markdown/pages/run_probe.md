# run_probe

标签：#类型/代码

> `run_probe` 在没有项目指令的隔离仓库中验证 Skill 未加载与精确加载两条路径，并执行 brief、pack、窄读、新鲜度、维护和 CLI fallback。 它提供跨 Harness 契约的真实运行证据，并检查 stdio 生命周期对象最终归零。

## 什么时候需要修改

当 Skill 激活、检索传输、OUTPUT 发现或维护触发规则变化时，应更新本探针和冻结基线。

## 在代码中的位置

[打开源码：tests/harness_retrieval_contract_probe.py 第 170 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/harness_retrieval_contract_probe.py:170:1)  `tests/harness_retrieval_contract_probe.py:170-496`

## 相关代码

- 实现时会用到 [[AutomationTest.register]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[_Transport.close 与 _StartGate 的协作实现]]。
- 实现时会用到 [[check_fact_freshness]]。
- 实现时会用到 [[ingest_event]]。
- 实现时会用到 [[ingest_event 与 default_registry_path 的协作实现]]。
- 实现时会用到 [[run_probe 等测试场景]]。
- 实现时会用到 [[web_input_adapter_contract 与 ReferenceInputRequest 的协作实现]]。

## 谁会来到这里

- [[ingest_event]] 关联到这里的验证场景。
- [[run_probe 等测试场景]] 汇总了本页。
- [[web_input_adapter_contract 与 ReferenceInputRequest 的协作实现]] 关联到这里的验证场景。

## 相关测试

- [[run_probe 等测试场景]]

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `run_probe.cleanup_probe_sessions` | 该函数完成无项目指令检索探针中的隔离准备、执行或证据收集。 |

</details>
