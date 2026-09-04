# run_probe 等测试场景

标签：#类型/代码

> 该文件实现无项目 Agent 指令条件下的 CKB Skill 检索闭环探针。 该文件承载 `tests/harness_retrieval_contract_probe.py` 所属能力的实现或测试入口。

## 什么时候需要修改

当 `tests/harness_retrieval_contract_probe.py` 的职责或可见行为变化时，应更新本页并重跑相关测试。

## 在代码中的位置

[打开源码：tests/harness_retrieval_contract_probe.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/harness_retrieval_contract_probe.py:1:1)  `tests/harness_retrieval_contract_probe.py:1-519`

## 相关代码

- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[SourceLinkRenderer.uri]]。
- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。
- 实现时会用到 [[parser]]。
- 主要代码单元是 [[run_probe]]。

## 谁会来到这里

- [[ingest_event]] 关联到这里的验证场景。
- [[run_probe]] 关联到这里的验证场景。
- 可从 [[tests 职责导览]] 进入本页。
- [[web_input_adapter_contract 与 ReferenceInputRequest 的协作实现]] 关联到这里的验证场景。

## 相关测试

- [[run_probe]]

## 内部细节

<details><summary>查看本页收纳的 10 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_git` | `_git` 在 `tests/harness_retrieval_contract_probe.py` 中完成其名称所示的局部辅助或验证步骤。 |
| `_run_ckb` | `_run_ckb` 在 `tests/harness_retrieval_contract_probe.py` 中完成其名称所示的局部辅助或验证步骤。 |
| `_assert_equal` | 该函数完成无项目指令检索探针中的隔离准备、执行或证据收集。 |
| `_assert` | `_assert` 在 `tests/harness_retrieval_contract_probe.py` 中完成其名称所示的局部辅助或验证步骤。 |
| `_file_evidence` | 该函数完成无项目指令检索探针中的隔离准备、执行或证据收集。 |
| `_activation_source` | 该函数完成无项目指令检索探针中的隔离准备、执行或证据收集。 |
| `_environment_value` | 该函数完成无项目指令检索探针中的隔离准备、执行或证据收集。 |
| `_make_fixture_repo` | 该函数完成无项目指令检索探针中的隔离准备、执行或证据收集。 |
| `_fallback_wrapper` | 该函数完成无项目指令检索探针中的隔离准备、执行或证据收集。 |
| `main` | `main` 在 `tests/harness_retrieval_contract_probe.py` 中完成其名称所示的局部辅助或验证步骤。 |

</details>
