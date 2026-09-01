# QueryTermsTests

标签：#类型/代码

> `QueryTermsTests` 是 `tests/test_query_terms.py` 第 25-107 行定义的类，本页绑定该固定源码范围。 该类作为可执行验证入口，检查标识符 `QueryTermsTests` 所指的行为与失败边界。

## 什么时候需要修改

当被测行为、输入夹具、断言或失败条件变化时，应同步更新 `QueryTermsTests` 的说明。

## 在代码中的位置

[打开源码：tests/test_query_terms.py 第 25 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_query_terms.py:25:1)  `tests/test_query_terms.py:25-107`

## 相关代码

- 实现时会用到 [[retrieve]]。
- 实现时会用到 [[search_terms]]。
- 实现时会用到 [[search_terms 与 _split_camel 的协作实现]]。

## 谁会来到这里

- [[QueryTermsTests 等测试场景]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 12 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `QueryTermsTests.test_mechanical_fragments_do_not_enter_fts_terms` | `QueryTermsTests.test_...` 是第 26-34 行的函数，供所属页面定位实现。 |
| `QueryTermsTests.test_complete_phrase_and_content_grams_are_preserved` | `QueryTermsTests.test_...` 是第 36-40 行的函数，供所属页面定位实现。 |
| `QueryTermsTests.test_mixed_camel_identifier_order_is_fixed` | `QueryTermsTests.test_...` 是第 42-47 行的函数，供所属页面定位实现。 |
| `QueryTermsTests.test_path_api_and_digits_are_preserved` | `QueryTermsTests.test_...` 是第 49-57 行的函数，供所属页面定位实现。 |
| `QueryTermsTests.test_empty_punctuation_and_single_han_boundaries` | `QueryTermsTests.test_...` 是第 59-63 行的函数，供所属页面定位实现。 |
| `QueryTermsTests.test_query_terms_are_bounded_but_index_terms_are_complete` | `QueryTermsTests.test_...` 是第 65-72 行的函数，供所属页面定位实现。 |
| `QueryTermsTests.test_fts_limit_and_order_are_explicit` | `QueryTermsTests.test_...` 是第 74-81 行的函数，供所属页面定位实现。 |
| `QueryTermsTests.test_deduplication_keeps_best_priority` | `QueryTermsTests.test_...` 是第 83-86 行的函数，供所属页面定位实现。 |
| `QueryTermsTests.test_nfkc_is_deterministic` | `QueryTermsTests.test_...` 是第 88-89 行的函数，供所属页面定位实现。 |
| `QueryTermsTests.test_no_synonym_is_synthesized_without_overlap` | `QueryTermsTests.test_...` 是第 91-94 行的函数，供所属页面定位实现。 |
| `QueryTermsTests.test_compatibility_index_uses_the_same_rules_and_negative_boundary` | `QueryTermsTests.test_...` 是第 96-101 行的函数，供所属页面定位实现。 |
| `QueryTermsTests.test_negative_limits_fail_closed` | `QueryTermsTests.test_...` 是第 103-107 行的函数，供所属页面定位实现。 |

</details>
