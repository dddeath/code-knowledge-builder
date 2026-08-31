from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ckb_core.machine_knowledge import _fts_query  # noqa: E402
from ckb_core.query_terms import (  # noqa: E402
    DEFAULT_FTS_TERM_LIMIT,
    MAX_QUERY_TERMS,
    explicit_anchors,
    fts_query_terms,
    index_terms,
    search_terms,
)


class QueryTermsTests(unittest.TestCase):
    def test_mechanical_fragments_do_not_enter_fts_terms(self) -> None:
        for text, fragment in (
            ("打包不满足", "包不满"),
            ("是否会回", "否会回"),
            ("回的检索", "回的检"),
        ):
            self.assertNotIn(fragment, fts_query_terms(text))
            self.assertNotIn(fragment, search_terms(text))
            self.assertIn(text, search_terms(text))

    def test_complete_phrase_and_content_grams_are_preserved(self) -> None:
        terms = search_terms("订单服务修改")
        self.assertEqual(terms[0], "订单服务修改")
        self.assertIn("订单服", terms)
        self.assertIn("服务", terms)

    def test_mixed_camel_identifier_order_is_fixed(self) -> None:
        self.assertEqual(
            search_terms("OrderService 服务修改"),
            ["orderservice", "服务修改", "service", "order", "务修改", "服务修", "修改", "务修", "服务"],
        )
        self.assertEqual(explicit_anchors("OrderService 服务修改"), ["orderservice"])

    def test_path_api_and_digits_are_preserved(self) -> None:
        terms = search_terms(r"scripts/ckb_core/machine_knowledge.py retrieveMachine FTS5")
        self.assertEqual(terms[0], "scripts/ckb_core/machine_knowledge.py")
        self.assertIn("retrievemachine", terms)
        self.assertIn("retrieve", terms)
        self.assertIn("machine", terms)
        self.assertIn("fts5", terms)
        self.assertEqual(search_terms("１２３"), ["123"])
        self.assertEqual(search_terms("7"), [])

    def test_empty_punctuation_and_single_han_boundaries(self) -> None:
        self.assertEqual(search_terms(""), [])
        self.assertEqual(search_terms("！？..."), [])
        self.assertEqual(search_terms("中"), ["中"])
        self.assertIsNone(_fts_query("中"))

    def test_query_terms_are_bounded_but_index_terms_are_complete(self) -> None:
        text = "".join(chr(0x4E00 + index) for index in range(120))
        query = search_terms(text)
        indexed = index_terms(text)
        self.assertEqual(len(query), MAX_QUERY_TERMS)
        self.assertGreater(len(indexed), MAX_QUERY_TERMS)
        self.assertEqual(query, indexed[:MAX_QUERY_TERMS])
        self.assertEqual(query[0], text)

    def test_fts_limit_and_order_are_explicit(self) -> None:
        values = fts_query_terms("订单服务修改")
        self.assertEqual(values, ["订单服务修改", "务修改", "单服务", "服务修", "订单服"])
        self.assertLessEqual(len(values), DEFAULT_FTS_TERM_LIMIT)
        self.assertEqual(
            _fts_query("订单服务修改"),
            '"订单服务修改" OR "务修改" OR "单服务" OR "服务修" OR "订单服"',
        )

    def test_deduplication_keeps_best_priority(self) -> None:
        terms = search_terms("OrderService OrderService")
        self.assertEqual(terms.count("orderservice"), 1)
        self.assertLess(terms.index("orderservice"), terms.index("service"))

    def test_nfkc_is_deterministic(self) -> None:
        self.assertEqual(search_terms("ＡＰＩ＿Client"), search_terms("API_Client"))

    def test_no_synonym_is_synthesized_without_overlap(self) -> None:
        terms = search_terms("落盘")
        self.assertNotIn("保存", terms)
        self.assertNotIn("写入", terms)

    def test_negative_limits_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            search_terms("查询", -1)
        with self.assertRaises(ValueError):
            fts_query_terms("查询", -1)


if __name__ == "__main__":
    unittest.main()
