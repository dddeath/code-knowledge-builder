# run_keyword_provider 与 KeywordProviderConfig 的协作实现

标签：#类型/代码

> `scripts/ckb_core/keyword_fallback.py` 页面汇总该文件在固定提交中的职责、入口与可审阅源码范围。 负责在确定性词项不足时执行受预算约束的 LLM 关键词备选慢路径。

## 什么时候需要修改

当 `scripts/ckb_core/keyword_fallback.py` 的职责、命令入口、数据契约或主要符号变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/keyword_fallback.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/keyword_fallback.py:1:1)  `scripts/ckb_core/keyword_fallback.py:1-633`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[normalize]]。
- 主要代码单元是 [[run_keyword_provider]]。

## 谁会来到这里

- [[KeywordFallbackRetrievalWiringTests]] 会使用这里提供的行为。
- [[KeywordFallbackRetrievalWiringTests 等测试场景]] 会使用这里提供的行为。
- [[keyword_provider_config]] 会使用这里提供的行为。
- [[keyword_provider_config 与 parser 的协作实现]] 会使用这里提供的行为。
- [[maintenance_check]] 会使用这里提供的行为。
- [[retrieve_machine]] 会使用这里提供的行为。
- [[run_keyword_benchmark]] 会使用这里提供的行为。
- [[run_keyword_benchmark 与 _text_list 的协作实现]] 会使用这里提供的行为。
- [[run_keyword_provider]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。
- [[serve_stdio 与 _write_line 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[CodeKnowledgeBuilderTests 等测试场景]]
- [[KeywordFallbackRetrievalWiringTests]]
- [[KeywordFallbackRetrievalWiringTests 等测试场景]]
- [[MigrationTest]]

> 还有更远的协作细节保存在机器审计层；遇到具体任务时可用图查询继续缩小范围。

## 内部细节

<details><summary>查看本页收纳的 23 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `KeywordProviderConfig` | `KeywordProviderConfig` 是第 81-90 行的类，供所属页面定位实现。 |
| `KeywordFallbackOptions` | `KeywordFallbackOptions` 是第 94-99 行的类，供所属页面定位实现。 |
| `keyword_input_hash` | `keyword_input_hash` 是第 102-103 行的函数，供所属页面定位实现。 |
| `keyword_request_id` | `keyword_request_id` 是第 106-107 行的函数，供所属页面定位实现。 |
| `keyword_cache_key` | `keyword_cache_key` 是第 110-120 行的函数，供所属页面定位实现。 |
| `canonical_keyword_request` | `canonical_keyword_req...` 是第 123-140 行的函数，供所属页面定位实现。 |
| `_machine_token` | `_machine_token` 是第 143-146 行的函数，供所属页面定位实现。 |
| `validate_provider_config` | `validate_provider_config` 是第 149-161 行的函数，供所属页面定位实现。 |
| `_bounded_strings` | `_bounded_strings` 是第 164-193 行的函数，供所属页面定位实现。 |
| `_usage` | `_usage` 是第 196-216 行的函数，供所属页面定位实现。 |
| `validate_provider_response` | `validate_provider_res...` 是第 219-300 行的函数，供所属页面定位实现。 |
| `parse_provider_json` | `parse_provider_json` 是第 303-307 行的函数，供所属页面定位实现。 |
| `_failure` | `_failure` 是第 310-323 行的函数，供所属页面定位实现。 |
| `keyword_cache_path` | `keyword_cache_path` 是第 326-327 行的函数，供所属页面定位实现。 |
| `_cache_path` | `_cache_path` 是第 330-331 行的函数，供所属页面定位实现。 |
| `_cache_record` | `_cache_record` 是第 334-346 行的函数，供所属页面定位实现。 |
| `_read_cache` | `_read_cache` 是第 349-366 行的函数，供所属页面定位实现。 |
| `_write_cache` | `_write_cache` 是第 369-373 行的函数，供所属页面定位实现。 |
| `_transient` | `_transient` 是第 376-377 行的函数，供所属页面定位实现。 |
| `audit_keyword_cache` | `audit_keyword_cache` 是第 464-507 行的函数，供所属页面定位实现。 |
| `write_keyword_fallback_record` | `write_keyword_fallbac...` 是第 510-549 行的函数，供所属页面定位实现。 |
| `audit_keyword_fallback` | `audit_keyword_fallback` 是第 552-620 行的函数，供所属页面定位实现。 |
| `unique_casefold` | `unique_casefold` 是第 623-632 行的函数，供所属页面定位实现。 |

</details>
